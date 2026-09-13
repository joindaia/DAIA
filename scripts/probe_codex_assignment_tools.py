"""Credential-free capture of pinned Codex's assignment MCP declarations.

No inference is served: the loopback provider always rejects. The synthetic host
has no identity, signing state or coordinator and refuses every tool invocation.
An observed request is evidence, never automatic authorization of a template.
"""
import argparse
import asyncio
import hashlib
import http.server
import json
import os
import re
from pathlib import Path
import subprocess
import sys
import tempfile
import threading


DEFAULT_MODEL = "gpt-5.3-codex-spark"


def model_identifier(value):
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", value):
        return value
    raise argparse.ArgumentTypeError("Explicit model identifier required")


def serve_fixture():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from daia.contributor import build_assignment_server

    class Host:
        job_authority = object()
        state = {"registered": True}
        def check_assignment_scope(self, assignment):
            if assignment != "a" * 32:
                raise ValueError("Synthetic assignment required")
        async def perform(self, *args, **kwargs):
            raise ValueError("Discovery fixture cannot perform work")

    asyncio.run(build_assignment_server(Host(), "a" * 32).run_stdio_async())


def assignment_tools(request):
    tools = request.get("tools")
    if not isinstance(tools, list):
        raise RuntimeError(
            "Unsupported native discovery protocol: enumerable top-level tools missing"
        )
    return tools


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serve-fixture", action="store_true")
    parser.add_argument("--binary", type=Path)
    parser.add_argument("--model", type=model_identifier, default=DEFAULT_MODEL,
                        help="Synthetic native model to observe (default: %(default)s)")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    if args.serve_fixture:
        serve_fixture()
        return
    binary = args.binary
    if (binary is None or binary.is_symlink() or not binary.is_file()
            or hashlib.sha256(binary.read_bytes()).hexdigest() !=
            "56ef98ab4032d317ab26e9b5e5a175650717351edb16ed9cde0cb6d1734d62da"):
        parser.error("Pinned original Codex binary required")
    requests = []

    class Capture(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get("Content-Length", "0"))
            if 0 < length <= 1024 * 1024:
                requests.append(json.loads(self.rfile.read(length)))
            self.send_response(403)
            self.end_headers()
        def log_message(self, *args):
            pass

    with tempfile.TemporaryDirectory(prefix="daia-tool-discovery-") as directory:
        home = Path(directory)
        with http.server.HTTPServer(("127.0.0.1", 0), Capture) as server:
            server.timeout = 20
            thread = threading.Thread(target=server.handle_request, daemon=True)
            thread.start()
            port = server.server_address[1]
            config = f'''model = {json.dumps(args.model)}
model_provider = "discovery_fixture"
approval_policy = "never"
web_search = "disabled"
[model_providers.discovery_fixture]
name = "Credential-free discovery"
base_url = "http://127.0.0.1:{port}/v1"
wire_api = "responses"
requires_openai_auth = false
request_max_retries = 0
stream_max_retries = 0
supports_websockets = false
[mcp_servers.daia_assignment]
command = {json.dumps(sys.executable)}
args = [{json.dumps(str(Path(__file__).resolve()))}, "--serve-fixture"]
startup_timeout_sec = 10
'''
            (home / "config.toml").write_text(config)
            try:
                run = subprocess.run(
                    [str(binary.resolve()), "--strict-config", "exec",
                     "--skip-git-repo-check", "--ephemeral", "--json",
                     "Discovery only; no work is authorized."],
                    cwd=home, env={"PATH": "/usr/bin:/bin", "HOME": directory,
                                   "CODEX_HOME": directory},
                    capture_output=True, timeout=25)
            finally:
                thread.join(timeout=21)
            if len(requests) != 1:
                raise RuntimeError("Expected exactly one rejected model request")
            if requests[0].get("model") != args.model:
                raise RuntimeError("Captured request model mismatch")
            namespaces = [t for t in assignment_tools(requests[0])
                          if t.get("name") == "mcp__daia_assignment"]
            if len(namespaces) != 1:
                raise RuntimeError("Assignment namespace missing or ambiguous")
            tools = namespaces[0]["tools"]
            if {t["name"] for t in tools} != {"heartbeat", "submit_result"}:
                raise RuntimeError("Unexpected assignment capabilities")
            if run.returncode == 0:
                raise RuntimeError("Rejected inference must not complete a turn")
            print(json.dumps({"model": args.model,
                "native_binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
                "captured_requests": len(requests), "provider_requests": 0,
                "native_exit": run.returncode, "tools": tools,
                "synthetic_helper": True, "provider_credentials_present": False,
                "template_automatically_authorized": False}))


if __name__ == "__main__":
    main()
