"""Trusted, bounded DATA-ONLY demo verifier. Never executes contributed code.

The demo certifies only a nontrivial integer factorization, not a new theorem.
No shell, imports, network, Lean, or arbitrary checker definitions are accepted.
"""
from pathlib import Path
from .crypto import strict_json, digest, digest_bytes

PRODUCER_SCHEMA = {"version": "source-finding-v1", "max_utf8_bytes": 4096,
    "fields": ["source_digest", "line", "finding", "reproduction_outline", "suggested_change"],
    "text_fields": ["finding", "reproduction_outline", "suggested_change"],
    "text_max_chars": 1200, "text_nonblank": True, "line": "integer-within-frozen-excerpt",
    "source_digest": "exact-source-sha256", "additional_fields": False}
REVIEW_SCHEMA = {"version": "source-review-v1", "max_utf8_bytes": 4096,
    "fields": ["source_digest", "candidate_digest", "line", "assessment", "objections", "next_check"],
    "text_fields": ["objections", "next_check"], "text_max_chars": 1200, "text_nonblank": True,
    "line": "integer-within-frozen-excerpt", "source_digest": "exact-source-sha256",
    "candidate_digest": "exact-candidate-sha256", "additional_fields": False,
    "assessments": {"pass": "supports", "fail": "concerns", "inconclusive": "unclear"}}
EVIDENCE_SCHEMAS = {"produce": PRODUCER_SCHEMA, "adversarial": REVIEW_SCHEMA}
EVIDENCE_SCHEMA_HASHES = {mode: digest(schema) for mode, schema in EVIDENCE_SCHEMAS.items()}
EVIDENCE_CHECKER_HASH = digest_bytes(Path(__file__).read_bytes())


def check_evidence_packet(context: dict, artifact: str, verdict="candidate") -> bool:
    """Validate attribution and shape only. This does not prove a finding is correct."""
    try:
        if not isinstance(artifact, str) or len(artifact.encode("utf-8")) > 4096:
            return False
        if (context.get("schema_hashes") != EVIDENCE_SCHEMA_HASHES
                or context.get("checker_hash") != EVIDENCE_CHECKER_HASH):
            return False
        value = strict_json(artifact)
        schema = PRODUCER_SCHEMA if context["mode"] == "produce" else REVIEW_SCHEMA
        source = context["source"]
        valid = (isinstance(value, dict) and set(value) == set(schema["fields"])
                and value["source_digest"] == source["sha256"]
                and type(value["line"]) is int
                and source["start_line"] <= value["line"] < source["start_line"] + len(source["text"].splitlines())
                and all(isinstance(value[k], str) and value[k].strip() and len(value[k]) <= 1200
                        for k in schema["text_fields"]))
        if not valid:
            return False
        if context["mode"] == "produce":
            return verdict == "candidate"
        return (value["candidate_digest"] == context["candidate_digest"]
                == digest_bytes(context["candidate_artifact"].encode("utf-8"))
                and verdict in REVIEW_SCHEMA["assessments"]
                and value["assessment"] == REVIEW_SCHEMA["assessments"][verdict])
    except (ValueError, TypeError, KeyError, RecursionError, UnicodeError):
        return False


def check_factorization(number: int, artifact: str) -> bool:
    if type(number) is not int or not 4 <= number <= 10**12:
        return False
    if not isinstance(artifact, str):
        return False
    try:
        size = len(artifact.encode("utf-8"))
    except UnicodeEncodeError:
        return False
    if size > 4096:
        return False
    try:
        value = strict_json(artifact)
    except (ValueError, TypeError, RecursionError):
        return False
    if not isinstance(value, dict) or set(value) != {"factors"}:
        return False
    factors = value["factors"]
    if not isinstance(factors, list) or not 2 <= len(factors) <= 40:
        return False
    product = 1
    for f in factors:
        if type(f) is not int or not 1 < f < number:
            return False
        product *= f
        if product > number:
            return False
    return product == number
