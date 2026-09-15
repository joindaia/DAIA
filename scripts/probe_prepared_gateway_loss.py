"""Credential-free gateway disappearance on the actual prepared VM transport.

Run under a bounded test service. Accept one research CONNECT with the actual
handler, then remove its listener. No START, model authority or public request.
The existing live TCP canary verifies that no direct fallback reaches the host.
"""
import json
import os
from pathlib import Path
import pwd
import socket
import threading

from daia.public_egress import handle_connection
from probe_prepared_network import prepare, report_for, fixed_control, network_state


def guest_probe():
    return """import socket
_request = b'CONNECT 127.0.0.1:443 HTTP/1.1\\r\\nHost: 127.0.0.1:443\\r\\n\\r\\n'
with socket.create_connection(('10.0.2.102',3128),timeout=5) as _s:
    _s.settimeout(5); _s.sendall(_request)
    assert _s.recv(4096).startswith(b'HTTP/1.1 403 ')
# The test host unlinks the listener before returning that first response.
with socket.create_connection(('10.0.2.102',3128),timeout=5) as _s:
    _s.settimeout(5)
    try:
        _s.sendall(_request)
        assert _s.recv(4096) == b''
    except (ConnectionResetError, BrokenPipeError):
        pass
print('DAIA_PREBOOT research_gateway_removed=true',flush=True)
"""


def probe(image, digest, bundle, parent):
    endpoint = Path('/run/daia-research/gateway.sock')
    if endpoint.exists() or endpoint.is_symlink():
        raise ValueError('Existing research endpoint; refuse to interfere')
    if not endpoint.parent.is_dir():
        raise ValueError('Provisioned research directory required')
    worker = pwd.getpwnam('daia-runtime')
    host = None
    accepted = []
    failures = []
    listener = socket.socket(socket.AF_UNIX)
    bound = False
    try:
        listener.bind(str(endpoint)); bound = True
        os.chown(endpoint, 0, worker.pw_gid); endpoint.chmod(0o660)
        listener.listen(1); listener.settimeout(120)
        def serve_once():
            try:
                client, _ = listener.accept()
                accepted.append(True)
                listener.close(); endpoint.unlink()
                handle_connection(client, frozenset())
            except Exception as error:
                failures.append(type(error).__name__)
        thread = threading.Thread(target=serve_once, daemon=True)
        thread.start()
        host = prepare(image, digest, bundle, parent)
        report = report_for(host, parent)
        thread.join(5)
        if thread.is_alive() or failures or accepted != [True] or endpoint.exists():
            raise RuntimeError('Gateway removal control failed')
        serial = Path('/proc') / str(report['main_pid']) / 'root' / str(host.root / 'work/serial.txt').lstrip('/')
        if 'DAIA_PREBOOT research_gateway_removed=true' not in serial.read_text(errors='replace'):
            raise RuntimeError('Guest gateway-loss marker missing')
        fixed_control(report['main_pid'])
        network_state(report['network_control'], 2)
        return {'gateway_connection_accepted': True, 'actual_handler_rejected_private_connect': True,
                'listener_removed': True, 'guest_reconnect_closed_without_timeout': True,
                'live_direct_controls': 2, 'unexpected_direct_connections': 0,
                'start_sent': False, 'credentials_used': False, 'provider_requests': 0}
    finally:
        listener.close()
        if bound:
            endpoint.unlink(missing_ok=True)
        if host is not None:
            host.close()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('image', 'digest', 'bundle', 'parent'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    print(json.dumps(probe(args.image, args.digest, args.bundle, args.parent)))
