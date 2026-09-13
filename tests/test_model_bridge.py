"""Real pipe/socket backpressure must obey the bridge's deadline and cap."""
import os
from pathlib import Path
import runpy
import socket
import threading
import sys
import time
import pytest

pytestmark = pytest.mark.skipif(sys.platform != 'linux', reason='Linux pipe/socket bridge')

relay = runpy.run_path(str(Path(__file__).parents[1] / "scripts/model_channel_bridge.py"))["relay"]


def test_drain_rejection_after_upload_breaks():
    connection, peer = socket.socketpair()
    reply = b"HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n\r\n"
    read_fd, write_fd = os.pipe(); out_read, out_write = os.pipe()
    try:
        os.write(write_fd, b"unfinished request body")
        peer.shutdown(socket.SHUT_RD)
        peer.sendall(reply)
        peer.shutdown(socket.SHUT_WR)
        relay(connection, read_fd, out_write, seconds=1)
        assert os.read(out_read, 4096) == reply
    finally:
        connection.close(); peer.close()
        for fd in (read_fd, write_fd, out_read, out_write): os.close(fd)


@pytest.mark.parametrize('direction', ['upload', 'download'])
def test_backpressure_cannot_hide_deadline(direction):
    connection, peer = socket.socketpair()
    read_fd, write_fd = os.pipe(); out_read, out_write = os.pipe()
    errors = []
    def run():
        try: relay(connection, read_fd, out_write, seconds=.2)
        except Exception as error: errors.append(error)
    thread = threading.Thread(target=run, daemon=True)
    started = time.monotonic()
    try:
        connection.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 4096)
        thread.start()
        source = write_fd if direction == 'upload' else peer.fileno()
        os.set_blocking(source, False)
        while time.monotonic() - started < .4 and thread.is_alive():
            try: os.write(source, b'x' * 8192)
            except BlockingIOError: time.sleep(.002)
        thread.join(1)
        assert not thread.is_alive()
        assert len(errors) == 1 and isinstance(errors[0], TimeoutError)
        assert time.monotonic() - started < 1.5
    finally:
        connection.close(); peer.close()
        for fd in (read_fd, write_fd, out_read, out_write): os.close(fd)
        thread.join(1)


def test_byte_limit():
    connection, peer = socket.socketpair()
    read_fd, write_fd = os.pipe(); out_read, out_write = os.pipe()
    try:
        os.write(write_fd, b'12345')
        with pytest.raises(ValueError, match='byte limit'):
            relay(connection, read_fd, out_write, max_bytes=4)
    finally:
        connection.close(); peer.close()
        for fd in (read_fd, write_fd, out_read, out_write): os.close(fd)
