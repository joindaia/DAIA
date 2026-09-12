"""Explicit cross-platform owner consent preserves the existing signing identity."""
import asyncio
import json
import subprocess
import sys
import pytest
from daia.contributor import Contributor
from test_contributor import direct, invite_file


def host_for(network, tmp_path):
    service, now = network
    path = invite_file(tmp_path, service, max_jobs=3, lifetime=120)
    host = direct(Contributor(path, clock=lambda: now[0]), service)
    asyncio.run(host.register())
    return host, service, now


def test_accept_absolute_week_and_restart_without_invite_change(network, tmp_path):
    host, service, now = host_for(network, tmp_path)
    before = host.state.copy()
    invite = host.invite_file.read_bytes()
    until = now[0] + 604800
    service.extend_grant(host.identity['root_id'], 50, until)
    accepted = asyncio.run(host.accept_grant(50, until))
    assert accepted['consent_changed'] and accepted['deadline'] == until
    assert host.state == {**before, 'max_jobs': 50, 'deadline': until, 'accepted_until': until}
    saved = host.path.read_bytes()
    assert not asyncio.run(host.accept_grant(50, until))['consent_changed']
    assert host.path.read_bytes() == saved and host.invite_file.read_bytes() == invite
    now[0] += 121
    restarted = direct(Contributor(host.invite_file, clock=lambda: now[0]), service)
    assert restarted.state == host.state
    assert restarted.status()['status'] == 'ready'
    # A later server extension does not silently expand the saved owner ceiling.
    service.extend_grant(host.identity['root_id'], 60, until + 60)
    assert Contributor(host.invite_file, clock=lambda: now[0]).state == host.state


@pytest.mark.parametrize('blocked', ['stopped','pending','claiming','releasing','lease','unregistered','capacity','expired','revoked','too_long','shrink'])
def test_accept_refuses_invalid_or_unsettled_state(network, tmp_path, blocked):
    host, service, now = host_for(network, tmp_path)
    until = now[0] + 300
    service.extend_grant(host.identity['root_id'], 50, until)
    if blocked in {'stopped','pending','claiming','releasing','lease'}:
        host.state[blocked] = True
    elif blocked == 'unregistered': host.state['registered'] = False
    elif blocked == 'expired': now[0] = until
    elif blocked == 'revoked': service.revoke(host.identity['root_id'])
    elif blocked == 'too_long': until = now[0] + 604801
    elif blocked == 'shrink': until = host.state['deadline'] - 1
    host.save()
    before = host.path.read_bytes()
    with pytest.raises(ValueError):
        asyncio.run(host.accept_grant(51 if blocked == 'capacity' else 50, until))
    assert host.path.read_bytes() == before


def test_accept_save_failure_keeps_old_consent(network, tmp_path, monkeypatch):
    host, service, now = host_for(network, tmp_path)
    until = now[0] + 300
    service.extend_grant(host.identity['root_id'], 50, until)
    before = host.state.copy()
    saved = host.path.read_bytes()
    def fail(): raise OSError('synthetic write failure')
    monkeypatch.setattr(host, 'save', fail)
    with pytest.raises(OSError): asyncio.run(host.accept_grant(50, until))
    assert host.state == before and host.path.read_bytes() == saved


def test_accept_cli_never_creates_identity_or_starts_host(network, tmp_path):
    service, now = network
    path = invite_file(tmp_path, service)
    result = subprocess.run([sys.executable, '-m', 'daia.contributor', '--invite', str(path),
        '--accept-grant', '--max-jobs', '50', '--until', str(now[0]+300)], capture_output=True, timeout=15)
    assert result.returncode == 1 and result.stdout == b''
    assert not path.with_suffix('.contributor.json').exists()
    for other in ('--configure', '--renew-consent'):
        result = subprocess.run([sys.executable, '-m', 'daia.contributor', '--invite', str(path),
            '--accept-grant', '--until', str(now[0]+300), other], capture_output=True, timeout=15)
        assert result.returncode == 2
