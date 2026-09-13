"""Guest-only stdio adapter for the prepared Linux worker's assignment channel.

Install inside the disposable VM, never as a host-side credential proxy. The
trusted VM launcher maps the fixed virtual address to one assignment-bound helper.
This module provides transport limits, not network isolation or authorization.
"""
import os
import socket
import sys
from contextlib import ExitStack
from types import SimpleNamespace

from .assignment_relay import relay


def main():
    if sys.platform != 'linux':
        print('Assignment guest transport requires Linux', file=sys.stderr)
        return 1
    try:
        with ExitStack() as stack:
            connection = stack.enter_context(socket.create_connection(
                ('10.0.2.100', 3128), timeout=8))
            # Reverse the helper-side pipes: model stdin goes to the socket,
            # socket replies go to model stdout. Duplicate before relay closes EOF.
            streams = SimpleNamespace(
                stdin=stack.enter_context(os.fdopen(os.dup(1), 'wb', buffering=0)),
                stdout=stack.enter_context(os.fdopen(os.dup(0), 'rb', buffering=0)),
            )
            # The adapter owns process stdout. Keeping fd 1 open would hide
            # helper EOF from a client that has not closed its request stream.
            os.close(1)
            sys.stdout = None
            result = relay(connection, streams, seconds=30, max_bytes=256 * 1024)
            return 0 if result == 'complete' else 124
    except (OSError, ValueError):
        print('Assignment guest transport refused or disconnected', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
