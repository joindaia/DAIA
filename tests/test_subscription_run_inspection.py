"""Retained state inspection must not resume work or mutate contributor data."""
import json
from pathlib import Path
import runpy
import sqlite3
import pytest


def fixture(tmp_path):
    tmp_path.chmod(0o700)
    for name in ('assignment', 'coordinator'):
        (tmp_path / name).mkdir(mode=0o700)
    meta = tmp_path / 'run.json'; meta.write_text(json.dumps({'assignment_id': 'a'*32})); meta.chmod(0o600)
    state = tmp_path / 'assignment/test.contributor.json'
    state.write_text(json.dumps({'pending': None, 'lease': None,
                                'receipt': {'receipt_hash': 'b'*64}, 'key': 'secret-canary'})); state.chmod(0o600)
    db = tmp_path / 'coordinator/network.sqlite3'
    with sqlite3.connect(db) as conn:
        conn.execute('CREATE TABLE assignments(id TEXT,state TEXT,receipt_hash TEXT)')
        conn.execute('INSERT INTO assignments VALUES(?,?,?)', ('a'*32, 'submitted', 'b'*64))
    db.chmod(0o600)
    return state, db


def inspector(monkeypatch):
    scripts = Path(__file__).parents[1] / 'scripts'
    monkeypatch.syspath_prepend(str(scripts))
    return runpy.run_path(str(scripts / 'inspect_subscription_run.py'))['inspect']


def test_acknowledgement_is_read_only_not_completed_or_resumed(tmp_path, monkeypatch):
    state, db = fixture(tmp_path); before = state.read_bytes(), db.read_bytes()
    result = inspector(monkeypatch)(tmp_path)
    assert result['delivery'] == 'acknowledged'
    assert result['automatic_resume_authorized'] is False
    assert result['model_budget_reconstructed'] is False
    assert result['worker_completion'] == 'not_established_by_this_inspection'
    assert 'secret-canary' not in json.dumps(result)
    assert before == (state.read_bytes(), db.read_bytes())


def test_mismatch_and_shared_state_are_not_trusted(tmp_path, monkeypatch):
    state, db = fixture(tmp_path); inspect = inspector(monkeypatch)
    with sqlite3.connect(db) as conn:
        conn.execute('UPDATE assignments SET receipt_hash=?', ('c'*64,))
    assert inspect(tmp_path)['delivery'] == 'unconfirmed'
    state.chmod(0o644)
    with pytest.raises(ValueError, match='permissions'):
        inspect(tmp_path)


def test_multiple_run_cli_only_returns_counts(tmp_path, monkeypatch, capsys):
    import sys
    script = Path(__file__).parents[1] / 'scripts/inspect_subscription_run.py'
    monkeypatch.syspath_prepend(str(script.parent))
    paths=[]
    for name in ('first','second'):
        folder=tmp_path/name;folder.mkdir();fixture(folder);paths.append(folder)
    monkeypatch.setattr(sys,'argv',[str(script),'--run',str(paths[0]),'--run',str(paths[1])])
    runpy.run_path(str(script),run_name='__main__')
    result=json.loads(capsys.readouterr().out)
    assert result == {'total':2,'acknowledged':2,'stored_unacknowledged':0,
        'unconfirmed':0,'worker_completion':'not_established_by_this_inspection'}
