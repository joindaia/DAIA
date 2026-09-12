"""Ed25519 identities and a deliberately restricted canonical-envelope profile.

Envelope strings/keys are ASCII; numbers are safe JSON integers, never floats.
For this subset, the encoder agrees with RFC 8785. Free text/artifacts are
hashed as EXACT UTF-8 bytes and are not canonicalized. Do not silently widen
this profile; adopt an audited full JCS implementation when it becomes needed.
"""
from __future__ import annotations
import hashlib
import json
from typing import Any
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization

PREFIX = b"DAIA-SIGNED-ENVELOPE-v1\x00"
MAX_SAFE_INTEGER = 2**53 - 1


def canonical(value: Any) -> bytes:
    def check(v: Any) -> None:
        if v is None or type(v) is bool:
            return
        if type(v) is int and abs(v) <= MAX_SAFE_INTEGER:
            return
        if isinstance(v, str) and v.isascii():
            return
        if isinstance(v, list):
            for item in v:
                check(item)
            return
        if isinstance(v, dict):
            for key, item in v.items():
                if not isinstance(key, str) or not key.isascii():
                    raise ValueError("Envelope keys must be ASCII strings")
                check(item)
            return
        raise ValueError("Unsupported canonical envelope value")
    check(value)
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest(value: Any) -> str:
    return digest_bytes(canonical(value))


def public_hex(key: Ed25519PrivateKey) -> str:
    return key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    ).hex()


def validate_public(public: str) -> bytes:
    if len(public) != 64 or public != public.lower():
        raise ValueError("Invalid Ed25519 public key encoding")
    raw = bytes.fromhex(public)
    if len(raw) != 32:
        raise ValueError("Invalid Ed25519 public key")
    Ed25519PublicKey.from_public_bytes(raw)
    return raw


def fingerprint(public: str) -> str:
    return digest_bytes(validate_public(public))


def sign(key: Ed25519PrivateKey, payload: dict) -> str:
    return key.sign(PREFIX + canonical(payload)).hex()


def verify(public: str, payload: dict, signature: str) -> bool:
    try:
        if len(signature) != 128 or signature != signature.lower():
            return False
        Ed25519PublicKey.from_public_bytes(validate_public(public)).verify(
            bytes.fromhex(signature), PREFIX + canonical(payload)
        )
        return True
    except (ValueError, TypeError, InvalidSignature):
        return False


def strict_json(text: str) -> Any:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result
    def reject_constant(_):
        raise ValueError("Non-finite JSON number")
    return json.loads(text, object_pairs_hook=unique, parse_constant=reject_constant)
