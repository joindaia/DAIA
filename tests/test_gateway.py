"""Closed launcher checks; real Unix-socket subprocess, no public listener."""
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import time

import httpx
import pytest

pytest.importorskip("mcp")
from daia.mcp_server import public_origin


@pytest.mark.parametrize("url", [
    "http://mcp.example.org/mcp", "https://mcp.example.org:443/mcp",
    "https://user@host.example/mcp", "https://mcp.example.org/mcp?x=1",
    "https://mcp.example.org/mcp#x", "https://mcp.example.org/other",
    "https://MCP.example.org/mcp", "https://127.0.0.1/mcp",
    "https://mcp.example.org./mcp", "https://a..example.org/mcp",
])
def test_public_resource_rejects_noncanonical_url(url):
    with pytest.raises(ValueError):
        public_origin(url)


def test_public_resource_canonical():
    assert public_origin("https://mcp.example.org/mcp") == "https://mcp.example.org"


@pytest.mark.skipif(os.name != "posix", reason="Unix deployment only")
def test_socket_permissions_and_existing_path(tmp_path):
    from daia.gateway import bind_private_socket
    parent = tmp_path / "run"
    parent.mkdir(mode=0o755)
    path = parent / "mcp.sock"
    with pytest.raises(ValueError):
        bind_private_socket(path)
    parent.chmod(0o750)
    with bind_private_socket(path):
        assert stat.S_IMODE(path.stat().st_mode) == 0o660
        with pytest.raises(OSError):
            bind_private_socket(path)
    assert path.exists()  # Deliberate restart cleanup; no blind unlink.


@pytest.mark.skipif(os.name != "posix", reason="Unix deployment only")
def test_real_closed_launcher(network, contributor, tmp_path):
    service, _ = network
    grant, aid, _ = contributor()
    parent = tmp_path / "run"
    parent.mkdir(mode=0o750)
    policy = tmp_path / "policy.json"
    policy.write_text(json.dumps({"resource": "https://mcp.example.org/mcp", "allowed_agents": [aid],
                                  "certificate_agents": {"a" * 64: aid}}))
    path = parent / "mcp.sock"
    database = tmp_path / "network.sqlite3"
    env = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")}
    process = subprocess.Popen([sys.executable, "-m", "daia.gateway", "--db", str(database),
                                "--config", str(policy), "--socket", str(path)], env=env,
                               stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        with httpx.Client(transport=httpx.HTTPTransport(uds=str(path)), base_url="http://mcp.example.org", timeout=2) as client:
            headers = {"Authorization": "Bearer " + grant["token"],
                       "Accept": "application/json, text/event-stream", "x-daia-client-cert-sha256": "a" * 64}
            request = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
                "protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "test", "version": "1"}}}
            deadline = time.monotonic() + 15
            while True:
                assert process.poll() is None
                try:
                    response = client.post("/mcp", json=request, headers=headers)
                    break
                except httpx.TransportError:
                    assert time.monotonic() < deadline
                    time.sleep(0.05)
            assert response.status_code == 200
            assert client.post("/mcp", json=request, headers={**headers, "Host": "localhost:8000"}).status_code == 421
            assert client.post("/mcp", json=request, headers={**headers, "Authorization": "Bearer wrong"}).status_code == 401
            assert client.post("/mcp", json=request, headers={**headers, "x-daia-client-cert-sha256": "b" * 64}).status_code == 403
    finally:
        process.terminate()
        try:
            process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()


def test_launcher_refuses_missing_database_without_creating_it(tmp_path):
    from daia.gateway import configured_app
    policy = tmp_path / "policy.json"
    policy.write_text(json.dumps({"resource": "https://mcp.example.org/mcp", "allowed_agents": [], "certificate_agents": {}}))
    database = tmp_path / "missing.sqlite3"
    with pytest.raises(ValueError, match="existing coordinator database"):
        configured_app(policy, database)
    assert not database.exists()
