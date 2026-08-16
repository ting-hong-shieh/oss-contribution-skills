from __future__ import annotations

import datetime as dt
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "adapters/shared"))
from gate_core import classify_command, evaluate_action, evaluate_payload  # noqa: E402


def base_case() -> dict:
    return {
        "case_id": "demo-1",
        "repo": "org/repo",
        "expected_head_sha": None,
        "work_state": "CLAIMS_VERIFIED",
        "upstream_state": "NOT_OPENED",
        "queue_state": "ACTIVE_LOCAL",
        "authority": {
            "read": True,
            "local_write": True,
            "remote_push": True,
            "open_draft_pr": True,
            "public_speech": False,
            "ready_transition": False,
            "force_push": False,
            "close_or_merge": False,
        },
        "traffic": {"state": "GREEN", "ready_slots_available": True},
        "gates": {
            "upstream_instructions_read": True,
            "local_validation": True,
            "generated_artifacts_checked": True,
            "self_review": True,
            "adversarial_review": True,
            "claims_verified": True,
            "ci_observed": False,
            "review_capacity_checked": False,
            "no_unresolved_changes_requested": False,
        },
        "lease": None,
        "next_action": "open draft",
    }


class GateTests(unittest.TestCase):
    def test_benign_command_is_allowed_without_case(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            result = evaluate_payload({"tool_input": {"command": "pytest -q"}}, Path("/tmp"))
        self.assertTrue(result.allow)

    def test_push_without_case_is_denied(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            result = evaluate_payload({"tool_input": {"command": "git push origin feature"}}, Path("/tmp"))
        self.assertFalse(result.allow)
        self.assertIn("no durable", result.reason)

    def test_draft_pr_allowed_with_gates(self) -> None:
        result = evaluate_action("open_draft_pr", base_case())
        self.assertTrue(result.allow)

    def test_ready_denied_without_ready_authority(self) -> None:
        result = evaluate_action("ready_transition", base_case())
        self.assertFalse(result.allow)
        self.assertIn("authority", result.reason)

    def test_ready_denied_when_capacity_saturated(self) -> None:
        case = base_case()
        case["authority"]["ready_transition"] = True
        case["traffic"] = {"state": "YELLOW", "ready_slots_available": False}
        case["gates"].update({"ci_observed": True, "review_capacity_checked": True, "no_unresolved_changes_requested": True})
        result = evaluate_action("ready_transition", case)
        self.assertFalse(result.allow)
        self.assertIn("GREEN", result.reason)

    def test_public_comment_denied_without_speech_authority(self) -> None:
        result = evaluate_action("public_speech", base_case())
        self.assertFalse(result.allow)

    def test_force_push_is_separate_authority(self) -> None:
        self.assertEqual(classify_command("git push --force-with-lease origin feature"), "force_push")
        result = evaluate_action("force_push", base_case())
        self.assertFalse(result.allow)

    def test_case_file_round_trip(self) -> None:
        case = base_case()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "case.json"
            path.write_text(json.dumps(case), encoding="utf-8")
            with mock.patch.dict(os.environ, {"OSS_CASE_FILE": str(path)}, clear=True):
                result = evaluate_payload({"tool_input": {"command": "gh pr create --draft"}}, Path(tmp))
        self.assertTrue(result.allow)


if __name__ == "__main__":
    unittest.main()
