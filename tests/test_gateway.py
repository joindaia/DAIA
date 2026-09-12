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
        with bind_private_socket(path):
            pass
    parent.chmod(0o750)
    with bind_private_socket(path):
        assert stat.S_IMODE(path.stat().st_mode) == 0o660
        with pytest.raises(OSError):
            with bind_private_socket(path):
                pass
    assert not path.exists()


@pytest.mark.skipif(os.name != "posix", reason="Unix deployment only")
def test_real_closed_launcher(network, contributor, tmp_path):
    service, _ = network
    grant, aid, _ = contributor()
    parent = tmp_path / "run"
    parent.mkdir(mode=0o750)
    policy = tmp_path / "policy.json"
    policy.write_text(json.dumps({"resource": "https://mcp.example.org/mcp", "allowed_agents": [aid],
                                  "certificate_agents": {"a" * 64: aid}}))
    policy.chmod(0o600)
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
    assert process.returncode == 0
    assert not path.exists()
    from daia.gateway import bind_private_socket
    with bind_private_socket(path):
        pass


def test_launcher_refuses_missing_database_without_creating_it(tmp_path):
    from daia.gateway import configured_app
    policy = tmp_path / "policy.json"
    policy.write_text(json.dumps({"resource": "https://mcp.example.org/mcp", "allowed_agents": [], "certificate_agents": {}}))
    policy.chmod(0o600)
    database = tmp_path / "missing.sqlite3"
    with pytest.raises(ValueError, match="existing coordinator database"):
        configured_app(policy, database)
    assert not database.exists()


@pytest.mark.skipif(os.name != "posix", reason="POSIX policy permissions")
@pytest.mark.parametrize("kind", ["symlink", "writable", "fifo"])
def test_policy_file_rejects_untrusted_inputs_before_database(tmp_path, kind):
    from daia.gateway import configured_app
    source = tmp_path / "source.json"
    source.write_text("{}")
    policy = tmp_path / "policy.json"
    if kind == "symlink":
        policy.symlink_to(source)
    elif kind == "fifo":
        os.mkfifo(policy)
    else:
        policy.write_text("{}")
        policy.chmod(0o666)
    with pytest.raises((OSError, ValueError)):
        configured_app(policy, tmp_path / "missing.sqlite3")


@pytest.mark.parametrize("kind", ["empty", "unrelated"])
def test_invalid_existing_database_refuses_startup_without_socket(tmp_path, kind):
    import sqlite3
    database = tmp_path / "invalid.sqlite3"
    database.touch(mode=0o600)
    if kind == "unrelated":
        with sqlite3.connect(database) as db:
            db.execute("CREATE TABLE unrelated (value TEXT)")
    policy = tmp_path / "policy.json"
    policy.write_text(json.dumps({"resource": "https://mcp.example.org/mcp", "allowed_agents": [], "certificate_agents": {}}))
    policy.chmod(0o600)
    path = tmp_path / "never.sock"
    result = subprocess.run([sys.executable, "-m", "daia.gateway", "--config", str(policy),
                             "--db", str(database), "--socket", str(path)],
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 1
    assert "refused startup" in result.stderr
    assert "Traceback" not in result.stderr
    assert not path.exists()


@pytest.mark.skipif(os.name != "posix", reason="Unix server lifecycle")
def test_lifespan_failure_is_failure_and_cleans_own_socket(tmp_path):
    from daia.gateway import bind_private_socket, run_bound, remove_own_socket
    parent = tmp_path / "run"
    parent.mkdir(mode=0o750)
    path = parent / "mcp.sock"
    async def failing(scope, receive, send):
        assert scope["type"] == "lifespan"
        await receive()
        await send({"type": "lifespan.startup.failed", "message": "synthetic startup failure"})
    with pytest.raises(SystemExit) as error:
        run_bound(failing, path)
    assert error.value.code != 0
    assert not path.exists()
    with bind_private_socket(path):
        info = path.lstat()
        identity = (info.st_dev, info.st_ino)
        path.unlink()
        path.write_text("replacement must survive")
        remove_own_socket(path, identity)
        assert path.read_text() == "replacement must survive"


@pytest.mark.skipif(os.name != "posix", reason="POSIX signal masking")
@pytest.mark.parametrize("phase", ["bound", "cleanup"])
def test_sigterm_in_socket_transition_cannot_leave_own_path(tmp_path, phase):
    import signal
    parent = tmp_path / "run"
    parent.mkdir(mode=0o750)
    path = parent / "mcp.sock"
    code = '''
import os, signal, sys
import daia.gateway as gateway
path, phase = sys.argv[1:]
if phase == "cleanup":
    original = gateway.remove_own_socket
    def interrupted(path, identity):
        os.kill(os.getpid(), signal.SIGTERM)
        original(path, identity)
    gateway.remove_own_socket = interrupted
with gateway.bind_private_socket(path):
    if phase == "bound":
        os.kill(os.getpid(), signal.SIGTERM)
    assert phase != "bound" or signal.SIGTERM in signal.sigpending()
'''
    result = subprocess.run([sys.executable, "-c", code, str(path), phase],
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == -signal.SIGTERM
    assert not path.exists()


@pytest.mark.skipif(os.name != "posix", reason="Unix socket paths")
def test_socket_cleanup_uses_captured_absolute_path(tmp_path, monkeypatch):
    from daia.gateway import bind_private_socket
    parent = tmp_path / "run"
    parent.mkdir(mode=0o750)
    monkeypatch.chdir(tmp_path)
    with bind_private_socket("run/mcp.sock"):
        monkeypatch.chdir(parent)
    assert not (parent / "mcp.sock").exists()
