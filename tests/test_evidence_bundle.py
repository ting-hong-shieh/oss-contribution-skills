from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_evidence_bundle import build  # noqa: E402


class EvidenceBundleTests(unittest.TestCase):
    def test_bundle_is_deterministic_for_same_spec(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = root / "result.txt"
            artifact.write_text("18 passed\n", encoding="utf-8")
            spec = {
                "run_id": "demo",
                "head_sha": "a" * 40,
                "meta": {"commands": ["pytest -q"], "environment": {"python": "3.12"}},
                "artifacts": [
                    {
                        "source_path": str(artifact),
                        "bundle_path": "reports/result.txt",
                        "kind": "test-output",
                        "source": "pytest -q",
                        "produced_by": "pytest",
                        "lane": "focused",
                    }
                ],
            }
            first, digest1 = build(spec, root / "bundle-1")
            second, digest2 = build(spec, root / "bundle-2")
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(digest1, digest2)
            manifest = json.loads(first.read_text(encoding="utf-8"))
            self.assertEqual(manifest["head_sha"], "a" * 40)
            self.assertEqual(manifest["artifacts"][0]["path"], "reports/result.txt")

    def test_rejects_path_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = root / "result.txt"
            artifact.write_text("x", encoding="utf-8")
            spec = {
                "run_id": "demo",
                "head_sha": "a" * 40,
                "meta": {},
                "artifacts": [
                    {
                        "source_path": str(artifact),
                        "bundle_path": "../result.txt",
                    }
                ],
            }
            with self.assertRaises(ValueError):
                build(spec, root / "bundle")

    def test_rejects_symlink_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "target.txt"
            target.write_text("x", encoding="utf-8")
            link = root / "link.txt"
            link.symlink_to(target)
            spec = {
                "run_id": "demo",
                "head_sha": "a" * 40,
                "meta": {},
                "artifacts": [
                    {
                        "source_path": str(link),
                        "bundle_path": "artifacts/link.txt",
                    }
                ],
            }
            with self.assertRaises(ValueError):
                build(spec, root / "bundle")

    def test_rejects_reserved_meta_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec = {
                "run_id": "demo",
                "head_sha": "a" * 40,
                "meta": {"head_sha": "b" * 40},
                "artifacts": [],
            }
            with self.assertRaisesRegex(ValueError, "reserved fields"):
                build(spec, root / "bundle")

    def test_requires_bounded_artifact_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = root / "result.txt"
            artifact.write_text("x", encoding="utf-8")
            spec = {
                "run_id": "demo",
                "head_sha": "a" * 40,
                "meta": {},
                "artifacts": [
                    {
                        "source_path": str(artifact),
                        "bundle_path": "reports/result.txt",
                    }
                ],
            }
            with self.assertRaisesRegex(ValueError, "source must be a non-empty string"):
                build(spec, root / "bundle")

    def test_does_not_record_local_source_path_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = root / "private-home" / "result.txt"
            artifact.parent.mkdir()
            artifact.write_text("x", encoding="utf-8")
            spec = {
                "run_id": "demo",
                "head_sha": "a" * 40,
                "meta": {},
                "artifacts": [
                    {
                        "source_path": str(artifact),
                        "bundle_path": "reports/result.txt",
                        "kind": "report",
                        "source": "focused validation command",
                        "produced_by": "validator",
                    }
                ],
            }
            manifest_path, _ = build(spec, root / "bundle")
            manifest_text = manifest_path.read_text(encoding="utf-8")
            self.assertNotIn(str(artifact), manifest_text)


if __name__ == "__main__":
    unittest.main()
