"""Existing-state commands must never bootstrap a replacement coordinator."""
import json
import sqlite3
import subprocess
import sys

import pytest

from daia.service import Coordinator, Denied
from daia.store import Store


@pytest.mark.parametrize("command", ["inspect-evidence", "resolve-evidence", "revoke"])
def test_existing_state_cli_does_not_create_missing_database(tmp_path, command):
    source = tmp_path / "missing-parent" / "missing.sqlite3"
    output = tmp_path / "exports" / "inspection.json"
    arguments = {
        "inspect-evidence": ["--output", str(output)],
        "resolve-evidence": ["--job", "a" * 32, "--disposition", "unclear", "--note", "Synthetic triage"],
        "revoke": ["b" * 32],
    }[command]
    result = subprocess.run([sys.executable, "-m", "daia.cli", "--db", str(source), command, *arguments],
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 1
    assert result.stdout == ""
    assert "Traceback" not in result.stderr and str(tmp_path) not in result.stderr
    assert not source.parent.exists()
    assert not output.parent.exists()


@pytest.mark.parametrize("kind", ["empty", "unrelated", "missing_identity"])
def test_inspection_rejects_uninitialized_database_without_repair(tmp_path, kind):
    source = tmp_path / "uninitialized.sqlite3"
    source.touch(mode=0o600)
    if kind == "unrelated":
        with sqlite3.connect(source) as db:
            db.execute("CREATE TABLE unrelated(value TEXT)")
            db.execute("INSERT INTO unrelated VALUES ('preserve')")
    elif kind == "missing_identity":
        Store(str(source))
    before = source.read_bytes()
    output = tmp_path / "exports" / "inspection.json"
    result = subprocess.run([sys.executable, "-m", "daia.cli", "--db", str(source),
                             "inspect-evidence", "--output", str(output)], capture_output=True, text=True, timeout=20)
    assert result.returncode == 1
    assert result.stdout == ""
    assert "Traceback" not in result.stderr and str(tmp_path) not in result.stderr
    assert source.read_bytes() == before
    assert not output.parent.exists()


def test_existing_store_never_recreates_deleted_file_or_identity(tmp_path):
    source = tmp_path / "network # literal.sqlite3"
    created = Coordinator(Store(str(source)))
    existing = Store(str(source), create=False)
    assert Coordinator(existing).network_id == created.network_id
    with existing.connect() as db:
        db.execute("DELETE FROM metadata WHERE key='network_id'")
    with pytest.raises(Denied, match="initialized"):
        Coordinator(existing)
    with existing.connect() as db:
        assert db.execute("SELECT COUNT(*) FROM metadata WHERE key='network_id'").fetchone()[0] == 0
    source.unlink()
    with pytest.raises(sqlite3.OperationalError):
        with existing.connect():
            pass
    assert not source.exists()


def test_existing_state_commands_preserve_identity_and_work_normally(network, tmp_path):
    from test_evidence import document
    service, _ = network
    job = service.admit_evidence(document())["job_id"]
    root = service.invite()["root_id"]
    output = tmp_path / "exports" / "inspection.json"
    for arguments in (
        ["inspect-evidence", "--output", str(output)],
        ["resolve-evidence", "--job", job, "--disposition", "cancelled", "--note", "Synthetic operator decision"],
        ["revoke", root],
    ):
        result = subprocess.run([sys.executable, "-m", "daia.cli", "--db", service.store.path, *arguments],
                                capture_output=True, text=True, timeout=20)
        assert result.returncode == 0, result.stderr
    assert json.loads(output.read_text(encoding="utf-8"))[0]["job_id"] == job
    with service.store.connect() as db:
        assert db.execute("SELECT value FROM metadata WHERE key='network_id'").fetchone()[0] == service.network_id
        assert db.execute("SELECT revoked FROM contributors WHERE id=?", (root,)).fetchone()[0] == 1
        assert db.execute("SELECT disposition FROM evidence_campaigns WHERE job_id=?", (job,)).fetchone()[0] == "cancelled"
