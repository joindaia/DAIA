"""Preparation refuses unapproved binary bytes before making output."""
from pathlib import Path
import runpy
import pytest

prepare = runpy.run_path(str(Path(__file__).parents[1] /
    'scripts/prepare_subscription_fixture.py'))['prepare']


def test_bad_native_pin_never_runs_builder(tmp_path, monkeypatch):
    native = tmp_path / 'native'; native.mkdir()
    (native / 'codex').write_bytes(b'not the approved original client')
    def forbidden(*a, **k):
        raise AssertionError('No child process permitted')
    monkeypatch.setattr('subprocess.run', forbidden)
    with pytest.raises(ValueError, match='pin mismatch'):
        prepare(tmp_path / 'template', native, tmp_path / 'out', '/unused', 'a' * 64)
    assert not (tmp_path / 'out').exists()


def test_bad_base_digest_refused_before_inputs(tmp_path):
    with pytest.raises(ValueError, match='base hash'):
        prepare('/missing', '/missing', tmp_path / 'out', '/unused', 'latest')
    assert not (tmp_path / 'out').exists()
