"""Exact acknowledged subscription candidate export stays read-only and bounded."""
import hashlib
import json
from pathlib import Path
import runpy
import sqlite3
import sys

import pytest

pytestmark = pytest.mark.skipif(sys.platform != "linux", reason="Linux private run permissions")


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def _fixture(tmp_path, *, duplicate=False):
    tmp_path.chmod(0o700)
    for name in ("assignment", "coordinator"):
        (tmp_path / name).mkdir(mode=0o700)
    assignment_id = "a" * 32
    job_id = "b" * 32
    agent_id = "c" * 64
    root_id = "d" * 32
    nonce = "e" * 32
    packet = {"suggested_change": "def newer(a, b): return a > b\n"}
    artifact = json.dumps(packet, separators=(",", ":"))
    artifact_hash = hashlib.sha256(artifact.encode()).hexdigest()
    envelope = {"action": "submit", "assignment_id": assignment_id, "job_id": job_id,
                "agent_id": agent_id, "nonce": nonce, "artifact_hash": artifact_hash}
    signature = "f" * 128
    receipt_hash = hashlib.sha256(_canonical({"envelope": envelope, "signature": signature})).hexdigest()

    metadata = tmp_path / "run.json"
    metadata.write_text(json.dumps({"assignment_id": assignment_id}) + "\n")
    metadata.chmod(0o600)
    state = tmp_path / "assignment/worker.contributor.json"
    state.write_text(json.dumps({"pending": None, "lease": None,
                                 "receipt": {"receipt_hash": receipt_hash}}))
    state.chmod(0o600)
    database = tmp_path / "coordinator/network.sqlite3"
    with sqlite3.connect(database) as db:
        db.executescript("""
            CREATE TABLE assignments(
                id TEXT, job_id TEXT, agent_id TEXT, root_id TEXT, nonce TEXT,
                state TEXT, receipt_hash TEXT
            );
            CREATE TABLE results(
                id TEXT, job_id TEXT, root_id TEXT, artifact TEXT,
                artifact_hash TEXT, envelope_json TEXT, signature TEXT
            );
        """)
        row = (assignment_id, job_id, agent_id, root_id, nonce, "submitted", receipt_hash)
        db.execute("INSERT INTO assignments VALUES (?,?,?,?,?,?,?)", row)
        result = ("1" * 32, job_id, root_id, artifact, artifact_hash,
                  json.dumps(envelope, separators=(",", ":")), signature)
        db.execute("INSERT INTO results VALUES (?,?,?,?,?,?,?)", result)
        if duplicate:
            db.execute("INSERT INTO results VALUES (?,?,?,?,?,?,?)", ("2" * 32, *result[1:]))
    database.chmod(0o600)
    return tmp_path, artifact, receipt_hash


def exporter(monkeypatch):
    scripts = Path(__file__).parents[1] / "scripts"
    monkeypatch.syspath_prepend(str(scripts))
    return runpy.run_path(str(scripts / "export_subscription_candidate.py"))["export_candidate"]


def test_exports_exact_suggested_change_without_mutating_run(tmp_path, monkeypatch):
    run, artifact, _ = _fixture(tmp_path)
    output = tmp_path / "candidate.json"
    before = (run / "assignment/worker.contributor.json").read_bytes(), (run / "coordinator/network.sqlite3").read_bytes()

    exporter(monkeypatch)(run, output)

    assert json.loads(output.read_text()) == "def newer(a, b): return a > b\n"
    assert output.stat().st_mode & 0o777 == 0o600
    assert json.loads(artifact)["suggested_change"] == json.loads(output.read_text())
    assert before == ((run / "assignment/worker.contributor.json").read_bytes(),
                      (run / "coordinator/network.sqlite3").read_bytes())


def test_existing_output_is_refused_without_replacement(tmp_path, monkeypatch):
    run, _, _ = _fixture(tmp_path)
    output = tmp_path / "candidate.json"
    output.write_text(chr(34) + "keep" + chr(34))
    output.chmod(0o600)

    with pytest.raises(FileExistsError, match="already exists"):
        exporter(monkeypatch)(run, output)
    assert output.read_text() == chr(34) + "keep" + chr(34)


@pytest.mark.parametrize("tamper,match", [
    ("artifact_hash", "artifact hash"),
    ("envelope_binding", "assignment binding"),
    ("duplicate", "Exactly one"),
])
def test_tampered_or_duplicate_result_fails_closed(tmp_path, monkeypatch, tamper, match):
    run, artifact, receipt_hash = _fixture(tmp_path, duplicate=tamper == "duplicate")
    database = run / "coordinator/network.sqlite3"
    if tamper == "artifact_hash":
        with sqlite3.connect(database) as db:
            db.execute("UPDATE results SET artifact_hash=?", ("0" * 64,))
    elif tamper == "envelope_binding":
        with sqlite3.connect(database) as db:
            envelope = json.loads(db.execute("SELECT envelope_json FROM results").fetchone()[0])
            envelope["assignment_id"] = "9" * 32
            signature = db.execute("SELECT signature FROM results").fetchone()[0]
            new_receipt = hashlib.sha256(_canonical({"envelope": envelope, "signature": signature})).hexdigest()
            db.execute("UPDATE results SET envelope_json=?", (json.dumps(envelope, separators=(",", ":")),))
            db.execute("UPDATE assignments SET receipt_hash=?", (new_receipt,))
            state = run / "assignment/worker.contributor.json"
            saved = json.loads(state.read_text())
            saved["receipt"]["receipt_hash"] = new_receipt
            state.write_text(json.dumps(saved))
    output = tmp_path / "candidate.json"
    with pytest.raises(ValueError, match=match):
        exporter(monkeypatch)(run, output)
    assert not output.exists()
