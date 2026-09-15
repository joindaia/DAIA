"""One-use start barrier for the trusted clean-host acceptance fixture.

The dedicated serial stream accepts no command, path, credential or deadline.
The host must wait for readiness BEFORE obtaining finite assignment authority.
This is correlation, not guest attestation or an authority mechanism.
"""
import os
import re
import select
import time


def marker(action, nonce):
    if action not in ('READY', 'START') or not re.fullmatch('[0-9a-f]{32}', nonce):
        raise ValueError('Fixed action and fresh correlation nonce required')
    return f'DAIA_{action} {nonce}\n'.encode('ascii')


def receive(stream, expected, deadline):
    """Read exactly one bounded marker, without buffering later result bytes."""
    os.set_inheritable(stream.fileno(), False)
    os.set_blocking(stream.fileno(), False)
    received = bytearray()
    while len(received) < len(expected):
        remaining = deadline - time.monotonic()
        if remaining <= 0 or not select.select([stream], [], [], remaining)[0]:
            raise TimeoutError('Clean-host start barrier expired')
        try:
            chunk = os.read(stream.fileno(), 1)
        except BlockingIOError:
            continue
        if not chunk:
            raise ConnectionError('Clean-host start barrier closed')
        received.extend(chunk)
        if not expected.startswith(received):
            raise ValueError('Unexpected clean-host start marker')


def send(stream, payload, deadline):
    """Support both the host Unix socket and the dedicated guest virtio port."""
    os.set_inheritable(stream.fileno(), False)
    os.set_blocking(stream.fileno(), False)
    while payload:
        remaining = deadline - time.monotonic()
        if remaining <= 0 or not select.select([], [stream], [], remaining)[1]:
            raise TimeoutError('Clean-host start barrier expired')
        try:
            count = os.write(stream.fileno(), payload)
        except BlockingIOError:
            continue
        if not count:
            raise ConnectionError('Clean-host start barrier closed')
        payload = payload[count:]


def wait_ready(stream, nonce, *, seconds=120):
    """Installation readiness only; must not create/extend a job allowance."""
    if not 0 < seconds <= 120:
        raise ValueError('Readiness wait must be bounded to 120 seconds')
    receive(stream, marker('READY', nonce), time.monotonic() + seconds)


def start(stream, nonce, *, deadline):
    """Send once, using the already frozen monotonic assignment deadline."""
    remaining = deadline - time.monotonic()
    if not 0 < remaining <= 150:
        raise TimeoutError('No valid remaining assignment time')
    send(stream, marker('START', nonce), deadline)


def ready_and_wait(stream, nonce, *, seconds=60):
    """Trusted fixture side, after preparation; never accepts executable input."""
    if not 0 < seconds <= 60:
        raise ValueError('Start wait must be bounded to 60 seconds')
    deadline = time.monotonic() + seconds
    send(stream, marker('READY', nonce), deadline)
    receive(stream, marker('START', nonce), deadline)
