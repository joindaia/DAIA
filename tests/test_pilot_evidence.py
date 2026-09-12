"""Opt-in technical peer review never upgrades ownership to independence."""
import json
import pytest
from conftest import submit
from test_evidence import document, packet
from daia.service import Denied


@pytest.mark.parametrize("same_root", [True, False])
@pytest.mark.parametrize("verdict,assessment,expected", [
    ("pass", "supports", "pilot_ready_for_maintainer"),
    ("fail", "concerns", "disputed"),
    ("inconclusive", "unclear", "in_review"),
])
def test_two_agent_pilot_preserves_human_gate(network, contributor, same_root, verdict, assessment, expected):
    service, _ = network
    job = service.admit_evidence(document(), pilot=True)["job_id"]
    producer = contributor()
    root = producer[0]["root_id"]
    reviewer = contributor(root=root if same_root else None)
    lease = service.request_work(root, producer[1])
    assert lease["context"]["review_assurance"] == "pilot-technical-not-independent"
    assert lease["context"]["independent_review"] is False
    assert lease["context"]["shared_ownership_allowed"] is True
    if same_root:
        assert service.request_work(root, reviewer[1])["status"] == "other_agent_has_lease"
    submit(service, producer, lease, packet(lease))
    assert service.request_work(root, producer[1])["status"] == "no_eligible_work"
    with pytest.raises(Denied, match="review first"):
        service.resolve_evidence(job, "useful", "Too early")
    review = service.request_work(reviewer[0]["root_id"], reviewer[1])
    assert review["mode"] == "adversarial" and review["policy_hash"] == lease["policy_hash"]
    assert review["context"]["independent_review"] is False
    receipt = submit(service, reviewer, review, packet(review, assessment=assessment), verdict)
    assert receipt["status"] == expected
    inspected = service.inspect_evidence()[0]
    assert inspected["result"]["correctness_verified"] is False
    assert inspected["result"]["state"] == expected
    assert inspected["disposition"] is None
    if verdict != "pass":
        with pytest.raises(Denied, match="review first"):
            service.resolve_evidence(job, "useful", "Cannot override the review")
    disposition = "useful" if verdict == "pass" else "unclear"
    assert service.resolve_evidence(job, disposition, "Human technical triage", dry_run=True)["approval_recorded"] is False
    service.resolve_evidence(job, disposition, "Human technical triage")
    assert service.metrics()["promoted"] == 0


def test_pilot_never_rewrites_existing_campaign_or_default_policy(network, contributor):
    service, _ = network
    old = service.admit_evidence(document())
    with service.store.connect() as db:
        before = list(db.iterdump())
    assert service.admit_evidence(document(), pilot=True)["status"] == "campaign_unresolved"
    with service.store.connect() as db:
        assert list(db.iterdump()) == before
    producer = contributor()
    reviewer = contributor(root=producer[0]["root_id"])
    lease = service.request_work(producer[0]["root_id"], producer[1])
    submit(service, producer, lease, packet(lease))
    assert service.request_work(reviewer[0]["root_id"], reviewer[1])["status"] == "no_eligible_work"
    service.resolve_evidence(old["job_id"], "unclear", "Fixture operator closes old policy")
    new = service.admit_evidence(document(), pilot=True)
    assert new["status"] == "admitted" and new["job_id"] != old["job_id"]
    assert service.admit_evidence(document(), pilot=True) == {"status": "already_admitted", "job_id": new["job_id"]}
    new_lease = service.request_work(producer[0]["root_id"], producer[1])
    assert new_lease["policy_hash"] != lease["policy_hash"]
    assert new_lease["context_hash"] != lease["context_hash"]
    assert new_lease["context"]["checker_hash"] == lease["context"]["checker_hash"]
    assert new_lease["context"]["schema_hashes"] == lease["context"]["schema_hashes"]


@pytest.mark.parametrize("expires", [False, True])
def test_pilot_review_release_keeps_root_exclusion(network, contributor, expires):
    service, now = network
    service.admit_evidence(document(), pilot=True)
    producer = contributor()
    root = producer[0]["root_id"]
    reviewer = contributor(root=root)
    lease = service.request_work(root, producer[1])
    submit(service, producer, lease, packet(lease))
    review = service.request_work(root, reviewer[1])
    if expires:
        now[0] += 301
    else:
        service.release(root, reviewer[1], review["assignment_id"])
        now[0] += 31
    replacement = contributor(root=root)
    for who in (producer, reviewer, replacement):
        assert service.request_work(root, who[1])["status"] == "no_eligible_work"
    with pytest.raises(Denied):
        submit(service, reviewer, review, packet(review), "pass")


def test_pilot_requires_operator_boolean_not_document_injection(network):
    service, _ = network
    for value in (1, "true", None):
        with pytest.raises(Denied):
            service.admit_evidence(document(), pilot=value)
    with pytest.raises(Denied):
        service.admit_evidence({**document(), "pilot": True})


def test_real_cli_pilot_preparation_and_admission(tmp_path):
    from pathlib import Path
    import subprocess
    import sys
    from daia.store import Store
    repository = Path(__file__).resolve().parents[1]
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repository, text=True).strip()
    source = subprocess.check_output(['git', 'show', f'{commit}:src/daia/policy.py'], cwd=repository, text=True)
    doc = {'objective': 'Inspect the frozen policy without executing source.', 'baseline_commit': commit,
           'source': {'path': 'src/daia/policy.py', 'start_line': 1, 'text': source.splitlines(keepends=True)[0]}}
    context = tmp_path / 'context.json'
    context.write_text(json.dumps(doc))
    database = tmp_path / 'pilot.sqlite3'
    command = [sys.executable, '-m', 'daia.cli', '--db', str(database), 'admit-evidence',
               '--context', str(context), '--pilot']
    prepared = subprocess.run(command + ['--dry-run'], cwd=repository, capture_output=True, text=True, timeout=30)
    assert prepared.returncode == 0, prepared.stderr
    assert json.loads(prepared.stdout)['admitted'] is False
    assert not database.exists()
    admitted = subprocess.run(command, cwd=repository, capture_output=True, text=True, timeout=30)
    assert admitted.returncode == 0, admitted.stderr
    assert json.loads(admitted.stdout)['status'] == 'admitted'
    with Store(str(database), create=False).connect() as db:
        policy, frozen = db.execute('SELECT policy_json,context_json FROM jobs').fetchone()
    assert json.loads(policy)['version'] == 'source-evidence-pilot-v1'
    assert json.loads(frozen)['independent_review'] is False
