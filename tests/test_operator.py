"""Existing-state commands must never bootstrap a replacement coordinator."""
import json
import sqlite3
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

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


def test_unknown_revocation_cli_fails_without_logging_or_disclosing_identifier(network):
    service, _ = network
    service.invite()
    with service.store.connect() as db:
        before = {table: [tuple(row) for row in db.execute(f"SELECT * FROM {table} ORDER BY rowid")]
                  for table in ("contributors", "events")}
    result = subprocess.run([sys.executable, "-m", "daia.cli", "--db", service.store.path,
                             "revoke", "unknown-root-private-canary"], capture_output=True, text=True, timeout=20)
    assert result.returncode == 1
    assert result.stdout == ""
    assert "Contributor not found" in result.stderr
    assert "Traceback" not in result.stderr and "unknown-root-private-canary" not in result.stderr
    assert service.store.path not in result.stderr
    with service.store.connect() as db:
        for table, rows in before.items():
            assert [tuple(row) for row in db.execute(f"SELECT * FROM {table} ORDER BY rowid")] == rows


@pytest.mark.parametrize("expired", [False, True])
def test_concurrent_revocation_is_idempotent_and_preserves_signed_history(network, contributor, expired):
    from conftest import submit
    service, now = network
    service.seed()
    who = contributor()
    root, agent = who[0]["root_id"], who[1]
    lease = service.request_work(root, agent)
    submit(service, who, lease)
    if expired:
        now[0] = who[0]["expires"]
    with service.store.connect() as db:
        history = {table: [tuple(row) for row in db.execute(f"SELECT * FROM {table} ORDER BY rowid")]
                   for table in ("assignments", "results", "jobs", "events")}
    with ThreadPoolExecutor(max_workers=4) as pool:
        assert list(pool.map(lambda _: service.revoke(root), range(8))) == [None] * 8
    with service.store.connect() as db:
        assert db.execute("SELECT revoked,assigned FROM contributors WHERE id=?", (root,)).fetchone()[:] == (1, 1)
        for table in ("assignments", "results", "jobs"):
            assert [tuple(row) for row in db.execute(f"SELECT * FROM {table} ORDER BY rowid")] == history[table]
        events = [tuple(row) for row in db.execute("SELECT * FROM events ORDER BY rowid")]
        assert events[:-1] == history["events"]
        assert json.loads(events[-1][1])["kind"] == "contributor_revoked"
    with pytest.raises(Denied):
        service.authenticate(who[0]["token"])
    with pytest.raises(Denied):
        service.request_work(root, agent)


@pytest.mark.parametrize("command", ["resolve-evidence", "revoke"])
@pytest.mark.parametrize("failure", ["before", "after_commit", "storage"])
def test_operator_write_error_reports_uncertainty_and_retry_is_idempotent(network, monkeypatch, capsys, command, failure):
    from daia.cli import main
    from test_evidence import document
    service, _ = network
    job = service.admit_evidence(document())["job_id"]
    root = service.invite()["root_id"]
    arguments = (["resolve-evidence", "--job", job, "--disposition", "cancelled", "--note", "Synthetic decision"]
                 if command == "resolve-evidence" else ["revoke", root])
    monkeypatch.setattr(sys, "argv", ["daia", "--db", service.store.path, *arguments])
    method = "resolve_evidence" if command == "resolve-evidence" else "revoke"
    original = getattr(Coordinator, method)
    reached = []

    def fail(*args, **kwargs):
        reached.append(True)
        if failure == "after_commit":
            original(*args, **kwargs)
        error = OSError if failure == "storage" else sqlite3.OperationalError
        raise error("private-operator-canary")

    with monkeypatch.context() as fault:
        fault.setattr(Coordinator, method, fail)
        with pytest.raises(SystemExit) as error:
            main()
        assert error.value.code == 1
    assert reached == [True]
    output = capsys.readouterr()
    assert output.out == ""
    assert "could not be confirmed" in output.err and "before retrying" in output.err
    assert "private-operator-canary" not in output.err and service.store.path not in output.err
    with service.store.connect() as db:
        disposition = db.execute("SELECT disposition FROM evidence_campaigns WHERE job_id=?", (job,)).fetchone()[0]
        revoked = db.execute("SELECT revoked FROM contributors WHERE id=?", (root,)).fetchone()[0]
        assert disposition == ("cancelled" if command == "resolve-evidence" and failure == "after_commit" else None)
        assert revoked == int(command == "revoke" and failure == "after_commit")
    main()
    main()
    with service.store.connect() as db:
        events = [json.loads(row[0])["kind"] for row in db.execute("SELECT event_json FROM events")]
        kind = "evidence_campaign_resolved" if command == "resolve-evidence" else "contributor_revoked"
        assert events.count(kind) == 1


def test_resolution_cli_refusal_keeps_gate_and_private_note(network):
    from test_evidence import document
    service, _ = network
    job = service.admit_evidence(document())["job_id"]
    result = subprocess.run([sys.executable, "-m", "daia.cli", "--db", service.store.path,
                             "resolve-evidence", "--job", job, "--disposition", "useful",
                             "--note", "private-note-canary"], capture_output=True, text=True, timeout=20)
    assert result.returncode == 1 and result.stdout == ""
    assert "Evidence disposition refused" in result.stderr
    assert all(value not in result.stderr for value in ("Traceback", "private-note-canary", service.store.path, job))
    with service.store.connect() as db:
        assert db.execute("SELECT disposition FROM evidence_campaigns WHERE job_id=?", (job,)).fetchone()[0] is None
