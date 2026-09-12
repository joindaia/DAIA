"""Contributor restart and loss recovery, plus the actual stdio -> HTTP SDK path."""
import asyncio
import json
import sys
import time
import tomllib

import pytest

pytest.importorskip("mcp")
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from daia.contributor import Contributor, configure, exclusive_host
from daia.mcp_server import build_mcp_app
from daia.service import Coordinator
from daia.store import Store
from test_mcp import call, running_server


def invite_file(tmp_path, service, url="http://127.0.0.1:8000/mcp"):
    invite = {**service.invite(max_jobs=3), "network_id": service.network_id, "url": url}
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
        assert (await host.perform("stop_contributing"))["status"] == "stopped"
        host = direct(Contributor(path), service)
        assert (await host.perform("request_work"))["status"] == "stopped"
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
                assert names == {"contribution_status", "request_work", "heartbeat", "submit_result", "stop_contributing"}
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
