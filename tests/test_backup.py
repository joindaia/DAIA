"""Snapshots use synthetic identities; recovery never touches a live pilot database."""
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest

from daia.crypto import sign
from daia.service import Coordinator, Denied
from daia.store import Store, backup_database


def test_live_snapshot_and_process_loss_preserve_receipts_and_fences(network, contributor, tmp_path):
    service, now = network
    service.seed()
    abandoned, producer, reviewer, revoked = contributor(), contributor(max_jobs=1), contributor(), contributor()
    replacement = contributor(root=abandoned[0]["root_id"])
    stale = service.request_work(abandoned[0]["root_id"], abandoned[1])
    artifact = '{"factors":[101,103]}'
    envelope = service.envelope(abandoned[0]["root_id"], abandoned[1], stale["assignment_id"], artifact, "candidate")
    signature = sign(abandoned[2], envelope)
    now[0] += 301  # Expiry and reassignment happen before the snapshot.
    lease = service.request_work(producer[0]["root_id"], producer[1])
    envelope = service.envelope(producer[0]["root_id"], producer[1], lease["assignment_id"], artifact, "candidate")
    submitted = (producer[0]["root_id"], producer[1], lease["assignment_id"], artifact, "candidate", sign(producer[2], envelope))
    receipt = service.submit(*submitted)
    active = service.request_work(reviewer[0]["root_id"], reviewer[1])
    service.revoke(revoked[0]["root_id"])

    # Keep committed pages in a live WAL and an uncommitted write in a separate process.
    child = subprocess.Popen([sys.executable, "-c", """
import sqlite3, sys
db = sqlite3.connect(sys.argv[1])
db.execute('PRAGMA journal_mode=WAL')
db.execute("INSERT INTO metadata VALUES ('snapshot_test', 'committed-in-wal')")
db.commit()
db.execute('BEGIN IMMEDIATE')
db.execute('UPDATE contributors SET assigned=0, revoked=0')
print('uncommitted', flush=True)
sys.stdin.read()
""", service.store.path], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    try:
        assert child.stdout.readline().strip() == "uncommitted"
        target = tmp_path / "snapshots" / "checked.sqlite3"
        result = subprocess.run([sys.executable, "-m", "daia.cli", "--db", service.store.path,
                                 "backup", "--output", str(target)], capture_output=True, text=True, timeout=20)
        assert result.returncode == 0, result.stderr
        assert "Private snapshot verified" in result.stdout
    finally:
        child.kill()  # Abrupt process loss, without COMMIT or orderly rollback.
        child.communicate(timeout=10)

    restored = Coordinator(Store(str(target)), clock=lambda: now[0])
    assert restored.network_id == service.network_id
    assert restored.metrics() == service.metrics()
    with restored.store.connect() as copy, service.store.connect() as original:
        assert copy.execute("SELECT value FROM metadata WHERE key='snapshot_test'").fetchone()[0] == "committed-in-wal"
        for table in ("contributors", "assignments", "results", "events", "jobs"):
            assert [tuple(row) for row in copy.execute(f"SELECT * FROM {table} ORDER BY rowid")] == [
                tuple(row) for row in original.execute(f"SELECT * FROM {table} ORDER BY rowid")]
    assert restored.submit(*submitted)["status"] == "already_recorded"
    assert restored.metrics()["results"] == 1
    assert receipt["status"] == "in_review"
    assert restored.request_work(producer[0]["root_id"], producer[1])["status"] == "budget_or_cooldown"
    for who in (abandoned, replacement):
        assert restored.request_work(who[0]["root_id"], who[1])["status"] == "no_eligible_work"
    with pytest.raises(Denied):
        restored.authenticate(revoked[0]["token"])
    with pytest.raises(Denied):
        restored.submit(abandoned[0]["root_id"], abandoned[1], stale["assignment_id"], artifact, "candidate", signature)
    assert restored.request_work(reviewer[0]["root_id"], reviewer[1]) == active
    now[0] = active["hard_deadline"]
    with pytest.raises(Denied):
        restored.heartbeat(reviewer[0]["root_id"], reviewer[1], active["assignment_id"])
    if os.name == "posix":
        assert target.stat().st_mode & 0o077 == 0


def test_backup_rejects_missing_corrupt_and_racing_destinations(network, tmp_path, monkeypatch):
    service, _ = network
    target = tmp_path / "private" / "copy.sqlite3"
    missing = tmp_path / "missing.sqlite3"
    with pytest.raises(ValueError, match="existing"):
        backup_database(missing, target)
    assert not missing.exists() and not target.exists()
    corrupt = tmp_path / "corrupt.sqlite3"
    corrupt.touch(mode=0o600)
    corrupt.write_bytes(b"not a database")
    with pytest.raises(sqlite3.DatabaseError):
        backup_database(corrupt, target)
    assert not target.exists()
    assert not list(target.parent.glob(".daia-backup-*"))
    with pytest.raises(FileExistsError):
        backup_database(service.store.path, service.store.path)
    link = os.link

    def competing_file(source, destination):
        Path(destination).write_bytes(b"keep existing bytes")
        link(source, destination)

    monkeypatch.setattr(os, "link", competing_file)
    with pytest.raises(FileExistsError):
        backup_database(service.store.path, target)
    assert target.read_bytes() == b"keep existing bytes"
    assert not list(target.parent.glob(".daia-backup-*"))


def test_busy_snapshot_times_out_without_publishing(network, tmp_path, monkeypatch):
    import daia.store as store
    service, _ = network
    target = tmp_path / "private" / "busy.sqlite3"
    ticks = iter((0, 11))
    monkeypatch.setattr(store.time, "monotonic", lambda: next(ticks))
    writer = sqlite3.connect(service.store.path)
    try:
        writer.execute("BEGIN EXCLUSIVE")
        with pytest.raises(TimeoutError):
            backup_database(service.store.path, target)
    finally:
        writer.close()
    assert not target.exists()
    assert not list(target.parent.glob(".daia-backup-*"))


def test_snapshot_rejects_foreign_key_damage(network, tmp_path):
    service, _ = network
    with sqlite3.connect(service.store.path) as db:
        db.execute("INSERT INTO agents VALUES (?, ?, ?, 0)", ("a" * 64, "missing-root", "b" * 64))
    target = tmp_path / "private" / "bad.sqlite3"
    with pytest.raises(ValueError, match="foreign-key"):
        backup_database(service.store.path, target)
    assert not target.exists()
