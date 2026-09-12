"""Optional real Nginx/Unix-socket TLS exercise; no public ports or real identities."""
import datetime
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


def test_real_nginx_to_closed_backend(network, contributor, tmp_path):
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
        config.write_text(f"daemon off; master_process on; error_log stderr; pid {tmp_path}/nginx.pid; events {{}} http {{ access_log off; client_body_temp_path {tmp_path}/body; proxy_temp_path {tmp_path}/proxy; include {tmp_path}/site.conf; }}")
        command = [shutil.which("nginx"), "-c", str(config), "-p", str(tmp_path) + "/"]
        subprocess.run(command + ["-t"], check=True, capture_output=True)
        proxy = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        def transport(identity="client"):
            context = ssl.create_default_context(cafile=str(tmp_path / "client-ca.pem"))
            if identity:
                context.load_cert_chain(str(tmp_path / (identity + ".pem")), str(tmp_path / (identity + ".key")))
            return httpx.Client(verify=context, base_url=f"https://127.0.0.1:{port}", headers={"Host": "mcp.example.org"}, timeout=3)
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
        crl(revoke=True)
        proxy.send_signal(signal.SIGHUP)
        deadline = time.monotonic() + 10
        while True:
            with transport() as client:
                status = client.post("/mcp", json=init, headers=headers).status_code
            if status in {400, 403}:
                break
            assert status == 200 and time.monotonic() < deadline
            time.sleep(0.1)
    finally:
        for process in [proxy, backend]:
            if process is not None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
