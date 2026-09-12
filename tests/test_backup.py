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


@pytest.mark.parametrize("corruption", ["payload", "link", "hash", "invalid_json"])
def test_backup_rejects_inconsistent_audit_log_without_repairing_source(network, tmp_path, corruption):
    service, _ = network
    service.seed(35)
    with service.store.connect() as db:
        first = db.execute("SELECT MIN(sequence) FROM events").fetchone()[0]
        assert first is not None
        column, value = {
            "payload": ("event_json", "{}"),
            "link": ("previous_hash", "f" * 64),
            "hash": ("event_hash", "f" * 64),
            "invalid_json": ("event_json", "private-event-invalid-json"),
        }[corruption]
        db.execute(f"UPDATE events SET {column}=? WHERE sequence=?", (value, first))
        before = [tuple(row) for row in db.execute("SELECT * FROM events ORDER BY sequence")]
        assert db.execute("PRAGMA integrity_check").fetchall()[0][0] == "ok"
        assert db.execute("PRAGMA foreign_key_check").fetchone() is None
    target = tmp_path / "private" / "invalid-audit.sqlite3"
    with pytest.raises(ValueError, match="Snapshot failed audit-log check") as error:
        backup_database(service.store.path, target)
    assert "private-event" not in str(error.value)
    assert not target.exists()
    assert not list(target.parent.glob(".daia-backup-*"))
    with service.store.connect() as db:
        assert [tuple(row) for row in db.execute("SELECT * FROM events ORDER BY sequence")] == before


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


@pytest.mark.parametrize("failure", ["missing", "corrupt", "occupied"])
def test_backup_cli_reports_expected_failures_without_private_paths(network, tmp_path, failure):
    service, _ = network
    source = Path(service.store.path)
    target = tmp_path / "private-path-canary" / "copy.sqlite3"
    if failure == "missing":
        source = tmp_path / "missing-source.sqlite3"
    elif failure == "corrupt":
        source = tmp_path / "corrupt-source.sqlite3"
        source.touch(mode=0o600)
        source.write_bytes(b"not a database")
    else:
        target.parent.mkdir(mode=0o700)
        target.write_bytes(b"preserve existing output")
    before = source.read_bytes() if source.exists() else None
    result = subprocess.run([sys.executable, "-m", "daia.cli", "--db", str(source),
                             "backup", "--output", str(target)], capture_output=True, text=True, timeout=20)
    assert result.returncode == 1
    assert result.stdout == ""
    assert "Traceback" not in result.stderr
    assert str(tmp_path) not in result.stderr
    assert "private-path-canary" not in result.stderr
    if failure == "occupied":
        assert "Choose a new filename" in result.stderr
        assert target.read_bytes() == b"preserve existing output"
    else:
        assert "Backup could not be confirmed" in result.stderr
        assert not target.exists()
    assert (source.read_bytes() if source.exists() else None) == before
    assert not list(target.parent.glob(".daia-backup-*"))


def test_backup_cli_preserves_published_output_on_late_failure(network, tmp_path, monkeypatch, capsys):
    import daia.store as store
    from daia.cli import main
    service, _ = network
    target = tmp_path / "private" / "published.sqlite3"
    cleanup = store.TemporaryDirectory.cleanup

    def cleanup_then_fail(temporary):
        cleanup(temporary)
        raise PermissionError("private-storage-canary")

    monkeypatch.setattr(store.TemporaryDirectory, "cleanup", cleanup_then_fail)
    monkeypatch.setattr(sys, "argv", ["daia", "--db", service.store.path, "backup", "--output", str(target)])
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 1
    output = capsys.readouterr()
    assert output.out == ""
    assert "Backup could not be confirmed" in output.err
    assert "Preserve any output" in output.err
    assert "private-storage-canary" not in output.err
    assert str(tmp_path) not in output.err
    assert target.exists()
    with sqlite3.connect(target) as db:
        assert db.execute("PRAGMA integrity_check").fetchone() == ("ok",)
    assert not list(target.parent.glob(".daia-backup-*"))
