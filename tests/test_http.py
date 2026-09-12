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
    for endpoint in ("/v1/invite", "/v1/deploy", "/v1/jobs/create", "/v1/policy/update", "/docs",
                     "/v1/evidence/admit", "/v1/evidence/inspect", "/v1/evidence/resolve",
                     "/v1/renew-consent", "/v1/extend-grant", "/v1/backup", "/v1/restore"):
        assert client.get(endpoint).status_code == 404
        assert client.post(endpoint, json={}).status_code == 404


@pytest.mark.parametrize("chunks, expected_status", [([b"ab", b"cd"], None), ([b"ab", b"cde"], 413)])
def test_body_limit_bounds_message_retention_and_preserves_bytes(chunks, expected_status):
    import asyncio
    import weakref
    from daia.http import BodyLimit

    class Message(dict):
        pass

    async def exercise():
        refs, sent, received = [], [], []
        step = 0

        async def receive():
            nonlocal step
            # Lazily produced events: the fixture itself does not retain messages.
            assert sum(ref() is not None for ref in refs) <= 2
            if step < 128:
                message = Message(type="http.request", body=b"", more_body=True)
            elif step < 128 + len(chunks):
                i = step - 128
                message = Message(type="http.request", body=chunks[i], more_body=i < len(chunks)-1)
            else:
                return {"type": "http.disconnect"}
            refs.append(weakref.ref(message))
            step += 1
            return message

        async def send(message):
            sent.append(message)

        async def app(scope, receive, send):
            body = bytearray()
            while True:
                message = await receive()
                body.extend(message.get("body", b""))
                if not message.get("more_body", False):
                    break
            received.append(bytes(body))
            assert await receive() == {"type": "http.disconnect"}

        await BodyLimit(app, maximum=4)({"type": "http", "headers": []}, receive, send)
        if expected_status is None:
            assert received == [b"abcd"]
        else:
            assert not received
            assert sent[0]["status"] == expected_status

    asyncio.run(exercise())
