"""Evidence campaigns check structure and provenance binding, never execute submitted code."""
from concurrent.futures import ThreadPoolExecutor
import json
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


def test_operator_cli_verifies_real_git_excerpt(tmp_path):
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


def test_evidence_flow_through_two_stdio_workers(network, tmp_path):
    pytest.importorskip("mcp")
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client
    from daia.mcp_server import build_mcp_app
    from test_contributor import invite_file
    from test_mcp import call, running_server
    import time
    service, now = network
    now[0] = int(time.time())
    service.admit_evidence(document())
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
        assert outcomes == ["in_review", "ready_for_maintainer"]
    with running_server(build_mcp_app(service)) as url:
        asyncio.run(exercise(url))
    assert service.metrics()["promoted"] == 0
