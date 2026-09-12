"""Evidence campaigns check structure and provenance binding, never execute submitted code."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import asyncio
import sys

import pytest

from conftest import submit
from daia.crypto import sign
from daia.cli import verify_evidence_source
from daia.service import Denied
from daia.verifier import check_evidence_packet


def document(objective="Find one concrete failure case in this frozen excerpt."):
    return {"objective": objective, "baseline_commit": "a" * 40,
            "source": {"path": "src/example.py", "start_line": 10,
                       "text": "def increment(value):\n    return value - 1\n"}}


def packet(lease, **changes):
    if lease["mode"] == "adversarial":
        return json.dumps({"source_digest": lease["context"]["source"]["sha256"],
            "candidate_digest": lease["context"]["candidate_digest"], "line": 11,
            "assessment": "supports", "objections": "The name is not a complete specification.",
            "next_check": "Ask for the intended function contract before changing behavior.", **changes})
    return json.dumps({"source_digest": lease["context"]["source"]["sha256"], "line": 11,
        "finding": "The function decrements the input despite its name.",
        "reproduction_outline": "For input 1 the expression gives 0. This is a source-reading inference.",
        "suggested_change": "Determine the intended contract before changing the operator.", **changes})


def test_two_root_campaign_never_promotes_and_requires_human_disposition(network, contributor):
    service, _ = network
    admitted = service.admit_evidence(document())
    producer, reviewer = contributor(), contributor()
    lease = service.request_work(producer[0]["root_id"], producer[1])
    assert lease["job_id"] == admitted["job_id"]
    first = submit(service, producer, lease, packet(lease))
    assert first["status"] == "in_review"
    assert service.request_work(producer[0]["root_id"], producer[1])["status"] == "no_eligible_work"
    with pytest.raises(Denied, match="review first"):
        service.resolve_evidence(admitted["job_id"], "useful", "Premature triage")
    review = service.request_work(reviewer[0]["root_id"], reviewer[1])
    assert review["mode"] == "adversarial"
    assert review["context"]["source"] == lease["context"]["source"]
    assert review["context"]["candidate_artifact"] == packet(lease)
    with pytest.raises(Denied, match="source-bound"):
        submit(service, reviewer, review, packet(lease), "pass")
    for verdict, assessment in (("pass", "supports"), ("fail", "concerns"), ("inconclusive", "unclear")):
        assert check_evidence_packet(review["context"], packet(review, assessment=assessment), verdict)
        with pytest.raises(Denied, match="source-bound"):
            submit(service, reviewer, review, packet(review, assessment=assessment, candidate_digest="0" * 64), verdict)
    result = submit(service, reviewer, review, packet(review), "pass")
    assert result["status"] == "ready_for_maintainer"
    assert service.metrics()["promoted"] == 0
    inspected = service.inspect_evidence()[0]
    assert inspected["result"]["shape_valid"] is True
    assert inspected["result"]["correctness_verified"] is False
    assert "root_id" not in json.dumps(inspected)
    assert service.admit_evidence(document("Another question"))["status"] == "campaign_unresolved"
    assert service.resolve_evidence(admitted["job_id"], "useful", "Human checked the exact packet")["status"] == "resolved"
    assert service.resolve_evidence(admitted["job_id"], "useful", "Human checked the exact packet")["status"] == "already_resolved"
    with pytest.raises(Denied, match="overwritten"):
        service.resolve_evidence(admitted["job_id"], "rejected", "Changed mind")
    assert service.admit_evidence(document())["status"] == "already_admitted"
    assert service.admit_evidence(document("Another question"))["status"] == "admitted"


def test_admission_idempotency_and_backlog_cap_are_transactional(network):
    service, _ = network
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(lambda _: service.admit_evidence(document()), range(12)))
    assert sum(r["status"] == "admitted" for r in results) == 1
    assert len({r["job_id"] for r in results}) == 1
    assert service.metrics()["jobs"] == 1
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(lambda n: service.admit_evidence(document(str(n))), range(6)))
    assert all(r["status"] == "campaign_unresolved" for r in results)


@pytest.mark.parametrize("verdict,assessment,state", [
    ("inconclusive", "unclear", "in_review"),
    ("fail", "concerns", "disputed"),
])
def test_human_utility_note_does_not_override_review(network, contributor, verdict, assessment, state):
    service, _ = network
    job = service.admit_evidence(document())["job_id"]
    producer, reviewer = contributor(), contributor()
    lease = service.request_work(producer[0]["root_id"], producer[1])
    submit(service, producer, lease, packet(lease))
    review = service.request_work(reviewer[0]["root_id"], reviewer[1])
    artifact = packet(review, assessment=assessment)
    root, agent, key = reviewer[0]["root_id"], reviewer[1], reviewer[2]
    signature = sign(key, service.envelope(root, agent, review["assignment_id"], artifact, verdict))
    receipt = service.submit(root, agent, review["assignment_id"], artifact, verdict, signature)
    assert receipt["status"] == state
    before = service.inspect_evidence()[0]
    note = "Useful for regression coverage; the proposed defect remains unconfirmed."
    with pytest.raises(Denied, match="review first"):
        service.resolve_evidence(job, "useful", note)
    assert service.inspect_evidence()[0] == before
    assert service.admit_evidence(document("Another question"))["status"] == "campaign_unresolved"

    # An explicit operator decision can close triage without changing the review.
    assert service.resolve_evidence(job, "unclear", note)["status"] == "resolved"
    assert service.resolve_evidence(job, "unclear", note)["status"] == "already_resolved"
    after = service.inspect_evidence()[0]
    assert after["disposition"] == "unclear"
    assert after["disposition_note"] == note
    assert after["result"] == before["result"]
    assert after["reviews"] == before["reviews"]
    assert after["context"] == before["context"]
    assert after["result"]["correctness_verified"] is False
    replay = service.submit(root, agent, review["assignment_id"], artifact, verdict, signature)
    assert replay == {"receipt_hash": receipt["receipt_hash"], "status": "already_recorded"}
    assert service.metrics()["promoted"] == 0
    with pytest.raises(Denied, match="overwritten"):
        service.resolve_evidence(job, "useful", note)
    assert service.admit_evidence(document())["status"] == "already_admitted"
    assert service.admit_evidence(document("Another question"))["status"] == "admitted"


def test_cancelled_campaign_fences_old_lease_and_preserves_exposure(network, contributor):
    service, _ = network
    job = service.admit_evidence(document())["job_id"]
    producer = contributor()
    lease = service.request_work(producer[0]["root_id"], producer[1])
    artifact = packet(lease)
    envelope = service.envelope(producer[0]["root_id"], producer[1], lease["assignment_id"], artifact, "candidate")
    service.resolve_evidence(job, "cancelled", "Human ended this campaign")
    with pytest.raises(Denied, match="expired assignment"):
        service.submit(producer[0]["root_id"], producer[1], lease["assignment_id"], artifact,
                       "candidate", sign(producer[2], envelope))
    with service.store.connect() as db:
        assert db.execute("SELECT state FROM assignments WHERE id=?", (lease["assignment_id"],)).fetchone()[0] == "cancelled"
    assert service.request_work(producer[0]["root_id"], producer[1])["status"] == "no_eligible_work"


def test_shape_check_binds_source_without_executing_text(network, contributor, tmp_path):
    service, _ = network
    service.admit_evidence(document())
    who = contributor()
    lease = service.request_work(who[0]["root_id"], who[1])
    canary = tmp_path / "must-not-exist"
    artifact = packet(lease, reproduction_outline=f"__import__('pathlib').Path({str(canary)!r}).touch()")
    assert check_evidence_packet(lease["context"], artifact)
    assert submit(service, who, lease, artifact)["status"] == "in_review"
    assert not canary.exists()
    for change in ({"line": True}, {"line": 9}, {"source_digest": "0" * 64}, {"finding": " "}):
        assert not check_evidence_packet(lease["context"], packet(lease, **change))
    assert not check_evidence_packet(lease["context"], '{"factors":[101,103]}')
    assert not check_evidence_packet({**lease["context"], "checker_hash": "0" * 64}, artifact)


def test_invalid_source_context_is_refused(network):
    service, _ = network
    for path in (".", "../src/example.py", ".private/invite.json", "src/../secret", "C:/private", "src\\example.py"):
        doc = document()
        doc["source"]["path"] = path
        with pytest.raises(Denied):
            service.admit_evidence(doc)
    doc = document()
    doc["source"]["text"] = "\ud800"
    with pytest.raises(Denied, match="UTF-8"):
        service.admit_evidence(doc)


def test_operator_cli_verifies_real_git_excerpt(tmp_path, network):
    def git(*args):
        return subprocess.check_output(["git", "-C", str(tmp_path), "-c", "core.autocrlf=false",
            "-c", "core.hooksPath=" + str(tmp_path / "empty-hooks"), "-c", "commit.gpgsign=false",
            "-c", "user.name=Example", "-c", "user.email=example@example.com", *args], stderr=subprocess.DEVNULL)
    git("init")
    (tmp_path / "src").mkdir()
    raw = b"def increment(value):\r\n    return value - 1\r\n"
    (tmp_path / "src/example.py").write_bytes(raw)
    git("add", "src/example.py")
    git("commit", "-m", "fixture")
    commit = git("rev-parse", "HEAD").decode().strip()
    doc = {"baseline_commit": commit, "source": {"path": "src/example.py", "start_line": 1, "text": raw.decode()}}
    verify_evidence_source(doc, tmp_path)
    for change in ({"start_line": 2}, {"path": "src/missing.py"}, {"text": raw.decode().replace("\r\n", "\n")}):
        with pytest.raises(ValueError, match="exactly match"):
            verify_evidence_source({**doc, "source": {**doc["source"], **change}}, tmp_path)
    for revision in ("0" * 40, git("rev-parse", "HEAD:src/example.py").decode().strip()):
        with pytest.raises(ValueError, match="exactly match"):
            verify_evidence_source({**doc, "baseline_commit": revision}, tmp_path)

    # Real CLI preparation works even while another campaign blocks live admission.
    service, _ = network
    service.admit_evidence(document())
    with sqlite3.connect(service.store.path) as db:
        before = list(db.iterdump())
    context = tmp_path / "context.json"
    prepared = {**doc, "objective": "Check the increment contract; do not execute the excerpt."}
    context.write_text(json.dumps(prepared), encoding="utf-8")
    environment = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")}

    def prepare(database):
        return subprocess.run([sys.executable, "-m", "daia.cli", "--db", str(database),
            "admit-evidence", "--context", str(context), "--dry-run"], cwd=tmp_path,
            env=environment, capture_output=True, text=True, timeout=30)

    missing = tmp_path / "must-not-exist" / "pilot.sqlite3"
    for database in (service.store.path, missing):
        result = prepare(database)
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout) == {"status": "validated", "admitted": False,
            "live_eligibility_checked": False, "baseline_commit": commit}
        assert not missing.parent.exists()
    with sqlite3.connect(service.store.path) as db:
        assert list(db.iterdump()) == before

    # Both Git provenance and the real admission schema are checked, with safe errors.
    for invalid in ({**prepared, "objective": ""}, {**prepared, "extra": "private-context-canary"},
                    {**prepared, "source": {**prepared["source"], "text": "private-context-canary"}}):
        context.write_text(json.dumps(invalid), encoding="utf-8")
        result = prepare(missing)
        assert result.returncode == 1 and result.stdout == ""
        assert "Evidence context validation failed" in result.stderr
        assert "private-context-canary" not in result.stderr and str(tmp_path) not in result.stderr
        assert not missing.parent.exists()
    context.write_text("x" * 16385, encoding="utf-8")
    assert prepare(missing).returncode == 1
    assert not missing.parent.exists()


@pytest.mark.parametrize("pilot", [False, True])
def test_evidence_flow_through_two_stdio_workers(network, tmp_path, pilot):
    pytest.importorskip("mcp")
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client
    from daia.mcp_server import build_mcp_app
    from test_contributor import invite_file
    from test_mcp import call, running_server
    import time
    service, now = network
    now[0] = int(time.time())
    service.admit_evidence(document(), pilot=pilot)
    async def exercise(url):
        outcomes = []
        for _ in range(2):
            path = invite_file(tmp_path, service, url)
            params = StdioServerParameters(command=sys.executable, args=[
                "-m", "daia.contributor", "--invite", str(path)])
            async with stdio_client(params) as streams:
                async with ClientSession(*streams) as session:
                    await session.initialize()
                    lease = await call(session, "request_work")
                    result = await call(session, "submit_result", artifact=packet(lease),
                                        verdict="candidate" if lease["mode"] == "produce" else "pass")
                    outcomes.append(result["status"])
        assert outcomes == ["in_review", "pilot_ready_for_maintainer" if pilot else "ready_for_maintainer"]
    with running_server(build_mcp_app(service)) as url:
        asyncio.run(exercise(url))
    assert service.metrics()["promoted"] == 0


@pytest.mark.parametrize("failure", ["initialization", "inspection", "recursion", "partial_write", "flush"])
def test_inspection_failure_leaves_no_final_file_and_allows_retry(network, tmp_path, monkeypatch, capsys, failure):
    from daia.cli import main
    from daia.service import Coordinator
    service, _ = network
    service.admit_evidence(document())
    target = tmp_path / "private" / "inspection.json"
    monkeypatch.setattr(sys, "argv", ["daia", "--db", service.store.path, "inspect-evidence", "--output", str(target)])

    def fail(*args, **kwargs):
        if failure == "recursion":
            raise RecursionError("private-export-canary")
        if failure == "initialization":
            raise sqlite3.OperationalError("private-export-canary")
        if failure == "partial_write":
            args[1].write('{"partial":')
            args[1].flush()
        raise OSError("private-export-canary")

    with monkeypatch.context() as fault:
        if failure == "initialization":
            fault.setattr(Coordinator, "__init__", fail)
        elif failure in {"inspection", "recursion"}:
            fault.setattr(Coordinator, "inspect_evidence", fail)
        elif failure == "partial_write":
            fault.setattr(json, "dump", fail)
        else:
            fault.setattr(os, "fsync", fail)
        with pytest.raises(SystemExit) as error:
            main()
        assert error.value.code == 1
    output = capsys.readouterr()
    assert output.out == ""
    assert "Inspection export could not be confirmed" in output.err
    assert "private-export-canary" not in output.err and str(tmp_path) not in output.err
    assert not target.exists()
    assert not list(target.parent.glob(".daia-inspection-*"))
    main()
    assert json.loads(target.read_text(encoding="utf-8")) == service.inspect_evidence()


@pytest.mark.parametrize("race", [False, True])
def test_inspection_publishes_complete_private_json_without_overwrite(network, tmp_path, monkeypatch, capsys, race):
    from daia.cli import main
    service, _ = network
    service.admit_evidence(document("Inspect a caf\u00e9 contract without executing it."))
    expected = service.inspect_evidence()
    target = tmp_path / "private" / "inspection.json"
    monkeypatch.setattr(sys, "argv", ["daia", "--db", service.store.path, "inspect-evidence", "--output", str(target)])
    link = os.link
    reached = []

    def publish(source, destination):
        reached.append(True)
        assert not target.exists()
        assert json.loads(Path(source).read_text(encoding="utf-8")) == expected
        if os.name == "posix":
            assert Path(source).stat().st_mode & 0o077 == 0
        if race:
            target.write_bytes(b"preserve competing output")
        link(source, destination)

    monkeypatch.setattr(os, "link", publish)
    if race:
        with pytest.raises(SystemExit) as error:
            main()
        assert error.value.code == 1
        assert target.read_bytes() == b"preserve competing output"
        assert capsys.readouterr().out == ""
    else:
        main()
        assert json.loads(target.read_text(encoding="utf-8")) == expected
        before = target.read_bytes()
        with pytest.raises(SystemExit):
            main()
        assert target.read_bytes() == before
    assert reached == [True]
    assert not list(target.parent.glob(".daia-inspection-*"))


def test_inspection_cleanup_error_preserves_complete_published_output(network, tmp_path, monkeypatch, capsys):
    import daia.cli as cli
    service, _ = network
    target = tmp_path / "private" / "inspection.json"
    monkeypatch.setattr(sys, "argv", ["daia", "--db", service.store.path, "inspect-evidence", "--output", str(target)])
    cleanup = cli.TemporaryDirectory.cleanup

    def cleanup_then_fail(temporary):
        cleanup(temporary)
        raise OSError("private-cleanup-canary")

    monkeypatch.setattr(cli.TemporaryDirectory, "cleanup", cleanup_then_fail)
    with pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code == 1
    assert json.loads(target.read_text(encoding="utf-8")) == []
    output = capsys.readouterr()
    assert output.out == ""
    assert "Preserve any output" in output.err and "private-cleanup-canary" not in output.err
