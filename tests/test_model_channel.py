import json
import socket
import threading

import pytest
from daia.model_channel import serve_once, AssignmentModelChannel
from daia.model_request import RequestGate

BODY = {"model": "fixture", "store": False, "stream": True, "tools": [],
        "input": [{"role": "user", "content": [{"type": "input_text", "text": "hello"}]}]}


def exchange(raw):
    client, server = socket.socketpair()
    seen = []
    secret = b"synthetic-upstream-secret"
    def forward(body):
        # A trusted adapter supplies the fixed upstream credential independently.
        seen.append((json.loads(body), secret))
        return b'data: {"type":"response.completed"}\n\n'
    thread = threading.Thread(target=serve_once, args=(server, RequestGate(json.dumps(BODY).encode()), forward))
    thread.start()
    with client:
        client.settimeout(3)
        client.sendall(raw); client.shutdown(socket.SHUT_WR)
        parts = []
        while True:
            try: part = client.recv(4096)
            except ConnectionResetError: break
            if not part: break
            parts.append(part)
    thread.join(5)
    assert not thread.is_alive()
    reply = b"".join(parts)
    assert secret not in reply
    return reply, seen


def wire(body=None, extra=b"", route=b"POST /v1/responses HTTP/1.1"):
    data = json.dumps(BODY if body is None else body).encode()
    return route + b"\r\nHost: daia-model\r\nContent-Type: application/json\r\nContent-Length: " + str(len(data)).encode() + b"\r\n" + extra + b"\r\n" + data


def test_valid_request_reaches_trusted_adapter_without_guest_headers():
    reply, seen = exchange(wire())
    assert reply.startswith(b"HTTP/1.1 200") and seen[0][0] == BODY
    assert len(seen) == 1


@pytest.mark.parametrize('extra', [
    b'Authorization: Bearer guest\r\n', b'Transfer-Encoding: chunked\r\n',
    b'Content-Length: 2\r\n', b'Upgrade: websocket\r\n',
    b'Host: evil.example\r\n', b'X-Forwarded-Host: evil.example\r\n',
    b'Content-Encoding: gzip\r\n', b' Content-Length: 2\r\n',
])
def test_ambiguous_or_authority_headers_never_reach_upstream(extra):
    reply, seen = exchange(wire(extra=extra))
    assert reply.startswith(b'HTTP/1.1 403') and not seen


@pytest.mark.parametrize('route', [b'CONNECT evil.example:443 HTTP/1.1',
    b'POST https://evil.example/v1/responses HTTP/1.1',
    b'POST /connectors HTTP/1.1', b'GET /v1/responses HTTP/1.1'])
def test_alternate_routes_denied(route):
    reply, seen = exchange(wire(route=route))
    assert reply.startswith(b'HTTP/1.1 403') and not seen


def test_provider_tool_injection_never_reaches_adapter():
    body = dict(BODY, tools=[{'type': 'mcp', 'server_url': 'https://example.org'}])
    reply, seen = exchange(wire(body))
    assert reply.startswith(b'HTTP/1.1 403') and not seen


def test_truncated_body_never_reaches_adapter():
    reply, seen = exchange(wire()[:-1])
    assert reply.startswith(b'HTTP/1.1 403') and not seen



def test_pipelined_second_request_is_never_forwarded():
    reply, seen = exchange(wire() + wire())
    assert reply.startswith(b'HTTP/1.1 200')
    assert len(seen) == 1


def test_template_binding_cannot_be_replaced_by_guest_model():
    body = dict(BODY, model='different-account-route')
    reply, seen = exchange(wire(body))
    assert reply.startswith(b'HTTP/1.1 403') and not seen



def test_partial_success_write_never_appends_error_response():
    class InterruptedWriter:
        def __init__(self):
            self.raw = wire(); self.writes = []; self.closed = False
        def __enter__(self): return self
        def __exit__(self, *args): self.closed = True
        def settimeout(self, value): pass
        def recv(self, size):
            part = self.raw[:size]; self.raw = self.raw[size:]; return part
        def sendall(self, value):
            self.writes.append(value[:50])
            raise TimeoutError('synthetic partial write')
    sock = InterruptedWriter()
    assert not serve_once(sock, RequestGate(json.dumps(BODY).encode()), lambda _: b'data: {}\n\n')
    assert sock.closed and len(sock.writes) == 1
    assert sock.writes[0].startswith(b'HTTP/1.1 200')



def test_native_metadata_is_accepted_but_not_forwarded():
    extra = b''.join(name + b': guest-value\r\n' for name in (
        b'originator', b'session-id', b'thread-id', b'x-client-request-id',
        b'x-codex-beta-features', b'x-codex-turn-metadata', b'x-codex-window-id'))
    reply, seen = exchange(wire(extra=extra))
    assert reply.startswith(b'HTTP/1.1 200') and seen[0][0] == BODY
    assert b'guest-value' not in reply


@pytest.mark.parametrize('route', [
    b'OPTIONS /v1/responses HTTP/1.1', b'GET /v1/models HTTP/1.1',
    b'GET /.well-known/oauth-authorization-server HTTP/1.1',
    b'GET /mcp HTTP/1.1', b'POST /mcp HTTP/1.1',
    b'GET /openapi.json HTTP/1.1', b'GET /tools/list HTTP/1.1',
])
def test_enumeration_routes_return_no_capability_details(route):
    reply, seen = exchange(wire(route=route))
    assert reply == b'HTTP/1.1 403 Forbidden\r\nConnection: close\r\nContent-Length: 0\r\n\r\n'
    assert seen == []


@pytest.mark.parametrize('method', ['initialize', 'tools/list', 'resources/list',
                                   'prompts/list', 'rpc.discover', 'unknown'])
def test_jsonrpc_discovery_on_model_route_is_not_dispatched(method):
    body = {'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': {}}
    reply, seen = exchange(wire(body))
    assert reply == b'HTTP/1.1 403 Forbidden\r\nConnection: close\r\nContent-Length: 0\r\n\r\n'
    assert seen == []


def bound_exchange(channel, raw):
    client, server = socket.socketpair()
    worker = threading.Thread(target=channel.serve, args=(server,))
    worker.start()
    with client:
        client.settimeout(3)
        client.sendall(raw)
        client.shutdown(socket.SHUT_WR)
        chunks = []
        while True:
            try:
                chunk = client.recv(4096)
            except ConnectionResetError:
                break
            if not chunk:
                break
            chunks.append(chunk)
    worker.join(5)
    assert not worker.is_alive()
    return b"".join(chunks)


def test_bound_channel_admits_only_its_completed_provider_reasoning():
    item = {"type": "reasoning", "summary": [],
            "encrypted_content": "synthetic-bound-state"}
    output = b"data: " + json.dumps({"type": "response.completed", "response": {
        "status": "completed", "output": [item]}}).encode() + b"\n\n"
    seen = []
    def forward(raw):
        seen.append(json.loads(raw))
        return output
    channel = AssignmentModelChannel(json.dumps(BODY).encode(), forward)
    history = dict(BODY, input=[item])
    # A guest cannot pre-register opaque state through its own request.
    assert bound_exchange(channel, wire(history)).startswith(b"HTTP/1.1 403")
    assert not seen
    assert bound_exchange(channel, wire()).startswith(b"HTTP/1.1 200")
    assert bound_exchange(channel, wire(history)).startswith(b"HTTP/1.1 200")
    assert len(seen) == 2
    other = AssignmentModelChannel(json.dumps(BODY).encode(), forward)
    assert bound_exchange(other, wire(history)).startswith(b"HTTP/1.1 403")
    assert len(seen) == 2


def test_bound_channel_does_not_admit_or_release_partial_response():
    item = {"type": "reasoning", "summary": [],
            "encrypted_content": "synthetic-incomplete-state"}
    calls = []
    def forward(raw):
        calls.append(raw)
        return b"data: " + json.dumps({"type": "response.output_item.done",
            "item": item}).encode() + b"\n\n"
    channel = AssignmentModelChannel(json.dumps(BODY).encode(), forward)
    reply = bound_exchange(channel, wire())
    assert reply.startswith(b"HTTP/1.1 403") and b"synthetic-incomplete-state" not in reply
    assert bound_exchange(channel, wire(dict(BODY,input=[item]))).startswith(b"HTTP/1.1 403")
    assert len(calls) == 1


@pytest.mark.parametrize("route", [
    b"GET /backend-api/conversations HTTP/1.1",
    b"POST /backend-api/connectors/invoke HTTP/1.1",
    b"POST /v1/responses?target=account HTTP/1.1",
    b"POST /v1/../backend-api/accounts HTTP/1.1",
    b"POST /v1/%72esponses HTTP/1.1",
])
def test_bound_channel_alternate_account_routes_cannot_call_upstream(route):
    calls = []
    channel = AssignmentModelChannel(json.dumps(BODY).encode(), lambda body: calls.append(body))
    assert bound_exchange(channel, wire(route=route)).startswith(b"HTTP/1.1 403")
    assert not calls


def test_bound_channel_rejects_concurrent_calls_and_releases_lock_after_failure():
    entered, release = threading.Event(), threading.Event()
    calls = []
    def forward(raw):
        calls.append(raw); entered.set()
        assert release.wait(3)
        raise ValueError("synthetic upstream failure")
    channel = AssignmentModelChannel(json.dumps(BODY).encode(), forward)
    first, first_server = socket.socketpair()
    thread = threading.Thread(target=channel.serve, args=(first_server,))
    thread.start()
    try:
        first.settimeout(3); first.sendall(wire())
        assert entered.wait(2)
        second, second_server = socket.socketpair()
        with second:
            second.settimeout(1)
            assert channel.serve(second_server) is False
            assert second.recv(1) == b""
        assert len(calls) == 1
    finally:
        release.set(); thread.join(5); first.close()
    assert not thread.is_alive()
    assert bound_exchange(channel, wire()).startswith(b"HTTP/1.1 403")
    assert len(calls) == 2
