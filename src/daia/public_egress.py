"""Experimental public CONNECT transport; never a provider credential proxy.

Run outside the worker under a separate service identity. The operator supplies
exact DNS names and host-network exclusions. TLS stays end-to-end: this limits
socket destinations, not SNI, HTTP paths or account actions on a shared endpoint.
"""
from __future__ import annotations

import ipaddress
import re
import selectors
import socket
import time
from collections.abc import Iterable

_NAME = re.compile(r"(?=.{1,253}\Z)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z][a-z0-9-]{0,62}\Z")
_TRANSITION = tuple(ipaddress.ip_network(x) for x in (
    "::ffff:0:0/96", "64:ff9b::/96", "64:ff9b:1::/48", "2002::/16", "2001::/32",
))


class Denied(ValueError):
    """A destination or request is outside the operator's public profile."""


def connect_public(authority: str, allowed: frozenset[str], excluded: Iterable[str] = ()) -> socket.socket:
    """Resolve once, validate every returned address, then dial a numeric sockaddr.

    A service watchdog must also bound DNS resolution, which the OS resolver can
    block on independently of the socket timeout. No environment proxy is used.
    """
    host, sep, port = authority.rpartition(":")
    if not sep or port != "443" or not _NAME.fullmatch(host) or host not in allowed:
        raise Denied("destination denied")
    networks = tuple(ipaddress.ip_network(x) for x in excluded)
    records = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)
    if not records:
        raise Denied("no destination")
    checked = []
    for family, kind, proto, _, address in records:
        if family not in (socket.AF_INET, socket.AF_INET6) or kind != socket.SOCK_STREAM or proto != socket.IPPROTO_TCP:
            raise Denied("unsupported address")
        text = address[0]
        if "%" in text:
            raise Denied("scoped address")
        ip = ipaddress.ip_address(text)
        if (not ip.is_global or ip.is_multicast or ip.is_reserved
                or any(ip in net for net in (*networks, *_TRANSITION))
                or address[1] != 443 or (family == socket.AF_INET6 and address[3] != 0)):
            raise Denied("non-public destination")
        checked.append((family, kind, proto, address))
    # One numeric attempt; callers can retry the whole authorization operation.
    family, kind, proto, address = checked[0]
    stream = socket.socket(family, kind, proto)
    try:
        stream.settimeout(5)
        stream.connect(address)
        peer = stream.getpeername()
        if ipaddress.ip_address(peer[0]) != ipaddress.ip_address(address[0]) or peer[1] != 443:
            raise Denied("peer mismatch")
        return stream
    except BaseException:
        stream.close()
        raise


def read_connect(client: socket.socket) -> str:
    """Read only the CONNECT header, preserving subsequent TLS bytes."""
    header = bytearray()
    deadline = time.monotonic() + 5
    while not header.endswith(b"\r\n\r\n"):
        remaining = deadline - time.monotonic()
        if remaining <= 0 or len(header) >= 4096:
            raise Denied("header limit")
        client.settimeout(remaining)
        data = client.recv(1)
        if not data:
            raise Denied("header incomplete")
        header.extend(data)
    try:
        lines = header.decode("ascii").split("\r\n")
        method, authority, version = lines[0].split(" ")
    except (ValueError, UnicodeError) as exc:
        raise Denied("invalid request") from exc
    if method != "CONNECT" or version not in ("HTTP/1.0", "HTTP/1.1"):
        raise Denied("unsupported request")
    for line in lines[1:-2]:
        name, separator, value = line.partition(":")
        if not separator or not re.fullmatch(r"[A-Za-z0-9-]+", name):
            raise Denied("invalid header")
        if name.lower() in ("content-length", "transfer-encoding"):
            raise Denied("body forbidden")
    return authority


def tunnel(client: socket.socket, upstream: socket.socket, *, seconds: float = 30, max_bytes: int = 8 * 1024 * 1024) -> None:
    """Bounded transport only; the external service also limits concurrency/time."""
    deadline = time.monotonic() + seconds
    transferred = 0
    with selectors.DefaultSelector() as selector:
        selector.register(client, selectors.EVENT_READ, upstream)
        selector.register(upstream, selectors.EVENT_READ, client)
        while transferred < max_bytes:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return
            for key, _ in selector.select(remaining):
                source, target = key.fileobj, key.data
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return
                source.settimeout(min(2, remaining))
                chunk = source.recv(min(65536, max_bytes - transferred))
                if not chunk:
                    selector.unregister(source)
                    target.shutdown(socket.SHUT_WR)
                    if not selector.get_map():
                        return
                    continue
                transferred += len(chunk)
                target.settimeout(min(2, max(0.001, deadline - time.monotonic())))
                target.sendall(chunk)
                if transferred >= max_bytes:
                    return


def handle_connection(client: socket.socket, allowed: frozenset[str], excluded: Iterable[str] = ()) -> None:
    """One connection, no credentials, body logs, listener or admission policy."""
    established = False
    try:
        authority = read_connect(client)
        with connect_public(authority, allowed, excluded) as upstream:
            client.settimeout(2)
            client.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
            established = True
            tunnel(client, upstream)
    except (OSError, ValueError):
        if not established:
            try:
                client.settimeout(1)
                client.sendall(b"HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\nConnection: close\r\n\r\n")
            except OSError:
                pass
    finally:
        client.close()
