"""Finite operator continuation preserves contributor history and host authority."""
from concurrent.futures import ThreadPoolExecutor
import asyncio
import json
import sqlite3
import subprocess
import sys
import time

import pytest

from conftest import submit
from daia.cli import main
from daia.crypto import digest
from daia.service import Coordinator, Denied
from daia.store import Store
from test_evidence import document, packet


def snapshot(service):
    with service.store.connect() as db:
        tables = [row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        return {table: [dict(row) for row in db.execute(f'SELECT * FROM "{table}" ORDER BY rowid')]
                for table in tables}


def test_extension_preserves_receipts_exposure_and_same_root_exclusions(network, contributor):
    service, now = network
    service.admit_evidence(document())
    producer, reviewer = contributor(max_jobs=1), contributor(max_jobs=1)
    root, agent = producer[0]["root_id"], producer[1]
    lease = service.request_work(root, agent)
    submit(service, producer, lease, packet(lease))
    review_root, review_agent = reviewer[0]["root_id"], reviewer[1]
    review = service.request_work(review_root, review_agent)
    service.release(review_root, review_agent, review["assignment_id"])
    other_key = contributor(root=review_root)
    before = snapshot(service)
    expires = now[0] + 172800
    for identity in (root, review_root):
        preview = service.extend_grant(identity, 3, expires, dry_run=True)
        assert preview["status"] == "preview" and not preview["changed"]
        assert preview["assigned"] == 1 and preview["remaining"] == 2
        assert preview["additional_capacity"] == 2 and not preview["local_consent_changed"]
    assert snapshot(service) == before
    for identity in (root, review_root):
        assert service.extend_grant(identity, 3, expires)["status"] == "extended"
    after = snapshot(service)
    for table in before:
        if table not in {"contributors", "events", "sqlite_sequence"}:
            assert after[table] == before[table]
    assert after["sqlite_sequence"] == [{**row, "seq": row["seq"] + 2} if row["name"] == "events" else row
                                        for row in before["sqlite_sequence"]]
    for old, new in zip(before["contributors"], after["contributors"]):
        assert new == {**old, "max_jobs": 3, "expires": expires}
    assert after["events"][:-2] == before["events"]
    for event in after["events"][-2:]:
        value = json.loads(event["event_json"])
        assert value["kind"] == "contributor_grant_extended"
        assert value["details"] == {"previous": {"max_jobs": 1, "expires": producer[0]["expires"]},
                                    "proposed": {"max_jobs": 3, "expires": expires}}
        assert event["event_hash"] == digest({"previous": event["previous_hash"], "event": value})
    assert service.authenticate(producer[0]["token"]) == root
    now[0] += 31
    for identity, key in ((root, agent), (review_root, review_agent), (review_root, other_key[1])):
        assert service.request_work(identity, key)["status"] == "no_eligible_work"
    service.resolve_evidence(lease["job_id"], "unclear", "Synthetic test decision")
    next_job = service.admit_evidence(document("A different test objective"))["job_id"]
    assert service.request_work(root, agent)["job_id"] == next_job
    assert snapshot(service)["contributors"][0]["assigned"] == 2


def test_identical_concurrent_extensions_are_idempotent_and_stale_limits_fail(network, contributor):
    service, now = network
    who = contributor(max_jobs=1)
    root = who[0]["root_id"]
    service.seed()
    lease = service.request_work(root, who[1])
    now[0] += 301  # Preview/extension must not expire or otherwise mutate this recorded lease.
    before = snapshot(service)
    expires = now[0] + 172800
    service.extend_grant(root, 3, expires, dry_run=True)
    assert snapshot(service) == before
    with ThreadPoolExecutor(max_workers=4) as pool:
        outcomes = list(pool.map(lambda _: service.extend_grant(root, 3, expires)["status"], range(8)))
    assert outcomes.count("extended") == 1 and outcomes.count("already_extended") == 7
    after = snapshot(service)
    assert len(after["events"]) == len(before["events"]) + 1
    assert after["assignments"] == before["assignments"]
    service.extend_grant(root, 4, expires + 60)
    before_stale = snapshot(service)
    with pytest.raises(Denied):
        service.extend_grant(root, 3, expires)
    assert snapshot(service) == before_stale
    assert lease["assignment_id"] == before["assignments"][0]["id"]


@pytest.mark.parametrize("kind", ["unknown", "revoked", "expired", "shrink_jobs", "shrink_expiry",
                                  "too_many_jobs", "too_far", "bool_jobs", "bool_expiry", "float_expiry"])
def test_extension_denials_preserve_all_rows(network, kind):
    service, now = network
    grant = service.invite(max_jobs=2)
    root, maximum, expires = grant["root_id"], 3, now[0] + 172800
    if kind == "unknown":
        root = "unknown"
    elif kind == "revoked":
        service.revoke(root)
    elif kind == "expired":
        now[0] = grant["expires"]
    elif kind == "shrink_jobs":
        maximum = 1
    elif kind == "shrink_expiry":
        expires = grant["expires"] - 1
    elif kind == "too_many_jobs":
        maximum = 10001
    elif kind == "too_far":
        expires = now[0] + 604801
    elif kind == "bool_jobs":
        maximum = True
    elif kind == "bool_expiry":
        expires = True
    else:
        expires = float(expires)
    before = snapshot(service)
    for preview in (True, False):
        with pytest.raises(Denied):
            service.extend_grant(root, maximum, expires, dry_run=preview)
        assert snapshot(service) == before


@pytest.mark.parametrize("change", ["revoked", "expired"])
def test_grant_change_after_preview_is_rechecked(network, change):
    service, now = network
    grant = service.invite()
    root, expires = grant["root_id"], now[0] + 172800
    service.extend_grant(root, 21, expires, dry_run=True)
    if change == "revoked":
        service.revoke(root)
    else:
        now[0] = grant["expires"]
    before = snapshot(service)
    with pytest.raises(Denied):
        service.extend_grant(root, 21, expires)
    assert snapshot(service) == before


def test_audit_failure_rolls_back_grant(network, monkeypatch):
    service, now = network
    root = service.invite()["root_id"]
    before = snapshot(service)
    def fail(*args, **kwargs):
        raise sqlite3.OperationalError("private-storage-canary")
    monkeypatch.setattr(service, "_event", fail)
    with pytest.raises(sqlite3.OperationalError):
        service.extend_grant(root, 21, now[0] + 172800)
    assert snapshot(service) == before


def test_real_extension_cli_preview_apply_retry_and_missing_database(tmp_path):
    path = tmp_path / "existing.sqlite3"
    service = Coordinator(Store(str(path)))
    root = service.invite(max_jobs=1)["root_id"]
    expires = int(time.time()) + 172800
    arguments = ["extend-grant", "--root", root, "--max-jobs", "4", "--expires", str(expires)]
    def run(database, *extra):
        return subprocess.run([sys.executable, "-m", "daia.cli", "--db", str(database), *arguments, *extra],
                              capture_output=True, text=True, timeout=30)
    missing = tmp_path / "absent" / "missing.sqlite3"
    for extra in ([], ["--dry-run"]):
        result = run(missing, *extra)
        assert result.returncode == 1 and result.stdout == ""
        assert str(tmp_path) not in result.stderr and "Traceback" not in result.stderr
        assert not missing.parent.exists()
    before = snapshot(service)
    # Inclusive upper bounds are valid without reserving them.
    service.extend_grant(root, 10000, int(time.time()) + 604800, dry_run=True)
    assert snapshot(service) == before
    preview = run(path, "--dry-run")
    assert preview.returncode == 0 and json.loads(preview.stdout)["status"] == "preview"
    assert snapshot(service) == before
    assert json.loads(run(path).stdout)["status"] == "extended"
    applied = snapshot(service)
    assert json.loads(run(path).stdout)["status"] == "already_extended"
    assert snapshot(service) == applied
    assert json.loads(run(path, "--dry-run").stdout)["additional_capacity"] == 0
    empty = tmp_path / "empty.sqlite3"
    empty.touch(mode=0o600)
    assert run(empty).returncode == 1 and empty.read_bytes() == b""
    arguments[2] = "unknown-root-private-canary"
    result = run(path)
    assert result.returncode == 1 and result.stdout == ""
    assert "Grant extension refused" in result.stderr
    assert "unknown-root-private-canary" not in result.stderr and str(tmp_path) not in result.stderr
    assert snapshot(service) == applied


def test_cli_commit_then_error_reports_uncertainty_and_absolute_retry(network, monkeypatch, capsys):
    service, now = network
    now[0] = int(time.time())
    root = service.invite(max_jobs=1)["root_id"]
    monkeypatch.setattr(sys, "argv", ["daia", "--db", service.store.path, "extend-grant",
        "--root", root, "--max-jobs", "3", "--expires", str(now[0] + 172800)])
    original = Coordinator.extend_grant
    def fail_after_commit(instance, *args, **kwargs):
        original(instance, *args, **kwargs)
        raise sqlite3.OperationalError("private-storage-canary")
    with monkeypatch.context() as fault:
        fault.setattr(Coordinator, "extend_grant", fail_after_commit)
        with pytest.raises(SystemExit) as error:
            main()
        assert error.value.code == 1
    output = capsys.readouterr()
    assert not output.out and "could not be confirmed" in output.err
    assert all(value not in output.err for value in ("private-storage-canary", service.store.path, root))
    before = snapshot(service)
    main()
    assert json.loads(capsys.readouterr().out)["status"] == "already_extended"
    assert snapshot(service) == before


@pytest.mark.parametrize("stopped", [False, True])
def test_server_extension_never_renews_helper_or_original_invite(network, tmp_path, stopped):
    from daia.contributor import Contributor
    from test_contributor import direct, invite_file
    service, now = network
    path = invite_file(tmp_path, service, max_jobs=1, lifetime=120)
    clock = lambda: now[0]
    host = direct(Contributor(path, minutes=1, clock=clock), service)
    service.seed()
    asyncio.run(host.perform("request_work"))
    if stopped:
        asyncio.run(host.perform("stop_contributing"))
    saved, invite = host.path.read_bytes(), path.read_bytes()
    service.extend_grant(host.identity["root_id"], 3, now[0] + 172800)
    assert host.path.read_bytes() == saved and path.read_bytes() == invite
    restarted = direct(Contributor(path, max_jobs=100, minutes=1440, clock=clock), service)
    assert restarted.state == host.state
    assert restarted.state["used"] == restarted.state["max_jobs"] == 1
    if stopped:
        with pytest.raises(ValueError, match="Stopped or expired"):
            asyncio.run(restarted.renew_consent(2, 1440))
    else:
        # Even a separate explicit local renewal cannot exceed the original invite.
        result = asyncio.run(restarted.renew_consent(2, 1440))
        assert result["deadline"] == host.identity["expires"]
    now[0] = host.identity["expires"]
    with pytest.raises(ValueError, match="Stopped or expired"):
        asyncio.run(restarted.renew_consent(1, 60))
