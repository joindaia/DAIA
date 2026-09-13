"""Offline assembly: pin copied bytes and never reuse existing output."""
import hashlib
import json
from pathlib import Path
import runpy
import pytest

prepare = runpy.run_path(str(Path(__file__).parents[1] / 'scripts/prepare_kvm_bundle.py'))['prepare']


def test_reproducible_bundle_and_rejected_inputs(tmp_path):
    base, seed = tmp_path / 'base', tmp_path / 'seed'
    base.write_bytes(b'synthetic base'); seed.write_bytes(b'synthetic seed')
    args = dict(base_sha256=hashlib.sha256(base.read_bytes()).hexdigest(),
                seed_sha256=hashlib.sha256(seed.read_bytes()).hexdigest(), nonce='a' * 32)
    first, second = tmp_path / 'first', tmp_path / 'second'
    one = prepare(base, seed, first, **args)
    assert prepare(base, seed, second, **args) == one
    assert len(one) == 7
    manifest = json.loads((first / 'network-config.json').read_text())
    assert manifest['base_sha256'] == args['base_sha256']
    for name, expected in manifest['bridge_sha256'].items():
        assert one[name] == expected
    assert '/run/daia-lab/model.sock' in (first / 'model-bridge.py').read_text()
    assert '/run/daia-research/gateway.sock' in (first / 'research-bridge.py').read_text()
    assert all(p.stat().st_mode & 0o222 == 0 for p in first.iterdir())
    with pytest.raises(FileExistsError):
        prepare(base, seed, first, **args)
    bad = tmp_path / 'bad'
    with pytest.raises(ValueError, match='digest mismatch'):
        prepare(base, seed, bad, **{**args, 'seed_sha256': '0' * 64})
    assert not bad.exists()
    link = tmp_path / 'linked'; link.symlink_to(base)
    with pytest.raises(ValueError, match='regular input'):
        prepare(link, seed, bad, **args)
    assert not bad.exists()
