import socket
import subprocess
import sys
import threading
import time
from contextlib import contextmanager

import pytest

from daia.assignment_relay import relay

pytestmark = pytest.mark.skipif(sys.platform != 'linux', reason='Linux pipe/socket relay')


@contextmanager
def exchange(program, **limits):
    client, peer = socket.socketpair()
    client.settimeout(3)
    helper = subprocess.Popen([sys.executable, '-I', '-u', '-c', program],
                              stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                              stderr=subprocess.DEVNULL)
    results, errors = [], []
    def run():
        try:
            results.append(relay(peer, helper, **limits))
        except Exception as error:
            errors.append(error)
        finally:
            peer.close()
    thread = threading.Thread(target=run)
    thread.start()
    try:
        yield client, helper, thread, results, errors
    finally:
        client.close()
        if helper.poll() is None:
            helper.kill()
        helper.communicate(timeout=3)
        thread.join(3)
        assert not thread.is_alive()


def test_half_close_drains_request_and_response():
    program = 'import sys; assert sys.stdin.buffer.read()==b"request"; sys.stdout.buffer.write(b"response")'
    with exchange(program, seconds=2) as (client, helper, thread, results, errors):
        client.sendall(b'request')
        client.shutdown(socket.SHUT_WR)
        received = bytearray()
        while data := client.recv(32):
            received.extend(data)
        thread.join(2)
        assert bytes(received) == b'response'
        assert results == ['complete'] and not errors
        assert helper.wait(timeout=2) == 0
        assert helper.stdin is None


def test_stalled_helper_cannot_block_deadline():
    start = time.monotonic()
    with exchange('import time; time.sleep(10)', seconds=.15) as (client, _, thread, results, errors):
        client.sendall(b'x' * (128 * 1024))  # More than a pipe buffer; helper never reads.
        thread.join(2)
        assert not thread.is_alive() and results == ['timeout'] and not errors
        assert time.monotonic() - start < 2


@pytest.mark.parametrize('program,payload,cap', [
    ('import sys;sys.stdout.buffer.write(b"12345")', b'', 4),
    ('import sys;assert sys.stdin.buffer.read(3)==b"abc";sys.stdout.buffer.write(b"1234")', b'abc', 6),
])
def test_combined_byte_limit_rejects_excess_response(program, payload, cap):
    with exchange(program, seconds=2, max_bytes=cap) as (client, _, thread, results, errors):
        if payload:
            client.sendall(payload)
        # A rejected transfer need not be delivered, but can never exceed its cap.
        data = client.recv(32)
        thread.join(2)
        assert len(data) <= cap and not results
        assert len(errors) == 1 and isinstance(errors[0], ValueError)
        assert str(errors[0]) == 'Relay output limit exceeded'


def test_invalid_limits_reject_before_touching_endpoints():
    for limits in ({'seconds': float('inf')}, {'seconds': 0}, {'max_bytes': 0}, {'max_bytes': True}):
        with pytest.raises(ValueError, match='finite positive'):
            relay(None, None, **limits)
