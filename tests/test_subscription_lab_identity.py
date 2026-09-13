"""Service identity separation must fail before any live credentials are used."""
from pathlib import Path
import runpy
from types import SimpleNamespace
import pytest

scope = runpy.run_path(str(Path(__file__).parents[1] / 'scripts/subscription_lab_identity.py'))
check = scope['check_identities']


@pytest.fixture
def identities(monkeypatch):
    accounts = {name: SimpleNamespace(pw_name=name, pw_uid=100+i, pw_gid=200+i)
                for i, name in enumerate(scope['NAMES'])}
    groups = {name: [a.pw_gid] for name, a in accounts.items()}
    monkeypatch.setattr(scope['pwd'], 'getpwnam', accounts.__getitem__)
    monkeypatch.setattr(scope['os'], 'getgrouplist', lambda name, gid: groups[name])
    return accounts, groups


def test_separate_accounts_pass(identities):
    assert all(check().values())


@pytest.mark.parametrize('bad', ['missing', 'root', 'duplicate', 'primary_group', 'secondary_group'])
def test_unsafe_identity_configuration_refused(identities, bad):
    accounts, groups = identities
    runtime = accounts['daia-runtime']
    peer = accounts['daia-egress']
    if bad == 'missing': del accounts['daia-egress']
    elif bad == 'root': peer.pw_uid = 0
    elif bad == 'duplicate': peer.pw_uid = runtime.pw_uid
    elif bad == 'primary_group':
        peer.pw_gid = runtime.pw_gid
        groups[peer.pw_name] = [runtime.pw_gid]
    else: groups[peer.pw_name].append(runtime.pw_gid)
    with pytest.raises(RuntimeError): check()


def test_both_entrypoints_check_before_effects():
    scripts = Path(__file__).parents[1] / 'scripts'
    for file, effect in [('run_subscription_lab.py', 'with open('),
                         ('run_subscription_lab_controller.py', 'bundle_hashes=prepare(')]:
        source = (scripts/file).read_text()
        assert source.index('check_identities()') < source.index(effect)
