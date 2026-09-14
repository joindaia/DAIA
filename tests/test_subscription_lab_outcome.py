"""Delivery evidence never converts a failed client turn into success."""
import json
from pathlib import Path
import runpy
import sys

import pytest

scope = runpy.run_path(str(Path(__file__).parents[1] / 'scripts/subscription_lab_outcome.py'))
outcome, write = scope['outcome'], scope['write_outcome']
ROW = {'id': 'a' * 32, 'state': 'submitted', 'receipt_hash': 'b' * 64}


def test_acknowledged_failure_is_not_success_and_drops_secrets():
    saved = {'pending': None, 'lease': None, 'receipt': {'receipt_hash': 'b'*64},
             'key': 'synthetic-private-key', 'artifact': 'untrusted-payload'}
    result = outcome(saved, ROW)
    assert result == {'worker_completed': False, 'delivery': 'acknowledged',
                      'automatic_retry_authorized': False, 'receipt_hash': 'b'*64}


@pytest.mark.skipif(sys.platform != 'linux', reason='Linux private filesystem helper')
def test_outcome_is_written_privately_and_atomically(tmp_path):
    result = outcome({'pending': None, 'lease': None,
                      'receipt': {'receipt_hash': 'b'*64}}, ROW)
    path = tmp_path / 'outcome.json'; write(path, result)
    assert json.loads(path.read_text()) == result
    assert path.stat().st_mode & 0o077 == 0
    assert 'synthetic-private-key' not in path.read_text()
    assert list(tmp_path.iterdir()) == [path]


def test_receipt_must_match_exact_assignment():
    saved = {'pending': None, 'lease': None, 'receipt': {'receipt_hash': 'c'*64}}
    assert outcome(saved, ROW)['delivery'] == 'unconfirmed'
    assert outcome(saved, None)['delivery'] == 'unconfirmed'
    assert outcome(saved, {**ROW, 'state': 'leased'})['delivery'] == 'unconfirmed'


def test_stored_pending_does_not_authorize_replay():
    saved = {'pending': {'assignment_id': 'a'*32}, 'pending_receipt_hash': 'b'*64}
    result = outcome(saved, ROW)
    assert result['delivery'] == 'stored_unacknowledged'
    assert result['automatic_retry_authorized'] is False
    saved['pending']['assignment_id'] = 'c'*32
    assert outcome(saved, ROW)['delivery'] == 'unconfirmed'


@pytest.mark.skipif(sys.platform != 'linux', reason='Linux private filesystem helper')
def test_persistent_runs_are_distinct_and_private(tmp_path):
    root = tmp_path / 'runs'
    first = scope['new_run_directory'](root)
    write(first / 'assignment' / 'outcome.json', {'worker_completed': False})
    second = scope['new_run_directory'](root)
    assert first != second
    assert json.loads((first / 'assignment' / 'outcome.json').read_text()) == {'worker_completed': False}
    for p in (root, first, second, first / 'assignment', first / 'coordinator'):
        assert p.stat().st_mode & 0o077 == 0
    assert list((second / 'assignment').iterdir()) == []


@pytest.mark.skipif(sys.platform != 'linux', reason='Linux private filesystem helper')
def test_shared_or_symlink_state_root_refused(tmp_path):
    import pytest
    root = tmp_path / 'shared'; root.mkdir(mode=0o755)
    with pytest.raises(ValueError, match='Private operator'):
        scope['new_run_directory'](root)
    target = tmp_path / 'private'; target.mkdir(mode=0o700)
    link = tmp_path / 'link'; link.symlink_to(target)
    with pytest.raises(ValueError, match='Private operator'):
        scope['new_run_directory'](link)
    assert list(root.iterdir()) == list(target.iterdir()) == []


def test_summary_counts_without_leaking_or_mutating_records():
    summarize = scope['summarize_outcomes']
    records = [{'delivery':'acknowledged','worker_completed':False,'key':'secret'},
               {'delivery':'stored_unacknowledged','worker_completed':True},
               {'delivery':'other','worker_completed':1}, {}]
    before = json.dumps(records)
    assert summarize(iter(records)) == {'total':4,'worker_completed':1,
        'acknowledged':1,'stored_unacknowledged':1,'unconfirmed':2}
    assert json.dumps(records) == before
    assert summarize([]) == dict.fromkeys(summarize(records), 0)


@pytest.mark.skipif(sys.platform != 'linux', reason='Linux private filesystem helper')
def test_failure_survives_runtime_cleanup_as_bounded_private_data(tmp_path):
    import shutil
    import subprocess
    run = scope['new_run_directory'](tmp_path / 'runs')
    runtime = tmp_path / 'runtime'; runtime.mkdir()
    result = subprocess.CompletedProcess([], 7, b'x' * 70000, b'bad byte: \xff')
    scope['retain_worker_failure'](run, result)
    shutil.rmtree(runtime)
    path = run / 'worker-failure-private.json'
    data = json.loads(path.read_text())
    assert data == {'returncode': 7, 'stdout': 'x' * 65536,
                    'stderr': 'bad byte: \ufffd'}
    assert path.stat().st_mode & 0o077 == 0
    assert set(p.name for p in run.iterdir()) == {
        'assignment', 'coordinator', 'worker-failure-private.json'}


@pytest.mark.skipif(sys.platform != 'linux', reason='Linux private filesystem helper')
def test_retained_model_counts_exclude_credentials_and_preserve_unknown(tmp_path):
    audit = tmp_path / 'audit.json'
    retain = scope['retain_model_counts']
    retain(tmp_path, audit)
    path = tmp_path / 'model-counts.json'
    assert json.loads(path.read_text()) == {'available': False}
    audit.write_text(json.dumps({'forwarded': 2, 'denied': 23, 'attempts': 2,
                                'token': 'synthetic-secret'}))
    retain(tmp_path, audit)
    assert json.loads(path.read_text()) == {
        'available': True, 'forwarded': 2, 'denied': 23, 'attempts': 2}
    assert path.stat().st_mode & 0o077 == 0
    for bad in ('{', 'x' * 65537, json.dumps({'forwarded': True, 'denied': 0, 'attempts': 0})):
        audit.write_text(bad); retain(tmp_path, audit)
        assert json.loads(path.read_text()) == {'available': False}
