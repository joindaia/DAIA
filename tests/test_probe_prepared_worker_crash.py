import importlib.util
from pathlib import Path
import sys

import pytest

if sys.platform != 'linux':
    pytest.skip('Linux/KVM host acceptance tests', allow_module_level=True)


scripts = Path(__file__).parents[1] / 'scripts'
sys.path.insert(0, str(scripts))
try:
    spec = importlib.util.spec_from_file_location(
        'probe_prepared_worker_crash', scripts / 'probe_prepared_worker_crash.py')
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
finally:
    sys.path.pop(0)


def test_parent_report_normalizes_the_systemd_unit_name():
    host = type('Host', (), {'unit': 'daia-prepared-' + 'a' * 32,
                             'root': Path('/run/daia-controller-job-' + 'b' * 32 + '/daia-prepared-abc')})()
    report = probe.prepared_report(host, 'daia-controller-job-' + 'b' * 32 + '.service',
                                   'crash-marker-token')
    assert report['prepared_unit'].endswith('.service')
    assert probe.validate_report(report)[0] == report['prepared_unit']


def test_crash_report_is_bound_to_one_prepared_root():
    report = {'prepared_unit': 'daia-prepared-' + 'a' * 32 + '.service',
              'parent_unit': 'daia-controller-job-' + 'b' * 32 + '.service',
              'prepared_root': '/run/daia-controller-job-' + 'b' * 32 + '/daia-prepared-abc',
              'private_marker': '/run/daia-controller-job-' + 'b' * 32 + '/daia-prepared-abc/work/crash-marker-token'}
    unit, root, marker = probe.validate_report(report)
    assert unit == report['prepared_unit']
    assert root / 'work' == marker.parent


@pytest.mark.parametrize('report', [
    {'parent_unit': 'daia-controller-job-' + 'b' * 32 + '.service',
     'prepared_unit': 'other.service', 'prepared_root': '/run/daia-controller-job-' + 'b' * 32 + '/daia-prepared-x',
     'private_marker': '/run/daia-controller-job-' + 'b' * 32 + '/daia-prepared-x/work/crash-marker-x'},
    {'parent_unit': 'daia-controller-job-' + 'b' * 32 + '.service',
     'prepared_unit': 'daia-prepared-' + 'a' * 32 + '.service', 'prepared_root': '/tmp/x',
     'private_marker': '/tmp/x/work/crash-marker-x'},
])
def test_crash_report_rejects_untrusted_cleanup_paths(report):
    with pytest.raises(ValueError, match='Unexpected'):
        probe.validate_report(report)


def test_parent_command_has_only_fixed_crash_probe_arguments(tmp_path):
    command = probe.command(Path('/trusted/probe.py'), Path('/trusted/image.qcow2'), 'a' * 64,
                            Path('/trusted/bundle'), tmp_path, 'daia-controller-job-' + 'a' * 32 + '.service',
                            'crash-marker-token')
    assert '--parent' in command and '--marker' in command
    assert '-p' in command and 'PrivateNetwork=yes' in command
    assert 'RuntimeDirectory=daia-controller-job-' + 'a' * 32 in command
    assert 'RuntimeDirectoryMode=0755' in command
    assert '--start' not in command and 'authority' not in ' '.join(command)


def test_empty_control_group_is_rejected_before_any_cgroup_walk(monkeypatch):
    monkeypatch.setattr(probe, 'show', lambda *_: '')
    with pytest.raises(RuntimeError, match='no cgroup'):
        probe.unit_pids('daia-prepared-' + 'a' * 32 + '.service')


def test_isolated_parent_adds_only_its_own_script_directory():
    assert probe.SCRIPT_DIRECTORY == scripts.resolve()


def test_report_rejects_a_root_outside_its_parent_runtime_directory():
    report = {'parent_unit': 'daia-controller-job-' + 'b' * 32 + '.service',
              'prepared_unit': 'daia-prepared-' + 'a' * 32 + '.service',
              'prepared_root': '/run/other/daia-prepared-x',
              'private_marker': '/run/other/daia-prepared-x/work/crash-marker-x'}
    with pytest.raises(ValueError, match='Unexpected'):
        probe.validate_report(report)


@pytest.mark.parametrize(('state', 'terminal'), [('active', False), ('deactivating', False),
                                                   ('inactive', True), ('failed', True)])
def test_parent_terminal_requires_systemd_stop_completion(monkeypatch, state, terminal):
    monkeypatch.setattr(probe, 'show', lambda *_: state)
    assert probe.parent_terminal('daia-controller-job-' + 'a' * 32 + '.service') is terminal
