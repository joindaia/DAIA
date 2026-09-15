"""Preparation must not reuse state or accept a moving revision."""
import runpy
from pathlib import Path
from types import SimpleNamespace
import pytest

prepare = runpy.run_path(str(Path(__file__).parents[1] / 'scripts/prepare_clean_subscription_lab.py'))['prepare']


def test_moving_revision_creates_nothing(tmp_path):
    output = tmp_path / 'new'
    with pytest.raises(ValueError, match='exact approved'):
        prepare(SimpleNamespace(revision='main', output=output))
    assert not output.exists()


def test_existing_destination_preserved(tmp_path):
    marker = tmp_path / 'sentinel'
    marker.write_text('keep')
    with pytest.raises(FileExistsError):
        prepare(SimpleNamespace(revision='a' * 40, output=tmp_path))
    assert marker.read_text() == 'keep'
    assert sorted(p.name for p in tmp_path.iterdir()) == ['sentinel']


def test_relative_destination_rejected():
    with pytest.raises(ValueError, match='absolute'):
        prepare(SimpleNamespace(revision='a' * 40, output=Path('relative')))
