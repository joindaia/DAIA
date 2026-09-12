"""The recovery acceptance probe must never run with its assertions disabled."""
import os
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.parametrize('flags,optimization', [(['-O'], '0'), ([], '1')])
def test_recovery_probe_refuses_optimized_python(flags, optimization):
    script = Path(__file__).resolve().parents[1] / 'scripts' / 'probe_recovery.py'
    result = subprocess.run(
        [sys.executable, *flags, '-B', str(script)],
        env={**os.environ, 'PYTHONOPTIMIZE': optimization},
        capture_output=True, text=True, timeout=15,
    )
    assert result.returncode != 0
    assert result.stdout == ''
    assert 'requires assertions' in result.stderr
