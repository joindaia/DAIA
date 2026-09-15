"""Root-only, credential-free systemd lifecycle experiment; no real worker tasks.

Creates uniquely named transient units and synthetic Unix endpoints. Demonstrates
controller crash propagation and post-stop cleanup, not VM/network isolation.
"""
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time
import uuid


def run(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def active(unit):
    return subprocess.run(['systemctl', 'is-active', '--quiet', unit]).returncode == 0


def main():
    if os.geteuid() != 0:
        raise SystemExit('Run only in the privileged disposable DAIA lab.')
    prefix = 'daia-lifecycle-' + uuid.uuid4().hex
    units = []
    with tempfile.TemporaryDirectory(prefix=prefix + '-') as directory:
        root = Path(directory)
        child = root / 'child.py'
        child.write_text('''import os,signal,socket,sys,time
signal.signal(signal.SIGTERM,signal.SIG_IGN)
if os.fork()==0:
 while True:time.sleep(1)
s=socket.socket(socket.AF_UNIX);s.bind(sys.argv[1]);s.listen()
while True:
 c,_=s.accept();c.sendall(b'lab-ready');c.close()
''')
        results = []
        try:
            for bound in (False, True):
                mode = 'bound' if bound else 'unbound'
                parent = prefix + '-' + mode + '.service'
                units.append(parent)
                run('systemd-run', '--quiet', '--unit=' + parent,
                    '-p', 'RuntimeMaxSec=60', '/usr/bin/sleep', '60')
                children = []
                for role in ('model', 'research', 'assignment', 'worker'):
                    unit = prefix + '-' + mode + '-' + role + '.service'
                    units.append(unit)
                    endpoint = root / (mode + '-' + role + '.sock')
                    artifact = root / (mode + '-' + role + '.temporary')
                    artifact.write_text('synthetic disposable state')
                    args = ['systemd-run', '--quiet', '--unit=' + unit,
                            '-p', 'RuntimeMaxSec=45', '-p', 'KillMode=control-group',
                            '-p', 'TimeoutStopSec=1', '-p', 'Restart=no',
                            '-p', 'ExecStopPost=/usr/bin/rm -f -- ' + str(endpoint) + ' ' + str(artifact)]
                    if bound:
                        args += ['-p', 'BindsTo=' + parent, '-p', 'After=' + parent]
                    run(*args, '/usr/bin/python3', str(child), str(endpoint))
                    children.append((unit, endpoint, artifact))
                for unit, endpoint, _ in children:
                    deadline = time.monotonic() + 5
                    while not endpoint.exists() and time.monotonic() < deadline:
                        time.sleep(.05)
                    with socket.socket(socket.AF_UNIX) as client:
                        client.settimeout(1); client.connect(str(endpoint))
                        assert client.recv(32) == b'lab-ready'
                    assert active(unit)
                run('systemctl', 'kill', '--kill-whom=main', '--signal=KILL', parent)
                started = time.monotonic()
                if bound:
                    while any(active(u) for u, _, _ in children) and time.monotonic() - started < 8:
                        time.sleep(.05)
                    # Inactive may precede ExecStopPost completion; require files gone too.
                    while any(e.exists() or a.exists() for _, e, a in children) and time.monotonic() - started < 8:
                        time.sleep(.05)
                    assert all(not active(u) and not e.exists() and not a.exists() for u,e,a in children)
                    unreachable = 0
                    for _, endpoint, _ in children:
                        with socket.socket(socket.AF_UNIX) as client:
                            try: client.connect(str(endpoint))
                            except OSError: unreachable += 1
                    assert unreachable == 4
                    results.append({'mode':mode,'all_endpoints_unreachable':True,'post_stop_cleanup':True,
                                    'termination_seconds':round(time.monotonic()-started,3)})
                else:
                    time.sleep(.3)
                    assert all(active(u) and e.exists() and a.exists() for u,e,a in children)
                    results.append({'mode':mode,'orphan_services_remained_active':4})
                run('systemctl','stop',*[u for u,_,_ in children])
            print(json.dumps({'synthetic_only':True,'results':results}))
        finally:
            subprocess.run(['systemctl','stop',*units],capture_output=True,timeout=30)
            subprocess.run(['systemctl','reset-failed',*units],capture_output=True)


if __name__ == '__main__':
    main()
