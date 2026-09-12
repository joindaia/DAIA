import importlib.util
from pathlib import Path
import os
import pytest
from daia.service import Denied
from daia.store import Store
from daia.verifier import check_factorization
from conftest import submit

spec = importlib.util.spec_from_file_location('privacy_guard', Path(__file__).parents[1]/'scripts/privacy_guard.py')
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


def test_nested_json_is_rejected():
    assert not check_factorization(10403, '[' * 1500 + '0' + ']' * 1500)


def test_surrogate_artifact_denied(network, contributor):
    c, _ = network
    c.seed()
    who = contributor()
    lease = c.request_work(who[0]['root_id'], who[1])
    with pytest.raises(Denied):
        c.envelope(who[0]['root_id'], who[1], lease['assignment_id'], '\ud800', 'candidate')
    assert not check_factorization(10403, '\ud800')


def test_empty_pass_evidence_denied(network, contributor):
    c, _ = network
    c.seed()
    producer = contributor()
    submit(c, producer, c.request_work(producer[0]['root_id'], producer[1]))
    for _ in range(2):
        reviewer = contributor()
        lease = c.request_work(reviewer[0]['root_id'], reviewer[1])
        if lease['mode'] == 'reproduce':
            submit(c, reviewer, lease)
        else:
            with pytest.raises(Denied):
                submit(c, reviewer, lease, '  ', 'pass')


def test_public_web_origin_denied(network):
    from fastapi.testclient import TestClient
    from daia.http import create_app
    with TestClient(create_app(network[0]), base_url='http://localhost') as client:
        response = client.get('/health', headers={'Origin':'https://attacker.example'})
        assert response.status_code == 403


def test_new_database_private_on_posix(tmp_path):
    path = tmp_path/'private.sqlite3'
    Store(str(path))
    if os.name == 'posix':
        assert path.stat().st_mode & 0o077 == 0


@pytest.mark.skipif(os.name != 'posix', reason='POSIX permissions are not Windows ACLs')
def test_reject_existing_world_readable_database(tmp_path):
    path = tmp_path/'private.sqlite3'
    path.touch(mode=0o644)
    path.chmod(0o644)
    with pytest.raises(ValueError):
        Store(str(path))


def test_private_scanner_does_not_print_values(capsys):
    sample = 'private-' + 'person@' + 'not-public.invalid'
    assert 'non-placeholder-email' in guard.scan_text(sample)
    assert sample not in capsys.readouterr().out


def test_privacy_placeholder_and_noreply_allowed():
    assert not guard.scan_text('tester@example.com alias@users.noreply.github.com')


def test_private_literal_and_secret_scanning():
    assert guard.scan_text('sensitive marker', ('sensitive marker',)) == {'private-literal'}
    block = '-----BEGIN ' + 'PRIVATE KEY-----'
    assert 'secret-format' in guard.scan_text(block)


@pytest.mark.parametrize('path', ['.env', '.runtime/demo.sqlite3', 'private.pem', '.private/identity'])
def test_private_paths_detected(path):
    assert guard.private_path(path)


def test_sample_env_is_allowed():
    assert not guard.private_path('.env.example')
