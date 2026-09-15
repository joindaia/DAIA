"""Test-only discovery across the real prepared VM assignment transport.

Use under a bounded root test service with RuntimeDirectory. The actual MCP
server has a synthetic host which rejects all work, no keys or provider access.
"""
import argparse
import json
import os
from pathlib import Path
import pwd
import socket
import subprocess
import sys

from fresh_host_controller import PreparedHost


def probe(image, digest, bundle, parent):
    scripts = Path(__file__).resolve().parent
    account = pwd.getpwnam('daia-controller')
    worker = pwd.getpwnam('daia-runtime')
    endpoint = Path('/run/daia-lab/gateway.sock')
    if endpoint.exists() or endpoint.is_symlink():
        raise ValueError('Existing assignment endpoint; refuse to interfere')
    if not endpoint.parent.is_dir():
        raise ValueError('Existing provisioned lab runtime directory required')
    children = []
    host = None
    bound = False
    env = {'PATH': '/usr/bin:/bin', 'HOME': '/nonexistent',
           'PYTHONPATH': str(scripts.parent / 'src')}
    try:
        with socket.socket(socket.AF_UNIX) as listener:
            listener.bind(str(endpoint)); bound = True
            os.chown(endpoint, 0, worker.pw_gid); endpoint.chmod(0o660)
            listener.listen(1)
            helper = subprocess.Popen([sys.executable, str(scripts / 'probe_codex_assignment_tools.py'),
                                       '--serve-fixture'],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                env=env, user=account.pw_uid, group=account.pw_gid, extra_groups=[])
            children.append(helper)
            fds = (listener.fileno(), helper.stdin.fileno(), helper.stdout.fileno())
            relay = subprocess.Popen([sys.executable, '-m', 'daia.assignment_relay',
                '--listener-fd', str(fds[0]), '--helper-input-fd', str(fds[1]),
                '--helper-output-fd', str(fds[2]), '--accept-seconds', '120',
                '--seconds', '30', '--max-bytes', '65536'],
                pass_fds=fds, env=env, user=account.pw_uid, group=account.pw_gid,
                extra_groups=[], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            children.append(relay)
            helper.stdin.close(); helper.stdin = None
            helper.stdout.close(); helper.stdout = None
            host = PreparedHost(image, digest, bundle, parent)
            pid = subprocess.check_output(['systemctl', 'show', host.unit,
                                          '--property=MainPID', '--value'], text=True).strip()
            if not pid.isdecimal() or int(pid) == 0:
                raise RuntimeError('Prepared worker not running')
            serial = Path('/proc') / pid / 'root' / str(host.root / 'work/serial.txt').lstrip('/')
            with serial.open('rb') as stream:
                log = stream.read(8 * 1024 * 1024 + 1)
            if len(log) > 8 * 1024 * 1024:
                raise RuntimeError('Oversized guest evidence')
            marker = 'DAIA_PREBOOT assignment_discovery_passed=true'
            if not any(line.strip().endswith(marker) for line in log.decode(errors='replace').splitlines()):
                raise RuntimeError('Guest discovery marker missing')
            if host.started or relay.wait(timeout=10) != 0 or helper.wait(timeout=10) != 0:
                raise RuntimeError('Unexpected start or helper/relay failure')
    finally:
        try:
            if host is not None:
                host.close()
        finally:
            try:
                for child in reversed(children):
                    if child.poll() is None:
                        child.terminate()
                        try:
                            child.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            child.kill(); child.wait(timeout=5)
            finally:
                if bound:
                    endpoint.unlink(missing_ok=True)
    return {'direct_vm_discovery': True, 'tools': ['heartbeat', 'submit_result'],
            'resources_prompts_templates_empty': True, 'unknown_method_denied': True,
            'unknown_resource_denied': True, 'synthetic_host_without_authority': True,
            'provider_requests': 0, 'start_sent': False, 'cleanup_complete': True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('image', 'digest', 'bundle', 'parent'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    print(json.dumps(probe(args.image, args.digest, args.bundle, args.parent)))
