"""An unapproved executable must never touch the dedicated auth profile."""
import os
from pathlib import Path
import subprocess
import sys
import pytest


@pytest.mark.parametrize('symlink', [False, True])
def test_unapproved_binary_never_starts_or_changes_profile(tmp_path, symlink):
    binary = tmp_path / 'fake-codex'
    binary.write_text('#!/bin/sh\nprintf started > marker\n')
    binary.chmod(0o700)
    if symlink:
        if os.name == 'nt':
            pytest.skip('POSIX symlink preflight')
        link = tmp_path / 'linked'; link.symlink_to(binary); binary = link
    home = tmp_path / 'auth'; home.mkdir(mode=0o700)
    auth = home / 'auth.json'; auth.write_bytes(b'synthetic-private-canary'); auth.chmod(0o600)
    script = Path(__file__).parents[1] / 'scripts/probe_codex_native_auth.py'
    r = subprocess.run([sys.executable, '-I', str(script), '--binary', str(binary), '--home', str(home)],
                       cwd=tmp_path, capture_output=True, timeout=5)
    assert r.returncode != 0
    assert not (tmp_path / 'marker').exists()
    assert auth.read_bytes() == b'synthetic-private-canary'
    assert b'synthetic-private-canary' not in r.stdout + r.stderr
