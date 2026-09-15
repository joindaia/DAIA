"""Credential-free direct-QEMU restrict=on network probe.

The guest must already carry the fixed pre-READY direct-TCP denial check.  This
probe instruments only PreparedHost's generated boot.py in its own transient
parent service; it adds no runtime API, relay, destination, START, authority, or
provider operation.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile
import time
import types
import uuid

SCRIPT_DIRECTORY = Path(__file__).resolve().parent
if str(SCRIPT_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIRECTORY))
import fresh_host_controller as fresh
from probe_prepared_worker_crash import bundle_path, regular, unit_stem, write_report

PORT = 38443
CONTROL = b'DAIA_PREPARED_NETWORK_CONTROL\n'
ACK = b'DAIA_PREPARED_NETWORK_ACK\n'
READY_MARKER = 'DAIA_PREBOOT boundary_direct_tcp_denied=true'
PARENT_UNIT = re.compile(r'daia-controller-job-[0-9a-f]{32}\.service')


def show(unit, property_name):
    return subprocess.run(['systemctl', 'show', unit, '--property=' + property_name,
                           '--value'], check=True, capture_output=True, text=True,
                          timeout=5).stdout.strip()


def private_view(pid, path):
    return Path('/proc') / str(pid) / 'root' / str(path).lstrip('/')


def listener_code(control_file):
    return """import socket,threading
_network_file = {control_file!r}
_network_control = {control!r}
_network_ack = {ack!r}
_network_state = {{'listener_active_before_qemu': False, 'controls': 0, 'unexpected': 0}}
def _network_write():
 temporary = _network_file + '.tmp'
 with open(temporary, 'w') as stream: json.dump(_network_state, stream)
 os.replace(temporary, _network_file)
_network_listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
_network_listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
_network_listener.bind(('127.0.0.1', {port}))
_network_listener.listen(4)
_network_listener.settimeout(.1)
_network_state['listener_active_before_qemu'] = True
_network_write()
def _network_serve():
 while True:
  try:
   connection, _ = _network_listener.accept()
  except socket.timeout:
   continue
  except OSError:
   return
  with connection:
   connection.settimeout(.5)
   try: payload = connection.recv(64)
   except OSError: payload = b''
   if payload == _network_control:
    _network_state['controls'] += 1
    _network_write()
    connection.sendall(_network_ack)
   else:
    _network_state['unexpected'] += 1
    _network_write()
threading.Thread(target=_network_serve, daemon=True).start()
with socket.create_connection(('127.0.0.1', {port}), timeout=2) as _network_client:
 _network_client.sendall(_network_control)
 if _network_client.recv(len(_network_ack)) != _network_ack: raise RuntimeError('Network control failed')
""".format(control_file=str(control_file), control=CONTROL, ack=ACK, port=PORT)


def instrument_prepared_launch(original_run, unit):
    state = {'injected': False}

    def run(argv, *args, **kwargs):
        if isinstance(argv, list) and argv and argv[0] == 'systemd-run' and '--unit=' + unit in argv:
            if (state['injected'] or argv[:4] != ['systemd-run', '--quiet', '--collect', '--unit=' + unit]
                    or len(argv) < 4 or argv[-3:-1] != ['/usr/bin/python3', '-I']
                    or Path(argv[-1]).name != 'boot.py'):
                raise RuntimeError('Unexpected generated PreparedHost launch')
            boot = Path(argv[-1])
            control_file = boot.parent / 'control' / 'network.json'
            if not control_file.parent.is_dir():
                raise RuntimeError('Generated PreparedHost control directory missing')
            code = boot.read_text()
            marker = 'r=subprocess.run('
            if code.count(marker) != 1:
                raise RuntimeError('Unique QEMU launch marker required')
            boot.write_text(code.replace(marker, listener_code(control_file) + marker))
            state['injected'] = True
        return original_run(argv, *args, **kwargs)

    return run, state


def prepare(image, digest, bundle, parent_unit):
    original = fresh.subprocess
    unit = 'daia-prepared-' + uuid.uuid4().hex
    # PreparedHost chooses the same name internally; freeze it only for this test call.
    original_uuid = fresh.uuid.uuid4
    fresh.uuid.uuid4 = lambda: types.SimpleNamespace(hex=unit.removeprefix('daia-prepared-'))
    intercepted, state = instrument_prepared_launch(original.run, unit)
    fresh.subprocess = types.SimpleNamespace(run=intercepted, CompletedProcess=original.CompletedProcess,
                                              SubprocessError=original.SubprocessError)
    try:
        host = fresh.PreparedHost(image, digest, bundle, parent_unit)
    finally:
        fresh.subprocess = original
        fresh.uuid.uuid4 = original_uuid
    if not state['injected']:
        host.close()
        raise RuntimeError('PreparedHost launch was not instrumented')
    return host


def network_state(path, controls):
    deadline = time.monotonic() + 5
    expected = {'listener_active_before_qemu': True, 'controls': controls, 'unexpected': 0}
    while True:
        if Path(path).exists() and json.loads(Path(path).read_text()) == expected:
            return expected
        if time.monotonic() >= deadline:
            raise TimeoutError('Durable prepared network control missing')
        time.sleep(.05)


def fixed_control(pid):
    code = ("import socket\n"
            f"control={CONTROL!r}; ack={ACK!r}\n"
            f"with socket.create_connection(('127.0.0.1',{PORT}),timeout=2) as s:\n"
            " s.sendall(control)\n"
            " assert s.recv(len(ack)) == ack\n")
    subprocess.run(['/usr/bin/nsenter', '-t', str(pid), '-n', '/usr/bin/python3', '-I', '-c', code],
                   check=True, capture_output=True, timeout=5)


def report_for(host, parent_unit):
    pid = show(host.unit, 'MainPID')
    if not pid.isdecimal() or int(pid) == 0:
        raise RuntimeError('Prepared worker has no main process')
    network = host.root / 'control' / 'network.json'
    serial = private_view(pid, host.root / 'work' / 'serial.txt')
    deadline = time.monotonic() + 5
    while not (network.exists() and serial.exists()):
        if time.monotonic() >= deadline:
            raise TimeoutError('Prepared network evidence unavailable')
        time.sleep(.05)
    network_state(network, 1)
    if READY_MARKER not in serial.read_text(errors='replace'):
        raise RuntimeError('Guest direct-TCP denial marker missing before READY')
    return {'parent_unit': parent_unit, 'prepared_unit': host.unit + '.service',
            'prepared_root': str(host.root), 'main_pid': int(pid),
            'network_control': str(network), 'guest_marker_before_ready': True,
            'listener_active_before_qemu': True, 'controls_before_guest': 1,
            'unexpected_before_guest': 0, 'start_sent': False,
            'credentials_used': False, 'provider_requests': 0}


def parent(image, digest, bundle, state, parent_unit):
    host = prepare(regular(image), digest, bundle_path(bundle), parent_unit)
    try:
        write_report(Path(state) / 'ready.json', report_for(host, parent_unit))
        signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
        while True:
            time.sleep(60)
    finally:
        host.close()


def parent_command(image, digest, bundle, state, unit):
    stem = unit_stem(unit)
    properties = {'Type': 'exec', 'RuntimeMaxSec': '160', 'TimeoutStopSec': '5',
                  'KillMode': 'control-group', 'PrivateNetwork': 'yes',
                  'NoNewPrivileges': 'yes', 'ProtectHome': 'yes',
                  'InaccessiblePaths': '/mnt', 'ReadWritePaths': '/run',
                  'RuntimeDirectory': stem, 'RuntimeDirectoryMode': '0755'}
    command = ['systemd-run', '--quiet', '--unit=' + unit]
    for key, value in properties.items():
        command += ['-p', key + '=' + value]
    return command + ['/usr/bin/python3', '-I', str(Path(__file__)), '--parent',
                      '--image', str(image), '--image-sha256', digest,
                      '--bundle', str(bundle), '--state', str(state), '--parent-unit', unit]


def wait_report(path):
    deadline = time.monotonic() + 130
    while not path.exists():
        if time.monotonic() >= deadline:
            raise TimeoutError('Prepared worker did not reach READY')
        time.sleep(.05)
    return json.loads(path.read_text())


def observer(image, digest, bundle):
    if os.geteuid() != 0:
        raise SystemExit('Requires the preconfigured isolated lab administrator')
    image, bundle = regular(image), bundle_path(bundle)
    if not re.fullmatch(r'[0-9a-f]{64}', digest):
        raise ValueError('Prepared image hash required')
    with image.open('rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() != digest:
            raise ValueError('Prepared image digest mismatch')
    parent_unit = 'daia-controller-job-' + uuid.uuid4().hex + '.service'
    if not PARENT_UNIT.fullmatch(parent_unit):
        raise AssertionError('Fixed parent unit required')
    result = {'credentials_used': False, 'provider_requests': 0, 'start_sent': False}
    with tempfile.TemporaryDirectory(prefix='daia-prepared-network-', dir='/run') as directory:
        state = Path(directory); state.chmod(0o700)
        prepared_unit = None
        report = None
        try:
            subprocess.run(parent_command(image, digest, bundle, state, parent_unit), check=True,
                           capture_output=True, timeout=10)
            report = wait_report(state / 'ready.json')
            prepared_unit = report['prepared_unit']
            fixed_control(report['main_pid'])
            network = network_state(report['network_control'], 2)
            if not (report['guest_marker_before_ready'] and report['listener_active_before_qemu']
                    and network == {'listener_active_before_qemu': True, 'controls': 2, 'unexpected': 0}):
                raise RuntimeError('Direct-QEMU network controls failed')
            result.update(real_qemu_network_namespace=True, guest_direct_tcp_denied_before_ready=True,
                          listener_active_before_qemu=True, positive_controls=2,
                          unexpected_guest_connections=0, ready_without_start=True)
        finally:
            subprocess.run(['systemctl', 'stop', parent_unit], capture_output=True, timeout=15)
            if prepared_unit:
                subprocess.run(['systemctl', 'stop', prepared_unit], capture_output=True, timeout=15)
            subprocess.run(['systemctl', 'reset-failed', parent_unit], capture_output=True, timeout=10)
            if prepared_unit:
                deadline = time.monotonic() + 12
                root = Path(report['prepared_root'])
                while show(prepared_unit, 'ActiveState') not in ('inactive', 'failed') or root.exists():
                    if time.monotonic() >= deadline:
                        raise TimeoutError('Prepared network cleanup not established')
                    time.sleep(.05)
                result['prepared_cleanup_complete'] = True
                subprocess.run(['systemctl', 'reset-failed', prepared_unit], capture_output=True, timeout=10)
    print(json.dumps(result))
    if (result.get('positive_controls') != 2 or result.get('unexpected_guest_connections') != 0
            or not result.get('prepared_cleanup_complete')):
        raise RuntimeError('Prepared network probe failed')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', required=True, type=Path)
    parser.add_argument('--image-sha256', required=True)
    parser.add_argument('--bundle', required=True, type=Path)
    parser.add_argument('--parent', action='store_true')
    parser.add_argument('--state', type=Path)
    parser.add_argument('--parent-unit')
    args = parser.parse_args()
    if args.parent:
        if not args.state or not args.parent_unit:
            parser.error('Parent state and unit required')
        parent(args.image, args.image_sha256, args.bundle, args.state, args.parent_unit)
    else:
        observer(args.image, args.image_sha256, args.bundle)


if __name__ == '__main__':
    main()
