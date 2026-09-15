"""The canary scanner must detect real process surfaces, not just return zero."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

SCRIPT = Path(__file__).parents[1] / 'scripts/probe_guest_process_canary.py'
spec = importlib.util.spec_from_file_location('process_probe', SCRIPT)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def test_digest_matching_does_not_accept_arbitrary_token():
    value = b'a' * 64
    digest = hashlib.sha256(value).hexdigest()
    assert probe.contains(b'CANARY=' + value + b'\0', digest)
    assert not probe.contains(b'b' * 64, digest)
    with pytest.raises(ValueError):
        probe.inspect('invalid')


@pytest.mark.skipif(sys.platform != 'linux', reason='Linux /proc acceptance probe')
def test_real_environment_arguments_and_open_file_are_detected(tmp_path):
    value = os.urandom(32).hex()
    canary = tmp_path / 'synthetic'; canary.write_text(value)
    digest = hashlib.sha256(value.encode()).hexdigest()
    code = ("import runpy,sys,json,os; "
            "p=runpy.run_path(sys.argv[1]); "
            "f=open(sys.argv[2]); "
            "print(json.dumps(p['inspect'](sys.argv[3])))")
    result = subprocess.run([sys.executable, '-I', '-c', code, str(SCRIPT),
        str(canary), digest, value], env=dict(os.environ, DAIA_SYNTHETIC_CANARY=value),
        capture_output=True, text=True, check=True, timeout=10)
    report = json.loads(result.stdout)
    assert report['matches'] >= 3
    assert report['environments'] and report['arguments'] and report['regular_handles']
    assert value not in result.stdout
