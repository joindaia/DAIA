"""Replay the observed cloud-init prefix against the actual probe runner."""
import ast
import json
from pathlib import Path
import runpy
import subprocess
import sys
import textwrap
from types import SimpleNamespace
import pytest

ROOT = Path(__file__).parents[1]


def runner_source():
    tree = ast.parse((ROOT / 'scripts/probe_fresh_host_ram.py').read_text())
    return textwrap.dedent(next(ast.literal_eval(n.value) for n in ast.walk(tree)
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'runner' for t in n.targets)))


@pytest.mark.parametrize('case', ['prefixed', 'bare', 'duplicate', 'wrong_nonce', 'bad_prefix'])
def test_report_and_cleanup(tmp_path, monkeypatch, capsys, case):
    nonce = 'a' * 32
    marker = 'DAIA_FRESH_HOST ' + json.dumps({'nonce': nonce, 'fresh_accounts': True,
        'native_manifests_installed': True, 'repeat_idempotent': True,
        'directories_checked': 5, 'nested_kvm_api': 12})
    line = '[   14.217959] cloud-init[932]: ' + marker
    if case == 'bare': line = marker
    if case == 'duplicate': line += '\n' + line
    if case == 'bad_prefix': line = 'arbitrary ' + line
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, 'argv', ['probe', '/base', '/seed', 'b'*32 if case == 'wrong_nonce' else nonce, '-', '150', '2048', '-', '0'])
    def fake_run(argv, **kwargs):
        if argv[0] == 'qemu-img':
            Path('guest.qcow2').write_bytes(b'fixture')
        else:
            assert argv[argv.index('-nic') + 1] == 'none'
            assert argv[argv.index('-m') + 1] == '2048'
            assert argv[argv.index('-object') + 1] == 'main-loop,id=daia-loop,thread-pool-max=8'
            Path('serial.txt').write_text(line)
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(subprocess, 'run', fake_run)
    if case in ('prefixed', 'bare'):
        exec(compile(runner_source(), '<runner>', 'exec'), {})
        assert json.loads(capsys.readouterr().out)['nonce'] == nonce
    else:
        with pytest.raises(AssertionError):
            exec(compile(runner_source(), '<runner>', 'exec'), {})
    assert not Path('guest.qcow2').exists()


def test_offline_installation_report_is_checked_before_export(tmp_path, monkeypatch):
    nonce = 'a' * 32
    base = {'nonce': nonce, 'fresh_accounts': True, 'native_manifests_installed': True,
            'repeat_idempotent': True, 'directories_checked': 5, 'nested_kvm_api': 12}
    offline = {'archives_supplied': True, 'daia_offline_install_verified': True,
               'mcp_import_verified': True, 'native_codex_version_verified': True,
               'nested_qemu_kvm_enabled': True, 'fresh_qemu_verified': True,
               'python_venv_pip_verified': True}

    def execute(report, expect_export):
        converted = []
        work = tmp_path / ('good' if expect_export else 'bad'); work.mkdir()
        monkeypatch.chdir(work)
        destination = work / 'host.qcow2'
        monkeypatch.setattr(sys, 'argv', ['probe', '/base', '/seed', nonce, '/packages.iso',
                                          '240', '2048', str(destination), '1'])

        def fake_run(argv, **kwargs):
            if argv[:2] == ['qemu-img', 'create']:
                Path('guest.qcow2').write_bytes(b'overlay')
            elif argv[0] == 'qemu-system-x86_64':
                Path('serial.txt').write_text('DAIA_FRESH_HOST ' + json.dumps(report))
            elif argv[:2] == ['qemu-img', 'convert']:
                assert kwargs['timeout'] == 120
                converted.append(True); destination.write_bytes(b'image')
            return SimpleNamespace(returncode=0)

        monkeypatch.setattr(subprocess, 'run', fake_run)
        if expect_export:
            exec(compile(runner_source(), '<runner>', 'exec'), {})
            assert converted == [True] and destination.read_bytes() == b'image'
        else:
            with pytest.raises(AssertionError, match='incomplete'):
                exec(compile(runner_source(), '<runner>', 'exec'), {})
            assert converted == [] and not destination.exists()

    execute(base, False)
    execute({**base, **offline}, True)


def test_child_failure_keeps_only_bounded_output():
    probe = runpy.run_path(str(ROOT / 'scripts/probe_fresh_host_ram.py'))
    detail = probe['child_failure'](SimpleNamespace(returncode=1, stdout='a' * 5000, stderr='b' * 5000))
    assert detail == {'returncode': 1, 'child_stdout_tail': 'a' * 4096,
                      'child_stderr_tail': 'b' * 4096}


def test_qemu_failure_retains_exit_and_diagnostic(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, 'argv', ['probe', '/base', '/seed', 'a'*32,
                                     '-', '150', '2048', '-', '0'])
    def failed_qemu(argv, **kwargs):
        if argv[0] == 'qemu-img':
            Path('guest.qcow2').write_bytes(b'fixture')
            return SimpleNamespace(returncode=0)
        Path('serial.txt').write_text('DAIA_FRESH_HOST {}\n')
        return SimpleNamespace(returncode=1, stderr=b'synthetic disk write failure')
    monkeypatch.setattr(subprocess, 'run', failed_qemu)
    with pytest.raises(AssertionError):
        exec(compile(runner_source(), '<runner>', 'exec'), {})
    report = json.loads(capsys.readouterr().out)
    assert report['qemu_exit'] == 1
    assert report['qemu_stderr_tail'] == 'synthetic disk write failure'
    assert not Path('guest.qcow2').exists()
