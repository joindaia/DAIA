"""Offline verification of an operator-signed, exact-file release manifest."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import sys
from typing import Sequence

from .crypto import MAX_SAFE_INTEGER, strict_json, verify

MANIFEST_KIND = "daia-release-manifest-v1"


class ReleaseIntegrityError(ValueError):
    """The release or its signed manifest failed integrity verification."""


def _fail(message: str) -> None:
    raise ReleaseIntegrityError(message)


def _safe_path(value: object) -> bool:
    if not isinstance(value, str) or not value or not value.isascii() or "\\" in value:
        return False
    path = PurePosixPath(value)
    return (
        not path.is_absolute()
        and not PureWindowsPath(value).drive
        and value == path.as_posix()
        and all(part not in {"", ".", ".."} for part in path.parts)
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
        with os.fdopen(descriptor, "rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        _fail(f"Cannot read release file: {path.name}: {exc.strerror or exc}")
    return digest.hexdigest()


def _release_files(root: Path) -> dict[str, str]:
    files: dict[str, str] = {}

    def visit(directory: Path, prefix: str = "") -> None:
        try:
            with os.scandir(directory) as iterator:
                entries = sorted(iterator, key=lambda entry: entry.name)
        except OSError as exc:
            _fail(f"Cannot inspect release directory: {exc.strerror or exc}")
        for entry in entries:
            relative = f"{prefix}/{entry.name}" if prefix else entry.name
            if not _safe_path(relative):
                _fail(f"Unsafe release path: {relative!r}")
            try:
                if entry.is_symlink():
                    _fail(f"Symlink in release root: {relative}")
                if entry.is_dir(follow_symlinks=False):
                    visit(Path(entry.path), relative)
                elif entry.is_file(follow_symlinks=False):
                    files[relative] = _sha256_file(Path(entry.path))
                else:
                    _fail(f"Non-regular entry in release root: {relative}")
            except OSError as exc:
                _fail(f"Cannot inspect release entry {relative}: {exc.strerror or exc}")

    visit(root)
    return files


def _validate_signed(value: object, minimum_sequence: int, current_time: int) -> dict:
    if type(minimum_sequence) is not int or not 0 <= minimum_sequence <= MAX_SAFE_INTEGER:
        _fail("Minimum sequence must be a non-negative safe integer")
    if type(current_time) is not int or not 0 <= current_time <= MAX_SAFE_INTEGER:
        _fail("Current time must be a non-negative Unix timestamp")
    if not isinstance(value, dict) or set(value) != {
        "kind", "version", "sequence", "expires", "files"
    }:
        _fail("Invalid signed manifest schema")
    if value["kind"] != MANIFEST_KIND:
        _fail("Unsupported manifest kind")
    if (
        not isinstance(value["version"], str)
        or not value["version"]
        or not value["version"].isascii()
    ):
        _fail("Invalid release version")
    if type(value["sequence"]) is not int or not 0 <= value["sequence"] <= MAX_SAFE_INTEGER:
        _fail("Invalid release sequence")
    if type(value["expires"]) is not int or not 0 <= value["expires"] <= MAX_SAFE_INTEGER:
        _fail("Invalid manifest expiry")
    if value["sequence"] < minimum_sequence:
        _fail("Release sequence is below the expected minimum")
    if value["expires"] <= current_time:
        _fail("Release manifest has expired")
    files = value["files"]
    if not isinstance(files, dict):
        _fail("Manifest files must be an object")
    for path, digest in files.items():
        if not _safe_path(path):
            _fail(f"Unsafe manifest path: {path!r}")
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or digest != digest.lower()
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            _fail(f"Invalid SHA256 digest for {path}")
    return value


def verify_release(
    manifest_path: str | Path,
    *,
    public_key: str,
    release_root: str | Path,
    minimum_sequence: int,
    current_time: int,
) -> dict:
    """Verify a manifest and exact release tree; return the authenticated payload."""
    manifest_input, root_input = Path(manifest_path), Path(release_root)
    if manifest_input.is_symlink() or root_input.is_symlink():
        _fail("Manifest and release root must not be symlinks")
    try:
        manifest = manifest_input.resolve(strict=True)
        root = root_input.resolve(strict=True)
    except OSError as exc:
        _fail(f"Manifest or release root is unavailable: {exc.strerror or exc}")
    if not manifest.is_file() or not root.is_dir():
        _fail("Manifest must be a file and release root must be a directory")
    if manifest == root or root in manifest.parents:
        _fail("Manifest must be outside the verified release root")
    try:
        document = strict_json(manifest.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError, TypeError, RecursionError) as exc:
        _fail(f"Invalid manifest JSON: {exc}")
    if not isinstance(document, dict) or set(document) != {"signed", "signature"}:
        _fail("Manifest must contain exactly signed and signature")
    if not isinstance(document["signature"], str) or not verify(
        public_key, document["signed"], document["signature"]
    ):
        _fail("Invalid manifest signature")
    signed = _validate_signed(document["signed"], minimum_sequence, current_time)
    if _release_files(root) != signed["files"]:
        _fail("Release file set or digest does not match the signed manifest")
    return signed


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", help="signed manifest outside the release root")
    parser.add_argument("release_root", help="directory whose exact file set is verified")
    parser.add_argument("--public-key", required=True, help="pinned Ed25519 public key (hex)")
    parser.add_argument("--minimum-sequence", required=True, type=int)
    parser.add_argument("--current-time", required=True, type=int, help="Unix timestamp")
    args = parser.parse_args(argv)
    try:
        signed = verify_release(
            args.manifest,
            public_key=args.public_key,
            release_root=args.release_root,
            minimum_sequence=args.minimum_sequence,
            current_time=args.current_time,
        )
    except ReleaseIntegrityError as exc:
        print(f"release verification failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({
        "status": "verified",
        "version": signed["version"],
        "sequence": signed["sequence"],
        "files": len(signed["files"]),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
