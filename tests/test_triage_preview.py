"""Decision previews are advisory operator packets, never human approval."""
import json
import subprocess
import sys

import pytest

from conftest import submit
from daia.service import Denied
from test_evidence import document, packet


def snapshot(service):
    with service.store.connect() as db:
        return list(db.iterdump())


@pytest.mark.parametrize("stage", ["queued", "overdue_producer", "overdue_review", "pass", "inconclusive", "fail"])
def test_preview_matches_resolution_and_preserves_all_rows(network, contributor, stage):
    service, now = network
    job = service.admit_evidence(document())["job_id"]
    if stage != "queued":
        producer = contributor()
        lease = service.request_work(producer[0]["root_id"], producer[1])
        if stage != "overdue_producer":
            submit(service, producer, lease, packet(lease))
            reviewer = contributor()
            lease = service.request_work(reviewer[0]["root_id"], reviewer[1])
            if stage != "overdue_review":
                assessment = {"pass": "supports", "inconclusive": "unclear", "fail": "concerns"}[stage]
                submit(service, reviewer, lease, packet(lease, assessment=assessment), stage)
        if stage.startswith("overdue"):
            now[0] = lease["hard_deadline"] + 1
    note = "  Human considered the caf\u00e9 example; no verified defect.\n"
    before = snapshot(service)
    if stage != "pass":
        for dry_run in (True, False):
            with pytest.raises(Denied, match="review first"):
                service.resolve_evidence(job, "useful", note, dry_run=dry_run)
        assert snapshot(service) == before
    disposition = "useful" if stage == "pass" else "unclear"
    preview = service.resolve_evidence(job, disposition, note, dry_run=True)
    assert snapshot(service) == before
    assert preview["status"] == "preview" and preview["outcome"] == "resolved"
    assert preview["proposal"] == {"job_id": job, "disposition": disposition, "note": note}
    assert preview["approval_recorded"] is False and preview["correctness_verified"] is False
    assert preview["effects"] == {"jobs_to_cancel": int(stage in {"queued", "overdue_producer", "overdue_review"}),
                                  "recorded_leases_to_cancel": int(stage.startswith("overdue")),
                                  "new_terminal_decision": True}
    if stage in {"pass", "inconclusive", "fail"}:
        assert preview["reviews"] == [{"mode": "adversarial", "verdict": stage}]
    assert all(field not in json.dumps(preview) for field in ("root_id", "token", "signature", "artifact"))

    # The human action is separate; normal resolution re-evaluates the original gate.
    assert service.resolve_evidence(job, disposition, note)["status"] == "resolved"
    with service.store.connect() as db:
        assert db.execute("SELECT count(*) FROM jobs WHERE state='cancelled'").fetchone()[0] == preview["effects"]["jobs_to_cancel"]
        assert db.execute("SELECT count(*) FROM assignments WHERE state='cancelled'").fetchone()[0] == preview["effects"]["recorded_leases_to_cancel"]
    after = snapshot(service)
    retry = service.resolve_evidence(job, disposition, note, dry_run=True)
    assert retry["outcome"] == "already_resolved"
    assert retry["effects"] == {"jobs_to_cancel": 0, "recorded_leases_to_cancel": 0, "new_terminal_decision": False}
    for dry_run in (True, False):
        with pytest.raises(Denied, match="overwritten"):
            service.resolve_evidence(job, disposition, "Changed note", dry_run=dry_run)
    assert snapshot(service) == after


def test_cli_preview_is_nonmutating_and_missing_database_is_not_created(network, tmp_path):
    service, _ = network
    job = service.admit_evidence(document())["job_id"]
    before = snapshot(service)
    args = ["resolve-evidence", "--job", job, "--disposition", "cancelled", "--note", "Human proposal", "--dry-run"]
    result = subprocess.run([sys.executable, "-m", "daia.cli", "--db", service.store.path, *args],
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["approval_recorded"] is False
    assert snapshot(service) == before
    missing = tmp_path / "missing" / "database.sqlite3"
    result = subprocess.run([sys.executable, "-m", "daia.cli", "--db", str(missing), *args],
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 1 and result.stdout == ""
    assert not missing.parent.exists()


def test_preview_does_not_authorize_overwriting_a_later_decision(network):
    service, _ = network
    job = service.admit_evidence(document())["job_id"]
    service.resolve_evidence(job, "unclear", "First proposal", dry_run=True)
    service.resolve_evidence(job, "cancelled", "Later human decision")
    before = snapshot(service)
    with pytest.raises(Denied, match="overwritten"):
        service.resolve_evidence(job, "unclear", "First proposal")
    assert snapshot(service) == before
