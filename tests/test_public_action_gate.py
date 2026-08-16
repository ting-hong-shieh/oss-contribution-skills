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
from gate_core import classify_command, evaluate_action, evaluate_payload  # noqa: E402


HEAD = "a" * 40
OTHER_HEAD = "b" * 40
MANIFEST_SHA = "c" * 64


def base_case() -> dict:
    return {
        "case_id": "demo-1",
        "repo": "org/repo",
        "expected_head_sha": HEAD,
        "risk": "LOW",
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
            "trust_boundary_checked": True,
            "upstream_instructions_read": True,
            "local_validation": True,
            "generated_artifacts_checked": True,
            "self_review": True,
            "adversarial_review": True,
            "claims_verified": True,
            "evidence_bundle_verified": True,
            "ci_observed": False,
            "review_capacity_checked": False,
            "no_unresolved_changes_requested": False,
        },
        "execution": {
            "trust": "TRUSTED_OWN_BRANCH",
            "mode": "HOST_LOCAL",
            "audited_head_sha": HEAD,
            "network_policy": "HOST_DEFAULT",
            "credentials_present": False,
            "lifecycle_scripts": "NOT_APPLICABLE",
        },
        "evidence": {
            "state": "CURRENT",
            "head_sha": HEAD,
            "manifest_path": ".oss-control/evidence/demo/manifest.json",
            "manifest_sha256": MANIFEST_SHA,
            "artifacts": 1,
            "manually_inspected": True,
            "limitations": [],
        },
        "verification": {
            "required": False,
            "state": "NOT_REQUIRED",
            "creator": "claude-code:a",
            "verifier": None,
            "verified_head_sha": None,
            "completed_at": None,
            "findings": [],
        },
        "run_provenance": {
            "participation": "AI_ASSISTED",
            "provider": "example",
            "model": "example-model",
            "client": "test",
            "skill_revision": "test",
            "recorded_at": "2026-08-17T00:00:00Z",
        },
        "shared_levers": [],
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

    def test_draft_pr_allowed_with_gates_and_evidence(self) -> None:
        result = evaluate_action("open_draft_pr", base_case())
        self.assertTrue(result.allow)

    def test_stale_evidence_denies_draft_publication(self) -> None:
        case = base_case()
        case["evidence"]["head_sha"] = OTHER_HEAD
        result = evaluate_action("open_draft_pr", case)
        self.assertFalse(result.allow)
        self.assertIn("evidence head", result.reason)

    def test_ready_denied_without_ready_authority(self) -> None:
        result = evaluate_action("ready_transition", base_case())
        self.assertFalse(result.allow)
        self.assertIn("authority", result.reason)

    def test_ready_denied_when_capacity_saturated(self) -> None:
        case = base_case()
        case["authority"]["ready_transition"] = True
        case["traffic"] = {"state": "YELLOW", "ready_slots_available": False}
        case["gates"].update(
            {
                "ci_observed": True,
                "review_capacity_checked": True,
                "no_unresolved_changes_requested": True,
            }
        )
        result = evaluate_action("ready_transition", case)
        self.assertFalse(result.allow)
        self.assertIn("GREEN", result.reason)

    def test_required_verification_must_be_independent(self) -> None:
        case = base_case()
        case["authority"]["ready_transition"] = True
        case["gates"].update(
            {
                "ci_observed": True,
                "review_capacity_checked": True,
                "no_unresolved_changes_requested": True,
            }
        )
        case["verification"] = {
            "required": True,
            "state": "PASSED",
            "creator": "claude-code:same",
            "verifier": "claude-code:same",
            "verified_head_sha": HEAD,
            "completed_at": "2026-08-17T00:10:00Z",
            "findings": [],
        }
        result = evaluate_action("ready_transition", case)
        self.assertFalse(result.allow)
        self.assertIn("cannot independently verify", result.reason)

    def test_required_verification_at_current_head_allows_ready(self) -> None:
        case = base_case()
        case["authority"]["ready_transition"] = True
        case["gates"].update(
            {
                "ci_observed": True,
                "review_capacity_checked": True,
                "no_unresolved_changes_requested": True,
            }
        )
        case["verification"] = {
            "required": True,
            "state": "PASSED",
            "creator": "claude-code:a",
            "verifier": "codex:b",
            "verified_head_sha": HEAD,
            "completed_at": "2026-08-17T00:10:00Z",
            "findings": ["no blocking findings"],
        }
        result = evaluate_action("ready_transition", case)
        self.assertTrue(result.allow)

    def test_untrusted_pr_head_cannot_run_in_control_checkout(self) -> None:
        case = base_case()
        case["execution"].update(
            {
                "trust": "UNTRUSTED_PR_HEAD",
                "mode": "HOST_LOCAL",
                "credentials_present": True,
            }
        )
        result = evaluate_action("open_draft_pr", case)
        self.assertFalse(result.allow)
        self.assertIn("untrusted PR head", result.reason)

    def test_shared_lever_must_be_held_by_current_agent(self) -> None:
        case = base_case()
        case["shared_levers"] = [
            {
                "id": "remote-branch",
                "kind": "REMOTE_BRANCH",
                "required_for": ["remote_push"],
                "state": "HELD",
                "owner": "claude-code:a",
                "acquired_at": "2026-08-17T00:00:00Z",
                "expires_at": "2099-08-17T01:00:00Z",
            }
        ]
        with mock.patch.dict(os.environ, {"OSS_AGENT_ID": "codex:b"}, clear=True):
            result = evaluate_action("remote_push", case)
        self.assertFalse(result.allow)
        self.assertIn("shared lever", result.reason)

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
            root = Path(tmp)
            manifest = root / "manifest.json"
            manifest_bytes = (json.dumps({"head_sha": HEAD}, sort_keys=True) + "\n").encode("utf-8")
            manifest.write_bytes(manifest_bytes)
            import hashlib
            case["evidence"]["manifest_path"] = "manifest.json"
            case["evidence"]["manifest_sha256"] = hashlib.sha256(manifest_bytes).hexdigest()
            path = root / "case.json"
            path.write_text(json.dumps(case), encoding="utf-8")
            with mock.patch.dict(os.environ, {"OSS_CASE_FILE": str(path)}, clear=True):
                result = evaluate_payload({"tool_input": {"command": "gh pr create --draft"}}, root)
        self.assertTrue(result.allow, result.reason)


if __name__ == "__main__":
    unittest.main()
