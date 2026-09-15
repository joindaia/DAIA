"""Builder checks only; no VM, provider, login or fixture workload runs."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest


SCRIPTS = Path(__file__).parents[1] / 'scripts'
spec = importlib.util.spec_from_file_location(
    'prepare_preboot_fixture', SCRIPTS / 'prepare_preboot_fixture.py')
builder = importlib.util.module_from_spec(spec)
sys.path.insert(0, str(SCRIPTS))
try:
    spec.loader.exec_module(builder)
finally:
    sys.path.pop(0)


def source(tmp_path, monkeypatch, code='import pathlib,subprocess,hashlib,json,os\nimport socket,copy\n',
           task=False):
    root = tmp_path / 'source'
    root.mkdir()
    seed = root / 'seed.iso'
    seed.write_bytes(b'approved-seed')
    config = {'nonce': 'a' * 32, 'model': 'gpt-5.3-codex-spark',
              'seed_sha256': hashlib.sha256(seed.read_bytes()).hexdigest(),
              'companion_present': False, 'companion_sha256': None, 'task': 'preserved'}
    if task:
        document = {'objective': 'preserved evidence', 'baseline_commit': 'a' * 40,
                    'source': {'path': 'src/example.py', 'start_line': 1, 'text': 'x = 1\n'}}
        raw = json.dumps(document, sort_keys=True).encode()
        (root / 'task.json').write_bytes(raw)
        config['task_sha256'] = hashlib.sha256(raw).hexdigest()
    (root / 'config.json').write_text(json.dumps(config))
    data = {'write_files': [{'path': '/tmp/probe.py', 'content': code, 'permissions': '0444'}],
            'runcmd': [['python3', '/tmp/probe.py']]}
    user = b'#cloud-config\n' + json.dumps(data).encode()
    (root / 'user-data').write_bytes(user)
    for name in ('meta-data', 'network-config'):
        (root / name).write_text(name)
    (root / 'probe.py').write_text('compatibility')

    def extracted(argv, **kwargs):
        return user if argv[-1] == '/user-data' else (root / argv[-1][1:]).read_bytes()

    monkeypatch.setattr(builder.subprocess, 'check_output', extracted)
    return root, config


def native(tmp_path, monkeypatch):
    root = tmp_path / 'native'
    root.mkdir()
    pins = {}
    for name in builder.NATIVE_PINS:
        path = root / name
        path.write_bytes(name.encode())
        pins[name] = builder.digest(path)
    monkeypatch.setattr(builder, 'NATIVE_PINS', pins)
    return root


def test_derives_bound_cloud_config_and_barrier(tmp_path, monkeypatch):
    old, config = source(tmp_path, monkeypatch, task=True)
    supplied = native(tmp_path, monkeypatch)
    calls = []

    def run(argv, **kwargs):
        calls.append((argv, kwargs))
        Path(argv[argv.index('-output') + 1]).write_bytes(b'new-seed')

    monkeypatch.setattr(builder.subprocess, 'run', run)
    result = builder.prepare(old, supplied, tmp_path / 'output', 'iso-builder', 'isoinfo')
    cloud = json.loads((tmp_path / 'output/user-data').read_text().split('\n', 1)[1])
    probe = next(x['content'] for x in cloud['write_files'] if x['path'] == '/tmp/probe.py')
    helper = next(x for x in cloud['write_files'] if x['path'] == '/opt/fresh_host_start.py')
    assert result['nonce'] == config['nonce'] and result['model'] == config['model']
    assert result['task'] == 'preserved'
    assert probe.index("with open('/dev/virtio-ports/daia.start'") < probe.index('import socket,copy')
    assert "sys.path.insert(0, '/opt')" in probe and helper['permissions'] == '0444'
    assert calls[0][0][-2:] == [str(supplied / 'codex'), str(supplied / 'bwrap')]
    assert calls[0][1]['timeout'] == 30
    assert (tmp_path / 'output/probe.py').read_text() == 'compatibility'
    assert (tmp_path / 'output/task.json').read_bytes() == (old / 'task.json').read_bytes()
    assert result['seed_sha256'] == hashlib.sha256(b'new-seed').hexdigest()


@pytest.mark.parametrize('name', ['user-data', 'meta-data', 'network-config'])
def test_refuses_source_sibling_not_bound_to_approved_iso(tmp_path, monkeypatch, name):
    old, _ = source(tmp_path, monkeypatch)
    supplied = native(tmp_path, monkeypatch)
    monkeypatch.setattr(
        builder.subprocess, 'check_output',
        lambda argv, **kwargs: b'changed' if argv[-1] == '/' + name
        else (old / argv[-1][1:]).read_bytes())
    with pytest.raises(ValueError, match='Approved seed ' + name + ' mismatch'):
        builder.prepare(old, supplied, tmp_path / 'output', 'iso-builder', 'isoinfo')
    assert not (tmp_path / 'output').exists()


def test_refuses_ambiguous_marker(tmp_path, monkeypatch):
    old, _ = source(tmp_path, monkeypatch, 'import socket,copy\nimport socket,copy\n')
    supplied = native(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match='Unique pre-network marker required'):
        builder.prepare(old, supplied, tmp_path / 'output', 'iso-builder', 'isoinfo')


def test_refuses_existing_helper(tmp_path, monkeypatch):
    old, _ = source(tmp_path, monkeypatch)
    supplied = native(tmp_path, monkeypatch)
    cloud = json.loads((old / 'user-data').read_text().split('\n', 1)[1])
    cloud['write_files'].append({'path': builder.HELPER_PATH, 'content': 'old helper'})
    user = b'#cloud-config\n' + json.dumps(cloud).encode()
    (old / 'user-data').write_bytes(user)
    monkeypatch.setattr(
        builder.subprocess, 'check_output',
        lambda argv, **kwargs: user if argv[-1] == '/user-data'
        else (old / argv[-1][1:]).read_bytes())
    with pytest.raises(ValueError, match='Unexpected preboot helper'):
        builder.prepare(old, supplied, tmp_path / 'output', 'iso-builder', 'isoinfo')


def test_refuses_existing_output(tmp_path, monkeypatch):
    old, _ = source(tmp_path, monkeypatch)
    supplied = native(tmp_path, monkeypatch)
    output = tmp_path / 'output'
    output.mkdir()
    with pytest.raises(ValueError, match='New output'):
        builder.prepare(old, supplied, output, 'iso-builder', 'isoinfo')
