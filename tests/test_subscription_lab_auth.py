import json
import os
from pathlib import Path
import runpy
import sys
import pytest

pytestmark = pytest.mark.skipif(sys.platform != "linux", reason='Linux private authentication profile')

read = runpy.run_path(str(Path(__file__).parents[1] / 'scripts/subscription_lab_auth.py'))['read_auth']


@pytest.fixture
def profile(tmp_path):
    home = tmp_path/'profile'; home.mkdir(mode=0o700)
    auth = home/'auth.json'
    auth.write_text(json.dumps({'tokens': {k:'synthetic-private-canary'
        for k in ('access_token','refresh_token','account_id')}}))
    auth.chmod(0o600)
    return home, auth


def test_private_profile_and_native_atomic_replacement(profile):
    home, auth = profile
    data, uid = read(home)
    replacement = home/'replacement'; replacement.write_bytes(auth.read_bytes()); replacement.chmod(0o600)
    replacement.replace(auth)
    assert read(home, owner_uid=uid)[0] == data


@pytest.mark.parametrize('bad', ['home_mode','file_mode','file_symlink','home_symlink',
    'hardlink','fifo','oversize','malformed','wrong_owner','worker_owner'])
def test_rejects_unsafe_profile_without_secret_in_error(profile, bad):
    home, auth = profile
    kwargs = {}
    if bad == 'home_mode': home.chmod(0o750)
    elif bad == 'file_mode': auth.chmod(0o640)
    elif bad == 'file_symlink':
        target=home/'target'; auth.rename(target); auth.symlink_to(target)
    elif bad == 'home_symlink':
        link=home.parent/'link'; link.symlink_to(home); home=link
    elif bad == 'hardlink': os.link(auth, home/'second')
    elif bad == 'fifo': auth.unlink(); os.mkfifo(auth,0o600)
    elif bad == 'oversize': auth.write_bytes(b'x'*(1024*1024+1))
    elif bad == 'malformed': auth.write_text('synthetic-private-canary')
    elif bad == 'wrong_owner': kwargs['owner_uid']=os.getuid()+1
    else: kwargs['forbidden_uids']={os.getuid()}
    with pytest.raises(RuntimeError) as error: read(home, **kwargs)
    assert 'synthetic-private-canary' not in str(error.value)
