"""Optional signing helper for a trusted host, not a background worker.

Private-key material never needs to enter the language-model context. For a
public client use an OS key store / approval-bound signer, not this dev helper.
"""
import argparse
import os
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from daia.crypto import public_hex, sign, strict_json
from daia.signer import validate_envelope

p = argparse.ArgumentParser()
p.add_argument("operation", choices=["generate", "public", "sign"])
p.add_argument("--key", type=Path, required=True, help="Private path outside version control")
p.add_argument("--envelope", type=Path)
p.add_argument("--identity", type=Path, help="Private invite JSON containing the expected root and network")
p.add_argument("--lease", type=Path, help="Host-saved assignment JSON, with latest heartbeat expiry")
p.add_argument("--artifact", type=Path, help="Exact UTF-8 artifact file; no newline normalization")
p.add_argument("--verdict", choices=["candidate", "pass", "fail", "inconclusive"])
a = p.parse_args()
if a.operation == "generate":
    key = Ed25519PrivateKey.generate()
    raw = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                            serialization.NoEncryption())
    fd = os.open(a.key, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(raw)
    print(public_hex(key))
else:
    key = serialization.load_pem_private_key(a.key.read_bytes(), password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise SystemExit("Expected Ed25519 private key")
    if a.operation == "public":
        print(public_hex(key))
    else:
        if a.envelope is None or a.identity is None:
            raise SystemExit("--envelope and --identity are required")
        document = strict_json(a.envelope.read_text(encoding="utf-8"))
        validate_envelope(key, document, strict_json(a.identity.read_text(encoding="utf-8")),
                          lease=strict_json(a.lease.read_text(encoding="utf-8")) if a.lease else None,
                          artifact=a.artifact.read_bytes() if a.artifact else None, verdict=a.verdict)
        print(sign(key, document))
