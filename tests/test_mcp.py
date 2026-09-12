"""Real SDK/HTTP interoperability; ephemeral loopback server and in-memory keys."""
import asyncio
import json
import socket
import threading
import time
from contextlib import contextmanager

import pytest
import httpx

pytest.importorskip("mcp")
import httpx2
import uvicorn
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client

from daia.crypto import public_hex, sign
from daia.mcp_server import build_mcp_app, pilot_origin
from daia.service import Coordinator
from daia.store import Store


@contextmanager
def running_server(app):
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
        server = uvicorn.Server(uvicorn.Config(
            app, log_level="critical", access_log=False, timeout_graceful_shutdown=2))
        thread = threading.Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
        thread.start()
        try:
            deadline = time.monotonic() + 10
            while not server.started:
                if not thread.is_alive() or time.monotonic() > deadline:
                    raise RuntimeError("MCP test server did not start")
                time.sleep(0.01)
            yield f"http://127.0.0.1:{port}/mcp"
        finally:
            server.should_exit = True
            thread.join(timeout=10)
            assert not thread.is_alive(), "MCP server did not stop"


async def call(session, name, **arguments):
    result = await session.call_tool(name, arguments)
    assert not result.is_error, result.content
    return result.structured_content or json.loads(result.content[0].text)


def test_real_mcp_three_contributors(tmp_path):
    service = Coordinator(Store(str(tmp_path / "mcp.sqlite3")))
    service.seed()
    grants = [service.invite(max_jobs=2) for _ in range(3)]

    async def exercise(url):
        statuses = []
        for grant in grants:
            async with httpx2.AsyncClient(headers={"Authorization": "Bearer " + grant["token"]}) as http:
                async with streamable_http_client(url, http_client=http) as streams:
                    async with ClientSession(streams[0], streams[1]) as session:
                        await session.initialize()
                        names = {t.name for t in (await session.list_tools()).tools}
                        assert names == {"registration_challenge", "register_agent", "request_work",
                                         "heartbeat", "release_work", "submission_envelope", "submit_result",
                                         "contribution_status"}
                        key = Ed25519PrivateKey.generate()
                        challenge = await call(session, "registration_challenge", public_key=public_hex(key))
                        identity = await call(session, "register_agent", challenge_id=challenge["challenge_id"],
                                              signature=sign(key, challenge))
                        aid = identity["agent_id"]
                        lease = await call(session, "request_work", agent_id=aid)
                        assert await call(session, "request_work", agent_id=aid) == lease
                        await call(session, "heartbeat", agent_id=aid, assignment_id=lease["assignment_id"])
                        artifact = '{"factors":[101,103]}'
                        verdict = "candidate" if lease["mode"] == "produce" else "pass"
                        args = dict(agent_id=aid, assignment_id=lease["assignment_id"],
                                    artifact=artifact, verdict=verdict)
                        envelope = await call(session, "submission_envelope", **args)
                        result = await call(session, "submit_result", **args, signature=sign(key, envelope))
                        statuses.append(result["status"])
                        replay = await call(session, "submit_result", **args, signature=sign(key, envelope))
                        assert replay["status"] == "already_recorded"
        assert statuses == ["in_review", "in_review", "promoted"]

    with running_server(build_mcp_app(service)) as url:
        asyncio.run(exercise(url))
    assert service.metrics() == {"jobs": 3, "results": 1, "promoted": 1}


def test_mcp_http_boundaries_and_revocation(tmp_path):
    service = Coordinator(Store(str(tmp_path / "auth.sqlite3")))
    first, second = service.invite(), service.invite()
    tailnet = "http://coordinator.example-tailnet.ts.net:8330/mcp"
    initialize = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
        "protocolVersion": "2025-03-26", "capabilities": {},
        "clientInfo": {"name": "daia-test", "version": "1"}}}
    headers = {"Accept": "application/json, text/event-stream",
               "Authorization": "Bearer " + first["token"],
               "Host": "coordinator.example-tailnet.ts.net:8330",
               "Origin": tailnet.removesuffix("/mcp")}
    with running_server(build_mcp_app(service, tailnet_url=tailnet)) as url, httpx.Client() as client:
        assert client.post(url, json=initialize).status_code == 401
        assert client.post(url, json=initialize, headers={**headers, "Authorization": "Bearer invalid"}).status_code == 401
        assert client.post(url, json=initialize, headers={**headers, "Host": "attacker.example"}).status_code == 421
        assert client.post(url, json=initialize, headers={**headers, "Origin": "https://attacker.example"}).status_code == 403
        assert client.post(url, content=b"x" * 16385, headers=headers).status_code == 413
        response = client.post(url, json=initialize, headers=headers)
        assert response.status_code == 200
        session_headers = {**headers, "Mcp-Session-Id": response.headers["mcp-session-id"],
                           "MCP-Protocol-Version": "2025-03-26"}
        client.post(url, json={"jsonrpc": "2.0", "method": "notifications/initialized"}, headers=session_headers)
        request = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
        assert client.post(url, json=request, headers=session_headers).status_code == 200
        # Another valid root cannot inherit the first root's session.
        changed = {**session_headers, "Authorization": "Bearer " + second["token"]}
        assert client.post(url, json=request, headers=changed).status_code in {403, 404}
        service.revoke(first["root_id"])
        assert client.post(url, json=request, headers=session_headers).status_code == 401


@pytest.mark.parametrize("url", [
    "http://attacker.example/mcp", "http://*.ts.net/mcp", "http://host.ts.net/not-mcp",
    "http://user:secret@" + "host.ts.net/mcp", "http://host.ts.net/mcp?extra=1",
    "http://host.ts.net:99999/mcp", "http://host.ts.net/mcp#fragment",
])
def test_pilot_origin_rejects_ambiguous_endpoints(url):
    with pytest.raises(ValueError):
        pilot_origin(url)


@pytest.mark.parametrize("raw", [b"null", b'"abc"', b"{}", b"[1]", b'["bad"]',
                                  b"[", b"x" * 20001])
def test_allowlist_invalid_file_is_rejected(tmp_path, raw):
    from daia.mcp_server import load_allowed_agents
    path = tmp_path / "allowlist.json"
    path.write_bytes(raw)
    with pytest.raises((ValueError, TypeError)):
        load_allowed_agents(path)


def test_allowlist_file_empty_duplicates_and_bound(tmp_path):
    from daia.mcp_server import load_allowed_agents
    path = tmp_path / "allowlist.json"
    path.write_text("[]")
    assert load_allowed_agents(path) == frozenset()
    path.write_text(json.dumps(["a" * 64]))
    assert load_allowed_agents(path) == frozenset({"a" * 64})
    for ids in [["a" * 64] * 2, [f"{i:064x}" for i in range(257)]]:
        path.write_text(json.dumps(ids))
        with pytest.raises(ValueError):
            load_allowed_agents(path)


@pytest.mark.parametrize("empty", [False, True])
def test_closed_mcp_admission_preserves_owner_binding_and_blocks_registration(network, contributor, empty):
    service, _ = network
    admitted = contributor()
    excluded = contributor(root=admitted[0]["root_id"])
    other = contributor()
    service.seed()
    allowed = [] if empty else [admitted[1]]
    app = build_mcp_app(service, allowed_agents=allowed)
    allowed.append(excluded[1])  # Runtime policy must not alias the caller's mutable list.

    async def exercise(url):
        async def connect(grant, action):
            async with httpx2.AsyncClient(headers={"Authorization": "Bearer " + grant["token"]}) as http:
                async with streamable_http_client(url, http_client=http) as streams:
                    async with ClientSession(streams[0], streams[1]) as session:
                        await session.initialize()
                        await action(session)

        async def owner(session):
            names = {t.name for t in (await session.list_tools()).tools}
            assert names == {"contribution_status", "request_work", "heartbeat", "release_work",
                             "submission_envelope", "submit_result"}
            for name, args in [("registration_challenge", {"public_key": public_hex(admitted[2])}),
                               ("register_agent", {"challenge_id": "0" * 32, "signature": "0" * 128})]:
                assert (await session.call_tool(name, args)).is_error
            for aid in ([admitted[1], excluded[1]] if empty else [excluded[1]]):
                for name in names:
                    args = {"agent_id": aid}
                    if name not in {"contribution_status", "request_work"}:
                        args["assignment_id"] = "0" * 32
                    if name in {"submission_envelope", "submit_result"}:
                        args.update(artifact="{}", verdict="candidate")
                    if name == "submit_result":
                        args["signature"] = "0" * 128
                    result = await session.call_tool(name, args)
                    assert result.is_error
                    assert "Agent not admitted" in str(result.content)
            if not empty:
                await call(session, "contribution_status", agent_id=admitted[1])
                lease = await call(session, "request_work", agent_id=admitted[1])
                args = dict(agent_id=admitted[1], assignment_id=lease["assignment_id"],
                            artifact='{"factors":[101,103]}', verdict="candidate")
                envelope = await call(session, "submission_envelope", **args)
                result = await call(session, "submit_result", **args, signature=sign(admitted[2], envelope))
                assert result["status"] == "in_review"
                assert (await call(session, "submit_result", **args,
                                   signature=sign(admitted[2], envelope)))["status"] == "already_recorded"

        async def wrong_owner(session):
            result = await session.call_tool("contribution_status", {"agent_id": admitted[1]})
            assert result.is_error

        await connect(admitted[0], owner)
        await connect(other[0], wrong_owner)

    with running_server(app) as url:
        asyncio.run(exercise(url))
    with service.store.connect() as db:
        assert db.execute("SELECT count(*) FROM agents").fetchone()[0] == 3
        assert db.execute("SELECT count(*) FROM challenges WHERE used=0").fetchone()[0] == 0
        assert db.execute("SELECT sum(assigned) FROM contributors").fetchone()[0] == (0 if empty else 1)


@pytest.mark.parametrize("missing", [False, True])
def test_cli_allowlist_error_does_not_start_server(tmp_path, missing):
    import subprocess
    import sys
    path = tmp_path / "private-allowlist-canary.json"
    if not missing:
        path.write_text("not json")
    result = subprocess.run([sys.executable, "-m", "daia.cli", "--db", str(tmp_path / "test.sqlite3"),
                             "serve-mcp", "--allowed-agents", str(path)],
                            capture_output=True, text=True, timeout=15)
    assert result.returncode == 1
    assert "Service not started" in result.stderr
    assert "private-allowlist-canary" not in result.stderr
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize("state", ["unregistered", "revoked"])
def test_closed_admission_does_not_replace_agent_validation(network, contributor, state):
    service, _ = network
    grant, aid, _ = contributor()
    if state == "unregistered":
        aid = "0" * 64
    else:
        with service.store.connect() as db:
            db.execute("UPDATE agents SET revoked=1 WHERE id=?", (aid,))
    service.seed()

    async def exercise(url):
        async with httpx2.AsyncClient(headers={"Authorization": "Bearer " + grant["token"]}) as http:
            async with streamable_http_client(url, http_client=http) as streams:
                async with ClientSession(streams[0], streams[1]) as session:
                    await session.initialize()
                    for tool in ["contribution_status", "request_work"]:
                        assert (await session.call_tool(tool, {"agent_id": aid})).is_error

    with running_server(build_mcp_app(service, allowed_agents={aid})) as url:
        asyncio.run(exercise(url))
    with service.store.connect() as db:
        assert db.execute("SELECT sum(assigned) FROM contributors").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM agents").fetchone()[0] == 1


@pytest.mark.parametrize("state", ["expired", "revoked"])
def test_closed_admission_does_not_replace_grant_validation(network, contributor, state):
    service, now = network
    grant, aid, _ = contributor()
    if state == "expired":
        now[0] = grant["expires"]
    else:
        service.revoke(grant["root_id"])
    with running_server(build_mcp_app(service, allowed_agents={aid})) as url:
        response = httpx.post(url, headers={"Authorization": "Bearer " + grant["token"],
                                           "Accept": "application/json, text/event-stream"},
                              json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        assert response.status_code == 401
