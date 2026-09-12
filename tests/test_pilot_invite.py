"""Private invite publication and compensating revocation use disposable grants."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from scripts import pilot_invite
from daia.service import Coordinator, Denied


URL = "http://coordinator.example-tailnet.ts.net:8330/mcp"


def arguments(service, target):
    return ["scripts/pilot_invite.py", "--db", service.store.path,
            "--output", str(target), "--url", URL, "--max-jobs", "2"]


def test_invite_cli_success_and_existing_destination(network, tmp_path):
    service, _ = network
    service.clock = time.time
    target = tmp_path / "private" / "invite.json"
    command = [sys.executable, *arguments(service, target)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    before = target.read_bytes()
    grant = json.loads(before)
    assert grant["url"] == URL and grant["network_id"] == service.network_id
    assert service.authenticate(grant["token"]) == grant["root_id"]
    if os.name == "posix":
        assert target.stat().st_mode & 0o077 == 0
    result = subprocess.run(command, capture_output=True, text=True, timeout=20)
    assert result.returncode == 1 and result.stdout == ""
    assert "Traceback" not in result.stderr and str(tmp_path) not in result.stderr
    assert target.read_bytes() == before
    with service.store.connect() as db:
        assert db.execute("SELECT max_jobs,revoked FROM contributors").fetchall()[0][:] == (2, 0)
        assert db.execute("SELECT count(*) FROM contributors").fetchone()[0] == 1


@pytest.mark.parametrize("failure", ["initialization", "partial_write", "fsync", "cleanup", "revoke", "invite_return"])
def test_invite_failure_preserves_output_and_reports_uncertain_revocation(network, tmp_path, monkeypatch, capsys, failure):
    service, _ = network
    service.clock = time.time
    target = tmp_path / "private" / "invite.json"
    monkeypatch.setattr(sys, "argv", arguments(service, target))
    reached = []

    def fail(*args, **kwargs):
        reached.append(True)
        if failure in {"partial_write", "revoke"}:
            args[1].write('{"partial":')
            args[1].flush()
        raise OSError("private-invite-canary")

    with monkeypatch.context() as fault:
        if failure == "initialization":
            fault.setattr(Coordinator, "__init__", fail)
        elif failure in {"partial_write", "revoke"}:
            fault.setattr(json, "dump", fail)
            if failure == "revoke":
                def revoke_failure(*args):
                    raise OSError("private-revoke-canary")
                fault.setattr(Coordinator, "revoke", revoke_failure)
        elif failure == "fsync":
            fault.setattr(os, "fsync", fail)
        elif failure == "invite_return":
            invite = Coordinator.invite
            def commit_then_fail(*args, **kwargs):
                invite(*args, **kwargs)
                fail()
            fault.setattr(Coordinator, "invite", commit_then_fail)
        else:
            cleanup = pilot_invite.TemporaryDirectory.cleanup
            def cleanup_then_fail(temporary):
                cleanup(temporary)
                fail()
            fault.setattr(pilot_invite.TemporaryDirectory, "cleanup", cleanup_then_fail)
        with pytest.raises(SystemExit) as error:
            pilot_invite.main()
        assert error.value.code == 1
    assert reached == [True]
    output = capsys.readouterr()
    assert output.out == ""
    assert "Do not use or share any output" in output.err
    assert "canary" not in output.err and str(tmp_path) not in output.err
    if failure in {"revoke", "invite_return"}:
        assert "Revocation could not be confirmed" in output.err
    assert target.exists() == (failure == "cleanup")
    assert not list(target.parent.glob(".daia-invite-*"))
    with service.store.connect() as db:
        rows = db.execute("SELECT revoked FROM contributors").fetchall()
        assert [row[0] for row in rows] == ([] if failure == "initialization" else [int(failure not in {"revoke", "invite_return"})])
    if target.exists():
        with pytest.raises(Denied):
            service.authenticate(json.loads(target.read_bytes())["token"])


def test_invite_destination_race_preserves_competing_grant(network, tmp_path, monkeypatch, capsys):
    service, _ = network
    service.clock = time.time
    competing = service.invite()
    target = tmp_path / "private" / "invite.json"
    monkeypatch.setattr(sys, "argv", arguments(service, target))
    link = os.link
    reached = []

    def race(source, destination):
        assert not target.exists()
        staged = json.loads(Path(source).read_bytes())
        reached.append(staged["root_id"])
        assert staged["url"] == URL
        if os.name == "posix":
            assert Path(source).stat().st_mode & 0o077 == 0
        target.write_text(json.dumps(competing), encoding="utf-8")
        link(source, destination)

    monkeypatch.setattr(os, "link", race)
    with pytest.raises(SystemExit) as error:
        pilot_invite.main()
    assert error.value.code == 1 and len(reached) == 1
    assert json.loads(target.read_bytes()) == competing
    assert service.authenticate(competing["token"]) == competing["root_id"]
    with service.store.connect() as db:
        assert db.execute("SELECT revoked FROM contributors WHERE id=?", (reached[0],)).fetchone()[0] == 1
    assert not list(target.parent.glob(".daia-invite-*"))
    output = capsys.readouterr()
    assert output.out == "" and str(tmp_path) not in output.err
