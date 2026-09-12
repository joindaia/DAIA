"""Checks for the development host signer. Inputs must be saved by the trusted host."""
import json
import time

from .crypto import digest_bytes, fingerprint, public_hex


def validate_envelope(key, envelope, identity, *, lease=None, artifact=None, verdict=None, now=None):
    now = int(time.time()) if now is None else now
    if not isinstance(envelope, dict) or envelope.get("network_id") != identity["network_id"]:
        raise ValueError("Wrong network or envelope")
    if envelope.get("action") == "register":
        fields = {"action", "network_id", "challenge_id", "root_id", "public_key", "nonce", "expires"}
        if (set(envelope) != fields or envelope["root_id"] != identity["root_id"]
                or envelope["public_key"] != public_hex(key)
                or type(envelope["expires"]) is not int
                or not now < envelope["expires"] <= now + 300):
            raise ValueError("Registration does not match the local identity or clock")
        return
    if envelope.get("action") != "submit" or lease is None or artifact is None or verdict is None:
        raise ValueError("Submission requires the saved lease, exact artifact bytes, and verdict")
    if lease["network_id"] != identity["network_id"] or now >= min(lease["expires"], lease["hard_deadline"]):
        raise ValueError("Wrong network or expired saved lease; save heartbeat expiry after renewal")
    if len(artifact) > 4096:
        raise ValueError("Artifact exceeds the development limit")
    artifact.decode("utf-8")
    context = json.dumps(lease["context"], ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    if digest_bytes(context) != lease["context_hash"]:
        raise ValueError("Saved context hash does not match")
    allowed = {"candidate"} if lease["mode"] == "produce" else {"pass", "fail", "inconclusive"}
    if verdict not in allowed:
        raise ValueError("Verdict does not match the assigned mode")
    expected = {field: lease[field] for field in (
        "network_id", "assignment_id", "job_id", "nonce", "mode", "target_id", "policy_hash", "context_hash")}
    expected.update(action="submit", agent_id=fingerprint(public_hex(key)),
                    artifact_hash=digest_bytes(artifact), verdict=verdict)
    if envelope != expected:
        raise ValueError("Envelope does not match the saved lease, signer, artifact, and verdict")
