"""Trusted fresh-host adapter for the three fixed outer QEMU guestfwd channels.

One externally supervised process per channel. No credentials, authentication,
assignment selection or authority renewal. Outer host services remain responsible
for protocol validation and the original assignment deadline. This adapter alone
is not a network sandbox or a completed subscription integration.
"""
import argparse
import os
from pathlib import Path
import socket
import time

from model_channel_bridge import relay

CHANNELS = {
    'assignment': ('/run/daia-lab/gateway.sock', '10.0.2.100', 150, 256 * 1024),
    'model': ('/run/daia-lab/model.sock', '10.0.2.101', 30, 16 * 1024 * 1024),
    'research': ('/run/daia-research/gateway.sock', '10.0.2.102', 30, 16 * 1024 * 1024),
}


def forward(client, channel):
    _, address, seconds, maximum = CHANNELS[channel]
    deadline = time.monotonic() + seconds
    with socket.create_connection((address, 3128), timeout=min(5, seconds)) as upstream:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('Fresh-host channel connection deadline exceeded')
        relay(upstream, client.fileno(), client.fileno(), seconds=remaining,
              max_bytes=maximum)


def serve(channel):
    path = Path(CHANNELS[channel][0])
    parent = path.parent
    if (parent.is_symlink() or not parent.is_dir()
            or parent.stat().st_uid != os.geteuid()
            or parent.stat().st_mode & 0o022):
        raise ValueError('Service-owned non-writable parent required')
    # A trusted installer creates the service-owned directory and runtime group.
    # Refuse stale sockets; never unlink a potentially live endpoint automatically.
    with socket.socket(socket.AF_UNIX) as listener:
        prior_mask = os.umask(0o117)
        try:
            listener.bind(str(path))
        finally:
            os.umask(prior_mask)
        listener.listen(4)
        while True:
            client, _ = listener.accept()
            with client:
                try:
                    forward(client, channel)
                except (OSError, ValueError):
                    pass  # Drop only this connection; never retry a submission.
            if channel == 'assignment':
                return  # One lease connection, never a fresh clock on reconnect.


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('channel', choices=CHANNELS)
    serve(parser.parse_args().channel)
