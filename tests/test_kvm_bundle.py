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
    assert len(one) == 8
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


def test_failed_launch_exports_only_bounded_private_diagnostics(tmp_path):
    import subprocess
    import sys
    bundle = tmp_path / 'bundle'; bundle.mkdir()
    (bundle / 'launcher.py').write_text("from pathlib import Path\nPath('serial.txt').write_bytes(b'DAIA_NATIVE_FAILURE synthetic error\\n'+b'x'*20000)\nraise SystemExit(1)\n")
    wrapper = Path(__file__).parents[1] / 'scripts/run_kvm_lab_report.py'
    result = subprocess.run([sys.executable, '-I', str(wrapper), '--bundle', str(bundle)],
                            cwd=tmp_path, capture_output=True, text=True, timeout=5)
    assert result.returncode == 1 and not result.stderr
    report = json.loads(result.stdout)
    assert report['ok'] is False
    assert 'DAIA_NATIVE_FAILURE synthetic error' in report['untrusted_failure_context']
    assert len(report['untrusted_failure_context'].encode()) <= 8192
    assert report['untrusted_diagnostics']['serial.txt'] == 'x' * 4096
    assert report['untrusted_diagnostics']['stderr.txt'] == ''
