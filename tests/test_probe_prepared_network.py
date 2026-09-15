import importlib.util
from pathlib import Path
import sys

import pytest


scripts = Path(__file__).parents[1] / 'scripts'
sys.path.insert(0, str(scripts))
try:
    spec = importlib.util.spec_from_file_location(
        'probe_prepared_network', scripts / 'probe_prepared_network.py')
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
finally:
    sys.path.pop(0)


def test_instruments_only_the_exact_generated_prepared_launch(tmp_path):
    boot = tmp_path / 'daia-prepared-test' / 'boot.py'
    control = boot.parent / 'control'; control.mkdir(parents=True)
    boot.write_text("import subprocess\nr=subprocess.run(['qemu-system-x86_64'])\n")
    calls = []
    intercept, state = probe.instrument_prepared_launch(
        lambda argv, **kwargs: calls.append((argv, kwargs)), 'daia-prepared-test')
    argv = ['systemd-run', '--quiet', '--collect', '--unit=daia-prepared-test',
            '/usr/bin/python3', '-I', str(boot)]
    intercept(argv, check=True, timeout=10)
    code = boot.read_text()
    assert state['injected'] and calls[0][0] == argv
    assert code.index('listener_active_before_qemu') < code.index('r=subprocess.run(')
    assert "('127.0.0.1', 38443)" in code


def test_rejects_nonunique_or_wrong_prepared_boot_launch(tmp_path):
    boot = tmp_path / 'wrong' / 'boot.py'; boot.parent.mkdir()
    (boot.parent / 'control').mkdir()
    boot.write_text('r=subprocess.run(1)\nr=subprocess.run(2)\n')
    intercept, _ = probe.instrument_prepared_launch(lambda *_a, **_k: None,
                                                     'daia-prepared-test')
    with pytest.raises(RuntimeError, match='Unique QEMU'):
        intercept(['systemd-run', '--quiet', '--collect', '--unit=daia-prepared-test',
                   '/usr/bin/python3', '-I', str(boot)])


def test_parent_command_is_fixed_and_has_no_start_or_relay(tmp_path):
    unit = 'daia-controller-job-' + 'a' * 32 + '.service'
    command = probe.parent_command(Path('/trusted/image'), 'b' * 64,
                                   Path('/trusted/bundle'), tmp_path, unit)
    assert 'PrivateNetwork=yes' in command
    assert 'RuntimeDirectory=daia-controller-job-' + 'a' * 32 in command
    text = ' '.join(command)
    assert '--start' not in text and 'relay' not in text and 'authority' not in text


def test_listener_code_has_fixed_controls_only():
    code = probe.listener_code('/run/private/network.json')
    assert 'DAIA_PREPARED_NETWORK_CONTROL' in code
    assert '127.0.0.1' in code and '38443' in code
    assert 'guestfwd' not in code and '10.0.2.2' not in code


def test_interceptor_leaves_nonprepared_commands_unchanged():
    calls = []
    intercept, state = probe.instrument_prepared_launch(
        lambda argv, **kwargs: calls.append((argv, kwargs)), 'daia-prepared-test')
    command = ['systemctl', 'show', 'unrelated.service']
    intercept(command, timeout=5)
    assert calls == [(command, {'timeout': 5})] and not state['injected']
