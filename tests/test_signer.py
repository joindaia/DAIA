import pytest

from daia.crypto import public_hex
from daia.signer import validate_envelope


def test_signer_checks_registration_identity(network, contributor):
    service, now = network
    grant, _, key = contributor()
    identity = {**grant, "network_id": service.network_id}
    challenge = service.challenge(grant["root_id"], public_hex(key))
    validate_envelope(key, challenge, identity, now=now[0])
    for change in ({"root_id": "wrong"}, {"network_id": "wrong"}, {"public_key": "0" * 64},
                   {"expires": now[0]}, {"extra": "field"}):
        with pytest.raises(ValueError):
            validate_envelope(key, {**challenge, **change}, identity, now=now[0])


@pytest.mark.parametrize("field", ["network_id", "assignment_id", "job_id", "nonce", "agent_id",
                                  "policy_hash", "context_hash", "artifact_hash", "mode", "target_id", "verdict"])
def test_signer_rejects_changed_submission(network, contributor, field):
    service, now = network
    service.seed()
    grant, aid, key = contributor()
    identity = {**grant, "network_id": service.network_id}
    lease = service.request_work(grant["root_id"], aid)
    artifact = b'{"factors":[101,103]}'
    envelope = service.envelope(grant["root_id"], aid, lease["assignment_id"], artifact.decode(), "candidate")
    args = dict(lease=lease, artifact=artifact, verdict="candidate", now=now[0])
    validate_envelope(key, envelope, identity, **args)
    with pytest.raises(ValueError):
        validate_envelope(key, {**envelope, field: "wrong"}, identity, **args)
    with pytest.raises(ValueError):
        validate_envelope(key, envelope, identity, **{**args, "artifact": artifact + b"\n"})
    with pytest.raises(ValueError):
        validate_envelope(key, envelope, identity, **{**args, "now": lease["expires"]})
    with pytest.raises(ValueError):
        validate_envelope(key, envelope, identity, **{**args, "lease": {**lease, "context": {}}})
