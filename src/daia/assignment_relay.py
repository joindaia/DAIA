"""Bounded Linux transport between one worker socket and one pinned MCP helper.

The trusted launcher supplies already-open endpoints and owns their lifecycle.
This module does not accept destinations, start processes, parse task content or
provide an isolation boundary. Run it without administrative privileges.
"""
import math
import os
import select
import socket
import sys
import time


def relay(connection, helper, *, seconds=30, max_bytes=256 * 1024):
    """Forward opaque bytes; return 'complete' or 'timeout', reject excess output.

    Endpoints are consumed and left nonblocking. On worker EOF, drain its request
    queue before closing helper stdin; clear that Popen property for safe later
    communicate(). On helper EOF, drain replies before half-closing the socket.
    The caller must close endpoints and terminate the helper on every exit path,
    including timeout, output rejection and exceptions. An independent process
    watchdog remains necessary if the launcher itself dies.
    """
    if (sys.platform != 'linux' or not math.isfinite(seconds) or seconds <= 0
            or type(max_bytes) is not int or max_bytes < 1):
        raise ValueError('Linux and finite positive relay limits required')
    incoming = connection.fileno()
    reply = helper.stdout.fileno()
    request = helper.stdin.fileno()
    for fd in (incoming, reply, request):
        os.set_blocking(fd, False)
    destinations = {incoming: request, reply: incoming}
    queues = {request: bytearray(), incoming: bytearray()}
    closing = set()
    deadline = time.monotonic() + seconds
    received = 0
    while True:
        if not destinations and not any(queues.values()):
            return 'complete'
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return 'timeout'
        readable, writable, _ = select.select(
            list(destinations), [fd for fd, data in queues.items() if data], [], remaining)
        if time.monotonic() >= deadline:
            return 'timeout'
        for fd in readable:
            try:
                data = os.read(fd, min(8192, max_bytes - received + 1))
            except BlockingIOError:
                continue
            if not data:
                closing.add(destinations.pop(fd))
                continue
            received += len(data)
            if received > max_bytes:
                raise ValueError('Relay output limit exceeded')
            queues[destinations[fd]].extend(data)
        for fd in writable:
            try:
                count = os.write(fd, queues[fd])
            except BlockingIOError:
                continue
            del queues[fd][:count]
        for fd in list(closing):
            if queues[fd]:
                continue
            if fd == request:
                helper.stdin.close()
                helper.stdin = None
            else:
                connection.shutdown(socket.SHUT_WR)
            closing.remove(fd)
