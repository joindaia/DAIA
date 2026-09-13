"""Lab-only fixed Unix-socket relay for the isolated QEMU model channel."""
import os
import selectors
import socket
import time


def relay(connection, input_fd, output_fd, seconds=30):
    deadline = time.monotonic() + seconds
    with selectors.DefaultSelector() as streams:
        streams.register(input_fd, selectors.EVENT_READ, "up")
        streams.register(connection, selectors.EVENT_READ, "down")
        while time.monotonic() < deadline:
            for key, _ in streams.select(max(0, deadline - time.monotonic())):
                if key.data == "up":
                    data = os.read(input_fd, 65536)
                    try:
                        if data:
                            connection.sendall(data)
                            continue
                        connection.shutdown(socket.SHUT_WR)
                    except (BrokenPipeError, ConnectionResetError):
                        # Early HTTP rejection can close input while its reply is
                        # still buffered. Stop uploading, but drain that reply.
                        pass
                    streams.unregister(input_fd)
                else:
                    try:
                        data = connection.recv(65536)
                    except ConnectionResetError:
                        return
                    if not data:
                        return
                    while data:
                        data = data[os.write(output_fd, data):]


if __name__ == "__main__":
    try:
        with socket.socket(socket.AF_UNIX) as connection:
            connection.connect("/run/daia-lab/gateway.sock")
            connection.settimeout(5)
            relay(connection, 0, 1)
    except OSError:
        raise SystemExit(1)
