"""Lab-only fixed Unix-socket relay for the isolated QEMU model channel."""
import os
import socket
import time


def relay(connection, input_fd, output_fd, seconds=30, max_bytes=16 * 1024 * 1024):
    """Bound both directions, including a peer that stops reading stdout.

    Consumes endpoint blocking modes. The external service watchdog remains
    responsible for process lifetime and resource limits if this process dies.
    """
    import math
    import select
    if (not math.isfinite(seconds) or seconds <= 0 or type(max_bytes) is not int
            or max_bytes < 1):
        raise ValueError('Finite positive limits required')
    connection.setblocking(False)
    for fd in (input_fd, output_fd):
        os.set_blocking(fd, False)
    upstream = connection.fileno()
    sources = {input_fd: upstream, upstream: output_fd}
    queues = {upstream: bytearray(), output_fd: bytearray()}
    uploaded_eof = False
    received = 0
    deadline = time.monotonic() + seconds
    while sources or any(queues.values()):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('Bridge deadline exceeded')
        # Bound each queue as well as total transfer. Stop reading until its
        # destination drains, so backpressure never becomes unbounded buffering.
        reads = [fd for fd, dest in sources.items() if len(queues[dest]) < 65536]
        writes = [fd for fd, data in queues.items() if data]
        readable, writable, _ = select.select(reads, writes, [], remaining)
        for fd in readable:
            try:
                data = os.read(fd, min(8192, max_bytes - received + 1))
            except BlockingIOError:
                continue
            except ConnectionResetError:
                data = b''
            if not data:
                sources.pop(fd)
                if fd == input_fd:
                    uploaded_eof = True
                else:
                    # Server has finished its response; no further upload.
                    sources.pop(input_fd, None)
                    queues[upstream].clear()
                continue
            received += len(data)
            if received > max_bytes:
                raise ValueError('Bridge byte limit exceeded')
            queues[sources[fd]].extend(data)
        for fd in writable:
            if not queues[fd]:
                continue
            try:
                count = os.write(fd, queues[fd])
            except BlockingIOError:
                continue
            except (BrokenPipeError, ConnectionResetError):
                if fd != upstream:
                    raise
                # Rejected upload: still drain the buffered HTTP rejection.
                queues[upstream].clear()
                sources.pop(input_fd, None)
                uploaded_eof = False
                continue
            del queues[fd][:count]
        if uploaded_eof and not queues[upstream]:
            try:
                connection.shutdown(socket.SHUT_WR)
            except OSError:
                pass
            uploaded_eof = False


if __name__ == "__main__":
    try:
        with socket.socket(socket.AF_UNIX) as connection:
            connection.settimeout(5)
            connection.connect("/run/daia-lab/gateway.sock")
            relay(connection, 0, 1)
    except OSError:
        raise SystemExit(1)
