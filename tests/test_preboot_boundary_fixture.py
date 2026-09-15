"""Boundary-seed builder checks only; no guest, provider, or canary access runs."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest


SCRIPTS = Path(__file__).parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
try:
    spec = importlib.util.spec_from_file_location(
        'prepare_preboot_boundary_fixture', SCRIPTS / 'prepare_preboot_boundary_fixture.py')
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
finally:
    sys.path.pop(0)


def approved_data():
    return {'write_files': [
        {'path': '/tmp/probe.py', 'content': (
            "print('DAIA_PREBOOT probe_entered', flush=True)\n"
            "print('DAIA_PREBOOT native_ready', flush=True)\n"
            "import socket,copy\n"), 'permissions': '0444'}]}


def test_derives_boundary_seed_before_ready_without_reading_canary(tmp_path, monkeypatch):
    source = tmp_path / 'source'; source.mkdir()
    (source / 'probe.py').write_text('controller compatibility')
    config = {'nonce': 'a' * 32, 'model': 'gpt-5.3-codex-spark', 'task': 'preserved'}
    monkeypatch.setattr(builder, 'canary_path', lambda _: Path('/run/daia-boundary-canary-' + 'b' * 32))
    monkeypatch.setattr(builder.preboot, 'cloud_data',
                        lambda *_: (config, approved_data(), {'meta-data': b'meta', 'network-config': b'network'}))
    native = tmp_path / 'native'; native.mkdir()
    supplied = native / 'codex'; supplied.write_bytes(b'codex')
    monkeypatch.setattr(builder.preboot, 'native_inputs', lambda *_: [supplied])
    calls = []
    def run(argv, **kwargs):
        calls.append((argv, kwargs))
        Path(argv[argv.index('-output') + 1]).write_bytes(b'boundary-seed')
    monkeypatch.setattr(builder.subprocess, 'run', run)

    result = builder.prepare(source, native, tmp_path / 'output', 'iso-builder', 'isoinfo',
                             '/run/daia-boundary-canary-' + 'b' * 32)
    cloud = json.loads((tmp_path / 'output/user-data').read_text().split('\n', 1)[1])
    code = cloud['write_files'][0]['content']
    assert code.index('boundary_host_file_denied=true') < code.index("DAIA_PREBOOT native_ready")
    assert 'from pathlib import Path' in code and "os.open(path" in code and '.read(' not in code
    assert '/var/lib/daia-provider/codex/auth.json' in code
    assert result['nonce'] == config['nonce'] and result['task'] == 'preserved'
    assert result['seed_sha256'] == hashlib.sha256(b'boundary-seed').hexdigest()
    assert (tmp_path / 'output/seed.iso').stat().st_mode & 0o777 == 0o444
    assert calls[0][1]['timeout'] == 30 and calls[0][0][-1] == str(supplied)
    assert (tmp_path / 'output/probe.py').read_text() == 'controller compatibility'


def test_refuses_nonrandom_or_nonunique_inputs(tmp_path, monkeypatch):
    monkeypatch.setattr(builder.preboot, 'regular', lambda path: Path(path))
    with pytest.raises(ValueError, match='random'):
        builder.canary_path('/run/not-a-canary')
    data = approved_data()
    data['write_files'][0]['content'] = 'no readiness marker\n'
    with pytest.raises(ValueError, match='Unique preboot'):
        builder.inject(data, Path('/run/daia-boundary-canary-' + 'a' * 32))


def test_refuses_existing_output(tmp_path, monkeypatch):
    output = tmp_path / 'output'; output.mkdir()
    monkeypatch.setattr(builder, 'canary_path', lambda _: Path('/run/daia-boundary-canary-' + 'a' * 32))
    monkeypatch.setattr(builder.preboot, 'cloud_data',
                        lambda *_: ({}, approved_data(), {'meta-data': b'', 'network-config': b''}))
    monkeypatch.setattr(builder.preboot, 'native_inputs', lambda *_: [])
    with pytest.raises(ValueError, match='New output'):
        builder.prepare(tmp_path, tmp_path, output, 'iso-builder', 'isoinfo',
                        '/run/daia-boundary-canary-' + 'a' * 32)


def test_network_probe_is_fixed_and_requires_explicit_test_profile():
    data = approved_data()
    builder.inject(data, Path('/run/daia-boundary-canary-' + 'b'*32))
    assert '38443' not in data['write_files'][0]['content']
    data = approved_data()
    builder.inject(data, Path('/run/daia-boundary-canary-' + 'b'*32), True)
    code = data['write_files'][0]['content']
    assert "('10.0.2.2', 38443), timeout=3" in code
    assert code.index('boundary_direct_tcp_denied=true') < code.index('DAIA_PREBOOT native_ready')
    compile(code, 'fixture', 'exec')

@pytest.mark.parametrize('unexpected_tool', [False, True])
def test_discovery_checks_actual_response_catalog_without_work(monkeypatch, unexpected_tool):
    import io
    import socket
    tools = [{'name': name} for name in ('heartbeat', 'submit_result')]
    if unexpected_tool:
        tools.append({'name': 'request_work'})
    replies = [{'result': {}}, {'result': {'tools': tools}},
               {'result': {'resources': []}}, {'result': {'resourceTemplates': []}},
               {'result': {'prompts': []}}, {'error': {'code': -32602}},
               {'error': {'code': -32601}}]
    incoming = io.BytesIO(b''.join((json.dumps(dict(reply, id=i))+'\n').encode()
                                  for i, reply in enumerate(replies, 1)))
    sent = []
    class Peer:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def settimeout(self, value): assert value == 5
        def makefile(self, *args, **kwargs): return self
        def readline(self, limit): return incoming.readline(limit)
        def write(self, value): sent.append(json.loads(value))
        def close(self): pass
    def connect(address, timeout):
        assert address == ('10.0.2.100', 3128) and timeout == 5
        return Peer()
    monkeypatch.setattr(socket, 'create_connection', connect)
    if unexpected_tool:
        with pytest.raises(AssertionError):
            exec(builder.assignment_discovery(), {})
    else:
        exec(builder.assignment_discovery(), {})
        assert len(sent) == 8
        assert all(message['method'] != 'tools/call' for message in sent)
