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


def main(argv=None):
    """Trusted-launcher entrypoint: one inherited listener and two helper pipes."""
    import argparse
    import stat
    from contextlib import ExitStack
    from types import SimpleNamespace

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--listener-fd', type=int, required=True)
    parser.add_argument('--helper-input-fd', type=int, required=True)
    parser.add_argument('--helper-output-fd', type=int, required=True)
    parser.add_argument('--accept-seconds', type=float, default=120)
    parser.add_argument('--seconds', type=float, default=30)
    parser.add_argument('--max-bytes', type=int, default=256 * 1024)
    args = parser.parse_args(argv)
    try:
        if (sys.platform != 'linux' or os.geteuid() == 0 or os.getuid() != os.geteuid()
                or os.getgid() != os.getegid()):
            raise ValueError('Non-root Linux identity required')
        import fcntl
        descriptors = (args.listener_fd, args.helper_input_fd, args.helper_output_fd)
        if len(set(descriptors)) != 3 or min(descriptors) < 3:
            raise ValueError('Distinct inherited descriptors required')
        if (not all(math.isfinite(x) and x > 0 for x in (args.seconds, args.accept_seconds))
                or args.max_bytes < 1):
            raise ValueError('Finite positive limits required')
        for fd, access in ((args.helper_input_fd, os.O_WRONLY), (args.helper_output_fd, os.O_RDONLY)):
            if (not stat.S_ISFIFO(os.fstat(fd).st_mode)
                    or fcntl.fcntl(fd, fcntl.F_GETFL) & os.O_ACCMODE != access):
                raise ValueError('Directional helper pipes required')
        with ExitStack() as stack:
            listener = stack.enter_context(socket.socket(fileno=args.listener_fd))
            if (listener.family != socket.AF_UNIX
                    or listener.getsockopt(socket.SOL_SOCKET, socket.SO_TYPE) != socket.SOCK_STREAM
                    or not listener.getsockopt(socket.SOL_SOCKET, socket.SO_ACCEPTCONN)):
                raise ValueError('Unix listener required')
            helper = SimpleNamespace(
                stdin=stack.enter_context(os.fdopen(args.helper_input_fd, 'wb', buffering=0)),
                stdout=stack.enter_context(os.fdopen(args.helper_output_fd, 'rb', buffering=0)),
            )
            listener.settimeout(args.accept_seconds)
            connection, _ = listener.accept()
            listener.close()  # This process accepts exactly one worker connection.
            with connection:
                result = relay(connection, helper, seconds=args.seconds, max_bytes=args.max_bytes)
            return 0 if result == 'complete' else 124
    except TimeoutError:
        return 124
    except (OSError, ValueError):
        print('Assignment relay refused or disconnected', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
