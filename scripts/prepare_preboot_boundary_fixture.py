"""Derive one immutable direct-PreparedHost boundary-check seed.

This trusted builder verifies the approved source fixture, writes no credentials,
and neither starts a VM nor contacts a provider.  The sole configurable path is a
host-created random canary under /run; guest code can only attempt to open it.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

import prepare_preboot_fixture as preboot

CANARY = re.compile(r'/run/daia-boundary-canary-[0-9a-f]{32}')
READY = "print('DAIA_PREBOOT native_ready', flush=True)"


def canary_path(path):
    path = preboot.regular(path)
    if not CANARY.fullmatch(str(path)):
        raise ValueError('One random /run boundary canary required')
    return path


def boundary_check(canary):
    return """import os, errno
from pathlib import Path
_boundary_canary = {canary!r}
_boundary_link = '/tmp/daia-boundary-canary-link'
def _must_not_open(path):
    try:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, 'O_CLOEXEC', 0))
    except OSError as error:
        if error.errno not in (errno.ENOENT, errno.EACCES, errno.EPERM):
            raise
        return
    os.close(descriptor)
    raise RuntimeError('DAIA_PREBOOT forbidden host path accessible')
_must_not_open(_boundary_canary)
try:
    os.unlink(_boundary_link)
except FileNotFoundError:
    pass
os.symlink(_boundary_canary, _boundary_link)
try:
    _must_not_open(_boundary_link)
finally:
    os.unlink(_boundary_link)
if os.environ.get('SSH_AUTH_SOCK') or any(os.path.exists(path) for path in
        ('/run/docker.sock', '/var/run/docker.sock')):
    raise RuntimeError('DAIA_PREBOOT forbidden host socket exposed')
_must_not_open('/var/lib/daia-provider/codex/auth.json')
_mounts = Path('/proc/self/mountinfo').read_text().splitlines()
if any(line.split()[4] in ('/mnt/c', '/home')
       for line in _mounts if ' - ' in line):
    raise RuntimeError('DAIA_PREBOOT host mount exposed')
print('DAIA_PREBOOT boundary_host_file_denied=true boundary_mounts_denied=true '
      'boundary_sockets_denied=true boundary_auth_open_denied=true', flush=True)
""".format(canary=str(canary))



def assignment_discovery():
    # Fixed test-only peer: the actual assignment server with no work authority.
    return """import socket, json
with socket.create_connection(('10.0.2.100', 3128), timeout=5) as _connection:
    _connection.settimeout(5)
    _stream = _connection.makefile('rwb', buffering=0)
    def _rpc(number, method, params):
        _stream.write((json.dumps({'jsonrpc':'2.0','id':number,'method':method,
                                  'params':params})+'\\n').encode())
        _line = _stream.readline(65537)
        if len(_line) > 65536 or not _line.endswith(b'\\n'):
            raise RuntimeError('Unbounded discovery response')
        _reply = json.loads(_line)
        if _reply.get('id') != number:
            raise RuntimeError('Discovery response mismatch')
        return _reply
    assert 'result' in _rpc(1, 'initialize', {'protocolVersion':'2025-03-26',
        'capabilities':{}, 'clientInfo':{'name':'daia-boundary','version':'1'}})
    _stream.write(b'{"jsonrpc":"2.0","method":"notifications/initialized"}\\n')
    assert {tool['name'] for tool in _rpc(2,'tools/list',{})['result']['tools']} == {'heartbeat','submit_result'}
    assert _rpc(3,'resources/list',{})['result']['resources'] == []
    assert _rpc(4,'resources/templates/list',{})['result']['resourceTemplates'] == []
    assert _rpc(5,'prompts/list',{})['result']['prompts'] == []
    assert _rpc(6,'resources/read',{'uri':'file:///state/helper.json'})['error']['code'] == -32602
    assert _rpc(7,'daia/unknown',{})['error']['code'] == -32601
    _stream.close()
print('DAIA_PREBOOT assignment_discovery_passed=true', flush=True)
"""

def inject(data, canary, network_canary=False, discover_assignment=False):
    entries = [entry for entry in data['write_files']
               if isinstance(entry, dict) and entry.get('path') == preboot.PROBE_PATH]
    if len(entries) != 1 or not isinstance(entries[0].get('content'), str):
        raise ValueError('Unique approved probe required')
    code = entries[0]['content']
    if code.count(READY) != 1:
        raise ValueError('Unique preboot readiness marker required')
    network = """import socket
try:
    _probe = socket.create_connection(('10.0.2.2', 38443), timeout=3)
except (TimeoutError, ConnectionRefusedError):
    pass
except OSError as error:
    if error.errno not in (errno.ENETUNREACH, errno.EHOSTUNREACH, errno.EACCES):
        raise
else:
    with _probe:
        _probe.sendall(b'daia-guest-network-probe')
    raise RuntimeError('DAIA_PREBOOT direct host TCP accessible')
print('DAIA_PREBOOT boundary_direct_tcp_denied=true', flush=True)
""" if network_canary else ''
    entries[0]['content'] = code.replace(READY, boundary_check(canary) + network +
        (assignment_discovery() if discover_assignment else "") + READY)
    compile(entries[0]['content'], 'preboot-boundary-probe', 'exec')


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def prepare(source, native, output, iso_builder, isoinfo, canary, network_canary=False, discover_assignment=False):
    canary = canary_path(canary)
    config, data, siblings = preboot.cloud_data(source, isoinfo)
    inputs = preboot.native_inputs(native, config)
    inject(data, canary, network_canary, discover_assignment)
    output = Path(output)
    if output.exists():
        raise ValueError('New output directory required')
    output.mkdir(mode=0o700)
    try:
        (output / 'user-data').write_text('#cloud-config\n' + json.dumps(data))
        for name in ('meta-data', 'network-config'):
            (output / name).write_bytes(siblings[name])
        for name in ('probe.py', 'task.json'):
            path = Path(source) / name
            if path.exists():
                shutil.copyfile(preboot.regular(path), output / name)
        subprocess.run([str(iso_builder), '-quiet', '-output', str(output / 'seed.iso'),
                        '-volid', 'CIDATA', '-joliet', '-rock',
                        *[str(output / name) for name in ('user-data', 'meta-data', 'network-config')],
                        *[str(path) for path in inputs]], check=True, timeout=30)
        (output / 'seed.iso').chmod(0o444)
        result = dict(config)
        result['seed_sha256'] = digest(output / 'seed.iso')
        (output / 'config.json').write_text(json.dumps(result))
        return result
    except BaseException:
        shutil.rmtree(output)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'native', 'output', 'iso-builder', 'isoinfo', 'canary'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--network-canary', action='store_true')
    parser.add_argument('--assignment-discovery', action='store_true')
    args = parser.parse_args()
    print(json.dumps(prepare(args.source, args.native, args.output, args.iso_builder,
                             args.isoinfo, args.canary, args.network_canary, args.assignment_discovery)))


if __name__ == '__main__':
    main()
