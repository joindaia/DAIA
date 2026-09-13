"""Experimental fixed Codex HTTPS destination; not a released subscription broker.

Trusted controller supplies a public IP, credentials and limits. Worker input
must pass RequestGate first. No DNS, proxy environment, redirects or guest headers.
Native login, account binding and runtime network isolation remain external gates.
"""
import ipaddress
import socket
import ssl

from .model_request import Denied, _decode
from .model_upstream import LocalModelUpstream, _check_secret


class CodexHTTPSUpstream(LocalModelUpstream):
    _host = "chatgpt.com"
    _target = "/backend-api/codex/responses"

    def __init__(self, address: str, secret: str, account: str, *, seconds: float, requests: int):
        # Pin a controller-resolved literal for the whole assignment. TLS still
        # authenticates chatgpt.com, never the literal or a guest-selected name.
        ip = ipaddress.ip_address(address)
        if (not ip.is_global or ip.is_multicast or getattr(ip, "ipv4_mapped", None)
                or getattr(ip, "sixtofour", None) or getattr(ip, "teredo", None)):
            raise ValueError("public provider address required")
        _check_secret(account)
        self._address = str(ip)
        self._family = socket.AF_INET if ip.version == 4 else socket.AF_INET6
        self._account = account
        # Use host trust roots; the trusted launcher must supply a clean environment.
        # No insecure-context constructor option is exposed.
        self._tls = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self._tls.load_default_certs()
        self._tls.minimum_version = ssl.TLSVersion.TLSv1_2
        self._tls.set_alpn_protocols(["http/1.1"])
        super().__init__("", secret, seconds=seconds, requests=requests)

    def _new_socket(self):
        return socket.socket(self._family)

    def _connect(self, sock):
        sock.connect((self._address, 443))
        with self._lock:
            if self._revoked:
                raise Denied("upstream binding unavailable")
            wrapped = self._tls.wrap_socket(sock, server_hostname=self._host,
                                            do_handshake_on_connect=False)
            self._active = wrapped
        # Handshake is interruptible by the shared deadline/revocation watchdog.
        wrapped.do_handshake()
        return wrapped

    def _headers(self):
        return {**super()._headers(), "ChatGPT-Account-Id": self._account,
                "Accept": "text/event-stream"}

    def _check_media_type(self, response):
        self._missing_media_type = not response.headers.get_all("Content-Type", [])
        if not self._missing_media_type:
            super()._check_media_type(response)

    def _check_output(self, output):
        super()._check_output(output)
        if not self._missing_media_type:
            return
        # The fixed provider has been observed omitting Content-Type for Spark.
        # Require a complete structured Responses stream before releasing bytes.
        try:
            text = output.decode("utf-8").replace("\r\n", "\n")
        except UnicodeError:
            raise Denied("invalid provider stream") from None
        if not text.endswith("\n\n"):
            raise Denied("incomplete provider stream")
        completed = False
        for block in text.split("\n\n"):
            if not block.strip():
                continue
            data, event = [], None
            for line in block.split("\n"):
                if line.startswith(":"):
                    continue
                name, separator, value = line.partition(":")
                if not separator or name not in ("data", "event"):
                    raise Denied("invalid provider event")
                value = value.removeprefix(" ")
                if name == "data":
                    data.append(value)
                elif event is None:
                    event = value
                else:
                    raise Denied("duplicate provider event")
            if not data:
                if event is not None:
                    raise Denied("missing provider event data")
                continue
            payload = "\n".join(data)
            if payload == "[DONE]" and completed and event is None:
                continue
            if completed:
                raise Denied("event after completion")
            value = _decode(payload.encode())
            kind = value.get("type")
            if (not isinstance(kind, str) or not kind.startswith("response.")
                    or event is not None and event != kind):
                raise Denied("invalid provider event type")
            if kind == "response.completed":
                response = value.get("response", {})
                if (not isinstance(response, dict) or response.get("status") != "completed"
                        or not isinstance(response.get("output"), list)):
                    raise Denied("invalid provider completion")
                completed = True
        if not completed:
            raise Denied("missing provider completion")
