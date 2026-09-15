"""Preboot one pinned, credential-free KVM worker before assignment authority.

Only a fixed READY/START nonce crosses the control port. Results come from
bounded untrusted serial output. No inner hypervisor or host-code fallback.
"""
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
import socket
import subprocess
import tempfile
import time
import uuid

from fresh_host_start import wait_ready, start

MAX_REPORT = 9 * 1024 * 1024


def result_bytes(path):
    with path.open('rb') as stream:
        raw = stream.read(MAX_REPORT + 1)
    if len(raw) > MAX_REPORT:
        raise ValueError('Oversized prepared result')
    report = json.loads(raw)
    if not isinstance(report, dict) or type(report.get('ok')) is not bool:
        raise ValueError('Invalid prepared result envelope')
    return raw, report['ok']


class PreparedHost:
    def __init__(self, image, digest, bundle, parent_unit):
        self.connection = None
        self.closed = False
        self.unit = 'daia-prepared-' + uuid.uuid4().hex
        if not re.fullmatch(r'daia-[a-z0-9-]+\.service', parent_unit):
            raise ValueError('Fixed DAIA parent service required')
        parent_root = Path('/run') / parent_unit.removesuffix('.service')
        if not parent_root.is_dir():
            raise ValueError('Parent systemd RuntimeDirectory required')
        self.folder = tempfile.TemporaryDirectory(prefix='daia-prepared-', dir=parent_root)
        self.root = Path(self.folder.name)
        self.root.chmod(0o755)
        try:
            self.prepare(Path(image), digest, Path(bundle), parent_unit)
        except BaseException:
            self.retain_boot_failure()
            self.close()
            raise

    def prepare(self, image, digest, bundle, parent_unit):
        with image.open('rb') as stream:
            if hashlib.file_digest(stream, 'sha256').hexdigest() != digest:
                raise ValueError('Prepared image digest mismatch')
        self.nonce = json.loads((bundle / 'network-config.json').read_bytes())['nonce']
        worker = pwd.getpwnam('daia-runtime')
        control = self.root / 'control'
        control.mkdir(mode=0o700)
        os.chown(control, worker.pw_uid, worker.pw_gid)
        self.result = control / 'result.json'
        work = self.root / 'work'
        work.mkdir(mode=0o755)
        forwards = ','.join(f'guestfwd=tcp:10.0.2.{100+i}:3128-cmd:/usr/bin/python3 -I {bundle/name}'
                           for i, name in enumerate(('bridge.py', 'model-bridge.py', 'research-bridge.py')))
        qemu = ['/usr/bin/qemu-system-x86_64', '-no-user-config', '-nodefaults',
                '-machine', 'q35', '-accel', 'kvm', '-cpu', 'host', '-m', '2048', '-smp', '2',
                '-display', 'none', '-monitor', 'none', '-no-reboot',
                '-nic', 'user,restrict=on,ipv6=off,' + forwards,
                '-drive', 'file=guest.qcow2,if=virtio,format=qcow2',
                '-drive', f'file={bundle}/network-seed.iso,media=cdrom,readonly=on',
                '-serial', 'file:serial.txt', '-device', 'virtio-serial-pci',
                '-chardev', f'socket,id=start,path={control}/start.sock,server=on,wait=off',
                '-device', 'virtserialport,chardev=start,name=daia.start']
        runner = self.root / 'boot.py'
        code = '''import json,pathlib,subprocess,os
subprocess.run(CREATE,check=True)
# Grow only the disposable virtual disk; cloud-init expands its root partition.
# Physical overlay allocation remains capped by the 1 GiB private tmpfs.
subprocess.run(['qemu-img','resize','guest.qcow2','8G'],check=True,capture_output=True)
r=subprocess.run(QEMU,timeout=265)
p=pathlib.Path('serial.txt')
with p.open('rb') as f: raw=f.read(8*1024*1024+1)
if len(raw)>8*1024*1024: raise ValueError('Oversized serial result')
rows=[json.loads(line[17:]) for line in raw.decode(errors='replace').splitlines() if line.startswith('DAIA_BOOT_RESULT ')]
valid=not r.returncode and len(rows)==1 and rows[0].get('nonce')==NONCE
report={'ok':True,'report':{'exit':0,'guest':rows[0] if valid else {},'uid_nonroot':True,'private_network':True,'network_none':False,'bundle_verified':True,'overlay_removed':True,'guest_claims_verified':False,'preboot_direct_worker':True}}
if not valid:
 text=raw.decode(errors='replace')
 errors='\\n'.join(line for line in text.splitlines() if any(word in line for word in ('DAIA_NATIVE_FAILURE','Traceback','Error')))
 report={'ok':False,'failure':'guest_failed','qemu_exit':r.returncode,'result_count':len(rows),'untrusted_diagnostics':{'native_error_excerpt':errors[-4096:],'serial_tail':text[-4096:]}}
pathlib.Path('guest.qcow2').unlink()
fd=os.open(__RESULT_PATH__+'.tmp',os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
with os.fdopen(fd,'w') as f: json.dump(report,f)
os.replace(__RESULT_PATH__+'.tmp',__RESULT_PATH__)
'''
        code = code.replace('CREATE', repr(['/usr/bin/qemu-img', 'create', '-q', '-f', 'qcow2',
            '-F', 'qcow2', '-b', str(image), 'guest.qcow2'])).replace('QEMU', repr(qemu))
        runner.write_text(code.replace('NONCE', repr(self.nonce)).replace('__RESULT_PATH__', repr(str(self.result))))
        props = {'User': 'daia-runtime', 'Group': 'daia-runtime', 'SupplementaryGroups': 'kvm',
                 'WorkingDirectory': str(work), 'NoNewPrivileges': 'yes', 'ProtectSystem': 'strict',
                 'ProtectHome': 'yes', 'InaccessiblePaths': '/mnt', 'PrivateNetwork': 'yes',
                 'PrivateTmp': 'yes', 'PrivateIPC': 'yes', 'DevicePolicy': 'closed',
                 'DeviceAllow': '/dev/kvm rw', 'CapabilityBoundingSet': '',
                 'ReadWritePaths': str(control), 'MemoryMax': '3G', 'MemorySwapMax': '0',
                 'TasksMax': '64', 'LimitFSIZE': '1100M', 'RuntimeMaxSec': '280',
                 'KillMode': 'control-group', 'TimeoutStopSec': '5',
                 'BindsTo': parent_unit, 'After': parent_unit,
                 'TemporaryFileSystem': f'{work}:size=1G,nr_inodes=4096,mode=0700,uid={worker.pw_uid},gid={worker.pw_gid}',
                 'ExecStopPost': '/usr/bin/rm -f -- ' + str(work / 'guest.qcow2')}
        command = ['systemd-run', '--quiet', '--collect', '--unit=' + self.unit]
        for k, v in props.items(): command += ['-p', k + '=' + v]
        subprocess.run(command + ['/usr/bin/python3', '-I', str(runner)], check=True,
                       capture_output=True, timeout=10)
        deadline = time.monotonic() + 120
        while not (control / 'start.sock').is_socket():
            if time.monotonic() >= deadline: raise TimeoutError('Worker control port not ready')
            time.sleep(.05)
        self.connection = socket.socket(socket.AF_UNIX)
        self.connection.settimeout(5)
        self.connection.connect(str(control / 'start.sock'))
        wait_ready(self.connection, self.nonce, seconds=max(.001, deadline-time.monotonic()))
        self.started = False

    def run(self, deadline):
        if self.started: raise ValueError('Prepared worker already started')
        self.started = True
        try:
            start(self.connection, self.nonce, deadline=deadline)
            self.connection.close()
            self.connection = None
            while not self.result.exists():
                if time.monotonic() >= deadline:
                    self.retain_boot_failure()
                    raise TimeoutError('Prepared worker result timeout')
                time.sleep(.1)
            raw, ok = result_bytes(self.result)
            return subprocess.CompletedProcess(['prepared-worker'], 0 if ok else 1, raw, b'')
        finally:
            self.close()

    def retain_boot_failure(self):
        try:
            pid = subprocess.run(['systemctl', 'show', self.unit, '--property=MainPID', '--value'],
                                 capture_output=True, text=True, timeout=5).stdout.strip()
            if not pid.isdecimal() or int(pid) == 0: return
            serial = Path('/proc') / pid / 'root' / str(self.root / 'work/serial.txt').lstrip('/')
            with serial.open('rb') as stream:
                stream.seek(0, 2); stream.seek(max(0, stream.tell() - 65536))
                tail = stream.read(65536).decode('utf-8', errors='replace')
            destination = Path('/var/lib/daia-lab') / (self.unit + '-boot-private.json')
            fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, 'w') as output: json.dump({'untrusted_boot_tail': tail}, output)
        except (OSError, subprocess.SubprocessError): pass

    def close(self):
        if self.closed: return
        if self.connection is not None:
            self.connection.close(); self.connection = None
        subprocess.run(['systemctl', 'stop', self.unit], capture_output=True, timeout=15)
        state = subprocess.run(['systemctl', 'is-active', self.unit],
                               capture_output=True, text=True, timeout=5).stdout.strip()
        if state not in ('inactive', 'failed', 'unknown'):
            raise RuntimeError('Prepared host teardown not established')
        # Remaining serial logs are private and bounded; the namespace must be gone.
        work = self.root / 'work'
        if work.exists() and any(work.iterdir()):
            raise RuntimeError('Prepared host storage survived teardown')
        self.folder.cleanup()
        if self.root.exists(): raise RuntimeError('Prepared control storage survived cleanup')
        self.closed = True
