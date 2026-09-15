"""Build one credential-free PreparedHost image from reviewed local inputs.

This builder never fetches, logs in, contacts a provider, or starts participation.
It performs the bounded, networkless fresh-host installation only when invoked by a
trusted lab administrator with KVM; unit tests validate construction without a boot.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import shutil
import subprocess
import sys
import tarfile
import tempfile
import uuid


NATIVE_PINS = {
    'codex': '56ef98ab4032d317ab26e9b5e5a175650717351edb16ed9cde0cb6d1734d62da',
    'codex-code-mode-host': '3e85d67471825f73d02ff5f7e047ca1f6ca8caa3f59e4c6e8d9ca6ca7302cb45',
}
INTEGRATION = ('fresh_host_channel.py', 'model_channel_bridge.py', 'run_kvm_lab_guest.py',
               'run_kvm_lab_report.py')


def regular(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError('Regular input required')
    return path


def digest(path):
    with regular(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def reviewed_source(path):
    root = Path(path)
    if root.is_symlink() or not root.is_dir():
        raise ValueError('Reviewed checkout directory required')
    prepared = json.loads(regular(root / 'prepared.json').read_text())
    revision = prepared.get('revision')
    lock = prepared.get('lock_sha256')
    if not isinstance(revision, str) or not re.fullmatch('[0-9a-f]{40}', revision):
        raise ValueError('Exact reviewed revision required')
    if not isinstance(lock, str) or not re.fullmatch('[0-9a-f]{64}', lock):
        raise ValueError('Reviewed lock digest required')
    actual = subprocess.check_output(['git', '-C', str(root / 'source'), 'rev-parse', 'HEAD'],
                                     text=True, timeout=10).strip()
    if actual != revision or digest(root / 'source/uv.lock') != lock:
        raise ValueError('Reviewed checkout binding mismatch')
    clean = subprocess.check_output(['git', '-C', str(root / 'source'), 'status', '--porcelain'],
                                    text=True, timeout=10)
    if clean:
        raise ValueError('Reviewed checkout must be clean')
    source = root / 'source'
    for relative in ('scripts/verify_lab_base_image.py', 'scripts/probe_fresh_host_ram.py',
                     'scripts/fresh_host_guest.py', 'deploy/subscription-lab/daia-lab.sysusers.conf',
                     'deploy/subscription-lab/daia-lab.tmpfiles.conf',
                     *('scripts/' + name for name in INTEGRATION)):
        regular(source / relative)
    return source, revision, lock


def snapshot_source(source, revision, destination):
    files = ('scripts/verify_lab_base_image.py', 'scripts/probe_fresh_host_ram.py',
             'scripts/fresh_host_guest.py', 'deploy/subscription-lab/daia-lab.sysusers.conf',
             'deploy/subscription-lab/daia-lab.tmpfiles.conf',
             *('scripts/' + name for name in INTEGRATION))
    hashes = {}
    for relative in files:
        origin = regular(source / relative)
        expected = subprocess.check_output(['git', '-C', str(source), 'show',
                                            revision + ':' + relative], timeout=10)
        if origin.read_bytes() != expected:
            raise ValueError('Reviewed source changed during snapshot')
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(expected)
        hashes[relative] = digest(target)
    return hashes


def package_inputs(manifest_path, archives):
    manifest_path = regular(manifest_path)
    archives = Path(archives)
    if archives.is_symlink() or not archives.is_dir():
        raise ValueError('Package archive directory required')
    document = json.loads(manifest_path.read_text())
    packages = document.get('packages') if isinstance(document, dict) else None
    if not isinstance(packages, list) or not packages:
        raise ValueError('Nonempty package manifest required')
    expected = {}
    for item in packages:
        if not isinstance(item, dict) or set(item) != {'url', 'filename', 'bytes', 'sha256'}:
            raise ValueError('Exact package manifest entry required')
        name, size, value = item['filename'], item['bytes'], item['sha256']
        if (not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._+%~-]*\.deb', name)
                or type(size) is not int or size <= 0 or not isinstance(value, str)
                or not re.fullmatch('[0-9a-f]{64}', value) or name in expected):
            raise ValueError('Invalid package manifest entry')
        expected[name] = (size, value)
    found = {path.name: path for path in archives.glob('*.deb')}
    if set(found) != set(expected):
        raise ValueError('Package archive set mismatch')
    for name, path in found.items():
        size, value = expected[name]
        if path.is_symlink() or not path.is_file() or path.stat().st_size != size or digest(path) != value:
            raise ValueError('Package archive digest mismatch')
    return archives, digest(manifest_path), len(found)


def stage_python(bundle, expected_digest, stage):
    bundle = regular(bundle)
    if not isinstance(expected_digest, str) or not re.fullmatch('[0-9a-f]{64}', expected_digest):
        raise ValueError('Approved Python bundle digest required')
    if digest(bundle) != expected_digest:
        raise ValueError('Python bundle digest mismatch')
    with tarfile.open(bundle) as archive:
        archive.extractall(stage, filter='data')
    python = stage / 'python'
    manifest = json.loads(regular(python / 'manifest.json').read_text())
    wheels = python / 'wheels'
    if (not wheels.is_dir() or wheels.is_symlink()
            or not regular(python / 'requirements.txt').is_file()
            or not regular(python / 'daia_coordinator-0.1.0-py3-none-any.whl').is_file()):
        raise ValueError('Complete Python bundle required')
    payloads = [python / 'requirements.txt', python / 'daia_coordinator-0.1.0-py3-none-any.whl']
    payloads.extend(sorted(wheels.iterdir()))
    if (not payloads[2:] or any(path.is_symlink() or not path.is_file() or path.suffix != '.whl'
                                for path in payloads[2:])):
        raise ValueError('Regular wheel files required')
    expected = {str(path.relative_to(stage)): path for path in payloads}
    all_files = []
    for path in python.rglob('*'):
        if path.is_symlink():
            raise ValueError('Python bundle links refused')
        if path.is_file() and path.name != 'manifest.json':
            all_files.append(str(path.relative_to(stage)))
    if (not isinstance(manifest, dict) or set(manifest) != set(expected)
            or set(all_files) != set(expected)):
        raise ValueError('Python bundle manifest coverage mismatch')
    for name, path in expected.items():
        value = manifest[name]
        if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value) or digest(path) != value:
            raise ValueError('Python bundle manifest mismatch')
    return expected_digest


def stage_native(native, stage):
    native = Path(native)
    if native.is_symlink() or not native.is_dir():
        raise ValueError('Native directory required')
    destination = stage / 'native'
    destination.mkdir()
    for name, value in NATIVE_PINS.items():
        source = regular(native / name)
        if digest(source) != value:
            raise ValueError('Native binary pin mismatch')
        shutil.copyfile(source, destination / name)
        (destination / name).chmod(0o755)


def stage_integration(source, stage):
    destination = stage / 'integration'
    destination.mkdir()
    for name in INTEGRATION:
        shutil.copyfile(regular(source / 'scripts' / name), destination / name)


def private_failure(output, error, probe_result=None):
    diagnostic = {'error': type(error).__name__, 'message': str(error)}
    if probe_result is not None:
        diagnostic.update(probe_returncode=probe_result.returncode,
                          probe_stdout_tail=probe_result.stdout[-24 * 1024:],
                          probe_stderr_tail=probe_result.stderr[-4096:])
    path = Path(output).parent / ('.daia-prepared-host-failure-' + uuid.uuid4().hex + '.json')
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'w') as stream:
        json.dump(diagnostic, stream)
    return path


def prepare(args):
    output = Path(args.output)
    if not output.is_absolute() or output.exists():
        raise ValueError('New absolute output directory required')
    staging_root = Path(args.staging_root)
    if (staging_root.is_symlink() or not staging_root.is_dir()
            or staging_root.stat().st_mode & 0o022 or not staging_root.stat().st_mode & 0o001):
        raise ValueError('Traversable non-writable staging root required')
    source, revision, lock = reviewed_source(args.reviewed)
    archives, package_manifest, package_count = package_inputs(args.package_manifest, args.package_archives)
    output.mkdir(mode=0o700)
    probe_result = None
    try:
        with tempfile.TemporaryDirectory(prefix='daia-prepared-host-', dir=staging_root) as folder:
            folder = Path(folder)
            folder.chmod(0o755)  # Contains only verified packages and transient guest storage.
            snapshot = folder / 'source'
            snapshot_hashes = snapshot_source(source, revision, snapshot)
            verifier = runpy.run_path(str(snapshot / 'scripts/verify_lab_base_image.py'))['verify']
            base_report = verifier(args.base_image, args.checksums, args.signature)
            stage = folder / 'stage'
            stage.mkdir(mode=0o755)
            python_digest = stage_python(args.python_bundle, args.python_bundle_sha256, stage)
            stage_native(args.native, stage)
            stage_integration(snapshot, stage)
            package_iso = folder / 'packages.iso'
            subprocess.run([str(args.iso_builder), '-quiet', '-output', str(package_iso),
                            '-volid', 'DAIA_PACKAGES', '-joliet', '-rock', str(archives), str(stage)],
                           check=True, capture_output=True, timeout=30)
            package_iso.chmod(0o444)
            staged_image = folder / 'host.qcow2'
            staged_report = folder / 'installation-report.json'
            command = [str(args.python), '-I', str(snapshot / 'scripts/probe_fresh_host_ram.py'),
                       '--base-image', str(args.base_image), '--package-iso', str(package_iso),
                       '--export', str(staged_image), '--report', str(staged_report),
                       '--guest-script', str(snapshot / 'scripts/fresh_host_guest.py'), '--install-offline']
            result = subprocess.run(command, capture_output=True, text=True, timeout=300)
            probe_result = result
            if result.returncode or not staged_image.is_file() or not staged_report.is_file():
                raise RuntimeError('Fresh-host preparation failed')
            report_bytes = staged_report.read_bytes()
            if len(report_bytes) > 8192:
                raise RuntimeError('Prepared guest installation report exceeds bound')
            installation = json.loads(report_bytes)
            required = {'archives_supplied': True, 'daia_offline_install_verified': True,
                        'mcp_import_verified': True, 'native_codex_version_verified': True,
                        'nested_qemu_kvm_enabled': True, 'fresh_qemu_verified': True,
                        'python_venv_pip_verified': True, 'nested_kvm_api': 12,
                        'directories_checked': 5}
            if any(installation.get(key) != value for key, value in required.items()):
                raise RuntimeError('Prepared guest installation report incomplete')
            image = output / 'host.qcow2'
            shutil.copyfile(staged_image, image)
            shutil.copyfile(staged_report, output / 'installation-report.json')
        image_digest = digest(image)
        image.chmod(0o444)
        report = {'revision': revision, 'lock_sha256': lock, 'base': base_report,
                  'package_manifest_sha256': package_manifest, 'packages_verified': package_count,
                  'python_bundle_sha256': python_digest, 'source_snapshot_sha256': snapshot_hashes,
                  'installation_report': 'installation-report.json', 'prepared_image': image.name,
                  'prepared_sha256': image_digest, 'prepared_bytes': image.stat().st_size,
                  'provider_called': False, 'credentials_copied': False, 'guest_booted': True}
        (output / 'prepared-host-image.json').write_text(json.dumps(report, indent=2) + '\n')
        # The completed image and report are credential-free and must be traversable by daia-runtime.
        output.chmod(0o755)
        return report
    except BaseException as error:
        try:
            private_failure(output, error, probe_result)
        finally:
            shutil.rmtree(output)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('reviewed', 'base-image', 'checksums', 'signature', 'package-manifest',
                 'package-archives', 'python-bundle', 'native', 'iso-builder', 'staging-root', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--python', type=Path, default=Path(sys.executable))
    parser.add_argument('--python-bundle-sha256', required=True)
    print(json.dumps(prepare(parser.parse_args())))


if __name__ == '__main__':
    main()
