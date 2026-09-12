import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from daia.crypto import public_hex, sign
from daia.service import Coordinator
from daia.store import Store

@pytest.fixture
def network(tmp_path):
    now = [1800000000]
    c = Coordinator(Store(str(tmp_path / "network.sqlite3")), clock=lambda: now[0])
    return c, now

@pytest.fixture
def contributor(network):
    c, _ = network
    def make(max_jobs=20, root=None):
        grant = c.invite(max_jobs=max_jobs) if root is None else {"root_id": root}
        key = Ed25519PrivateKey.generate()
        ch = c.challenge(grant["root_id"], public_hex(key))
        aid = c.register(grant["root_id"], ch["challenge_id"], sign(key, ch))["agent_id"]
        return grant, aid, key
    return make


def submit(c, contributor, lease, artifact='{"factors":[101,103]}', verdict=None):
    grant, aid, key = contributor
    verdict = verdict or ("candidate" if lease["mode"] == "produce" else "pass")
    env = c.envelope(grant["root_id"], aid, lease["assignment_id"], artifact, verdict)
    return c.submit(grant["root_id"], aid, lease["assignment_id"], artifact, verdict, sign(key, env))
