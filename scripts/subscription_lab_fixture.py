"""Trusted local lab setup, never exposed to assignment workers.

Uses the actual loopback MCP server. This creates only the temporary lab network's
existing finite grant; it is not a production admission or participant installer.
"""
import json
import socket
import threading
import time
from contextlib import contextmanager
import uvicorn

def invite_file(tmp_path, service, url="http://127.0.0.1:8000/mcp", *, max_jobs=3, lifetime=86400):
    invite = {**service.invite(max_jobs=max_jobs, lifetime=lifetime),
              "network_id": service.network_id, "url": url}
    path = tmp_path / (invite["root_id"] + ".json")
    path.write_text(json.dumps(invite), encoding="utf-8")
    return path


def approve(host, lease, capabilities):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from daia.crypto import public_hex
    from daia.job_authorization import authorize_job
    key = Ed25519PrivateKey.generate()
    approval = authorize_job(lease, key=key, agent_id=host.agent,
                             capabilities=capabilities, expires=lease['hard_deadline'],
                             now=int(host.clock()))
    return {'public_key': public_hex(key), 'capabilities': capabilities,
            'jobs': {lease['job_id']: approval}}


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
