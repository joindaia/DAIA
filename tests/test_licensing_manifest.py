"""Synthetic references only. Tests do not clear any real contribution."""
import contextlib
from copy import deepcopy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location(
    "licensing_preview", Path(__file__).resolve().parents[1] / "scripts/check_licensing_manifest.py")
preview = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(preview)


def fixture():
    ref = "ref_" + "a" * 32
    inventory = [{"path": "src/daia/example.py", "sha256": "b" * 64}]
    manifest = {"schema": "daia-rights-preview-v1", "scope": preview.SCOPE,
                "repository_id": preview.REPOSITORY_ID, "source_commit": "c" * 40,
                "agpl_source_commit": "c" * 40,
                "inventory_sha256": preview.inventory_digest(inventory), "licensor_ref": ref,
                "records": [{**inventory[0], "category": "core", "status": "cleared",
                             "rights_map_ref": ref, "grant_ref": ref,
                             "acceptance_ref": ref, "patent_ref": ref}]}
    return manifest, inventory


class LicensingManifestTests(unittest.TestCase):
    def test_structurally_complete_is_not_a_legal_verdict(self):
        self.assertEqual(preview.assess(*fixture()), [])

    def test_every_unresolved_status_blocks(self):
        for status in ("agpl-only", "unverified", "excluded", "third-party", None):
            with self.subTest(status=status):
                m, inventory = fixture()
                m["records"][0]["status"] = status
                self.assertIn("core-not-commercially-cleared", preview.assess(m, inventory))

    def test_each_evidence_reference_is_required(self):
        for key in ("rights_map_ref", "grant_ref", "acceptance_ref", "patent_ref"):
            with self.subTest(key=key):
                m, inventory = fixture()
                m["records"][0][key] = None
                self.assertIn("missing-private-evidence-reference", preview.assess(m, inventory))

    def test_missing_and_additional_artifacts_block(self):
        m, inventory = fixture()
        inventory.append({"path": "tests/example.py", "sha256": "d" * 64})
        m["inventory_sha256"] = preview.inventory_digest(inventory)
        self.assertIn("artifact-inventory-mismatch", preview.assess(m, inventory))
        m, inventory = fixture()
        extra = deepcopy(m["records"][0])
        extra["path"] = "tests/example.py"
        m["records"].append(extra)
        self.assertIn("artifact-inventory-mismatch", preview.assess(m, inventory))

    def test_changed_content_blocks(self):
        m, inventory = fixture()
        m["records"][0]["sha256"] = "f" * 64
        self.assertIn("artifact-inventory-mismatch", preview.assess(m, inventory))

    def test_independently_hashed_file_change_needs_reconciliation(self):
        m, _ = fixture()
        with tempfile.TemporaryDirectory() as directory:
            artifact = Path(directory) / "example.py"
            artifact.write_bytes(b"synthetic artifact")
            def inventory():
                return [{"path": "src/daia/example.py",
                         "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest()}]
            original = inventory()
            m["records"][0].update(original[0])
            # The independent inventory producer binds its own description.
            canonical = json.dumps(original, sort_keys=True, separators=(",", ":"),
                                   ensure_ascii=True).encode()
            m["inventory_sha256"] = hashlib.sha256(canonical).hexdigest()
            self.assertEqual(preview.assess(m, original), [])
            artifact.write_bytes(b"changed after review")
            self.assertIn("artifact-inventory-mismatch", preview.assess(m, inventory()))
            # Stale descriptions cannot detect actual disk changes by themselves.
            self.assertEqual(preview.assess(m, original), [])

    def test_duplicates_block(self):
        m, inventory = fixture()
        m["records"].append(deepcopy(m["records"][0]))
        self.assertIn("duplicate-record-path", preview.assess(m, inventory))
        self.assertIn("duplicate-inventory-path", preview.assess(m, inventory + inventory))

    def test_external_jobs_are_not_core(self):
        m, inventory = fixture()
        m["records"][0]["category"] = "external-job"
        self.assertIn("unexpected-record-category-or-fields", preview.assess(m, inventory))

    def test_private_or_unknown_fields_are_rejected(self):
        m, inventory = fixture()
        m["records"][0]["legal_name"] = "synthetic"
        self.assertIn("unexpected-record-category-or-fields", preview.assess(m, inventory))
        m, inventory = fixture()
        m["active"] = True
        self.assertIn("unexpected-or-missing-manifest-fields", preview.assess(m, inventory))

    def test_identity_scope_and_community_reference(self):
        for key, value, error in (
            ("repository_id", 1, "wrong-repository"),
            ("scope", "all-work", "unsupported-schema-or-scope"),
            ("agpl_source_commit", "d" * 40, "missing-identical-agpl-source-reference"),
            ("licensor_ref", None, "missing-licensor-evidence-reference"),
            ("inventory_sha256", "0" * 64, "inventory-digest-mismatch"),
        ):
            with self.subTest(key=key):
                m, inventory = fixture()
                m[key] = value
                self.assertIn(error, preview.assess(m, inventory))

    def test_third_party_is_not_relicensed(self):
        m, inventory = fixture()
        ref = "ref_" + "e" * 32
        m["records"] = [{**inventory[0], "category": "third-party", "status": "third-party",
                         "rights_map_ref": ref, "license_id": "MIT",
                         "review_ref": ref, "notices_ref": ref}]
        self.assertEqual(preview.assess(m, inventory), [])
        m["records"][0]["status"] = "cleared"
        self.assertIn("third-party-must-retain-own-licence", preview.assess(m, inventory))

    def test_label_syntax_is_not_spdx_membership_or_compatibility(self):
        m, inventory = fixture()
        ref = "ref_" + "e" * 32
        m["records"] = [{**inventory[0], "category": "third-party", "status": "third-party",
                         "rights_map_ref": ref, "license_id": "SyntheticUnverifiedLabel",
                         "review_ref": ref, "notices_ref": ref}]
        self.assertEqual(preview.assess(m, inventory), [])

    def test_empty_malformed_and_private_inputs(self):
        for inventory in ([], None, [{}], [{"path": "../private", "sha256": "b" * 64}]):
            self.assertTrue(preview.assess({}, inventory))
        for path in (".", "C:/absolute", "/absolute", "../parent", "a/../b", "a//b", "a\\b", ".private/a", ".env"):
            self.assertFalse(preview.public_path(path))
        with self.assertRaises(ValueError):
            json.loads('{"a":1,"a":2}', object_pairs_hook=preview.unique_object)

    def test_release_always_fails_closed(self):
        m, inventory = fixture()
        with tempfile.TemporaryDirectory() as directory:
            first, second = Path(directory) / "manifest.json", Path(directory) / "inventory.json"
            first.write_text(json.dumps(m), encoding="utf-8")
            second.write_text(json.dumps(inventory), encoding="utf-8")
            for flag, code in (([], 0), (["--release"], 2)):
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    result = preview.main([str(first), str(second), *flag])
                self.assertEqual(result, code)
                self.assertIs(json.loads(output.getvalue())["commercial_release_authorized"], False)
            first.write_text('{"a":1,"a":2}', encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(preview.main([str(first), str(second)]), 1)


if __name__ == "__main__":
    unittest.main()
