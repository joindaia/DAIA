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
