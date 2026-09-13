'''Credential-free proof probe for deferred DAIA MCP tool discovery.'''
import argparse
import hashlib
import http.server
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import threading


PIN = "56ef98ab4032d317ab26e9b5e5a175650717351edb16ed9cde0cb6d1734d62da"
COMPANION_PIN = "3e85d67471825f73d02ff5f7e047ca1f6ca8caa3f59e4c6e8d9ca6ca7302cb45"
EXPECTED_NAMES = {"mcp__daia_assignment__heartbeat",
                  "mcp__daia_assignment__submit_result"}
DEFAULT_MODEL = "gpt-5.6-luna"
CODE = "text(ALL_TOOLS.filter(x => /daia_assignment/.test(x.name)))"


def model_identifier(value):
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", value):
        return value
    raise argparse.ArgumentTypeError("Explicit model identifier required")


def validate_binary(binary):
    binary = Path(binary)
    if (not binary.is_absolute() or binary.is_symlink() or not binary.is_file()
            or hashlib.sha256(binary.read_bytes()).hexdigest() != PIN):
        raise ValueError("Pinned original Codex binary required")
    return binary


def custom_tool_events():
    item = {"id": "item_deferred_exec", "type": "custom_tool_call",
            "status": "completed", "call_id": "call_deferred_exec",
            "name": "exec", "namespace": "functions", "input": CODE}
    response = {"id": "resp_deferred_exec", "object": "response",
                "status": "completed", "output": [item]}
    events = [
        ("response.created", {"response": {**response, "status": "in_progress",
                                             "output": []}}),
        ("response.output_item.added", {"output_index": 0, "item":
            {**item, "input": ""}}),
        ("response.custom_tool_call_input.delta", {"item_id": item["id"],
            "output_index": 0, "delta": CODE}),
        ("response.custom_tool_call_input.done", {"item_id": item["id"],
            "output_index": 0, "input": CODE}),
        ("response.output_item.done", {"output_index": 0, "item": item}),
        ("response.completed", {"response": response}),
    ]
    return "".join("event: " + name + "\ndata: " +
                    json.dumps({"type": name, **payload}) + "\n\n"
                    for name, payload in events).encode()


def _output_text(value):
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(_output_text(item) for item in value)
    if isinstance(value, dict):
        if isinstance(value.get("text"), str):
            return value["text"]
        if "output" in value:
            return _output_text(value["output"])
    return ""


def deferred_output(request):
    if not isinstance(request, dict):
        return ""
    return "\n".join(_output_text(item.get("output"))
                      for item in request.get("input", [])
                      if isinstance(item, dict)
                      and item.get("type") in {"custom_tool_call_output",
                                                "function_call_output"})


def extract_assignment_names(output):
    return sorted(set(re.findall(r'"name"\s*:\s*"([^"]*daia_assignment[^"]*)"',
                                 output)))


def validate_companion(binary, companion):
    companion = Path(companion)
    if (companion.is_symlink() or not companion.is_file()
            or companion.name != "codex-code-mode-host"
            or companion.parent != binary.parent
            or hashlib.sha256(companion.read_bytes()).hexdigest() != COMPANION_PIN):
        raise ValueError("Pinned companion in the client directory required")
    return companion


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--companion", type=Path, required=True)
    parser.add_argument("--model", type=model_identifier, default=DEFAULT_MODEL)
    return parser


def main():
    args = build_parser().parse_args()
    binary = validate_binary(args.binary)
    companion = validate_companion(binary, args.companion)
    requests = []
    request_limits = {"extra_requests_refused": False}

    class Capture(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get("Content-Length", "0"))
            if self.path != "/v1/responses" or not 0 < length <= 1024 * 1024:
                self.send_response(403); self.end_headers(); return
            nonlocal_extra = len(requests) >= 2
            if nonlocal_extra:
                self.send_response(403); self.end_headers()
                request_limits["extra_requests_refused"] = True
                return
            requests.append(json.loads(self.rfile.read(length)))
            if len(requests) == 1:
                data = custom_tool_events()
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers(); self.wfile.write(data); self.wfile.flush()
            else:
                self.send_response(403); self.end_headers()
                threading.Thread(target=server.shutdown, daemon=True).start()
        def log_message(self, *args):
            pass

    with tempfile.TemporaryDirectory(prefix="daia-deferred-discovery-") as directory:
        home = Path(directory)
        with http.server.HTTPServer(("127.0.0.1", 0), Capture) as server:
            server.timeout = 0.25
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            config = f'''model = {json.dumps(args.model)}
model_provider = "discovery_fixture"
approval_policy = "never"
web_search = "disabled"
[model_providers.discovery_fixture]
name = "Credential-free deferred discovery"
base_url = "http://127.0.0.1:{server.server_port}/v1"
wire_api = "responses"
requires_openai_auth = false
request_max_retries = 0
stream_max_retries = 0
supports_websockets = false
[mcp_servers.daia_assignment]
command = {json.dumps(sys.executable)}
args = [{json.dumps(str(Path(__file__).resolve().with_name("probe_codex_assignment_tools.py")))}, "--serve-fixture"]
startup_timeout_sec = 10
'''
            (home / "config.toml").write_text(config)
            try:
                try:
                    run = subprocess.run(
                        [str(binary), "--strict-config", "exec", "--skip-git-repo-check",
                         "--ephemeral", "--json", "Discovery only; no work is authorized."],
                        cwd=home,
                        env={"PATH": str(companion.parent) + ":/usr/bin:/bin",
                             "HOME": directory, "CODEX_HOME": directory},
                        capture_output=True, text=True, timeout=20)
                    native_error = run.stderr[-2000:]
                except subprocess.TimeoutExpired as error:
                    run = None
                    native_error = str(error)
            finally:
                server.shutdown(); thread.join(3)

    output = deferred_output(requests[1]) if len(requests) >= 2 else ""
    names = extract_assignment_names(output)
    result = {
        "model": args.model, "native_binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        "companion_sha256": hashlib.sha256(companion.read_bytes()).hexdigest(),
        "loopback_requests": len(requests), "provider_requests": 0,
        "extra_requests_refused": request_limits["extra_requests_refused"],
        "deferred_output_present": bool(output), "assignment_names": names,
        "native_exit": None if run is None else run.returncode,
        "unsupported_protocol": not output,
        "template_automatically_authorized": False,
    }
    if output and set(names) == EXPECTED_NAMES:
        result["proof"] = "deferred_daia_catalog_observed"
    else:
        result["proof"] = "deferred_daia_catalog_not_observed"
        result["failure"] = ("No enumerable deferred DAIA catalog output was captured"
                              if not output else "Deferred output did not name both assignment capabilities")
    if native_error:
        result["native_error"] = next((line.strip() for line in native_error.splitlines()
                                       if "unsupported custom tool call:" in line),
                                      "native stderr reported an error")
    print(json.dumps(result))
    return 0 if result["proof"] == "deferred_daia_catalog_observed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
