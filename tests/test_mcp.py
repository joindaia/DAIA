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
def running_server(app, **tls):
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
        server = uvicorn.Server(uvicorn.Config(
            app, log_level="critical", access_log=False, timeout_graceful_shutdown=2, **tls))
        thread = threading.Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
        thread.start()
        try:
            deadline = time.monotonic() + 10
            while not server.started:
                if not thread.is_alive() or time.monotonic() > deadline:
                    raise RuntimeError("MCP test server did not start")
                time.sleep(0.01)
            yield f"{'https' if tls else 'http'}://127.0.0.1:{port}/mcp"
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


def test_contributor_mutual_tls_real_mcp(tmp_path, monkeypatch):
    import datetime
    import ipaddress
    import ssl
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID
    from daia.contributor import Contributor

    now = datetime.datetime.now(datetime.timezone.utc)
    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Test CA")])

    def certificate(name, key, ca=False, client=False):
        builder = (x509.CertificateBuilder()
                   .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, name)]))
                   .issuer_name(ca_name).public_key(key.public_key())
                   .serial_number(x509.random_serial_number())
                   .not_valid_before(now - datetime.timedelta(minutes=1))
                   .not_valid_after(now + datetime.timedelta(days=1))
                   .add_extension(x509.BasicConstraints(ca=ca, path_length=None), critical=True)
                   .add_extension(x509.SubjectKeyIdentifier.from_public_key(key.public_key()), False)
                   .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()), False)
                   .add_extension(x509.KeyUsage(digital_signature=True, content_commitment=False,
                       key_encipherment=not ca, data_encipherment=False, key_agreement=False,
                       key_cert_sign=ca, crl_sign=ca, encipher_only=False, decipher_only=False), True))
        if not ca:
            builder = builder.add_extension(x509.ExtendedKeyUsage([
                ExtendedKeyUsageOID.CLIENT_AUTH if client else ExtendedKeyUsageOID.SERVER_AUTH]), False)
            if not client:
                builder = builder.add_extension(x509.SubjectAlternativeName([
                    x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]), False)
        return builder.sign(ca_key, hashes.SHA256()).public_bytes(serialization.Encoding.PEM)

    ca_path = tmp_path / "ca.pem"
    ca_path.write_bytes(certificate("Test CA", ca_key, ca=True))
    for name in ["server", "client"]:
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        (tmp_path / (name + ".pem")).write_bytes(certificate(name, key, client=name == "client"))
        (tmp_path / (name + ".key")).write_bytes(key.private_bytes(
            serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))

    service = Coordinator(Store(str(tmp_path / "tls.sqlite3")))
    grant = service.invite()
    with running_server(build_mcp_app(service),
                        ssl_certfile=str(tmp_path / "server.pem"),
                        ssl_keyfile=str(tmp_path / "server.key"),
                        ssl_ca_certs=str(ca_path), ssl_cert_reqs=ssl.CERT_REQUIRED) as url:
        identity = {**grant, "network_id": service.network_id, "url": url,
                    "tls": {"ca_file": "ca.pem", "certificate": "client.pem", "private_key": "client.key"}}
        invite = tmp_path / "invite.json"
        invite.write_text(json.dumps(identity))
        host = Contributor(invite)
        host.tls_context.verify_flags |= ssl.VERIFY_X509_STRICT
        asyncio.run(host.register())
        host.save()
        previous = dict(host.state)
        host = Contributor(invite)
        assert host.state == previous
        host.tls_context.verify_flags |= ssl.VERIFY_X509_STRICT
        result = asyncio.run(host.remote("contribution_status", agent_id=host.agent))
        assert isinstance(result, dict)
        assert host.state["used"] == 0
        # Exercise the migration transaction over real HTTP -> mutual TLS.
        # Only canonical public routing is replaced by this ephemeral loopback URL;
        # TLS verification, SDK calls and saved state are real.
        import daia.contributor as contributor_module
        with running_server(build_mcp_app(service)) as old_url:
            original = tmp_path / "migration-invite.json"
            original.write_text(json.dumps({**grant, "network_id": service.network_id, "url": old_url}))
            moving = Contributor(original)
            asyncio.run(moving.register())
            before = dict(moving.state)
            with monkeypatch.context() as local_route:
                local_route.setattr(contributor_module, "public_origin", lambda value: value if value == url else (_ for _ in ()).throw(ValueError()))
                asyncio.run(moving.migrate_endpoint({"url": url, "tls": identity["tls"]}, tmp_path))
                reloaded = Contributor(original)
                reply = asyncio.run(reloaded.remote("contribution_status", agent_id=reloaded.agent))
                assert reply["agent_id"] == moving.agent and reloaded.transport["url"] == url
                asyncio.run(reloaded.migrate_endpoint(rollback=True))
                assert reloaded.transport is None
                assert all(reloaded.state[k] == value for k, value in before.items())
        # A trusted signer does not make the wrong server hostname acceptable.
        host.identity["url"] = url.replace("127.0.0.1", "localhost")
        with pytest.raises(ValueError, match="Coordinator unavailable"):
            asyncio.run(host.remote("contribution_status", agent_id=host.agent))
        host.identity["url"] = url
        # Trusting the server alone is insufficient: the server requires the client key.
        host.tls_context = ssl.create_default_context(cafile=str(ca_path))
        with pytest.raises(ValueError, match="Coordinator unavailable"):
            asyncio.run(host.remote("contribution_status", agent_id=host.agent))
        # A client certificate cannot bypass server trust verification either.
        host.tls_context = ssl.create_default_context()
        host.tls_context.load_cert_chain(str(tmp_path / "client.pem"), str(tmp_path / "client.key"))
        with pytest.raises(ValueError, match="Coordinator unavailable"):
            asyncio.run(host.remote("contribution_status", agent_id=host.agent))


@pytest.mark.parametrize("tls", [None, {}, {"ca_file": "private-canary.pem", "certificate": "x", "private_key": "y"}])
def test_contributor_tls_config_failure_precedes_state_creation(tmp_path, tls):
    from daia.contributor import Contributor
    invite = tmp_path / "invite.json"
    invite.write_text(json.dumps({"url": "https://127.0.0.1:8000/mcp", "tls": tls}))
    with pytest.raises(ValueError) as error:
        Contributor(invite)
    assert "private-canary" not in str(error.value)
    assert not invite.with_suffix(".contributor.json").exists()


def test_contributor_legacy_http_real_mcp(tmp_path):
    from daia.contributor import Contributor
    service = Coordinator(Store(str(tmp_path / "legacy.sqlite3")))
    grant = service.invite()
    with running_server(build_mcp_app(service)) as url:
        invite = tmp_path / "invite.json"
        invite.write_text(json.dumps({**grant, "network_id": service.network_id, "url": url}))
        host = Contributor(invite)
        asyncio.run(host.register())
        assert isinstance(asyncio.run(host.remote("contribution_status", agent_id=host.agent)), dict)
        assert host.state["used"] == 0
        # Certificate configuration must never silently fall back to plaintext.
        identity = json.loads(invite.read_text())
        identity["tls"] = {"ca_file": "ca.pem", "certificate": "client.pem", "private_key": "client.key"}
        invite.write_text(json.dumps(identity))
        previous = invite.with_suffix(".contributor.json").read_bytes()
        with pytest.raises(ValueError, match="Invalid contributor TLS configuration"):
            Contributor(invite)
        assert invite.with_suffix(".contributor.json").read_bytes() == previous


@pytest.mark.skipif(not hasattr(socket, "AF_UNIX") or __import__("os").name == "nt", reason="Unix gateway socket")
def test_certificate_binding_over_real_unix_socket(network, contributor, tmp_path):
    service, now = network
    first = contributor()
    second = contributor(root=first[0]["root_id"])
    other = contributor()
    mapping = {"a" * 64: first[1], "b" * 64: second[1]}
    app = build_mcp_app(service, allowed_agents={first[1], second[1]}, certificate_agents=mapping)
    mapping["c" * 64] = first[1]  # Policy is copied, not a mutable caller-owned gate.
    path = str(tmp_path / "gateway.sock")
    server = uvicorn.Server(uvicorn.Config(app, uds=path, log_level="critical", access_log=False))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    try:
        deadline = time.monotonic() + 10
        while not server.started:
            assert thread.is_alive() and time.monotonic() < deadline
            time.sleep(0.01)
        with httpx.Client(transport=httpx.HTTPTransport(uds=path), base_url="http://localhost:8000") as client:
            headers = {"Authorization": "Bearer " + first[0]["token"],
                       "Accept": "application/json, text/event-stream",
                       "x-daia-client-cert-sha256": "a" * 64}
            init = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
                "protocolVersion": "2025-03-26", "capabilities": {},
                "clientInfo": {"name": "gateway-test", "version": "1"}}}
            for cert in ["", "c" * 64, "bad"]:
                assert client.post("/mcp", json=init, headers={**headers, "x-daia-client-cert-sha256": cert}).status_code == 403
            assert client.post("/mcp", json=init, headers=[*headers.items(), ("x-daia-client-cert-sha256", "a" * 64)]).status_code == 403
            response = client.post("/mcp", json=init, headers=headers)
            assert response.status_code == 200
            headers["Mcp-Session-Id"] = response.headers["mcp-session-id"]
            headers["MCP-Protocol-Version"] = "2025-03-26"
            client.post("/mcp", json={"jsonrpc": "2.0", "method": "notifications/initialized"}, headers=headers)
            request = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
            assert client.post("/mcp", json=request, headers={**headers, "x-daia-client-cert-sha256": "b" * 64}).status_code in {403, 404}
            assert client.post("/mcp", json=request, headers={**headers, "Authorization": "Bearer " + other[0]["token"]}).status_code == 401
            def result(payload):
                response = client.post("/mcp", json=payload, headers=headers)
                assert response.status_code == 200
                return json.loads(next(line[6:] for line in response.text.splitlines() if line.startswith("data: ")))["result"]
            names = {t["name"] for t in result(request)["tools"]}
            assert "register_agent" not in names and "registration_challenge" not in names
            for aid, denied in [(first[1], False), (second[1], True)]:
                output = result({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
                    "name": "contribution_status", "arguments": {"agent_id": aid}}})
                assert output.get("isError", False) == denied
            now[0] = first[0]["expires"]
            assert client.post("/mcp", json=request, headers=headers).status_code == 401
    finally:
        server.should_exit = True
        thread.join(timeout=10)
        assert not thread.is_alive()


def test_certificate_gateway_rejects_tcp_even_with_header(network, contributor):
    service, _ = network
    grant, aid, _ = contributor()
    app = build_mcp_app(service, allowed_agents={aid}, certificate_agents={"a" * 64: aid})
    with running_server(app) as url:
        assert httpx.post(url, headers={"Authorization": "Bearer " + grant["token"],
                         "x-daia-client-cert-sha256": "a" * 64}, json={}).status_code == 403


def test_migration_maintenance_blocks_writes_and_status_expiry(network, contributor):
    service, now = network
    grant, aid, key = contributor()
    service.seed()
    lease = service.request_work(grant['root_id'], aid)
    now[0] += 1000

    def snapshot():
        with service.store.connect() as db:
            return list(db.iterdump())

    before = snapshot()

    async def exercise(url):
        async with httpx2.AsyncClient(headers={'Authorization': 'Bearer ' + grant['token']}) as http:
            async with streamable_http_client(url, http_client=http) as streams:
                async with ClientSession(streams[0], streams[1]) as session:
                    await session.initialize()
                    status = await call(session, 'contribution_status', agent_id=aid, migration_check=True)
                    assert len(status['history_hash']) == 64
                    assert status['lease']['assignment_id'] == lease['assignment_id']
                    actions = {
                        'registration_challenge': {'public_key': public_hex(key)},
                        'register_agent': {'challenge_id': '0' * 32, 'signature': '0' * 128},
                        'request_work': {'agent_id': aid},
                        'heartbeat': {'agent_id': aid, 'assignment_id': lease['assignment_id']},
                        'release_work': {'agent_id': aid, 'assignment_id': lease['assignment_id']},
                        'submission_envelope': {'agent_id': aid, 'assignment_id': lease['assignment_id'], 'artifact': '{}', 'verdict': 'candidate'},
                        'submit_result': {'agent_id': aid, 'assignment_id': lease['assignment_id'], 'artifact': '{}', 'verdict': 'candidate', 'signature': '0' * 128},
                    }
                    for name, args in actions.items():
                        result = await session.call_tool(name, args)
                        assert result.is_error, name
                        assert 'migration maintenance' in str(result.content), name

    with running_server(build_mcp_app(service, maintenance=True)) as url:
        asyncio.run(exercise(url))
    assert snapshot() == before
    service.contribution_status(grant['root_id'], aid)
    assert snapshot() != before  # Normal operation still expires this stale lease.
