"""Delivery evidence never converts a failed client turn into success."""
import json
from pathlib import Path
import runpy

scope = runpy.run_path(str(Path(__file__).parents[1] / 'scripts/subscription_lab_outcome.py'))
outcome, write = scope['outcome'], scope['write_outcome']
ROW = {'id': 'a' * 32, 'state': 'submitted', 'receipt_hash': 'b' * 64}


def test_acknowledged_failure_is_not_success_and_drops_secrets(tmp_path):
    saved = {'pending': None, 'lease': None, 'receipt': {'receipt_hash': 'b'*64},
             'key': 'synthetic-private-key', 'artifact': 'untrusted-payload'}
    result = outcome(saved, ROW)
    assert result == {'worker_completed': False, 'delivery': 'acknowledged',
                      'automatic_retry_authorized': False, 'receipt_hash': 'b'*64}
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
