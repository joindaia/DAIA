import pytest
from fastapi.testclient import TestClient
from daia.http import create_app

@pytest.fixture
def client(network):
    c, _ = network
    return TestClient(create_app(c), base_url="http://127.0.0.1")


def test_no_auth_denied(client):
    assert client.post("/v1/work/request", json={"agent_id":"a"*64}).status_code == 403


def test_no_selectable_job_parameter(client, contributor):
    grant, aid, _ = contributor()
    response = client.post("/v1/work/request", headers={"Authorization": "Bearer "+grant["token"]},
                           json={"agent_id":aid, "job_id":"pick-me"})
    assert response.status_code == 422
    assert "pick-me" not in response.text


def test_bad_host_denied(client):
    assert client.get("/health", headers={"host":"attacker.example"}).status_code == 400


def test_size_limit(client):
    assert client.post("/v1/work/request", content=b"x"*20000).status_code == 413


def test_owner_is_from_token(client, contributor, network):
    c, _ = network
    c.seed()
    one, two = contributor(), contributor()
    response = client.post("/v1/work/request", headers={"Authorization":"Bearer "+one[0]["token"]},
                           json={"agent_id":two[1]})
    assert response.status_code == 403


def test_admin_endpoints_absent(client):
    for endpoint in ("/v1/invite", "/v1/deploy", "/v1/jobs/create", "/v1/policy/update", "/docs"):
        assert client.get(endpoint).status_code == 404
