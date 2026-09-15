"""Credential-free crash probe for the direct PreparedHost preboot path.

The parent reaches READY only.  It never sends START, obtains authority, reads
credentials, or makes a network request.  The observer SIGKILLs that parent and
reports BindsTo teardown before explicitly removing any parent-owned control
folder that SIGKILL necessarily bypasses.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
import uuid

SCRIPT_DIRECTORY = Path(__file__).resolve().parent
if str(SCRIPT_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIRECTORY))
from fresh_host_controller import PreparedHost

READY_SECONDS = 130
STOP_SECONDS = 12
PARENT_UNIT = re.compile(r'daia-controller-job-[0-9a-f]{32}\.service')


def regular(path):
    path = Path(path)
    if not path.is_absolute() or path.is_symlink() or not path.is_file():
        raise ValueError('Trusted regular file required')
    return path


def bundle_path(path):
    path = Path(path)
    if not path.is_absolute() or path.is_symlink() or not path.is_dir():
        raise ValueError('Trusted bundle directory required')
    for name in ('network-config.json', 'network-seed.iso', 'bridge.py',
                 'model-bridge.py', 'research-bridge.py'):
        regular(path / name)
    return path


def show(unit, property_name):
    return subprocess.run(['systemctl', 'show', unit, '--property=' + property_name,
                           '--value'], check=True, capture_output=True, text=True,
                          timeout=5).stdout.strip()


def unit_pids(unit):
    group = show(unit, 'ControlGroup')
    if not group or group == '/':
        raise RuntimeError('Prepared unit has no cgroup')
    root = Path('/sys/fs/cgroup') / group.lstrip('/')
    if not root.exists():
        return {}, root
    pids = {}
    for path in root.rglob('cgroup.procs'):
        for value in path.read_text().split():
            if value.isdecimal():
                stat = Path('/proc') / value / 'stat'
                if stat.exists():
                    pids[int(value)] = stat.read_text().rsplit(')', 1)[1].split()[19]
    return pids, root


def parent_terminal(unit):
    return show(unit, 'ActiveState') in ('inactive', 'failed')


def empty_cgroup(root):
    events = root / 'cgroup.events'
    return not root.exists() or ('populated 1' not in events.read_text()
                                 and not unit_process_files(root))


def unit_process_files(root):
    return any(path.read_text().strip() for path in root.rglob('cgroup.procs'))


def private_view(pid, path):
    return Path('/proc') / str(pid) / 'root' / str(path).lstrip('/')


def write_report(path, value):
    temporary = path.with_suffix('.tmp')
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(value, stream)
    os.replace(temporary, path)


def unit_stem(unit):
    if not isinstance(unit, str) or not PARENT_UNIT.fullmatch(unit):
        raise ValueError('Trusted parent unit required')
    return unit.removesuffix('.service')


def validate_report(report):
    parent_unit = report.get('parent_unit')
    unit = report.get('prepared_unit')
    root = Path(report.get('prepared_root', ''))
    marker = Path(report.get('private_marker', ''))
    if not (isinstance(unit, str) and re.fullmatch(r'daia-prepared-[0-9a-f]{32}\.service', unit)
            and root.parent == Path('/run') / unit_stem(parent_unit)
            and root.name.startswith('daia-prepared-')
            and marker.parent == root / 'work' and marker.name.startswith('crash-marker-')):
        raise ValueError('Unexpected prepared-host crash report')
    return unit, root, marker


def prepared_report(host, parent_unit, marker):
    return {'parent_unit': parent_unit, 'prepared_unit': host.unit + '.service',
            'prepared_root': str(host.root),
            'private_marker': str(host.root / 'work' / marker),
            'marker_value': 'credential-free crash marker'}


def parent(image, digest, bundle, state, parent_unit, marker):
    state = Path(state)
    host = PreparedHost(regular(image), digest, bundle_path(bundle), parent_unit)
    pid = show(host.unit, 'MainPID')
    if not pid.isdecimal() or int(pid) == 0:
        raise RuntimeError('Prepared worker has no main process')
    report = prepared_report(host, parent_unit, marker)
    visible_marker = private_view(pid, Path(report['private_marker']))
    visible_marker.write_text(report['marker_value'])
    write_report(state / 'ready.json', report)
    while True:
        time.sleep(60)


def command(script, image, digest, bundle, state, unit, marker):
    stem = unit_stem(unit)
    properties = {
        'Type': 'exec', 'RuntimeMaxSec': '150', 'TimeoutStopSec': '5',
        'KillMode': 'control-group', 'PrivateNetwork': 'yes',
        'NoNewPrivileges': 'yes', 'ProtectHome': 'yes',
        'InaccessiblePaths': '/mnt', 'ReadWritePaths': '/run',
        'RuntimeDirectory': stem, 'RuntimeDirectoryMode': '0755',
    }
    result = ['systemd-run', '--quiet', '--unit=' + unit]
    for key, value in properties.items():
        result += ['-p', key + '=' + value]
    return result + ['/usr/bin/python3', '-I', str(script), '--parent',
                     '--image', str(image), '--image-sha256', digest,
                     '--bundle', str(bundle), '--state', str(state),
                     '--parent-unit', unit, '--marker', marker]


def wait_for_report(path):
    deadline = time.monotonic() + READY_SECONDS
    while not path.exists():
        if time.monotonic() >= deadline:
            raise TimeoutError('Prepared worker did not reach READY')
        time.sleep(.05)
    return json.loads(path.read_text())


def process_gone(recorded):
    for pid, start_time in recorded.items():
        stat = Path('/proc') / str(pid) / 'stat'
        if stat.exists() and stat.read_text().rsplit(')', 1)[1].split()[19] == start_time:
            return False
    return True


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
    marker = 'crash-marker-' + uuid.uuid4().hex
    prepared_unit = prepared_root = None
    result = {'credentials_used': False, 'provider_requests': 0,
              'start_sent': False, 'authority_opened': False}
    with tempfile.TemporaryDirectory(prefix='daia-prepared-crash-', dir='/run') as directory:
        state = Path(directory)
        state.chmod(0o700)
        try:
            subprocess.run(command(Path(__file__), image, digest, bundle, state,
                                   parent_unit, marker), check=True, capture_output=True, timeout=10)
            report = wait_for_report(state / 'ready.json')
            prepared_unit, prepared_root, private_marker = validate_report(report)
            pids, cgroup = unit_pids(prepared_unit)
            qemu = []
            for pid in pids:
                comm = Path('/proc') / str(pid) / 'comm'
                if comm.exists() and comm.read_text().startswith('qemu-system'):
                    qemu.append(pid)
            main_pid = show(prepared_unit, 'MainPID')
            marker_view = private_view(main_pid, private_marker)
            result.update(prepared_unit=prepared_unit, prepared_root=str(prepared_root),
                          private_marker=str(private_marker),
                          real_qemu_running_before_kill=bool(qemu),
                          marker_in_private_tmpfs_before_kill=marker_view.read_text() == report['marker_value'])
            if not (result['real_qemu_running_before_kill']
                    and result['marker_in_private_tmpfs_before_kill']):
                raise RuntimeError('Prepared worker did not reach the credential-free crash point')
            subprocess.run(['systemctl', 'kill', '--kill-whom=main', '--signal=KILL', parent_unit],
                           check=True, capture_output=True, timeout=5)
            deadline = time.monotonic() + STOP_SECONDS
            while not (empty_cgroup(cgroup) and parent_terminal(parent_unit)):
                if time.monotonic() >= deadline:
                    raise TimeoutError('Parent stop or prepared cgroup survived SIGKILL')
                time.sleep(.05)
            result.update(parent_main_sigkilled=True, parent_terminal_after_sigkill=True,
                          binds_to_stopped_prepared_unit=True,
                          prepared_cgroup_empty=True, recorded_processes_gone=process_gone(pids),
                          private_work_empty_after_unmount=(not (prepared_root / 'work').exists()
                                                            or not any((prepared_root / 'work').iterdir())),
                          parent_root_survived_sigkill=prepared_root.exists())
            if not result['recorded_processes_gone'] or not result['private_work_empty_after_unmount']:
                raise RuntimeError('Prepared worker process or private work survived')
        finally:
            subprocess.run(['systemctl', 'stop', parent_unit], capture_output=True, timeout=15)
            if prepared_unit:
                subprocess.run(['systemctl', 'stop', prepared_unit], capture_output=True, timeout=15)
            if prepared_root and prepared_root.exists():
                result['observer_cleanup_required'] = True
                try:
                    shutil.rmtree(prepared_root)
                    result['observer_cleanup_complete'] = not prepared_root.exists()
                except OSError as exc:
                    result['observer_cleanup_complete'] = False
                    result['observer_cleanup_error'] = type(exc).__name__
                    print(json.dumps(result))
            subprocess.run(['systemctl', 'reset-failed', parent_unit], capture_output=True, timeout=10)
            if prepared_unit:
                subprocess.run(['systemctl', 'reset-failed', prepared_unit], capture_output=True, timeout=10)
    result['parent_cleanup_established'] = not result.get('parent_root_survived_sigkill', False)
    print(json.dumps(result))
    if not result.get('observer_cleanup_complete', not result.get('parent_root_survived_sigkill')):
        raise RuntimeError('Prepared control-folder cleanup failed')
    if not result['parent_cleanup_established']:
        raise RuntimeError('Parent crash left a prepared control folder; observer cleanup was required')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', required=True, type=Path)
    parser.add_argument('--image-sha256', required=True)
    parser.add_argument('--bundle', required=True, type=Path)
    parser.add_argument('--parent', action='store_true')
    parser.add_argument('--state', type=Path)
    parser.add_argument('--parent-unit')
    parser.add_argument('--marker')
    args = parser.parse_args()
    if args.parent:
        if not (args.state and args.parent_unit and args.marker):
            parser.error('Parent state, unit and marker required')
        parent(args.image, args.image_sha256, args.bundle, args.state,
               args.parent_unit, args.marker)
    else:
        observer(args.image, args.image_sha256, args.bundle)


if __name__ == '__main__':
    main()
