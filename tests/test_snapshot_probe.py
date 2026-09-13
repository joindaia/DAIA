import json
import sqlite3

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from daia.crypto import public_hex, sign
from daia.service import Coordinator
from daia.store import Store, backup_database
from daia.snapshot_probe import inspect_snapshot


def test_status_comparison_preserves_snapshot_and_detects_changed_usage(tmp_path):
    tmp_path.chmod(0o700)
    source = tmp_path / 'source.sqlite3'
    service = Coordinator(Store(str(source)), clock=lambda: 1800000000)
    service.seed()
    grant = service.invite(max_jobs=2)
    key = Ed25519PrivateKey.generate()
    challenge = service.challenge(grant['root_id'], public_hex(key))
    agent = service.register(grant['root_id'], challenge['challenge_id'], sign(key, challenge))['agent_id']
    snapshot = tmp_path / 'snapshot.sqlite3'
    backup_database(source, snapshot)
    before = snapshot.read_bytes()
    first = inspect_snapshot(snapshot, 1800000000)
    assert first == inspect_snapshot(snapshot, 1800000000)
    assert first['agents_checked'] == 1 and snapshot.read_bytes() == before
    expired = inspect_snapshot(snapshot, grant['expires'] + 1)
    assert expired['agents_checked'] == 1 and expired['status_digest'] != first['status_digest']
    assert snapshot.read_bytes() == before
    assert agent not in json.dumps(first) and grant['root_id'] not in json.dumps(first)
    service.request_work(grant['root_id'], agent)
    changed = tmp_path / 'changed.sqlite3'
    backup_database(source, changed)
    assert inspect_snapshot(changed, 1800000000)['status_digest'] != first['status_digest']


def test_corrupt_snapshot_is_rejected_without_changing_original(tmp_path):
    source = tmp_path / 'broken.sqlite3'
    source.write_bytes(b'not a database'); source.chmod(0o600)
    with pytest.raises((ValueError, sqlite3.DatabaseError)):
        inspect_snapshot(source, 1800000000)
    assert source.read_bytes() == b'not a database'


def test_sidecar_rejects_live_source_before_sqlite(tmp_path):
    source = tmp_path / 'live.sqlite3'
    source.write_bytes(b'unchanged'); source.chmod(0o600)
    (tmp_path / 'live.sqlite3-wal').touch()
    with pytest.raises(ValueError, match='standalone backup'):
        inspect_snapshot(source, 1800000000)
    assert source.read_bytes() == b'unchanged'
