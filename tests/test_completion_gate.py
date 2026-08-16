from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "adapters/shared"))
from completion_core import check_completion  # noqa: E402


class CompletionGateTests(unittest.TestCase):
    def test_static_only_cannot_claim_runtime_validation(self) -> None:
        record = {
            "objective": "review an external pull request",
            "starting_state": "IN_REVIEW",
            "ending_state": "RESPONSE_READY",
            "head_sha": "a" * 40,
            "material_delta": "completed static review",
            "execution_mode": "STATIC_ONLY",
            "trust_boundary": "untrusted head; sandbox unavailable",
            "runtime_validated": True,
            "evidence_added": [],
            "files_changed": [],
            "public_actions": [],
            "next_action": "report execution blocker",
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "run.json"
            path.write_text(json.dumps(record), encoding="utf-8")
            with mock.patch.dict(os.environ, {"OSS_RUN_RECORD": str(path)}, clear=True):
                ok, reason = check_completion()
        self.assertFalse(ok)
        self.assertIn("STATIC_ONLY", reason)

    def test_bounded_run_record_passes(self) -> None:
        record = {
            "objective": "prepare a draft",
            "starting_state": "LOCAL_VALIDATED",
            "ending_state": "DRAFT_READY",
            "head_sha": "a" * 40,
            "material_delta": "built evidence bundle and narrowed claims",
            "execution_mode": "HOST_LOCAL",
            "trust_boundary": "trusted own branch",
            "runtime_validated": True,
            "evidence_added": ["manifest.json"],
            "files_changed": ["src/example.py"],
            "public_actions": [],
            "next_action": "request draft publication authority",
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "run.json"
            path.write_text(json.dumps(record), encoding="utf-8")
            with mock.patch.dict(os.environ, {"OSS_RUN_RECORD": str(path)}, clear=True):
                ok, reason = check_completion()
        self.assertTrue(ok, reason)


if __name__ == "__main__":
    unittest.main()
