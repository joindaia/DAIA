import json
from concurrent.futures import ThreadPoolExecutor
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from daia.crypto import canonical, public_hex, sign, verify, strict_json, digest
from daia.policy import Policy, evaluate
from daia.service import Denied
from daia.verifier import check_factorization
from conftest import submit


def test_complete_demo(network, contributor):
    c, _ = network
    c.seed()
    statuses = []
    for _ in range(3):
        who = contributor()
        lease = c.request_work(who[0]["root_id"], who[1])
        statuses.append(submit(c, who, lease)["status"])
    assert statuses == ["in_review", "in_review", "promoted"]
    assert c.metrics()["promoted"] == 1


def test_signature_tampering():
    key = Ed25519PrivateKey.generate()
    payload = {"action": "submit", "hash": "abc"}
    signature = sign(key, payload)
    assert verify(public_hex(key), payload, signature)
    assert not verify(public_hex(key), {**payload, "hash": "def"}, signature)
    assert not verify(public_hex(Ed25519PrivateKey.generate()), payload, signature)

@pytest.mark.parametrize("value", [float("nan"), 1.5, 2**53, "\u03bb", {1: "bad"}])
def test_canonical_rejects_unsupported(value):
    with pytest.raises(ValueError):
        canonical(value)


def test_canonical_golden_vector():
    assert canonical({"z": 3, "a": [True, None, "hello"]}) == b'{"a":[true,null,"hello"],"z":3}'


def test_duplicate_json_rejected():
    with pytest.raises(ValueError):
        strict_json('{"a":1,"a":2}')


def test_challenge_one_use_and_owner_bound(network, contributor):
    c, _ = network
    g1 = c.invite()
    g2 = c.invite()
    key = Ed25519PrivateKey.generate()
    ch = c.challenge(g1["root_id"], public_hex(key))
    sig = sign(key, ch)
    with pytest.raises(Denied):
        c.register(g2["root_id"], ch["challenge_id"], sig)
    c.register(g1["root_id"], ch["challenge_id"], sig)
    with pytest.raises(Denied):
        c.register(g1["root_id"], ch["challenge_id"], sig)


def test_expired_challenge(network):
    c, now = network
    grant = c.invite()
    key = Ed25519PrivateKey.generate()
    ch = c.challenge(grant["root_id"], public_hex(key))
    now[0] += 301
    with pytest.raises(Denied):
        c.register(grant["root_id"], ch["challenge_id"], sign(key, ch))


def test_same_owner_cannot_self_review_even_with_new_key(network, contributor):
    c, _ = network
    c.seed()
    who = contributor()
    lease = c.request_work(who[0]["root_id"], who[1])
    submit(c, who, lease)
    other = contributor(root=who[0]["root_id"])
    assert c.request_work(other[0]["root_id"], other[1])["status"] == "no_eligible_work"


def test_one_contributor_cannot_fill_two_review_modes(network, contributor):
    c, _ = network
    c.seed()
    producer, reviewer = contributor(), contributor()
    submit(c, producer, c.request_work(producer[0]["root_id"], producer[1]))
    submit(c, reviewer, c.request_work(reviewer[0]["root_id"], reviewer[1]))
    assert c.request_work(reviewer[0]["root_id"], reviewer[1])["status"] == "no_eligible_work"


def test_request_is_sticky_not_job_roulette(network, contributor):
    c, _ = network
    c.seed(); c.seed(35)
    who = contributor()
    a = c.request_work(who[0]["root_id"], who[1])
    assert c.request_work(who[0]["root_id"], who[1]) == a


def test_concurrent_requests_do_not_double_lease(network, contributor):
    c, _ = network
    c.seed()
    people = [contributor() for _ in range(8)]
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda w: c.request_work(w[0]["root_id"], w[1]), people))
    assert sum("assignment_id" in result for result in results) == 1


def test_release_keeps_exposure_history(network, contributor):
    c, now = network
    c.seed()
    who = contributor()
    lease = c.request_work(who[0]["root_id"], who[1])
    c.release(who[0]["root_id"], who[1], lease["assignment_id"])
    now[0] += 31
    assert c.request_work(who[0]["root_id"], who[1])["status"] == "no_eligible_work"


def test_expired_assignment_rejected_and_reassigned(network, contributor):
    c, now = network
    c.seed()
    first, second = contributor(), contributor()
    a = c.request_work(first[0]["root_id"], first[1])
    artifact = '{"factors":[101,103]}'
    env = c.envelope(first[0]["root_id"], first[1], a["assignment_id"], artifact, "candidate")
    signature = sign(first[2], env)
    now[0] += 301
    b = c.request_work(second[0]["root_id"], second[1])
    assert a["job_id"] == b["job_id"] and a["nonce"] != b["nonce"]
    with pytest.raises(Denied):
        c.submit(first[0]["root_id"], first[1], a["assignment_id"], artifact, "candidate", signature)


def test_heartbeat_hard_deadline(network, contributor):
    c, now = network
    c.seed()
    who = contributor()
    a = c.request_work(who[0]["root_id"], who[1])
    for _ in range(7):
        now[0] += 240
        expiry = c.heartbeat(who[0]["root_id"], who[1], a["assignment_id"])["expires"]
        assert expiry <= a["hard_deadline"]
    now[0] = a["hard_deadline"]
    with pytest.raises(Denied):
        c.heartbeat(who[0]["root_id"], who[1], a["assignment_id"])


def test_idempotent_submission(network, contributor):
    c, _ = network
    c.seed()
    who = contributor()
    a = c.request_work(who[0]["root_id"], who[1])
    text = '{"factors":[101,103]}'
    env = c.envelope(who[0]["root_id"], who[1], a["assignment_id"], text, "candidate")
    args = (who[0]["root_id"], who[1], a["assignment_id"], text, "candidate", sign(who[2], env))
    c.submit(*args)
    assert c.submit(*args)["status"] == "already_recorded"
    assert c.metrics()["results"] == 1


def test_tampered_submission_rejected(network, contributor):
    c, _ = network
    c.seed()
    who = contributor()
    a = c.request_work(who[0]["root_id"], who[1])
    text = '{"factors":[101,103]}'
    env = c.envelope(who[0]["root_id"], who[1], a["assignment_id"], text, "candidate")
    with pytest.raises(Denied):
        c.submit(who[0]["root_id"], who[1], a["assignment_id"], text + " ", "candidate", sign(who[2], env))


def test_bad_certificate_never_reaches_review(network, contributor):
    c, _ = network
    c.seed()
    who = contributor()
    a = c.request_work(who[0]["root_id"], who[1])
    assert submit(c, who, a, '{"factors":[2,3]}')["status"] == "rejected"
    assert c.metrics()["jobs"] == 1


def test_blind_reproduction_context(network, contributor):
    c, _ = network
    c.seed()
    who = contributor()
    submit(c, who, c.request_work(who[0]["root_id"], who[1]))
    contexts = []
    for _ in range(2):
        reviewer = contributor()
        contexts.append(c.request_work(reviewer[0]["root_id"], reviewer[1]))
    repro = next(a for a in contexts if a["mode"] == "reproduce")
    assert "candidate_artifact" not in repro["context"]
    assert "root_id" not in repro and "author" not in repro


def test_bad_reproduction_cannot_pass(network, contributor):
    c, _ = network
    c.seed(policy=Policy(modes=("reproduce",), min_roots=1))
    producer, reviewer = contributor(), contributor()
    submit(c, producer, c.request_work(producer[0]["root_id"], producer[1]))
    a = c.request_work(reviewer[0]["root_id"], reviewer[1])
    with pytest.raises(Denied):
        submit(c, reviewer, a, '{"factors":[2,3]}')


def test_grant_exhaustion_and_revocation(network, contributor):
    c, _ = network
    c.seed()
    who = contributor(max_jobs=0)
    assert c.request_work(who[0]["root_id"], who[1])["status"] == "budget_or_cooldown"
    c.revoke(who[0]["root_id"])
    with pytest.raises(Denied):
        c.authenticate(who[0]["token"])


def test_failing_review_opens_dispute(network, contributor):
    c, _ = network
    c.seed()
    producer, reviewer = contributor(), contributor()
    submit(c, producer, c.request_work(producer[0]["root_id"], producer[1]))
    a = c.request_work(reviewer[0]["root_id"], reviewer[1])
    assert submit(c, reviewer, a, "Needs independent examination", "fail")["status"] == "disputed"


def test_human_gate_is_never_bypassed(network, contributor):
    c, _ = network
    c.seed(policy=Policy(human_gate=True))
    result = None
    for _ in range(3):
        who = contributor()
        result = submit(c, who, c.request_work(who[0]["root_id"], who[1]))
    assert result["status"] == "ready_for_maintainer"
    assert c.metrics()["promoted"] == 0


def test_policy_fail_closed():
    p = Policy()
    votes = [{"root_id":"a", "mode":"reproduce", "verdict":"pass"},
             {"root_id":"b", "mode":"adversarial", "verdict":"pass"}]
    assert evaluate(p, False, votes) == "rejected"
    assert evaluate(p, None, votes) == "in_review"
    assert evaluate(p, True, votes[:1]) == "in_review"
    assert evaluate(p, True, [votes[0], {**votes[1], "root_id":"a"}]) == "in_review"
    assert evaluate(p, True, votes) == "promoted"


def test_event_chain(network, contributor):
    c, _ = network
    c.seed(); contributor()
    with c.store.connect() as db:
        events = db.execute("SELECT * FROM events ORDER BY sequence").fetchall()
    previous = "0"*64
    for event in events:
        assert event["previous_hash"] == previous
        assert event["event_hash"] == digest({"previous": previous, "event": json.loads(event["event_json"])})
        previous = event["event_hash"]

@pytest.mark.parametrize("text", [
    '{"factors":[true,10403]}', '{"factors":[1,10403]}', '{"factors":[101.0,103]}',
    '{"factors":[-101,-103]}', '{"factors":[101,103],"factors":[2,3]}',
    '{"factors":[101,103],"extra":"ignored?"}', '{"factors":[NaN,103]}',
])
def test_malformed_certificates(text):
    assert not check_factorization(10403, text)
