import os
from pathlib import Path
import subprocess
import sys

import pytest

from daia.isolation import sandbox_command

pytestmark = pytest.mark.skipif(
    sys.platform != 'linux' or not Path('/usr/bin/bwrap').is_file(),
    reason='Linux bubblewrap required',
)


def test_snapshot_rejects_checkout_and_symlink(tmp_path):
    snapshot = tmp_path / 'input'
    snapshot.mkdir()
    (snapshot / '.git').mkdir()
    with pytest.raises(ValueError):
        sandbox_command(snapshot, ['/bin/true'])
    (snapshot / '.git').rmdir()
    (snapshot / 'escape').symlink_to('/etc/passwd')
    with pytest.raises(ValueError):
        sandbox_command(snapshot, ['/bin/true'])


@pytest.mark.skipif(os.environ.get('DAIA_RUN_ISOLATION_TESTS') != '1',
                    reason='Explicit real namespace integration test')
def test_real_process_cannot_reach_host_data_or_network(tmp_path):
    snapshot = tmp_path / 'input'
    snapshot.mkdir()
    (snapshot / 'source.txt').write_text('approved input')
    canary = tmp_path / 'operator-canary'
    canary.write_text('synthetic secret')
    program = '''import os,socket,pathlib
assert not pathlib.Path(CANARY).exists()
assert not pathlib.Path('/mnt/c').exists()
assert not pathlib.Path('/run/docker.sock').exists()
assert 'SYNTHETIC_SECRET' not in os.environ
assert pathlib.Path('/input/source.txt').read_text() == 'approved input'
try:
 pathlib.Path('/input/source.txt').write_text('changed')
except OSError: pass
else: raise AssertionError('input is writable')
pathlib.Path('/work/result.txt').write_text('scratch output')
s = socket.socket();s.settimeout(.2)
try: s.connect(('192.0.2.1',443))
except OSError: pass
else: raise AssertionError('unexpected network route')
print('boundary checks passed')
'''.replace('CANARY', repr(str(canary)))
    result = subprocess.run(sandbox_command(snapshot, ['/usr/bin/python3', '-c', program]),
                            env={'SYNTHETIC_SECRET': 'must not reach job'},
                            close_fds=True, capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == 'boundary checks passed'
    assert (snapshot / 'source.txt').read_text() == 'approved input'
    assert not (tmp_path / 'result.txt').exists()


@pytest.mark.skipif(os.environ.get('DAIA_RUN_ISOLATION_TESTS') != '1',
                    reason='Explicit real namespace integration test')
def test_cli_enforces_wall_clock_limit(tmp_path):
    snapshot = tmp_path / 'input'
    snapshot.mkdir()
    import time
    started = time.monotonic()
    result = subprocess.run([sys.executable, '-m', 'daia.isolation',
                             '--input', str(snapshot), '--timeout', '1', '--',
                             '/usr/bin/python3', '-c', 'import time; time.sleep(60)'],
                            capture_output=True, text=True, timeout=8)
    assert result.returncode == 124, result.stderr
    assert 'wall-clock limit' in result.stderr
    assert time.monotonic() - started < 6


def test_snapshot_rejects_external_hardlink(tmp_path):
    outside = tmp_path / 'canary'; outside.write_text('synthetic secret')
    snapshot = tmp_path / 'input'; snapshot.mkdir()
    os.link(outside, snapshot / 'linked')
    with pytest.raises(ValueError):
        sandbox_command(snapshot, ['/bin/cat', '/input/linked'])


@pytest.mark.skipif(os.environ.get('DAIA_RUN_ISOLATION_TESTS') != '1',
                    reason='Explicit real namespace integration test')
def test_cli_does_not_inherit_host_stdin(tmp_path):
    snapshot = tmp_path / 'input'; snapshot.mkdir()
    result = subprocess.run([sys.executable, '-m', 'daia.isolation',
                             '--input', str(snapshot), '--', '/bin/cat'],
                            input='synthetic operator secret', capture_output=True,
                            text=True, timeout=8)
    assert result.returncode == 0, result.stderr
    assert result.stdout == ''


@pytest.mark.skipif(os.environ.get('DAIA_RUN_ISOLATION_TESTS') != '1',
                    reason='Explicit real namespace integration test')
def test_cli_bounds_combined_output(tmp_path):
    snapshot = tmp_path / 'input'; snapshot.mkdir()
    program = "import os; data=b'x'*8192\nwhile True: os.write(1,data); os.write(2,data)"
    result = subprocess.run([sys.executable, '-m', 'daia.isolation',
                             '--input', str(snapshot), '--', '/usr/bin/python3', '-c', program],
                            capture_output=True, timeout=8)
    assert result.returncode == 125
    assert b'output limit' in result.stderr
    assert len(result.stdout) + len(result.stderr) <= 1024 * 1024 + 100
