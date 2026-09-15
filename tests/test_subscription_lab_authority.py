"""Authority preparation binds the original task without storing credentials."""
import json
from pathlib import Path
import runpy
import sys
import time
import pytest

if sys.platform != 'linux':
    pytest.skip('Linux request accounting', allow_module_level=True)


def prepare(monkeypatch):
    scripts=Path(__file__).parents[1]/'scripts'
    monkeypatch.syspath_prepend(str(scripts))
    return runpy.run_path(str(scripts/'subscription_lab_authority.py'))['prepare']


def test_original_scope_is_bound_once_and_account_not_stored(tmp_path, monkeypatch):
    call=prepare(monkeypatch)
    scope=dict(lease={'assignment_id':'a'*32,'hard_deadline':1000},
               consent_deadline=900,template=b'{"model":"fixed"}',
               account='synthetic-account-canary',deadline=time.clock_gettime(time.CLOCK_BOOTTIME)+30)
    first=tmp_path/'one';first.mkdir(mode=0o700)
    digest=call(first,**scope)
    authority=first/'model-authority'
    assert json.loads((authority/'requests.json').read_text())['remaining']==6
    assert json.loads((authority/'binding.json').read_text())=={'binding':digest}
    for entry in authority.iterdir():
        assert entry.stat().st_mode & 0o077 == 0
        assert 'synthetic-account-canary' not in entry.read_text()
    with pytest.raises(FileExistsError):call(first,**scope)
    for number,change in enumerate([{'lease':{'assignment_id':'b'*32}},
                                   {'account':'different-account'},
                                   {'template':b'{"model":"different"}'},
                                   {'consent_deadline':800}]):
        other=tmp_path/str(number);other.mkdir(mode=0o700)
        assert call(other,**(scope|change)) != digest
