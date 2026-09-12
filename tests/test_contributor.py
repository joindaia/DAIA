"""Contributor restart and loss recovery, plus the actual stdio -> HTTP SDK path."""
import asyncio
import errno
import json
import subprocess
import sys
import time
import tomllib

import pytest

pytest.importorskip("mcp")
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from daia.contributor import Contributor, configure, exclusive_host
import daia.contributor as contributor_module
from daia.mcp_server import build_mcp_app
from daia.service import Coordinator
from daia.store import Store
from test_mcp import call, running_server


def invite_file(tmp_path, service, url="http://127.0.0.1:8000/mcp", *, max_jobs=3, lifetime=86400):
    invite = {**service.invite(max_jobs=max_jobs, lifetime=lifetime),
              "network_id": service.network_id, "url": url}
    path = tmp_path / (invite["root_id"] + ".json")
    path.write_text(json.dumps(invite), encoding="utf-8")
    return path


def direct(host, service, lose=None):
    async def remote(name, **args):
        root = service.authenticate(host.identity["token"])
        routes = {
            "registration_challenge": lambda: service.challenge(root, args["public_key"]),
            "register_agent": lambda: service.register(root, args["challenge_id"], args["signature"]),
            "contribution_status": lambda: service.contribution_status(root, args["agent_id"]),
            "request_work": lambda: service.request_work(root, args["agent_id"]),
            "heartbeat": lambda: service.heartbeat(root, args["agent_id"], args["assignment_id"]),
            "release_work": lambda: service.release(root, args["agent_id"], args["assignment_id"]),
            "submission_envelope": lambda: service.envelope(root, args["agent_id"], args["assignment_id"], args["artifact"], args["verdict"]),
            "submit_result": lambda: service.submit(root, args["agent_id"], args["assignment_id"], args["artifact"], args["verdict"], args["signature"]),
        }
        result = routes[name]()
        if name == lose:
            raise ValueError("Simulated response loss after committed operation")
        return result
    host.remote = remote
    return host


def test_restart_lost_claim_and_receipt_keep_budget(tmp_path):
    now = [int(time.time())]
    clock = lambda: now[0]
    service = Coordinator(Store(str(tmp_path / "state.sqlite3")), clock=clock)
    service.seed()
    path = invite_file(tmp_path, service)

    async def exercise():
        host = direct(Contributor(path, minutes=1, clock=clock), service, lose="request_work")
        with pytest.raises(ValueError, match="response loss"):
            await host.perform("request_work")
        host = direct(Contributor(path, max_jobs=10, minutes=60, clock=clock), service)
        lease = await host.perform("request_work")
        assert lease["mode"] == "produce"
        assert host.state["used"] == host.state["max_jobs"] == 1
        assert host.state["deadline"] == now[0] + 60
        direct(host, service, lose="submit_result")
        with pytest.raises(ValueError, match="response loss"):
            await host.perform("submit_result", artifact='{"factors":[101,103]}', verdict="candidate")
        now[0] += 301
        host = direct(Contributor(path, clock=clock), service)
        with pytest.raises(ValueError, match="exact pending"):
            await host.perform("submit_result", artifact="changed", verdict="candidate")
        receipt = await host.perform("submit_result", artifact='{"factors":[101,103]}', verdict="candidate")
        assert receipt["status"] == "already_recorded"
        assert (await host.perform("request_work"))["status"] == "expired"
        assert service.metrics() == {"jobs": 3, "results": 1, "promoted": 0}
    asyncio.run(exercise())


def test_explicit_renewal_is_finite_capped_and_survives_restart(tmp_path):
    now = [int(time.time())]
    clock = lambda: now[0]
    service = Coordinator(Store(str(tmp_path / "state.sqlite3")), clock=clock)
    service.seed()
    path = invite_file(tmp_path, service, lifetime=60)

    async def exercise():
        host = direct(Contributor(path, minutes=1, clock=clock), service)
        lease = await host.perform("request_work")
        preserved = {key: host.state[key] for key in (
            "key", "identity", "used", "lease", "pending", "receipt", "stopped")}
        renewed = await host.renew_consent(additional_jobs=10, minutes=120)
        assert renewed["jobs_added"] == 2
        assert renewed["max_jobs"] == 3
        assert renewed["deadline"] == host.identity["expires"]
        assert {key: host.state[key] for key in preserved} == preserved

        # Ordinary launch flags neither expand nor erase the explicit renewal.
        restarted = Contributor(path, max_jobs=1, minutes=1, clock=clock)
        assert restarted.state["max_jobs"] == 3
        assert restarted.state["deadline"] == host.identity["expires"]
        assert restarted.state["lease"] == lease

    asyncio.run(exercise())


def test_renewal_refuses_stopped_and_revoked_grants(tmp_path):
    service = Coordinator(Store(str(tmp_path / "state.sqlite3")))
    path = invite_file(tmp_path, service)

    async def exercise():
        host = direct(Contributor(path), service)
        await host.perform("stop_contributing")
        with pytest.raises(ValueError, match="Stopped or expired"):
            await host.renew_consent(1, 60)

        other_path = invite_file(tmp_path, service)
        other = direct(Contributor(other_path), service)
        service.revoke(other.identity["root_id"])
        with pytest.raises(ValueError, match="Unauthorized"):
            await other.renew_consent(1, 60)

    asyncio.run(exercise())


def test_renewal_refuses_expired_grant(tmp_path):
    now = [int(time.time())]
    clock = lambda: now[0]
    service = Coordinator(Store(str(tmp_path / "state.sqlite3")), clock=clock)
    path = invite_file(tmp_path, service, lifetime=60)
    host = direct(Contributor(path, clock=clock), service)
    now[0] += 60
    with pytest.raises(ValueError, match="Stopped or expired"):
        asyncio.run(host.renew_consent(1, 60))


def test_explicit_renewal_reopens_expired_local_window(tmp_path):
    now = [int(time.time())]
    clock = lambda: now[0]
    service = Coordinator(Store(str(tmp_path / "state.sqlite3")), clock=clock)
    path = invite_file(tmp_path, service)
    host = direct(Contributor(path, minutes=1, clock=clock), service)
    now[0] += 60
    assert host.status()["status"] == "expired"
    renewed = asyncio.run(host.renew_consent(1, 60))
    assert renewed["status"] == "ready"
    assert renewed["jobs_added"] == 1
    assert renewed["deadline"] == now[0] + 3600


def test_renewal_cli_is_one_shot_and_rejects_unpaired_argument(tmp_path, monkeypatch, capsys):
    service = Coordinator(Store(str(tmp_path / "state.sqlite3")))
    path = invite_file(tmp_path, service)
    calls = []

    async def renew(host, additional_jobs, minutes):
        calls.append((additional_jobs, minutes))
        return {"jobs_added": additional_jobs, "deadline": 123}

    def unexpected_server(host):
        raise AssertionError("renewal must not start the MCP host")

    monkeypatch.setattr(Contributor, "renew_consent", renew)
    monkeypatch.setattr(contributor_module, "build_server", unexpected_server)
    monkeypatch.setattr(sys, "argv", ["daia.contributor", "--invite", str(path),
                                      "--renew-consent", "--additional-jobs", "2",
                                      "--minutes", "60"])
    contributor_module.main()
    assert calls == [(2, 60)]
    assert "2 jobs added" in capsys.readouterr().out

    other = invite_file(tmp_path, service)
    monkeypatch.setattr(sys, "argv", ["daia.contributor", "--invite", str(other),
                                      "--additional-jobs", "1"])
    with pytest.raises(SystemExit) as error:
        contributor_module.main()
    assert error.value.code == 2
    assert not other.with_suffix(".contributor.json").exists()


def test_failed_renewal_write_exits_without_serving_or_expanding_consent(tmp_path, monkeypatch, capsys):
    service = Coordinator(Store(str(tmp_path / "state.sqlite3")))
    path = invite_file(tmp_path, service)
    host = direct(Contributor(path), service)
    asyncio.run(host.register())
    saved = host.path.read_bytes()
    before = json.loads(saved)
    replace = contributor_module.os.replace
    failure_injected = False

    def fail_renewed_write(source, target):
        nonlocal failure_injected
        proposed = json.loads(source.read_text(encoding="utf-8"))
        if proposed["max_jobs"] > before["max_jobs"]:
            failure_injected = True
            raise PermissionError("Injected replacement failure")
        return replace(source, target)

    async def remote(current, name, **arguments):
        return await direct(current, service).remote(name, **arguments)

    def unexpected_server(current):
        raise AssertionError("Failed renewal must exit instead of serving MCP")

    monkeypatch.setattr(Contributor, "remote", remote)
    monkeypatch.setattr(contributor_module.os, "replace", fail_renewed_write)
    monkeypatch.setattr(contributor_module, "build_server", unexpected_server)
    monkeypatch.setattr(sys, "argv", ["daia.contributor", "--invite", str(path),
                                      "--renew-consent", "--additional-jobs", "1",
                                      "--minutes", "60"])
    with pytest.raises(SystemExit) as error:
        contributor_module.main()
    assert failure_injected
    assert error.value.code == 1
    assert "consent renewed" not in capsys.readouterr().out
    assert host.path.read_bytes() == saved
    assert not list(tmp_path.glob(".contributor-*"))
    with exclusive_host(path.with_suffix(".contributor.lock")):
        restarted = Contributor(path, max_jobs=100, minutes=1440)
    assert restarted.state == before
    assert service.contribution_status(host.identity["root_id"], host.agent)["assigned"] == 0


def test_stop_persists_when_disconnected_and_lock_releases(tmp_path):
    service = Coordinator(Store(str(tmp_path / "state.sqlite3")))
    service.seed()
    path = invite_file(tmp_path, service)

    async def exercise():
        host = direct(Contributor(path), service)
        await host.perform("request_work")
        async def offline(*args, **kwargs):
            raise ValueError("Disconnected")
        host.remote = offline
        assert (await host.perform("release_work"))["status"] == "release_pending"
        assert (await host.perform("stop_contributing"))["status"] == "stopped"
        host = direct(Contributor(path), service)
        assert (await host.perform("request_work"))["status"] == "stopped"
        assert (await host.perform("release_work"))["status"] == "stopped"
        assert (await host.perform("stop_contributing"))["lease"] is None
        assert service.contribution_status(host.identity["root_id"], host.agent)["lease"] is None
    asyncio.run(exercise())
    lock = tmp_path / "host.lock"
    with exclusive_host(lock):
        with pytest.raises(ValueError, match="active contributor"):
            with exclusive_host(lock):
                pass
    with exclusive_host(lock):
        pass


def test_native_stdio_host_through_real_http(tmp_path):
    service = Coordinator(Store(str(tmp_path / "state.sqlite3")))
    service.seed()
    async def exercise(path):
        parameters = StdioServerParameters(command=sys.executable, args=[
            "-m", "daia.contributor", "--invite", str(path)])
        async with stdio_client(parameters) as streams:
            async with ClientSession(*streams) as session:
                result = await session.initialize()
                assert "untrusted data" in result.instructions
                names = {t.name for t in (await session.list_tools()).tools}
                assert names == {"contribution_status", "request_work", "heartbeat", "submit_result", "release_work", "stop_contributing"}
                assert (await call(session, "contribution_status"))["status"] == "ready"
                lease = await call(session, "request_work")
                assert lease["mode"] == "produce"
                assert "token" not in json.dumps(lease)
                await call(session, "heartbeat")
                receipt = await call(session, "submit_result", artifact='{"factors":[101,103]}', verdict="candidate")
                assert receipt["status"] == "in_review"
        # A fresh OS process retains its budget and receipt.
        async with stdio_client(parameters) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                status = await call(session, "request_work")
                assert status["status"] == "budget_exhausted"
                assert status["receipt"] == receipt
                assert (await call(session, "release_work"))["status"] == "budget_exhausted"
                await call(session, "stop_contributing")
    with running_server(build_mcp_app(service)) as url:
        asyncio.run(exercise(invite_file(tmp_path, service, url)))


def test_project_configuration_preserves_settings(tmp_path):
    directory = tmp_path / ".codex"
    directory.mkdir()
    config = directory / "config.toml"
    config.write_text('model = "existing"\n[mcp_servers.other]\ncommand = "other"\n')
    invite = tmp_path / "invite.json"
    invite.write_text('{"token":"never-copy-this-token"}')
    configure(tmp_path, invite)
    original = config.read_text()
    configure(tmp_path, invite)
    assert config.read_text() == original
    assert "never-copy-this-token" not in original
    parsed = tomllib.loads(original)
    assert parsed["model"] == "existing"
    assert parsed["mcp_servers"]["other"]["command"] == "other"
    with pytest.raises(ValueError, match="different DAIA"):
        configure(tmp_path, invite, max_jobs=2)


def test_busy_cli_reports_contention_without_changing_private_state(tmp_path):
    service = Coordinator(Store(str(tmp_path / "state.sqlite3")))
    path = invite_file(tmp_path, service)
    host = Contributor(path)
    saved = host.path.read_bytes()
    with exclusive_host(path.with_suffix(".contributor.lock")):
        result = subprocess.run([sys.executable, "-m", "daia.contributor", "--invite", str(path)],
                                stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=15)
    assert result.returncode == 1
    assert result.stdout == ""
    assert "already has an active contributor host" in result.stderr
    assert "Keep the saved state" in result.stderr
    assert "Traceback" not in result.stderr
    assert str(path) not in result.stderr
    assert host.identity["token"] not in result.stderr
    assert host.state["key"] not in result.stderr
    assert host.path.read_bytes() == saved
    with exclusive_host(path.with_suffix(".contributor.lock")):
        assert Contributor(path).state == host.state


def test_other_lock_errors_are_not_reported_as_contention(tmp_path, monkeypatch):
    if sys.platform == "win32":
        import msvcrt as locking_module
        operation = "locking"
    else:
        import fcntl as locking_module
        operation = "flock"

    def fail(*arguments):
        raise OSError(errno.EIO, "Injected I/O failure")

    monkeypatch.setattr(locking_module, operation, fail)
    with pytest.raises(OSError) as error:
        with exclusive_host(tmp_path / "host.lock"):
            pytest.fail("Lock failure must not admit a helper")
    assert error.value.errno == errno.EIO


@pytest.mark.skipif(sys.platform != "win32", reason="Windows file-sharing semantics")
@pytest.mark.parametrize("release_reader", [True, False])
def test_atomic_save_retries_same_stage_under_windows_reader(tmp_path, monkeypatch, release_reader):
    service = Coordinator(Store(str(tmp_path / "state.sqlite3")))
    path = invite_file(tmp_path, service)
    host = Contributor(path)
    before = host.path.read_bytes()
    host.state["stopped"] = True
    replace = contributor_module.os.replace
    stages, waits = [], []
    with host.path.open("rb") as reader:
        def held_replace(source, target):
            stages.append((source, source.read_bytes()))
            try:
                return replace(source, target)
            except OSError as error:
                assert error.winerror in {5, 32, 33}
                assert host.path.read_bytes() == before
                if release_reader:
                    reader.close()
                raise

        monkeypatch.setattr(contributor_module.os, "replace", held_replace)
        monkeypatch.setattr(contributor_module.time, "sleep", waits.append)
        if release_reader:
            host.save()
            assert json.loads(host.path.read_bytes()) == host.state
            assert len(stages) == 2 and waits == [0.05]
        else:
            with pytest.raises(OSError):
                host.save()
            assert host.path.read_bytes() == before
            assert len(stages) == 3 and waits == [0.05, 0.05]
    assert all(stage == stages[0] for stage in stages)
    assert not list(tmp_path.glob(".contributor-*"))


def test_atomic_save_does_not_retry_unrelated_errors(tmp_path, monkeypatch):
    service = Coordinator(Store(str(tmp_path / "state.sqlite3")))
    host = Contributor(invite_file(tmp_path, service))
    before = host.path.read_bytes()
    attempts, waits = [], []

    def fail(source, target):
        attempts.append(source)
        raise OSError(errno.EIO, "Injected I/O failure")

    monkeypatch.setattr(contributor_module.os, "replace", fail)
    monkeypatch.setattr(contributor_module.time, "sleep", waits.append)
    with pytest.raises(OSError) as error:
        host.save()
    assert error.value.errno == errno.EIO
    assert len(attempts) == 1 and not waits
    assert host.path.read_bytes() == before
    assert not list(tmp_path.glob(".contributor-*"))


def test_empty_queue_tampered_envelope_and_revocation(tmp_path):
    service = Coordinator(Store(str(tmp_path / "state.sqlite3")))
    path = invite_file(tmp_path, service)
    async def exercise():
        host = direct(Contributor(path), service)
        assert (await host.perform("request_work"))["status"] == "no_eligible_work"
        assert host.state["used"] == 0
        service.seed()
        await host.perform("request_work")
        original = host.remote
        async def tampered(name, **arguments):
            result = await original(name, **arguments)
            if name == "submission_envelope":
                result["job_id"] = "different-job"
            return result
        host.remote = tampered
        with pytest.raises(ValueError, match="does not match"):
            await host.perform("submit_result", artifact='{"factors":[101,103]}', verdict="candidate")
        assert host.state["pending"] is None
        assert service.metrics()["results"] == 0
        direct(host, service)
        service.revoke(host.identity["root_id"])
        with pytest.raises(ValueError, match="Unauthorized"):
            await host.perform("request_work")
        assert (await host.perform("stop_contributing"))["status"] == "stopped"
    asyncio.run(exercise())


def test_release_keeps_budget_cooldown_and_exposure(tmp_path):
    now = [int(time.time())]
    clock = lambda: now[0]
    service = Coordinator(Store(str(tmp_path / "state.sqlite3")), clock=clock)
    service.seed()
    path = invite_file(tmp_path, service)

    async def exercise():
        host = direct(Contributor(path, max_jobs=3, clock=clock), service)
        await host.perform("request_work")
        deadline, key = host.state["deadline"], host.state["key"]
        result = await host.perform("release_work")
        assert result["release"] == "confirmed" and result["lease"] is None
        assert result["jobs_used"] == 1 and not host.state["stopped"]
        grant = service.contribution_status(host.identity["root_id"], host.agent)
        assert grant["assigned"] == 1 and grant["cooldown_until"] == now[0] + 30
        assert (await host.perform("request_work"))["status"] == "budget_or_cooldown"
        now[0] += 31
        assert (await host.perform("request_work"))["status"] == "no_eligible_work"
        assert host.state["used"] == 1
        del host.state["releasing"]  # Existing helper state files predate per-job refusal.
        host.save()
        restarted = direct(Contributor(path, max_jobs=9, clock=clock), service)
        assert restarted.state["key"] == key and restarted.state["deadline"] == deadline
        service.seed(35)
        assert (await restarted.perform("request_work"))["context"]["number"] == 35
        assert restarted.state["used"] == 2 and restarted.state["max_jobs"] == 3
    asyncio.run(exercise())


@pytest.mark.parametrize("failure", ["status_offline", "before_release", "after_release"])
def test_release_intent_survives_failure_restart_and_local_expiry(tmp_path, failure):
    now = [int(time.time())]
    clock = lambda: now[0]
    service = Coordinator(Store(str(tmp_path / "state.sqlite3")), clock=clock)
    service.seed()
    path = invite_file(tmp_path, service)

    async def exercise():
        host = direct(Contributor(path, max_jobs=2, minutes=1, clock=clock), service)
        lease = await host.perform("request_work")
        remote = host.remote

        async def unreliable(name, **arguments):
            if name == "release_work":
                saved = json.loads(host.path.read_text())
                assert saved["releasing"]["assignment_id"] == arguments["assignment_id"] == lease["assignment_id"]
                if failure == "before_release":
                    raise ValueError("Offline before release")
            if failure == "status_offline" and name == "contribution_status":
                raise ValueError("Offline before status")
            result = await remote(name, **arguments)
            if failure == "after_release" and name == "release_work":
                raise ValueError("Lost committed release response")
            return result

        host.remote = unreliable
        assert (await host.perform("release_work"))["status"] == "release_pending"
        # Pending refusal also fences attempts to keep working before a reconnect.
        if failure != "after_release":
            assert (await host.perform("heartbeat"))["status"] == "release_pending"
            assert (await host.perform("submit_result", artifact="must not submit", verdict="candidate"))["status"] == "release_pending"
        now[0] += 61
        host = direct(Contributor(path, clock=clock), service)
        result = await host.perform("request_work")  # Cleanup only, even after local expiry.
        assert result["status"] == "expired" and not result["release_pending"]
        assert result["lease"] is None and result["jobs_used"] == 1
        assert not host.state["stopped"]
        assert service.contribution_status(host.identity["root_id"], host.agent)["assigned"] == 1
        with service.store.connect() as db:
            assert db.execute("SELECT state FROM assignments WHERE id=?", (lease["assignment_id"],)).fetchone()[0] == "released"
    asyncio.run(exercise())


def test_release_does_not_follow_a_changed_assignment(tmp_path):
    now = [int(time.time())]
    clock = lambda: now[0]
    service = Coordinator(Store(str(tmp_path / "state.sqlite3")), clock=clock)
    service.seed()
    path = invite_file(tmp_path, service)

    async def exercise():
        host = direct(Contributor(path, max_jobs=3, clock=clock), service)
        old = await host.perform("request_work")
        direct(host, service, lose="release_work")
        assert (await host.perform("release_work"))["status"] == "release_pending"
        now[0] += 31
        service.seed(35)
        # Simulate outside activity with the same key; stale refusal must not target it.
        new = service.request_work(host.identity["root_id"], host.agent)
        assert new["assignment_id"] != old["assignment_id"]
        host = direct(Contributor(path, clock=clock), service)
        result = await host.perform("heartbeat")
        assert result["release"] == "assignment_changed" and result["lease"] == new
        assert service.contribution_status(host.identity["root_id"], host.agent)["lease"] == new
        assert (await host.perform("stop_contributing"))["status"] == "stopped"
        assert service.contribution_status(host.identity["root_id"], host.agent)["lease"] is None
    asyncio.run(exercise())


def test_release_recovers_lost_claim_but_preserves_pending_receipts(tmp_path):
    service = Coordinator(Store(str(tmp_path / "state.sqlite3")))
    service.seed()
    path = invite_file(tmp_path, service)

    async def exercise():
        host = direct(Contributor(path), service, lose="request_work")
        with pytest.raises(ValueError):
            await host.perform("request_work")
        assert host.state["lease"] is None and host.state["claiming"]
        direct(host, service)
        assert (await host.perform("release_work"))["release"] == "confirmed"
        assert host.state["used"] == 1
        other = direct(Contributor(invite_file(tmp_path, service)), service)
        await other.perform("request_work")
        direct(other, service, lose="submit_result")
        with pytest.raises(ValueError):
            await other.perform("submit_result", artifact='{"factors":[101,103]}', verdict="candidate")
        saved = other.path.read_bytes()
        with pytest.raises(ValueError, match="pending receipt"):
            await other.perform("release_work")
        assert other.path.read_bytes() == saved
        direct(other, service)
        assert (await other.perform("stop_contributing"))["status"] == "stopped"
        assert other.state["pending"] is not None and service.metrics()["results"] == 1
    asyncio.run(exercise())


def test_native_stdio_release_declines_one_job(tmp_path):
    service = Coordinator(Store(str(tmp_path / "state.sqlite3")))
    service.seed()

    async def exercise(path):
        parameters = StdioServerParameters(command=sys.executable, args=[
            "-m", "daia.contributor", "--invite", str(path)])
        async with stdio_client(parameters) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                lease = await call(session, "request_work")
                assert lease["mode"] == "produce"
                result = await call(session, "release_work")
                assert result["release"] == "confirmed" and result["status"] == "budget_exhausted"
        async with stdio_client(parameters) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                status = await call(session, "contribution_status")
                assert status["status"] == "budget_exhausted" and status["jobs_used"] == 1
                assert status["lease"] is None and status["grant"]["assigned"] == 1
    with running_server(build_mcp_app(service)) as url:
        asyncio.run(exercise(invite_file(tmp_path, service, url)))
