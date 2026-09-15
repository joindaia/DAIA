"""Credential-free fresh-host provisioning probe in a networkless RAM-backed VM.

Trusted administrator in the existing dedicated Linux lab only. Reuses the pinned
base and host KVM/QEMU; this is not a full installer or a hostile-code test.
No participant login, provider traffic, host account changes or disk overlay.
"""
import argparse
import hashlib
import json
import os
import pathlib
import pwd
import shutil
import subprocess
import tempfile
import uuid


PIN = '612b2c0cc1bc413a6cb8c38fd611794caf0f2b436c50013d8b3794db12ad7354'
P = pathlib.Path


def regular(path):
    path = P(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError('Regular probe input required')
    return path


def run_is_tmpfs(mountinfo):
    return any(line.split()[4] == '/run' and ' - tmpfs ' in line
               for line in mountinfo.splitlines())


def child_failure(result):
    return {'returncode': result.returncode, 'child_stdout_tail': result.stdout[-4096:],
            'child_stderr_tail': result.stderr[-4096:]}


def validated_child_report(result, nonce, install_offline):
    if result.returncode:
        raise RuntimeError('Fresh-host probe failed')
    raw_report = result.stdout.encode()
    if len(raw_report) > 24 * 1024:
        raise ValueError('Fresh-host guest report exceeds bound')
    return required_report(json.loads(raw_report), nonce, install_offline)


def required_report(value, nonce, install_offline):
    required = {'fresh_accounts': True, 'native_manifests_installed': True,
                'repeat_idempotent': True, 'directories_checked': 5,
                'nested_kvm_api': 12, 'nonce': nonce}
    if install_offline:
        required.update({'archives_supplied': True, 'daia_offline_install_verified': True,
                         'mcp_import_verified': True, 'native_codex_version_verified': True,
                         'nested_qemu_kvm_enabled': True, 'fresh_qemu_verified': True,
                         'python_venv_pip_verified': True})
    if not isinstance(value, dict) or any(value.get(key) != expected for key, expected in required.items()):
        raise ValueError('Fresh-host guest report incomplete')
    return {key: value[key] for key in required}


def main(base_image=None, package_iso=None, export=None, guest_script=None, install_offline=False,
         report_path=None):
    if not __debug__ or os.geteuid() != 0:
        raise SystemExit('Normal Python and trusted lab administrator required')
    repo = P(__file__).resolve().parents[1]
    sysusers = (repo / 'deploy/subscription-lab/daia-lab.sysusers.conf').read_text()
    tmpfiles = (repo / 'deploy/subscription-lab/daia-lab.tmpfiles.conf').read_text()
    guest = regular(guest_script or repo / 'scripts/fresh_host_guest.py').read_text()
    if not run_is_tmpfs(P('/proc/self/mountinfo').read_text()):
        raise ValueError('/run must be a tmpfs')
    if int(next(x.split()[1] for x in P('/proc/meminfo').read_text().splitlines()
                if x.startswith('MemAvailable:'))) <= 5 * 1024 * 1024:
        raise ValueError('Insufficient RAM for bounded fresh-host probe')
    base = regular(base_image or '/var/lib/daia-lab/templates/base.qcow2')
    with base.open('rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() != PIN:
            raise ValueError('Pinned base image required')
    package = regular(package_iso) if package_iso else None
    if bool(package) != bool(install_offline):
        raise ValueError('Offline package ISO and installation mode must agree')
    export = P(export) if export else None
    report_path = P(report_path) if report_path else None
    if report_path is not None and (report_path.exists() or not report_path.is_absolute()
                                    or report_path.parent.is_symlink()):
        raise ValueError('New absolute guest report path required')
    if export is not None:
        if export.exists() or not export.is_absolute() or export.parent.is_symlink():
            raise ValueError('New absolute prepared image path required')
        export.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
        export.touch(mode=0o600)
    worker = pwd.getpwnam('daia-runtime')
    nonce = uuid.uuid4().hex
    unit = 'daia-fresh-host-' + nonce
    values = {'qemu_timeout': 240 if install_offline else 150,
              'runtime': 270 if install_offline else 170,
              'supervisor_timeout': 280 if install_offline else 180,
              'overlay': 1024 if install_offline else 512,
              'memory': '4G' if install_offline else '3G'}
    with tempfile.TemporaryDirectory(dir='/run', prefix='daia-fresh-host-') as folder:
        root = P(folder); root.chmod(0o755)
        work = root / 'work'; work.mkdir(); work.chmod(0o755)
        command = ['python3', '/tmp/fresh.py'] + (['--install-offline'] if install_offline else [])
        cloud = {'users': [], 'package_update': False, 'package_upgrade': False,
                 'write_files': [{'path': '/etc/sysusers.d/daia.conf', 'content': sysusers},
                                 {'path': '/etc/tmpfiles.d/daia.conf', 'content': tmpfiles},
                                 {'path': '/tmp/fresh.py', 'content': guest.replace('NONCE', nonce)}],
                 'runcmd': [command],
                 'power_state': {'mode': 'poweroff', 'delay': 'now', 'timeout': 30, 'condition': True}}
        (root / 'user-data').write_text('#cloud-config\n' + json.dumps(cloud))
        (root / 'meta-data').write_text('instance-id: ' + nonce + '\n')
        (root / 'network-config').write_text(json.dumps({'version': 2, 'ethernets': {'unused': {
            'match': {'name': 'en*'}, 'dhcp4': False, 'dhcp6': False, 'optional': True}}}))
        subprocess.run(['genisoimage', '-quiet', '-output', str(root / 'seed.iso'), '-volid', 'CIDATA',
                        '-joliet', '-rock', *[str(root / x) for x in
                        ('user-data', 'meta-data', 'network-config')]], check=True, capture_output=True)
        runner = r'''
import pathlib,subprocess,json,sys,re
p=pathlib.Path('.')
subprocess.run(['qemu-img','create','-q','-f','qcow2','-F','qcow2','-b',sys.argv[1],'guest.qcow2'],check=True)
try:
 qemu=['qemu-system-x86_64','-no-user-config','-nodefaults','-machine','q35','-accel','kvm','-cpu','host','-object','main-loop,id=daia-loop,thread-pool-max=8','-m',sys.argv[6],'-smp','2','-display','none','-nic','none','-monitor','none','-no-reboot','-drive','file=guest.qcow2,if=virtio,format=qcow2','-drive','file='+sys.argv[2]+',media=cdrom,readonly=on']
 if sys.argv[4] != '-': qemu += ['-drive','file='+sys.argv[4]+',media=cdrom,readonly=on']
 qemu += ['-serial','file:serial.txt']
 r=subprocess.run(qemu,capture_output=True,timeout=int(sys.argv[5]))
 assert r.returncode==0
 with p.joinpath('serial.txt').open('rb') as stream:raw=stream.read(4*1024*1024+1)
 assert len(raw)<4*1024*1024
 rows=[json.loads(x.split('DAIA_FRESH_HOST ',1)[1]) for x in raw.decode(errors='replace').splitlines() if re.fullmatch(r'(?:\[\s*[0-9.]+\] cloud-init\[[0-9]+\]: )?DAIA_FRESH_HOST .+',x)]
 required={'fresh_accounts':True,'native_manifests_installed':True,'repeat_idempotent':True,'directories_checked':5,'nested_kvm_api':12,'nonce':sys.argv[3]}
 if sys.argv[8] == '1': required.update({'archives_supplied':True,'daia_offline_install_verified':True,'mcp_import_verified':True,'native_codex_version_verified':True,'nested_qemu_kvm_enabled':True,'fresh_qemu_verified':True,'python_venv_pip_verified':True})
 assert len(rows)==1 and all(rows[0].get(key)==value for key,value in required.items()), 'Guest provisioning report incomplete'
 if sys.argv[7] != '-': subprocess.run(['qemu-img','convert','-O','qcow2','guest.qcow2',sys.argv[7]],check=True,timeout=120)
 print(json.dumps(rows[0]),flush=True)
except BaseException as error:
 serial=p/'serial.txt';raw=b''
 if serial.exists():
  with serial.open('rb') as stream:raw=stream.read(4*1024*1024+1)
 print(json.dumps({'failed':type(error).__name__,'serial_bytes':len(raw),'serial_findings':[line for line in raw.decode(errors='replace').splitlines() if any(word in line for word in ('DAIA_FRESH','Traceback','fresh.py','AssertionError','Error:','CalledProcessError','DAIA_INSTALL_FAILURE','scripts-user'))][-12:],'qemu_exit':getattr(locals().get('r'),'returncode',None),'qemu_stderr_tail':getattr(locals().get('r'),'stderr',b'')[-2048:].decode(errors='replace')}),flush=True)
 raise
finally:p.joinpath('guest.qcow2').unlink(missing_ok=True)
'''
        (root / 'runner.py').write_text(runner)
        props = {'User': str(worker.pw_uid), 'Group': str(worker.pw_gid), 'SupplementaryGroups': 'kvm',
                 'WorkingDirectory': str(work), 'TemporaryFileSystem':
                 f'{work}:size={values["overlay"]}M,nr_inodes=4096,mode=0700,uid={worker.pw_uid},gid={worker.pw_gid}',
                 'NoNewPrivileges': 'yes', 'ProtectSystem': 'strict', 'ProtectHome': 'yes',
                 'InaccessiblePaths': '/mnt', 'PrivateNetwork': 'yes', 'PrivateTmp': 'yes',
                 'DevicePolicy': 'closed', 'DeviceAllow': '/dev/kvm rw', 'CapabilityBoundingSet': '',
                 'MemoryMax': values['memory'], 'MemorySwapMax': '0', 'TasksMax': '64',
                 'RuntimeMaxSec': str(values['runtime']), 'TimeoutStopSec': '5', 'KillMode': 'control-group'}
        if export is not None:
            props['ReadWritePaths'] = str(export)
            os.chown(export, worker.pw_uid, worker.pw_gid)
        launch = ['systemd-run', '--quiet', '--unit=' + unit, '--wait', '--pipe']
        for key, value in props.items():
            launch += ['-p', key + '=' + value]
        # Preserve the proven 2 GiB guest allocation. MemoryMax also covers the
        # RAM-backed overlay and QEMU overhead; it is not the guest RAM size.
        launch += ['/usr/bin/python3', '-I', str(root / 'runner.py'), str(base), str(root / 'seed.iso'), nonce,
                   str(package) if package else '-', str(values['qemu_timeout']), '2048',
                   str(export) if export else '-', '1' if install_offline else '0']
        try:
            result = subprocess.run(launch, capture_output=True, text=True,
                                    timeout=values['supervisor_timeout'])
            try:
                guest_report = validated_child_report(result, nonce, install_offline)
            except BaseException:
                print(json.dumps({'fresh_host_failure': child_failure(result)}), flush=True)
                raise
            if report_path is not None:
                report_path.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
                report_path.write_text(json.dumps(guest_report) + '\n')
                report_path.chmod(0o444)
            report = {'returncode': result.returncode, 'guest_report': guest_report,
                      'error_tail': result.stderr[-700:], 'provider_used': False, 'network_enabled': False,
                      'overlay_ram_limit_mib': values['overlay'],
                      'offline_installation': install_offline}
            print(json.dumps(report))
            if export is not None:
                subprocess.run(['qemu-img', 'check', str(export)], check=True, capture_output=True, timeout=40)
                os.chown(export, 0, 0); export.chmod(0o444)
        finally:
            subprocess.run(['systemctl', 'stop', unit], capture_output=True, timeout=15)
            active = subprocess.run(['systemctl', 'is-active', unit], capture_output=True, text=True).stdout.strip()
            if active in ('active', 'activating', 'deactivating'):
                raise RuntimeError('Fresh-host service survived cleanup')
            if any(work.iterdir()):
                raise RuntimeError('Fresh-host RAM overlay survived cleanup')
            subprocess.run(['systemctl', 'reset-failed', unit], capture_output=True)
            print(json.dumps({'stopped': True, 'ram_overlay_removed': True}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-image', type=P)
    parser.add_argument('--package-iso', type=P)
    parser.add_argument('--export', type=P)
    parser.add_argument('--guest-script', type=P)
    parser.add_argument('--report', type=P)
    parser.add_argument('--install-offline', action='store_true')
    args = parser.parse_args()
    main(args.base_image, args.package_iso, args.export, args.guest_script, args.install_offline, args.report)
