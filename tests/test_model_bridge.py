"""An early upstream rejection must survive an interrupted upload."""
import os
from pathlib import Path
import runpy
import socket

relay = runpy.run_path(str(Path(__file__).parents[1] / "scripts/model_channel_bridge.py"))["relay"]


def test_drain_rejection_after_upload_breaks():
    client, peer = socket.socketpair()
    reply = b"HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n\r\n"
    class EarlyReject(socket.socket):
        def sendall(self, data):
            assert data == b"unfinished request body"
            peer.sendall(reply)
            peer.shutdown(socket.SHUT_WR)
            raise BrokenPipeError("upstream stopped reading")
    connection = EarlyReject(fileno=client.detach())
    read_fd, write_fd = os.pipe(); out_read, out_write = os.pipe()
    try:
        os.write(write_fd, b"unfinished request body")
        relay(connection, read_fd, out_write, seconds=1)
        os.close(out_write); out_write = None
        assert os.read(out_read, 4096) == reply
    finally:
        connection.close(); peer.close()
        for fd in (read_fd, write_fd, out_read, out_write):
            if fd is not None: os.close(fd)
