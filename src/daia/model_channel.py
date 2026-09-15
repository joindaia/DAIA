"""One-request experimental HTTP channel for an external model gate.

Use only in the credential-free lab until native VM integration is established.
The trusted forward callback owns destination, credentials and response handling.
Guest headers are never forwarded. No CONNECT, upgrade, redirect or keep-alive.
"""
import socket
import threading
from collections.abc import Callable

from .model_request import Denied, RequestGate
from .model_response import completed_output


def serve_once(connection: socket.socket, gate: RequestGate,
               forward: Callable[[bytes], bytes], *, authority: str = "daia-model") -> bool:
    """Handle one bounded request and close; return whether forwarding succeeded.

    An external watchdog must bound total time, including the trusted callback.
    Response callbacks return bounded, already-reviewed SSE, never arbitrary
    upstream headers. This does not itself establish response secret filtering.
    """
    with connection:
        connection.settimeout(5)
        response_started = False
        try:
            wire = bytearray()
            while b"\r\n\r\n" not in wire:
                part = connection.recv(1)
                if not part:
                    raise Denied("incomplete headers")
                wire.extend(part)
                if len(wire) > 8192:
                    raise Denied("headers too large")
            lines = bytes(wire[:-4]).decode("ascii").split("\r\n")
            if lines[0] != "POST /v1/responses HTTP/1.1":
                raise Denied("route denied")
            headers = {}
            for line in lines[1:]:
                name, sep, value = line.partition(":")
                if not sep or not name or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-" for c in name):
                    raise Denied("invalid header")
                name = name.lower()
                if name in headers:
                    raise Denied("duplicate header")
                headers[name] = value.strip(" ")
            # Native client metadata is accepted only by exact name and discarded.
            if set(headers) - {"host", "content-length", "content-type", "accept", "connection", "user-agent",
                               "originator", "session-id", "thread-id", "x-client-request-id",
                               "x-codex-beta-features", "x-codex-turn-metadata", "x-codex-window-id",
                               "x-openai-internal-codex-responses-lite"}:
                raise Denied("header denied")
            if headers.get("host") != authority or headers.get("content-type") != "application/json":
                raise Denied("destination or encoding denied")
            length = headers.get("content-length", "")
            if not length.isascii() or not length.isdecimal() or not 0 < int(length) <= 1024 * 1024:
                raise Denied("invalid length")
            body = bytearray()
            while len(body) < int(length):
                part = connection.recv(min(65536, int(length) - len(body)))
                if not part:
                    raise Denied("incomplete body")
                body.extend(part)
            cleaned = gate.validate("POST", "/v1/responses", bytes(body))
            output = forward(cleaned)
            if type(output) is not bytes or len(output) > 8 * 1024 * 1024:
                raise Denied("invalid response")
            reply = b"HTTP/1.1 200 OK\r\nContent-Type: text/event-stream\r\nConnection: close\r\nContent-Length: " + str(len(output)).encode() + b"\r\n\r\n" + output
            response_started = True
            connection.sendall(reply)
            return True
        except (Denied, ValueError, OSError):
            if response_started:
                return False
            try:
                connection.sendall(b"HTTP/1.1 403 Forbidden\r\nConnection: close\r\nContent-Length: 0\r\n\r\n")
            except OSError:
                pass
            return False


class AssignmentModelChannel:
    """One assignment's request gate and completed-response admission sequence.

    Construct outside the worker with an independently approved template and a
    fixed authenticated upstream callback. The callback owns credentials,
    deadline, request budget and revocation. A new object is required for every
    assignment/account binding; neither its state nor methods are worker tools.
    This does not supply a listener, process isolation or native OAuth login.
    """

    def __init__(self, approved_template: bytes, forward: Callable[[bytes], bytes],
                 *, authority: str = "daia-model"):
        self._gate = RequestGate(approved_template)
        self._forward = forward
        self._authority = authority
        self._busy = threading.Lock()

    def serve(self, connection: socket.socket) -> bool:
        # A queued request must not race the preceding response's reasoning
        # admission. Reject rather than allocate unbounded waiting threads.
        if not self._busy.acquire(blocking=False):
            connection.close()
            return False
        try:
            def forward(cleaned):
                output = self._forward(cleaned)
                self._gate.record_provider_output(completed_output(output))
                return output
            return serve_once(connection, self._gate, forward,
                              authority=self._authority)
        finally:
            self._busy.release()
