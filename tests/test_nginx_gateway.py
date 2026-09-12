"""Optional real Nginx/Unix-socket TLS exercise; no public ports or real identities."""
import datetime
import asyncio
from contextlib import ExitStack
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import ssl
import subprocess
import sys
import time

import httpx
import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID

pytest.importorskip("mcp")
if os.environ.get("DAIA_REQUIRE_NGINX") == "1" and not shutil.which("nginx"):
    raise RuntimeError("Required Nginx integration dependency is missing")
pytestmark = pytest.mark.skipif(os.name != "posix" or not shutil.which("nginx"), reason="Requires installed Nginx on POSIX")


def test_real_nginx_to_closed_backend(network, contributor, tmp_path, monkeypatch):
    import ipaddress
    from daia.crypto import sign
    service, _ = network
    grant, aid, signing_key = contributor()
    service.seed()
    root = Path(__file__).resolve().parents[1]
    now = datetime.datetime.now(datetime.timezone.utc)
    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Test CA")])
    def issue(name, serial, ca=False, client=False):
        key = ca_key if ca else rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = ca_name if ca else x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, name)])
        cert = (x509.CertificateBuilder().subject_name(subject).issuer_name(ca_name)
                .public_key(key.public_key()).serial_number(serial)
                .not_valid_before(now - datetime.timedelta(minutes=1)).not_valid_after(now + datetime.timedelta(days=1))
                .add_extension(x509.BasicConstraints(ca=ca, path_length=None), True)
                .add_extension(x509.SubjectKeyIdentifier.from_public_key(key.public_key()), False)
                .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()), False)
                .add_extension(x509.KeyUsage(True, False, not ca, False, False, ca, ca, False, False), True))
        if not ca:
            cert = cert.add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.CLIENT_AUTH if client else ExtendedKeyUsageOID.SERVER_AUTH]), False)
            if not client:
                cert = cert.add_extension(x509.SubjectAlternativeName([x509.DNSName("mcp.example.org"), x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]), False)
        cert = cert.sign(ca_key, hashes.SHA256())
        (tmp_path / (name + ".pem")).write_bytes(cert.public_bytes(serialization.Encoding.PEM))
        keypath = tmp_path / (name + ".key")
        keypath.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
        keypath.chmod(0o600)
        return cert
    issue("client-ca", 1, ca=True)
    issue("server", 2)
    client_cert = issue("client", 3, client=True)
    issue("outsider", 4, client=True)
    def crl(revoke=False):
        builder = x509.CertificateRevocationListBuilder().issuer_name(ca_name).last_update(now).next_update(now + datetime.timedelta(days=1))
        if revoke:
            builder = builder.add_revoked_certificate(x509.RevokedCertificateBuilder().serial_number(3).revocation_date(now).build())
        (tmp_path / "client-ca.crl").write_bytes(builder.sign(ca_key, hashes.SHA256()).public_bytes(serialization.Encoding.PEM))
    crl()
    runtime = tmp_path / "run"
    runtime.mkdir(mode=0o750)
    policy = tmp_path / "policy.json"
    policy.write_text(json.dumps({"resource": "https://mcp.example.org/mcp", "allowed_agents": [aid],
                                  "certificate_agents": {client_cert.fingerprint(hashes.SHA256()).hex(): aid}}))
    policy.chmod(0o600)
    sock = runtime / "mcp.sock"
    env = {**os.environ, "PYTHONPATH": str(root / "src")}
    backend = subprocess.Popen([sys.executable, "-m", "daia.gateway", "--db", str(tmp_path / "network.sqlite3"),
                                "--config", str(policy), "--socket", str(sock)], env=env,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    proxy = None
    try:
        deadline = time.monotonic() + 10
        while not sock.exists():
            assert backend.poll() is None and time.monotonic() < deadline
            time.sleep(0.05)
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        site = (root / "deploy/nginx-closed-mcp.conf.example").read_text()
        site = site.replace("127.0.0.1:8443", f"127.0.0.1:{port}").replace("/etc/daia/gateway", str(tmp_path)).replace("/run/daia-gateway/mcp.sock", str(sock))
        (tmp_path / "site.conf").write_text(site)
        config = tmp_path / "nginx.conf"
        main = (root / "deploy/nginx-gateway-main.conf.example").read_text()
        config.write_text(main.replace("/run/daia-proxy", str(tmp_path)).replace("/etc/daia/gateway/site.conf", str(tmp_path / "site.conf")))
        command = [shutil.which("nginx"), "-c", str(config), "-p", str(tmp_path) + "/"]
        subprocess.run(command + ["-t"], check=True, capture_output=True)
        proxy = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        def tls_context(identity="client"):
            context = ssl.create_default_context(cafile=str(tmp_path / "client-ca.pem"))
            if identity:
                context.load_cert_chain(str(tmp_path / (identity + ".pem")), str(tmp_path / (identity + ".key")))
            return context
        def transport(identity="client"):
            return httpx.Client(verify=tls_context(identity), base_url=f"https://127.0.0.1:{port}", headers={"Host": "mcp.example.org"}, timeout=3)
        init = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "nginx-test", "version": "1"}}}
        headers = {"Authorization": "Bearer " + grant["token"], "Accept": "application/json, text/event-stream",
                   "X-DAIA-Client-Cert": "spoofed", "X-DAIA-Client-Cert-SHA256": "spoofed"}
        with transport() as client:
            deadline = time.monotonic() + 10
            while True:
                assert proxy.poll() is None
                try:
                    response = client.post("/mcp", json=init, headers=headers)
                    break
                except httpx.TransportError:
                    assert time.monotonic() < deadline
                    time.sleep(0.05)
            assert response.status_code == 200
            session_headers = {**headers, "Mcp-Session-Id": response.headers["mcp-session-id"], "MCP-Protocol-Version": "2025-03-26"}
            client.post("/mcp", json={"jsonrpc": "2.0", "method": "notifications/initialized"}, headers=session_headers)
            def call(name, arguments):
                response = client.post("/mcp", json={"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": name, "arguments": arguments}}, headers=session_headers)
                assert response.status_code == 200
                result = json.loads(next(line[6:] for line in response.text.splitlines() if line.startswith("data: ")))["result"]
                assert not result.get("isError")
                return result.get("structuredContent") or json.loads(result["content"][0]["text"])
            lease = call("request_work", {"agent_id": aid})
            args = {"agent_id": aid, "assignment_id": lease["assignment_id"], "artifact": '{"factors":[101,103]}', "verdict": "candidate"}
            envelope = call("submission_envelope", args)
            args["signature"] = sign(signing_key, envelope)
            assert call("submit_result", args)["status"] == "in_review"
            assert call("submit_result", args)["status"] == "already_recorded"
            assert client.post("/mcp", content=b"x" * 16385, headers=headers).status_code == 413
            assert client.post("/mcp?unexpected=1", json=init, headers=headers).status_code == 404
        for identity in [None, "outsider"]:
            with transport(identity) as client:
                assert client.post("/mcp", json=init, headers=headers).status_code in {400, 403}
        # Leave one header and one body incomplete. The configured ten-second
        # idle limits must close both connections without waiting for more bytes.
        with ExitStack() as stack:
            idle = []
            context = tls_context()
            for partial in [
                b"POST /mcp HTTP/1.1\r\nHost: mcp.example.org\r\nX-Incomplete: ",
                b"POST /mcp HTTP/1.1\r\nHost: mcp.example.org\r\nContent-Length: 100\r\n"
                + ("Authorization: Bearer " + grant["token"] + "\r\n\r\n{").encode(),
            ]:
                raw = stack.enter_context(socket.create_connection(("127.0.0.1", port), timeout=3))
                connection = stack.enter_context(context.wrap_socket(raw, server_hostname="mcp.example.org"))
                connection.settimeout(14)
                connection.sendall(partial)
                idle.append(connection)
            started = time.monotonic()
            for connection in idle:
                remaining = 14 - (time.monotonic() - started)
                assert remaining > 0
                connection.settimeout(remaining)
                response = connection.recv(4096)
                assert response == b"" or response.startswith(b"HTTP/1.1 408 ")
                received = len(response)
                while response:
                    remaining = 14 - (time.monotonic() - started)
                    assert remaining > 0 and received <= 8192
                    connection.settimeout(remaining)
                    response = connection.recv(4096)
                    received += len(response)
                assert time.monotonic() - started < 14
        # Timed-out clients must not prevent a normal authenticated request.
        with transport() as client:
            assert client.post("/mcp", json=init, headers=headers).status_code == 200
        # Pace below 5 requests/s so a 429 here measures concurrent requests,
        # not the independent request-rate limiter. Each session has one SSE GET.
        with ExitStack() as streams:
            for _ in range(20):
                client = streams.enter_context(transport())
                opened = client.post("/mcp", json=init, headers=headers)
                assert opened.status_code == 200
                bound = {**session_headers, "Mcp-Session-Id": opened.headers["mcp-session-id"]}
                notified = client.post("/mcp", json={"jsonrpc": "2.0", "method": "notifications/initialized"}, headers=bound)
                assert notified.status_code == 202
                stream = streams.enter_context(client.stream("GET", "/mcp", headers=bound))
                assert stream.status_code == 200
                time.sleep(0.7)
            with transport() as overflow:
                assert overflow.post("/mcp", json=init, headers=headers).status_code == 429
        # Closing the held streams must release the slots for an admitted client.
        deadline = time.monotonic() + 3
        with transport() as recovered:
            while True:
                status = recovered.post("/mcp", json=init, headers=headers).status_code
                assert time.monotonic() < deadline
                if status == 200:
                    break
                assert status == 429 and time.monotonic() < deadline
                time.sleep(0.25)
        # Sequential requests keep concurrency at one: overflow here must be
        # the request-rate limit rather than the active-stream ceiling.
        with transport() as burst:
            statuses = []
            deadline = time.monotonic() + 10
            for _ in range(80):
                status = burst.post("/mcp", json=init, headers=headers).status_code
                assert status in {200, 429} and time.monotonic() < deadline
                statuses.append(status)
            assert 429 in statuses
            # The configured burst drains in four seconds at five requests/s.
            time.sleep(5)
            assert burst.post("/mcp", json=init, headers=headers).status_code == 200
        # Run the real helper through the canonical public URL and closed proxy.
        # Only TCP routing maps the reserved example hostname to our loopback port;
        # URL validation, HTTP Host, TLS SNI/certificate checks and MCP stay intact.
        # Reopen only the disposable backend against a checked snapshot. The
        # source keeps its original DB, so migration cannot pass by sharing state.
        from daia.store import backup_database
        restored_db = tmp_path / "restored.sqlite3"
        backend.terminate()
        backend.wait(timeout=10)
        backup_database(service.store.path, restored_db)
        backend = subprocess.Popen([sys.executable, "-m", "daia.gateway", "--db", str(restored_db),
                                    "--config", str(policy), "--socket", str(sock)], env=env,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        deadline = time.monotonic() + 10
        while not sock.exists():
            assert backend.poll() is None and time.monotonic() < deadline
            time.sleep(0.05)
        import httpcore2
        from daia.contributor import Contributor
        from daia.mcp_server import build_mcp_app
        from test_mcp import running_server
        connect_tcp = httpcore2.AnyIOBackend.connect_tcp
        gateway_port = port
        async def local_gateway(backend, host, port, *args, **kwargs):
            if host == "mcp.example.org" and port == 443:
                host, port = "127.0.0.1", gateway_port
            return await connect_tcp(backend, host, port, *args, **kwargs)
        with running_server(build_mcp_app(service)) as source_url:
            invite = tmp_path / "migration-invite.json"
            invite.write_text(json.dumps({**grant, "network_id": service.network_id, "url": source_url}))
            helper = Contributor(invite, clock=service.clock)
            helper.state.update(key=signing_key.private_bytes_raw().hex(), registered=True,
                                used=1, pending=dict(args))
            helper.save()
            helper = Contributor(invite, clock=service.clock)
            assert helper.agent == aid
            original = json.loads(helper.path.read_text())
            destination = {"url": "https://mcp.example.org/mcp", "tls": {
                "ca_file": "client-ca.pem", "certificate": "client.pem", "private_key": "client.key"}}
            with monkeypatch.context() as route:
                route.setenv("NO_PROXY", "mcp.example.org,127.0.0.1,localhost")
                route.setattr(httpcore2.AnyIOBackend, "connect_tcp", local_gateway)
                asyncio.run(helper.migrate_endpoint(destination, tmp_path))
                helper = Contributor(invite, clock=service.clock)
                assert helper.transport["url"] == destination["url"]
                recovered = asyncio.run(helper.perform("submit_result", artifact=args["artifact"], verdict=args["verdict"]))
                assert recovered["status"] == "already_recorded"
                assert helper.state["used"] == original["used"]
                assert helper.state["deadline"] == original["deadline"]
                # Switchback is a separate operator action; let the preceding
                # SDK sessions drain their request-rate burst first.
                time.sleep(5)
                asyncio.run(helper.migrate_endpoint(rollback=True))
                assert helper.transport is None and helper.state["pending"] is None
                assert helper.state["key"] == original["key"]
        with transport() as active:
            # Process restart invalidates MCP sessions; durable receipts survive.
            initialized = active.post("/mcp", json=init, headers=headers)
            assert initialized.status_code == 200
            fresh_headers = {**session_headers, "Mcp-Session-Id": initialized.headers["mcp-session-id"]}
            assert active.post("/mcp", json={"jsonrpc": "2.0", "method": "notifications/initialized"}, headers=fresh_headers).status_code == 202
            with active.stream("GET", "/mcp", headers=fresh_headers, timeout=8) as stream:
                assert stream.status_code == 200
                crl(revoke=True)
                reload_started = time.monotonic()
                proxy.send_signal(signal.SIGHUP)
                deadline = time.monotonic() + 10
                while True:
                    with transport() as client:
                        status = client.post("/mcp", json=init, headers=headers).status_code
                    if status in {400, 403}:
                        break
                    assert status == 200 and time.monotonic() < deadline
                    time.sleep(0.1)
                # An already-authorized idle stream must not retain old TLS authority.
                # A forced worker close may finish chunking or abort it; a read timeout
                # instead means the old authenticated stream remained open too long.
                try:
                    for chunk in stream.iter_raw():
                        assert time.monotonic() - reload_started < 8
                except httpx.RemoteProtocolError:
                    pass
                assert time.monotonic() - reload_started < 8
    finally:
        for process in [proxy, backend]:
            if process is not None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
