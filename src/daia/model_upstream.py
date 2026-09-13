"""Lab-only credential adapter for a fixed local Unix-socket model provider.

No internet transport or subscription support. Run outside the worker. Pass only
RequestGate output. The socket path, secret and limits are trusted controller input.
"""
import http.client
import socket
import threading
import time

from .model_request import Denied


def _check_secret(secret: str) -> None:
    if not isinstance(secret, str) or not 0 < len(secret) <= 8192 or any(
        c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_." for c in secret
    ):
        raise ValueError("invalid lab credential")


class LocalModelUpstream:
    _host = "daia-upstream"
    _target = "/v1/responses"

    def _new_socket(self):
        return socket.socket(socket.AF_UNIX)

    def _connect(self, sock):
        sock.connect(self._path)
        return sock

    def _headers(self):
        return {"Authorization": "Bearer " + self._secret,
                "Content-Type": "application/json", "Connection": "close"}

    def __init__(self, path: str, secret: str, *, seconds: float, requests: int):
        _check_secret(secret)
        if not 0 < seconds <= 300 or type(requests) is not int or not 0 < requests <= 100:
            raise ValueError("invalid lab budget")
        self._path = path
        self._secret = secret
        self._deadline = time.monotonic() + seconds
        self._remaining = requests
        self._lock = threading.Lock()
        self._revoked = False
        self._active = None

    def replace_credential(self, secret: str) -> None:
        """Trusted controller only: rotate between calls without renewing authority.

        This is not a guest API or an OAuth verifier. The caller establishes
        credential freshness and account binding before supplying it.
        """
        _check_secret(secret)
        with self._lock:
            if (self._revoked or time.monotonic() >= self._deadline
                    or self._remaining == 0 or self._active is not None):
                raise Denied("upstream binding unavailable")
            self._secret = secret

    def revoke(self) -> None:
        with self._lock:
            self._revoked = True
            if self._active is not None:
                try:
                    self._active.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass

    def __call__(self, body: bytes) -> bytes:
        if type(body) is not bytes or not 0 < len(body) <= 1024 * 1024:
            raise Denied("invalid upstream body")
        with self._lock:
            left = self._deadline - time.monotonic()
            if self._revoked or left <= 0 or self._remaining == 0 or self._active is not None:
                raise Denied("upstream binding unavailable")
            self._remaining -= 1  # Failed attempts consume budget too.
            sock = self._new_socket()
            self._active = sock
        conn = http.client.HTTPConnection(self._host, timeout=min(5, left))
        # A socket timeout only limits inactivity; a trickling peer can keep
        # resetting it. Revoke at the assignment deadline even during I/O.
        watchdog = threading.Timer(left, self.revoke)
        watchdog.daemon = True
        watchdog.start()
        try:
            sock.settimeout(min(5, left))
            sock = self._connect(sock)
            conn.sock = sock
            with self._lock:
                if self._revoked or time.monotonic() >= self._deadline:
                    raise Denied("upstream binding unavailable")
            # Never hold the state lock over blocking I/O: revoke must be able
            # to shut down a blocked request as well as a blocked response.
            conn.request("POST", self._target, body=body, headers=self._headers())
            response = conn.getresponse()
            if response.status != 200 or response.getheader("Content-Type") != "text/event-stream":
                raise Denied("upstream response rejected")
            if response.getheader("Transfer-Encoding") or response.getheader("Content-Encoding"):
                raise Denied("upstream encoding rejected")
            lengths = response.headers.get_all("Content-Length", [])
            if len(lengths) != 1 or not lengths[0].isascii() or not lengths[0].isdecimal():
                raise Denied("upstream length rejected")
            size = int(lengths[0])
            if size > 8 * 1024 * 1024:
                raise Denied("upstream response too large")
            output = response.read(size)
            if len(output) != size or self._secret.encode() in output:
                raise Denied("upstream body rejected")
            with self._lock:
                if self._revoked or time.monotonic() >= self._deadline:
                    raise Denied("upstream binding unavailable")
            return output
        except (OSError, http.client.HTTPException):
            raise Denied("upstream transport failed") from None
        finally:
            watchdog.cancel()
            watchdog.join()
            conn.close()
            sock.close()
            with self._lock:
                if self._active is not None:
                    self._active.close()
                self._active = None
