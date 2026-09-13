import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import pytest

scope=runpy.run_path(str(Path(__file__).parents[1]/'scripts/prepare_codex_profile.py'))
prepare=scope['prepare']


@pytest.fixture
def client(tmp_path,monkeypatch):
    p=tmp_path/'client';p.write_bytes(b'synthetic client, never executed')
    monkeypatch.setitem(prepare.__globals__,'PIN',hashlib.sha256(p.read_bytes()).hexdigest())
    return p


def test_private_empty_profile_and_existing_profile_refusal(client,tmp_path):
    home=tmp_path/'profile'
    assert prepare(client,home)['login_started'] is False
    assert home.stat().st_mode & 0o777 == 0o700
    assert sorted(p.name for p in home.iterdir()) == ['config.toml']
    config=home/'config.toml'; before=config.read_bytes()
    assert config.stat().st_mode & 0o777 == 0o600
    with pytest.raises(FileExistsError): prepare(client,home)
    assert config.read_bytes()==before


@pytest.mark.parametrize('bad',['shared_parent','symlink_parent','symlink_client'])
def test_unsafe_input_refused(client,tmp_path,bad):
    parent=tmp_path/'parent';parent.mkdir(mode=0o700)
    if bad=='shared_parent': parent.chmod(0o755)
    elif bad=='symlink_parent':
        link=tmp_path/'linked';link.symlink_to(parent);parent=link
    else:
        link=tmp_path/'client-link';link.symlink_to(client);client=link
    with pytest.raises(ValueError): prepare(client,parent/'profile')
    assert not (parent/'profile').exists()


def test_wrong_binary_rejected_even_with_optimized_python(tmp_path):
    binary=tmp_path/'fake';binary.write_text('not codex')
    home=tmp_path/'profile'
    script=Path(__file__).parents[1]/'scripts/prepare_codex_profile.py'
    r=subprocess.run([sys.executable,'-I','-O',str(script),'--binary',str(binary),'--home',str(home)],capture_output=True)
    assert r.returncode!=0 and not home.exists()
