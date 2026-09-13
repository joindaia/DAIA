"""No provider credentials or external requests; real processes and durable files."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
if sys.platform != 'linux':
    pytest.skip('Linux boot-bound request accounting', allow_module_level=True)

from daia import request_ledger as ledger
from daia.model_request import Denied

BINDING = 'a' * 64


def child(path, *, crash=False):
    code = ('import os,sys; from daia.request_ledger import reserve; '
            'reserve(sys.argv[1], sys.argv[2]); os._exit(23)' if crash else
            'import sys; from daia.request_ledger import reserve; reserve(sys.argv[1], sys.argv[2])')
    return subprocess.Popen([sys.executable, '-c', code, str(path), BINDING],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            env={**os.environ, 'PYTHONPATH': str(Path(__file__).parents[1] / 'src')})


def test_crash_and_new_process_do_not_refill_budget(tmp_path):
    path = tmp_path / 'requests.json'
    ledger.create(path, BINDING, seconds=30, requests=2)
    original = json.loads(path.read_text())
    first = child(path, crash=True); first.communicate(timeout=10)
    assert first.returncode == 23
    second = child(path); second.communicate(timeout=10)
    assert second.returncode == 0
    third = child(path); third.communicate(timeout=10)
    assert third.returncode != 0
    after = json.loads(path.read_text())
    assert after == {**original, 'remaining': 0}
    with pytest.raises(FileExistsError):
        ledger.create(path, BINDING, seconds=30, requests=2)
    assert json.loads(path.read_text()) == after


def test_competing_processes_cannot_overspend(tmp_path):
    path = tmp_path / 'requests.json'
    ledger.create(path, BINDING, seconds=30, requests=3)
    workers = [child(path) for _ in range(8)]
    for worker in workers:
        worker.communicate(timeout=10)
    accepted = sum(p.returncode == 0 for p in workers)
    assert 1 <= accepted <= 3
    assert json.loads(path.read_text())['remaining'] == 3 - accepted


@pytest.mark.parametrize('fault', ['missing', 'corrupt', 'shared', 'symlink', 'hardlink', 'wrong-binding', 'reboot', 'expired', 'boolean-count', 'fsync'])
def test_invalid_state_never_authorizes(fault, tmp_path, monkeypatch):
    path = tmp_path / 'requests.json'
    ledger.create(path, BINDING, seconds=30, requests=1)
    before = json.loads(path.read_text())
    if fault == 'missing': path.unlink()
    elif fault == 'corrupt': path.write_text('{')
    elif fault == 'shared': path.chmod(0o644)
    elif fault == 'symlink':
        original = tmp_path / 'original'; path.rename(original); path.symlink_to(original)
    elif fault == 'hardlink': os.link(path, tmp_path / 'alias')
    elif fault == 'wrong-binding': monkeypatch.setitem(before, 'binding', 'b'*64); path.write_text(json.dumps(before))
    elif fault == 'reboot': monkeypatch.setattr(ledger, '_boot', lambda: 'different-boot')
    elif fault == 'expired': monkeypatch.setattr(ledger, '_now', lambda: before['deadline'])
    elif fault == 'boolean-count': before['remaining'] = True; path.write_text(json.dumps(before))
    elif fault == 'fsync':
        def fail(fd): raise OSError('synthetic storage failure')
        monkeypatch.setattr(ledger.os, 'fsync', fail)
    with pytest.raises(Denied, match='Persisted request authority unavailable'):
        ledger.reserve(path, BINDING)


def test_wrong_binding_does_not_consume_valid_authority(tmp_path):
    path = tmp_path / 'requests.json'
    ledger.create(path, BINDING, seconds=30, requests=1)
    before = path.read_bytes()
    with pytest.raises(Denied): ledger.reserve(path, 'b'*64)
    assert path.read_bytes() == before
    ledger.reserve(path, BINDING)
    assert json.loads(path.read_text())['remaining'] == 0


def test_revocation_survives_a_fresh_process_and_is_idempotent(tmp_path):
    path = tmp_path / 'requests.json'
    ledger.create(path, BINDING, seconds=30, requests=6)
    ledger.revoke(path, BINDING)
    ledger.revoke(path, BINDING)
    worker = child(path); worker.communicate(timeout=10)
    assert worker.returncode != 0
    assert json.loads(path.read_text())['remaining'] == 0


def test_revocation_of_expired_or_previous_boot_does_not_renew(tmp_path, monkeypatch):
    path = tmp_path / 'requests.json'
    ledger.create(path, BINDING, seconds=30, requests=6)
    original = json.loads(path.read_text())
    monkeypatch.setattr(ledger, '_boot', lambda: 'different-boot')
    monkeypatch.setattr(ledger, '_now', lambda: original['deadline'] + 1)
    ledger.revoke(path, BINDING)
    assert json.loads(path.read_text()) == {**original, 'remaining': 0}


def test_revocation_wrong_binding_preserves_valid_authority(tmp_path):
    path = tmp_path / 'requests.json'
    ledger.create(path, BINDING, seconds=30, requests=6)
    original = path.read_bytes()
    with pytest.raises(Denied): ledger.revoke(path, 'e' * 64)
    assert path.read_bytes() == original


@pytest.mark.parametrize('explicit', [False, True])
def test_creation_delay_never_extends_original_deadline(tmp_path, monkeypatch, explicit):
    clock=[100.0]
    monkeypatch.setattr(ledger,'_now',lambda: clock[0])
    original_open=ledger._open
    def delayed_open(path,flags):
        clock[0]+=5
        return original_open(path,flags)
    monkeypatch.setattr(ledger,'_open',delayed_open)
    path=tmp_path/'requests.json'
    options={'deadline':110.0} if explicit else {}
    ledger.create(path,BINDING,seconds=30,requests=1,**options)
    assert json.loads(path.read_text())['deadline']==(110.0 if explicit else 130.0)
    if explicit:
        # Opening the record consumes the last five seconds: reservation must deny.
        with pytest.raises(Denied):ledger.reserve(path,BINDING)


@pytest.mark.parametrize('deadline',[False,float('nan'),float('inf'),99.0,100.0])
def test_invalid_original_deadline_creates_no_authority(tmp_path,monkeypatch,deadline):
    monkeypatch.setattr(ledger,'_now',lambda:100.0)
    path=tmp_path/'requests.json'
    with pytest.raises(ValueError):ledger.create(path,BINDING,seconds=30,requests=1,deadline=deadline)
    assert not path.exists()
