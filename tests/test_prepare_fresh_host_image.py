import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import tarfile
from types import SimpleNamespace

import sys

import pytest

if sys.platform != 'linux':
    pytest.skip('Linux/KVM host acceptance tests', allow_module_level=True)

ROOT = Path(__file__).parents[1]
scope = runpy.run_path(str(ROOT / 'scripts/prepare_fresh_host_image.py'))
probe_scope = runpy.run_path(str(ROOT / 'scripts/probe_fresh_host_ram.py'))


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def reviewed(tmp_path):
    root = tmp_path / 'reviewed'
    source = root / 'source'
    source.mkdir(parents=True)
    for relative in ('scripts/verify_lab_base_image.py', 'scripts/probe_fresh_host_ram.py',
                     'scripts/fresh_host_guest.py', 'scripts/fresh_host_channel.py',
                     'deploy/subscription-lab/daia-lab.sysusers.conf',
                     'deploy/subscription-lab/daia-lab.tmpfiles.conf',
                     'scripts/model_channel_bridge.py', 'scripts/run_kvm_lab_guest.py',
                     'scripts/run_kvm_lab_report.py'):
        target = source / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / relative).read_bytes())
    (source / 'uv.lock').write_text('locked\n')
    for command in (['git', 'init', '-q'], ['git', 'config', 'user.email', 'test@example.invalid'],
                    ['git', 'config', 'user.name', 'Test'], ['git', 'add', '.'],
                    ['git', 'commit', '-qm', 'reviewed']):
        subprocess.run(command, cwd=source, check=True)
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip()
    root.mkdir(exist_ok=True)
    (root / 'prepared.json').write_text(json.dumps({
        'revision': revision, 'lock_sha256': hashlib.sha256((source / 'uv.lock').read_bytes()).hexdigest()}))
    return root


def package_inputs(tmp_path):
    archives = tmp_path / 'archives'; archives.mkdir()
    package = write(archives / 'qemu.deb', b'approved package')
    manifest = tmp_path / 'packages.json'
    manifest.write_text(json.dumps({'packages': [{'url': 'https://example.invalid/qemu.deb',
        'filename': package.name, 'bytes': package.stat().st_size,
        'sha256': hashlib.sha256(package.read_bytes()).hexdigest()}]}))
    return manifest, archives


def python_bundle(tmp_path):
    files = {'python/requirements.txt': b'', 'python/daia_coordinator-0.1.0-py3-none-any.whl': b'wheel',
             'python/wheels/mcp.whl': b'mcp'}
    manifest = {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}
    bundle = tmp_path / 'python.tgz'
    staging = tmp_path / 'python-stage'
    for name, data in files.items():
        write(staging / name, data)
    write(staging / 'python/manifest.json', json.dumps(manifest).encode())
    with tarfile.open(bundle, 'w:gz') as archive:
        archive.add(staging / 'python', arcname='python')
    return bundle


def test_reviewed_checkout_rejects_untracked_file(tmp_path):
    root = reviewed(tmp_path)
    (root / 'source/unreviewed').write_text('no')
    with pytest.raises(ValueError, match='clean'):
        scope['reviewed_source'](root)


def test_package_set_requires_exact_manifest(tmp_path):
    manifest, archives = package_inputs(tmp_path)
    assert scope['package_inputs'](manifest, archives)[2] == 1
    write(archives / 'extra.deb', b'extra')
    with pytest.raises(ValueError, match='set mismatch'):
        scope['package_inputs'](manifest, archives)


def test_builder_uses_only_local_reviewed_inputs(tmp_path, monkeypatch):
    source = reviewed(tmp_path)
    manifest, archives = package_inputs(tmp_path)
    bundle = python_bundle(tmp_path)
    native = tmp_path / 'native'; native.mkdir()
    pins = {name: hashlib.sha256(name.encode()).hexdigest() for name in ('codex', 'codex-code-mode-host')}
    for name in pins:
        write(native / name, name.encode())
    monkeypatch.setitem(scope['stage_native'].__globals__, 'NATIVE_PINS', pins)
    base = write(tmp_path / 'base', b'base')
    checksums, signature = write(tmp_path / 'checksums', b'x'), write(tmp_path / 'signature', b'x')
    iso = write(tmp_path / 'genisoimage', b'placeholder')
    output = tmp_path / 'output'
    staging = tmp_path / 'staging'; staging.mkdir(mode=0o755)
    original_run = scope['subprocess'].run

    def fake_run(argv, **kwargs):
        if argv[0] == str(iso):
            Path(argv[argv.index('-output') + 1]).write_bytes(b'iso')
            return SimpleNamespace(returncode=0)
        if argv[0] == str(Path('/usr/bin/python3')) and 'probe_fresh_host_ram.py' in argv[2]:
            Path(argv[argv.index('--export') + 1]).write_bytes(b'prepared image')
            Path(argv[argv.index('--report') + 1]).write_text(json.dumps({
                'archives_supplied': True, 'daia_offline_install_verified': True,
                'mcp_import_verified': True, 'native_codex_version_verified': True,
                'nested_qemu_kvm_enabled': True, 'fresh_qemu_verified': True,
                'python_venv_pip_verified': True, 'nested_kvm_api': 12,
                'directories_checked': 5}))
            return SimpleNamespace(returncode=0, stdout='local probe', stderr='')
        return original_run(argv, **kwargs)

    monkeypatch.setattr(scope['runpy'], 'run_path', lambda _: {'verify': lambda *_: {'signature_verified': True}})
    monkeypatch.setattr(scope['subprocess'], 'run', fake_run)
    report = scope['prepare'](SimpleNamespace(reviewed=source, base_image=base, checksums=checksums,
        signature=signature, package_manifest=manifest, package_archives=archives, python_bundle=bundle,
        native=native, iso_builder=iso, output=output, staging_root=staging,
        python_bundle_sha256=hashlib.sha256(bundle.read_bytes()).hexdigest(), python=Path('/usr/bin/python3')))
    assert report['packages_verified'] == 1
    assert report['provider_called'] is False and report['credentials_copied'] is False
    assert (output / 'host.qcow2').stat().st_mode & 0o777 == 0o444
    assert output.stat().st_mode & 0o777 == 0o755
    assert json.loads((output / 'prepared-host-image.json').read_text()) == report
    assert json.loads((output / 'installation-report.json').read_text())['nested_kvm_api'] == 12


def test_probe_default_has_no_package_drive():
    source = (ROOT / 'scripts/probe_fresh_host_ram.py').read_text()
    assert "if sys.argv[4] != '-': qemu += ['-drive'" in source
    assert "['--install-offline'] if install_offline else []" in source


def test_run_tmpfs_detection_requires_a_tmpfs_mount():
    assert probe_scope['run_is_tmpfs']('35 1 0:32 / /run rw - tmpfs tmpfs rw\n')
    assert not probe_scope['run_is_tmpfs']('35 1 8:1 /run /run rw - ext4 /dev/sda rw\n')


def test_python_bundle_requires_approved_digest_and_complete_manifest(tmp_path):
    bundle = python_bundle(tmp_path)
    stage = tmp_path / 'stage'; stage.mkdir()
    with pytest.raises(ValueError, match='digest'):
        scope['stage_python'](bundle, '0' * 64, stage)
    stage.mkdir(exist_ok=True)
    tampered = tmp_path / 'tampered.tgz'
    shutil = __import__('shutil')
    unpacked = tmp_path / 'unpacked'
    with tarfile.open(bundle) as archive:
        archive.extractall(unpacked, filter='data')
    write(unpacked / 'python/unlisted.txt', b'no')
    with tarfile.open(tampered, 'w:gz') as archive:
        archive.add(unpacked / 'python', arcname='python')
    tampered_digest = hashlib.sha256(tampered.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match='coverage'):
        scope['stage_python'](tampered, tampered_digest, stage)


def test_offline_guest_report_requires_every_installation_field():
    nonce = 'a' * 32
    complete = {'nonce': nonce, 'fresh_accounts': True, 'native_manifests_installed': True,
                'repeat_idempotent': True, 'directories_checked': 5, 'nested_kvm_api': 12,
                'archives_supplied': True, 'daia_offline_install_verified': True,
                'mcp_import_verified': True, 'native_codex_version_verified': True,
                'nested_qemu_kvm_enabled': True, 'fresh_qemu_verified': True,
                'python_venv_pip_verified': True}
    assert probe_scope['required_report'](complete, nonce, True)['archives_supplied'] is True
    incomplete = dict(complete); incomplete['mcp_import_verified'] = False
    with pytest.raises(ValueError, match='incomplete'):
        probe_scope['required_report'](incomplete, nonce, True)


def test_failed_probe_diagnostic_is_private_and_bounded(tmp_path):
    output = tmp_path / 'private-output'
    result = SimpleNamespace(returncode=1, stdout='a' * 5000, stderr='b' * 5000)
    diagnostic = scope['private_failure'](output, RuntimeError('Fresh-host preparation failed'), result)
    assert diagnostic.parent == tmp_path and diagnostic.name.startswith('.daia-prepared-host-failure-')
    assert diagnostic.stat().st_mode & 0o777 == 0o600
    data = json.loads(diagnostic.read_text())
    assert data['probe_returncode'] == 1
    assert data['probe_stdout_tail'] == 'a' * 5000
    assert data['probe_stderr_tail'] == 'b' * 4096


def test_builder_failure_keeps_private_probe_diagnostic(tmp_path, monkeypatch):
    source = reviewed(tmp_path)
    manifest, archives = package_inputs(tmp_path)
    bundle = python_bundle(tmp_path)
    native = tmp_path / 'native'; native.mkdir()
    pins = {name: hashlib.sha256(name.encode()).hexdigest() for name in ('codex', 'codex-code-mode-host')}
    for name in pins:
        write(native / name, name.encode())
    monkeypatch.setitem(scope['stage_native'].__globals__, 'NATIVE_PINS', pins)
    base = write(tmp_path / 'base', b'base')
    checksums, signature = write(tmp_path / 'checksums', b'x'), write(tmp_path / 'signature', b'x')
    iso = write(tmp_path / 'genisoimage', b'placeholder')
    output = tmp_path / 'output'; staging = tmp_path / 'staging'; staging.mkdir(mode=0o755)
    original_run = scope['subprocess'].run

    def fake_run(argv, **kwargs):
        if argv[0] == str(iso):
            Path(argv[argv.index('-output') + 1]).write_bytes(b'iso')
            return SimpleNamespace(returncode=0)
        if argv[0] == str(Path('/usr/bin/python3')) and 'probe_fresh_host_ram.py' in argv[2]:
            return SimpleNamespace(returncode=1, stdout='guest failure', stderr='probe failure')
        return original_run(argv, **kwargs)

    monkeypatch.setattr(scope['runpy'], 'run_path', lambda _: {'verify': lambda *_: {'signature_verified': True}})
    monkeypatch.setattr(scope['subprocess'], 'run', fake_run)
    args = SimpleNamespace(reviewed=source, base_image=base, checksums=checksums, signature=signature,
        package_manifest=manifest, package_archives=archives, python_bundle=bundle, native=native,
        iso_builder=iso, output=output, staging_root=staging,
        python_bundle_sha256=hashlib.sha256(bundle.read_bytes()).hexdigest(), python=Path('/usr/bin/python3'))
    with pytest.raises(RuntimeError, match='preparation failed'):
        scope['prepare'](args)
    assert not output.exists()
    diagnostics = list(tmp_path.glob('.daia-prepared-host-failure-*.json'))
    assert len(diagnostics) == 1
    assert json.loads(diagnostics[0].read_text())['probe_stdout_tail'] == 'guest failure'


def test_zero_exit_invalid_child_report_is_rejected_with_retained_output():
    result = SimpleNamespace(returncode=0, stdout='not-json', stderr='child stderr')
    with pytest.raises(json.JSONDecodeError):
        probe_scope['validated_child_report'](result, 'a' * 32, True)
    detail = probe_scope['child_failure'](result)
    assert detail['child_stdout_tail'] == 'not-json'
    assert detail['child_stderr_tail'] == 'child stderr'


def test_private_diagnostic_retains_complete_inner_failure_envelope(tmp_path):
    inner = json.dumps({'fresh_host_failure': {'child_stdout_tail': 'CAUSE:' + 'a' * 4090,
                                                'child_stderr_tail': 'b' * 4096}})
    result = SimpleNamespace(returncode=1, stdout=inner, stderr='outer stderr')
    diagnostic = scope['private_failure'](tmp_path / 'output', RuntimeError('failed'), result)
    data = json.loads(diagnostic.read_text())
    assert data['probe_stdout_tail'] == inner
    assert 'CAUSE:' in data['probe_stdout_tail']
    assert data['probe_stderr_tail'] == 'outer stderr'
