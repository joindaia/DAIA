"""Trusted, credential-free provisioning fixture; execute only inside the fresh VM."""
import argparse
import json
import pwd
import pathlib
import subprocess
import os
import fcntl
import shutil

P = pathlib.Path
NAMES = ['daia-controller', 'daia-runtime', 'daia-egress', 'daia-research']


def install_offline():
    """Install only the fixed package ISO supplied by the prepared-image builder."""
    assert shutil.which('qemu-system-x86_64') is None, 'Fresh host already has QEMU'
    mount = P('/media/daia-packages')
    mount.mkdir()
    subprocess.run(['mount', '-o', 'ro', '/dev/sr1', str(mount)], check=True, capture_output=True)
    try:
        packages = sorted(mount.glob('*.deb'))
        if not packages:
            raise ValueError('Offline package archive missing')
        install = subprocess.run(
            ['apt-get', '--yes', '--no-install-recommends', 'install', *map(str, packages)],
            env={**os.environ, 'DEBIAN_FRONTEND': 'noninteractive'}, capture_output=True, text=True, timeout=150)
        if install.returncode:
            print('DAIA_INSTALL_FAILURE ' + json.dumps(
                {'stderr': install.stderr[-3000:], 'stdout': install.stdout[-16000:]}), flush=True)
            raise RuntimeError('Offline guest installation failed')
        for command in (['qemu-system-x86_64', '--version'], ['qemu-img', '--version'],
                        ['genisoimage', '--version']):
            subprocess.run(command, check=True, capture_output=True)
        subprocess.run(['python3', '-m', 'venv', '/opt/daia-runtime'], check=True, capture_output=True)
        runtime = '/opt/daia-runtime/bin/python'
        subprocess.run([runtime, '-m', 'pip', 'install', '--no-index', '--require-hashes',
                        '--find-links', str(mount / 'python/wheels'), '-r',
                        str(mount / 'python/requirements.txt')], check=True, capture_output=True, timeout=90)
        subprocess.run([runtime, '-m', 'pip', 'install', '--no-index', '--no-deps',
                        str(mount / 'python/daia_coordinator-0.1.0-py3-none-any.whl')],
                       check=True, capture_output=True, timeout=30)
        subprocess.run([runtime, '-I', '-m', 'daia.cli', '--help'], check=True, capture_output=True)
        subprocess.run([runtime, '-I', '-c', 'import daia.contributor,mcp,cryptography'],
                       check=True, capture_output=True)
        shutil.copytree(mount / 'integration', '/opt/daia-probe')
        P('/opt/native').mkdir()
        for name in ('codex', 'codex-code-mode-host'):
            shutil.copyfile(mount / 'native' / name, '/opt/native/' + name)
            P('/opt/native/' + name).chmod(0o755)
        native = subprocess.run(['/opt/native/codex', '--version'],
                                env={'PATH': '/usr/bin:/bin', 'HOME': '/tmp/clean-native'},
                                check=True, capture_output=True, text=True)
        assert '0.153.4' in native.stdout
        nested = subprocess.run(
            ['qemu-system-x86_64', '-machine', 'q35,accel=kvm', '-cpu', 'host', '-m', '128',
             '-S', '-nodefaults', '-display', 'none', '-nic', 'none', '-monitor', 'stdio'],
            input='info kvm\nquit\n', capture_output=True, text=True, timeout=15)
        assert nested.returncode == 0 and 'enabled' in nested.stdout, nested.stderr
    finally:
        subprocess.run(['umount', str(mount)], capture_output=True, timeout=15)
    return {'archives_supplied': True, 'daia_offline_install_verified': True,
            'mcp_import_verified': True, 'native_codex_version_verified': True,
            'nested_qemu_kvm_enabled': True, 'fresh_qemu_verified': True,
            'python_venv_pip_verified': True}


def main(install=False):
    assert all(n not in {a.pw_name for a in pwd.getpwall()} for n in NAMES)
    assert P('/proc/1/comm').read_text().strip() == 'systemd'
    for repeat in range(2):
        subprocess.run(['systemd-sysusers', '/etc/sysusers.d/daia.conf'], check=True, capture_output=True)
        subprocess.run(['systemd-tmpfiles', '--create', '/etc/tmpfiles.d/daia.conf'],
                       check=True, capture_output=True)
        accounts = [pwd.getpwnam(n) for n in NAMES]
        assert len({a.pw_uid for a in accounts}) == 4
        assert all(a.pw_uid != 0 and a.pw_shell == '/usr/sbin/nologin' for a in accounts)
        state = P('/etc/passwd').read_bytes()
        if repeat == 0:
            before = state
        else:
            assert before == state
    for path, mode in [('/var/lib/daia-lab', 0o755), ('/var/lib/daia-lab/templates', 0o755),
                       ('/var/lib/daia-lab/runs', 0o700), ('/run/daia-lab', 0o750),
                       ('/run/daia-research', 0o750)]:
        assert P(path).stat().st_mode & 0o777 == mode
    subprocess.run(['modprobe', 'kvm_intel'], check=True, capture_output=True)
    fd = os.open('/dev/kvm', os.O_RDWR)
    try:
        api = fcntl.ioctl(fd, 0xAE00, 0)
    finally:
        os.close(fd)
    assert api == 12
    report = {'fresh_accounts': True, 'native_manifests_installed': True,
              'repeat_idempotent': True, 'directories_checked': 5,
              'nested_kvm_api': api, 'nonce': 'NONCE'}
    if install:
        report.update(install_offline())
    print('DAIA_FRESH_HOST ' + json.dumps(report), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--install-offline', action='store_true')
    main(parser.parse_args().install_offline)
