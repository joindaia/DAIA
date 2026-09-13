"""Offline preparation must preserve exact bytes and never run a candidate."""
import hashlib
import json
from pathlib import Path
import runpy
import pytest

prepare = runpy.run_path(str(Path(__file__).parents[1] /
    'scripts/prepare_version_evaluator.py'))['prepare']


@pytest.mark.parametrize("task", ["version", "outcome-summary"])
def test_exact_candidate_is_data_only(tmp_path, monkeypatch, task):
    sentinel = tmp_path / 'executed'
    source = f"from pathlib import Path; Path({str(sentinel)!r}).touch()\n"
    candidate = tmp_path / 'candidate.json'
    candidate.write_text(json.dumps(source))
    output = tmp_path / 'seed'
    def build(argv, **kwargs):
        assert argv[0] == '/approved/iso-builder'
        assert kwargs == {'check': True}
        Path(argv[argv.index('-output') + 1]).write_bytes(b'synthetic ISO')
    monkeypatch.setattr('subprocess.run', build)
    report = prepare(candidate, output, '/approved/iso-builder', task=task)
    assert not sentinel.exists()
    cloud = json.loads((output / 'user-data').read_text().split('\n', 1)[1])
    stored = next(f['content'] for f in cloud['write_files']
                  if f['path'] == '/tmp/candidate.json')
    assert json.loads(stored) == source
    assert report['source_sha256'] == hashlib.sha256(source.encode()).hexdigest()
    guest = next(f['content'] for f in cloud['write_files'] if f['path'] == '/tmp/probe.py')
    assert report['nonce'] in guest
    assert report['required_network'] == 'none'
    network = json.loads((output / 'network-config').read_text())
    assert network['ethernets']['unused']['optional'] is True
    assert network['ethernets']['unused']['dhcp4'] is False
    with pytest.raises(FileExistsError):
        prepare(candidate, output, '/approved/iso-builder', task=task)


@pytest.mark.parametrize('raw', [b'x' * 65537, b'{}', json.dumps('x' * 8192).encode()])
def test_reject_before_output_or_process(tmp_path, monkeypatch, raw):
    candidate = tmp_path / 'candidate.json'; candidate.write_bytes(raw)
    def forbidden(*a, **kw):
        raise AssertionError('must not launch anything')
    monkeypatch.setattr('subprocess.run', forbidden)
    with pytest.raises(ValueError):
        prepare(candidate, tmp_path / 'seed', '/approved/iso-builder')
    assert not (tmp_path / 'seed').exists()
