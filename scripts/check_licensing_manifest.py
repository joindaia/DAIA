"""Offline draft-manifest consistency check, never a legal clearance service.

The inventory must come independently from the exact built release, not be copied
from the manifest. References need authenticated private evidence and legal review.
The scope identifier names this preview schema; it does not activate the supplied
commercial programme or any agreement. Licence labels are syntax-checked, not SPDX-validated.
Even success cannot authorize an alternative licence; --release always fails closed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys

REPOSITORY_ID = 1367256015
SCOPE = "daia-core-v2"
REF = re.compile(r"ref_[0-9a-f]{32}\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
COMMIT = re.compile(r"[0-9a-f]{40}\Z")
TOP = {"schema", "scope", "repository_id", "source_commit", "agpl_source_commit",
       "inventory_sha256", "licensor_ref", "records"}
COMMON = {"path", "sha256", "category", "status", "rights_map_ref"}
CORE = COMMON | {"grant_ref", "acceptance_ref", "patent_ref"}
THIRD_PARTY = COMMON | {"license_id", "review_ref", "notices_ref"}


def exact_keys(value: object, keys: set[str]) -> bool:
    return isinstance(value, dict) and set(value) == keys


def matches(pattern: re.Pattern[str], value: object) -> bool:
    return isinstance(value, str) and pattern.fullmatch(value) is not None


def public_path(value: object) -> bool:
    if not isinstance(value, str) or not value or len(value) > 512:
        return False
    if any(ord(c) < 32 for c in value) or "\\" in value or "@" in value or ":" in value:
        return False
    path = PurePosixPath(value)
    if not path.parts or path.is_absolute() or str(path) != value or ".." in path.parts:
        return False
    private = {".private", ".runtime", ".git", ".env", "__pycache__"}
    return not (private & set(path.parts))


def inventory_digest(inventory: list[dict[str, str]]) -> str:
    canonical = json.dumps(sorted(inventory, key=lambda row: row["path"]),
                           sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def assess(manifest: object, inventory: object) -> list[str]:
    """Return safe diagnostics. Do not echo untrusted fields or private evidence."""
    errors: list[str] = []
    if not isinstance(inventory, list) or not inventory or len(inventory) > 100000:
        return ["invalid-or-empty-inventory"]
    expected: dict[str, str] = {}
    for row in inventory:
        if (not exact_keys(row, {"path", "sha256"})
                or not public_path(row.get("path"))
                or not matches(SHA256, row.get("sha256"))):
            return ["invalid-inventory-entry"]
        if row["path"] in expected:
            return ["duplicate-inventory-path"]
        expected[row["path"]] = row["sha256"]
    if not exact_keys(manifest, TOP):
        return ["unexpected-or-missing-manifest-fields"]
    if manifest["schema"] != "daia-rights-preview-v1" or manifest["scope"] != SCOPE:
        errors.append("unsupported-schema-or-scope")
    if type(manifest["repository_id"]) is not int or manifest["repository_id"] != REPOSITORY_ID:
        errors.append("wrong-repository")
    if (not matches(COMMIT, manifest["source_commit"])
            or manifest["agpl_source_commit"] != manifest["source_commit"]):
        errors.append("missing-identical-agpl-source-reference")
    if manifest["inventory_sha256"] != inventory_digest(inventory):
        errors.append("inventory-digest-mismatch")
    if not matches(REF, manifest["licensor_ref"]):
        errors.append("missing-licensor-evidence-reference")
    records = manifest["records"]
    if not isinstance(records, list) or not records or len(records) > 100000:
        return errors + ["invalid-or-empty-records"]
    observed: dict[str, str] = {}
    for row in records:
        if not isinstance(row, dict):
            errors.append("invalid-record")
            continue
        category = row.get("category")
        fields = CORE if category == "core" else THIRD_PARTY
        if category not in ("core", "third-party") or not exact_keys(row, fields):
            errors.append("unexpected-record-category-or-fields")
            continue
        if not public_path(row["path"]) or not matches(SHA256, row["sha256"]):
            errors.append("invalid-artifact-reference")
            continue
        if row["path"] in observed:
            errors.append("duplicate-record-path")
        observed[row["path"]] = row["sha256"]
        refs = ("rights_map_ref", "grant_ref", "acceptance_ref", "patent_ref") if category == "core" else (
            "rights_map_ref", "review_ref", "notices_ref")
        if any(not matches(REF, row[key]) for key in refs):
            errors.append("missing-private-evidence-reference")
        if category == "core" and row["status"] != "cleared":
            errors.append("core-not-commercially-cleared")
        if category == "third-party":
            if row["status"] != "third-party":
                errors.append("third-party-must-retain-own-licence")
            if (not isinstance(row["license_id"], str)
                    or re.fullmatch(r"[A-Za-z0-9.+-]{1,80}", row["license_id"]) is None):
                errors.append("invalid-third-party-licence-id")
    if observed != expected:
        errors.append("artifact-inventory-mismatch")
    return sorted(set(errors))


def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def load(path: str) -> object:
    source = Path(path)
    if source.stat().st_size > 20_000_000:
        raise ValueError("input too large")
    return json.loads(source.read_text(encoding="utf-8"), object_pairs_hook=unique_object)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest")
    parser.add_argument("inventory")
    parser.add_argument("--release", action="store_true",
                        help="Fail closed: production clearance is not implemented")
    args = parser.parse_args(argv)
    try:
        errors = assess(load(args.manifest), load(args.inventory))
    except (OSError, ValueError, TypeError, RecursionError):
        errors = ["input-unreadable-or-invalid"]
    print(json.dumps({"manifest_consistent": not errors,
                      "commercial_release_authorized": False,
                      "authority": "draft-preview-only", "errors": errors}, sort_keys=True))
    return 2 if args.release else (1 if errors else 0)


if __name__ == "__main__":
    sys.exit(main())
