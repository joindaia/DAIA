"""The barrier cannot start work before readiness or after expired authority."""
import importlib.util
from pathlib import Path
import socket
import threading
import time

import pytest

spec = importlib.util.spec_from_file_location('fresh_host_start',
    Path(__file__).parents[1] / 'scripts/fresh_host_start.py')
barrier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(barrier)
NONCE = 'a' * 32


def test_preparation_precedes_authority_and_fixed_start():
    host, guest = socket.socketpair()
    events = []
    errors = []
    def worker():
        try:
            events.append('prepared')
            barrier.ready_and_wait(guest, NONCE, seconds=2)
            events.append('started')
            guest.sendall(b'{"ok":true}')
        except Exception as exc:
            errors.append(exc)
    with host, guest:
        thread = threading.Thread(target=worker)
        thread.start()
        barrier.wait_ready(host, NONCE, seconds=2)
        events.append('authority')
        deadline = time.monotonic() + 2
        barrier.start(host, NONCE, deadline=deadline)
        host.settimeout(2)
        assert host.recv(100) == b'{"ok":true}'
        thread.join(2)
        assert not thread.is_alive() and not errors
        assert events == ['prepared', 'authority', 'started']


@pytest.mark.parametrize('payload', [b'DAIA_READY '+b'b'*32+b'\n', b'run shell\n', b''])
def test_bad_readiness_never_reaches_authority(payload):
    host, guest = socket.socketpair()
    with host, guest:
        guest.sendall(payload)
        guest.shutdown(socket.SHUT_WR)
        with pytest.raises((ValueError, ConnectionError)):
            barrier.wait_ready(host, NONCE, seconds=1)


def test_expired_assignment_sends_nothing():
    host, guest = socket.socketpair()
    with host, guest:
        with pytest.raises(TimeoutError):
            barrier.start(host, NONCE, deadline=time.monotonic() - 1)
        guest.setblocking(False)
        with pytest.raises(BlockingIOError):
            guest.recv(1)


def test_silent_peer_has_bounded_readiness_wait():
    host, guest = socket.socketpair()
    with host, guest:
        with pytest.raises(TimeoutError):
            barrier.wait_ready(host, NONCE, seconds=.01)


def test_guest_device_file_supports_same_handshake():
    import os
    import pty
    import tty
    master, slave = pty.openpty()
    tty.setraw(slave)
    errors = []
    with os.fdopen(master, 'r+b', buffering=0) as host, os.fdopen(slave, 'r+b', buffering=0) as guest:
        def worker():
            try:
                barrier.ready_and_wait(guest, NONCE, seconds=2)
            except Exception as exc:
                errors.append(exc)
        thread = threading.Thread(target=worker)
        thread.start()
        os.set_inheritable(host.fileno(), True)
        barrier.wait_ready(host, NONCE, seconds=2)
        assert not os.get_inheritable(host.fileno())
        barrier.start(host, NONCE, deadline=time.monotonic() + 2)
        thread.join(2)
        assert not thread.is_alive() and not errors
