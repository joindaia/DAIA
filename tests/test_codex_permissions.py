"""Opt-in native command-boundary probe; not whole-agent certification."""
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys

import pytest

pytestmark = pytest.mark.skipif(
    sys.platform != "linux" or os.environ.get("DAIA_RUN_CODEX_SANDBOX_TESTS") != "1",
    reason="Explicit native Codex sandbox integration test",
)


def test_native_profile_denies_outside_reads_and_live_loopback(tmp_path):
    executable = shutil.which("codex")
    assert executable, "Install Codex before requesting this integration check"
    binary = Path(executable).resolve(strict=True)
    workspace = tmp_path / "work"
    workspace.mkdir()
    canary = tmp_path / "operator-canary"
    canary.write_text("synthetic secret")
    (workspace / "escape").symlink_to(canary)
    codex_home = tmp_path / "codex-home"
    codex_home.mkdir()
    # Use an empty configuration home: never load operator MCP servers or auth.
    env = {"PATH": "/usr/bin:/bin", "HOME": str(tmp_path),
           "CODEX_HOME": str(codex_home)}
    profile = ('permissions={daia-probe={filesystem={":root"="deny",'
               '":minimal"="read",' + json.dumps(str(binary)) +
               '="read",":workspace_roots"={"."="write"}},network={enabled=false}}}')
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen(2)
        port = listener.getsockname()[1]
        # A reachable control avoids mistaking an absent route for enforcement.
        with socket.create_connection(("127.0.0.1", port), timeout=2):
            connection, _ = listener.accept()
            connection.close()
        program = """import pathlib,socket,sys
for filename in sys.argv[1:3]:
    try: pathlib.Path(filename).read_bytes()
    except OSError: pass
    else: raise AssertionError('outside read succeeded')
try:
    with socket.create_connection(('127.0.0.1', int(sys.argv[3])), timeout=1):
        pass
except OSError: pass
else: raise AssertionError('host loopback was reachable')
pathlib.Path('result.txt').write_text('workspace write succeeded')
print('native command boundary passed')
"""
        result = subprocess.run(
            [str(binary), "sandbox", "-P", "daia-probe", "-C", str(workspace),
             "-c", profile, "--", "/usr/bin/python3", "-c", program,
             str(canary), str(workspace / "escape"), str(port)],
            env=env, stdin=subprocess.DEVNULL, close_fds=True,
            capture_output=True, text=True, timeout=20,
        )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "native command boundary passed"
    assert (workspace / "result.txt").read_text() == "workspace write succeeded"
    assert canary.read_text() == "synthetic secret"
