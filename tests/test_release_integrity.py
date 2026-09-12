import hashlib
import json

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from daia.crypto import public_hex, sign
from daia.release_integrity import (
    MANIFEST_KIND,
    ReleaseIntegrityError,
    main,
    verify_release,
)


def make_release(tmp_path, *, sequence=7, expires=200):
    root = tmp_path / "release"
    (root / "bin").mkdir(parents=True)
    (root / "bin" / "daia").write_bytes(b"trusted release bytes\n")
    key = Ed25519PrivateKey.generate()
    signed = {
        "kind": MANIFEST_KIND,
        "version": "1.2.3",
        "sequence": sequence,
        "expires": expires,
        "files": {
            "bin/daia": hashlib.sha256((root / "bin" / "daia").read_bytes()).hexdigest()
        },
    }
    manifest = tmp_path / "release-manifest.json"
    manifest.write_text(json.dumps({"signed": signed, "signature": sign(key, signed)}))
    return root, manifest, key, signed


def check(root, manifest, key, *, minimum_sequence=7, current_time=100):
    return verify_release(
        manifest,
        public_key=public_hex(key),
        release_root=root,
        minimum_sequence=minimum_sequence,
        current_time=current_time,
    )


def test_good_manifest_and_cli(tmp_path, capsys):
    root, manifest, key, signed = make_release(tmp_path)
    assert check(root, manifest, key) == signed
    assert (
        main([
            str(manifest),
            str(root),
            "--public-key",
            public_hex(key),
            "--minimum-sequence",
            "7",
            "--current-time",
            "100",
        ])
        == 0
    )
    assert json.loads(capsys.readouterr().out) == {
        "files": 1, "sequence": 7, "status": "verified", "version": "1.2.3"
    }


@pytest.mark.parametrize("change", ["changed", "added", "missing"])
def test_exact_file_set_and_digests_are_enforced(tmp_path, change):
    root, manifest, key, _ = make_release(tmp_path)
    if change == "changed":
        (root / "bin" / "daia").write_bytes(b"tampered")
    elif change == "added":
        (root / "extra").write_text("unexpected")
    else:
        (root / "bin" / "daia").unlink()
    with pytest.raises(ReleaseIntegrityError, match="file set or digest"):
        check(root, manifest, key)


def test_symlink_escape_is_rejected(tmp_path):
    root, manifest, key, _ = make_release(tmp_path)
    outside = tmp_path / "outside"
    outside.write_text("outside bytes")
    (root / "escape").symlink_to(outside)
    with pytest.raises(ReleaseIntegrityError, match="Symlink"):
        check(root, manifest, key)


@pytest.mark.parametrize(
    ("minimum_sequence", "current_time", "message"),
    [(8, 100, "expected minimum"), (7, 200, "expired")],
)
def test_expiry_and_rollback_are_rejected(tmp_path, minimum_sequence, current_time, message):
    root, manifest, key, _ = make_release(tmp_path)
    with pytest.raises(ReleaseIntegrityError, match=message):
        check(
            root,
            manifest,
            key,
            minimum_sequence=minimum_sequence,
            current_time=current_time,
        )


def test_wrong_key_and_signature_are_rejected(tmp_path):
    root, manifest, key, _ = make_release(tmp_path)
    with pytest.raises(ReleaseIntegrityError, match="signature"):
        check(root, manifest, Ed25519PrivateKey.generate())
    document = json.loads(manifest.read_text())
    document["signature"] = "0" * 128
    manifest.write_text(json.dumps(document))
    with pytest.raises(ReleaseIntegrityError, match="signature"):
        check(root, manifest, key)


def test_duplicate_keys_and_traversal_are_rejected(tmp_path):
    root, manifest, key, signed = make_release(tmp_path)
    manifest.write_text('{"signed":{},"signed":{},"signature":"' + "0" * 128 + '"}')
    with pytest.raises(ReleaseIntegrityError, match="Duplicate JSON key"):
        check(root, manifest, key)

    signed["files"] = {"../outside": "0" * 64}
    manifest.write_text(json.dumps({"signed": signed, "signature": sign(key, signed)}))
    with pytest.raises(ReleaseIntegrityError, match="Unsafe manifest path"):
        check(root, manifest, key)


def test_manifest_must_be_external_and_signed(tmp_path):
    root, manifest, key, signed = make_release(tmp_path)
    inside = root / "manifest.json"
    inside.write_text(manifest.read_text())
    with pytest.raises(ReleaseIntegrityError, match="outside"):
        check(root, inside, key)
    manifest.write_text(json.dumps({"signed": signed}))
    with pytest.raises(ReleaseIntegrityError, match="exactly signed and signature"):
        check(root, manifest, key)
