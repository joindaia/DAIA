"""An unapproved executable must never touch the dedicated auth profile."""
import os
import json
from pathlib import Path
import subprocess
import sys
import pytest


@pytest.mark.parametrize('optimized', [False, True])
@pytest.mark.parametrize('symlink', [False, True])
def test_unapproved_binary_never_starts_or_changes_profile(tmp_path, symlink, optimized):
    binary = tmp_path / 'fake-codex'
    binary.write_text('#!/bin/sh\nprintf started > "$CODEX_HOME/marker"\nexit 1\n')
    binary.chmod(0o700)
    if symlink:
        if os.name == 'nt':
            pytest.skip('POSIX symlink preflight')
        link = tmp_path / 'linked'; link.symlink_to(binary); binary = link
    home = tmp_path / 'auth'; home.mkdir(mode=0o700)
    auth = home / 'auth.json'
    original = json.dumps({'tokens':{k:'synthetic-private-canary' for k in ('access_token','refresh_token','account_id')}}).encode()
    auth.write_bytes(original); auth.chmod(0o600)
    script = Path(__file__).parents[1] / 'scripts/probe_codex_native_auth.py'
    r = subprocess.run([sys.executable, '-I', *(['-O'] if optimized else []), str(script), '--binary', str(binary), '--home', str(home)],
                       cwd=tmp_path, capture_output=True, timeout=5)
    assert r.returncode != 0
    assert not (home / 'marker').exists()
    assert auth.read_bytes() == original
    assert b'synthetic-private-canary' not in r.stdout + r.stderr
