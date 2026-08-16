#!/usr/bin/env python3
"""Shared, host-neutral public action gate.

The gate is intentionally conservative. It does not grant GitHub authority; it checks
whether a durable case already grants the exact action and whether action-specific
state, evidence, verification, leases, and shared levers are consistent.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


RISKY_GATES = (
    "trust_boundary_checked",
    "upstream_instructions_read",
    "local_validation",
    "generated_artifacts_checked",
    "self_review",
    "adversarial_review",
    "claims_verified",
    "evidence_bundle_verified",
)

PUBLISH_ACTIONS = {"open_draft_pr", "open_ready_pr", "ready_transition"}
HEAD_BOUND_ACTIONS = {
    "remote_push",
    "force_push",
    "open_draft_pr",
    "open_ready_pr",
    "ready_transition",
}


@dataclass(frozen=True)
class Decision:
    allow: bool
    action: str
    reason: str


def _flatten_command(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(_flatten_command(item) for item in value)
    if isinstance(value, dict):
        for key in ("command", "cmd", "script", "shell_command"):
            if key in value:
                return _flatten_command(value[key])
    return ""


def extract_command(payload: dict[str, Any]) -> str:
    """Extract a shell command from Claude/Codex-shaped hook payloads."""
    candidates = [
        payload.get("tool_input"),
        payload.get("input"),
        payload.get("arguments"),
        payload.get("command"),
    ]
    for candidate in candidates:
        command = _flatten_command(candidate)
        if command:
            return command.strip()
    return ""


def classify_command(command: str) -> str:
    """Classify a command into one authority class or benign."""
    normalized = " ".join(command.strip().split())
    lower = normalized.lower()

    if not normalized:
        return "benign"
    if re.search(r"(^|[;&|]\s*)git\s+push\b", lower):
        if "--force" in lower or " -f" in lower:
            return "force_push"
        return "remote_push"
    if re.search(r"(^|[;&|]\s*)gh\s+pr\s+create\b", lower):
        return "open_draft_pr" if "--draft" in lower else "open_ready_pr"
    if re.search(r"(^|[;&|]\s*)gh\s+pr\s+ready\b", lower):
        return "ready_transition"
    if re.search(r"(^|[;&|]\s*)gh\s+(pr|issue)\s+(comment|review)\b", lower):
        return "public_speech"
    if re.search(r"(^|[;&|]\s*)gh\s+pr\s+(close|merge)\b", lower):
        return "close_or_merge"
    if re.search(r"(^|[;&|]\s*)gh\s+issue\s+close\b", lower):
        return "close_or_merge"
    if re.search(r"(^|[;&|]\s*)gh\s+pr\s+edit\b", lower):
        return "public_speech"
    if re.search(r"(^|[;&|]\s*)gh\s+issue\s+edit\b", lower):
        return "public_speech"
    if re.search(r"(^|[;&|]\s*)gh\s+api\b", lower):
        mutating = (
            " -x post",
            " -x patch",
            " -x put",
            " -x delete",
            "--method post",
            "--method patch",
            "--method put",
            "--method delete",
            " -f ",
            " --field ",
        )
        if any(token in lower for token in mutating):
            return "unclassified_mutation"
    if "api.github.com" in lower and any(
        token in lower
        for token in (
            "-x post",
            "-x patch",
            "-x put",
            "-x delete",
            "--request post",
            "--request patch",
            "--request put",
            "--request delete",
        )
    ):
        return "unclassified_mutation"
    return "benign"


def discover_case_file(start: Path | None = None) -> Path | None:
    explicit = os.environ.get("OSS_CASE_FILE")
    if explicit:
        return Path(explicit).expanduser().resolve()
    current = (start or Path.cwd()).resolve()
    for directory in (current, *current.parents):
        candidate = directory / ".oss-control" / "current-case.json"
        if candidate.exists():
            return candidate
    return None


def load_case(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _current_head(cwd: Path | None = None) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    head = result.stdout.strip()
    return head if result.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}", head) else None


def _heads_match(left: str | None, right: str | None) -> bool:
    if not left or not right:
        return False
    return left.startswith(right) or right.startswith(left)


def _parse_expiry(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _lease_valid(case: dict[str, Any], now: dt.datetime | None = None) -> tuple[bool, str]:
    lease = case.get("lease")
    if not lease or not lease.get("required", False):
        return True, "writer lease not required"
    owner = lease.get("owner")
    expected_owner = os.environ.get("OSS_AGENT_ID")
    if not owner:
        return False, "writer lease is required but no owner is recorded"
    if expected_owner and owner != expected_owner:
        return False, f"writer lease belongs to {owner!r}, not {expected_owner!r}"
    expires = _parse_expiry(lease.get("expires_at"))
    if expires is None:
        return False, "writer lease expiry is missing or invalid"
    moment = now or dt.datetime.now(dt.timezone.utc)
    if expires <= moment:
        return False, "writer lease is expired"
    return True, "writer lease valid"


def _shared_levers_valid(
    action: str, case: dict[str, Any], now: dt.datetime | None = None
) -> tuple[bool, str]:
    required = [
        lever
        for lever in case.get("shared_levers", [])
        if action in lever.get("required_for", [])
    ]
    if not required:
        return True, "no shared lever required"
    expected_owner = os.environ.get("OSS_AGENT_ID")
    moment = now or dt.datetime.now(dt.timezone.utc)
    for lever in required:
        lever_id = lever.get("id", "<unnamed>")
        if lever.get("state") != "HELD":
            return False, f"shared lever {lever_id!r} is not HELD"
        owner = lever.get("owner")
        if not owner:
            return False, f"shared lever {lever_id!r} has no owner"
        if expected_owner and owner != expected_owner:
            return False, f"shared lever {lever_id!r} belongs to {owner!r}, not {expected_owner!r}"
        expires = _parse_expiry(lever.get("expires_at"))
        if expires is None or expires <= moment:
            return False, f"shared lever {lever_id!r} is expired or has invalid expiry"
    return True, "required shared levers valid"


def _execution_boundary_valid(case: dict[str, Any]) -> tuple[bool, str]:
    execution = case.get("execution", {})
    trust = execution.get("trust")
    mode = execution.get("mode")
    if not trust or not mode:
        return False, "execution trust boundary is not recorded"
    if trust == "UNTRUSTED_PR_HEAD":
        if mode not in {"DISPOSABLE_SANDBOX", "STATIC_ONLY"}:
            return False, "untrusted PR head must use a disposable sandbox or STATIC_ONLY review"
        if execution.get("credentials_present", True):
            return False, "untrusted PR execution record indicates credentials were present"
        if mode == "DISPOSABLE_SANDBOX" and execution.get("network_policy") not in {
            "DENY_BY_DEFAULT",
            "ALLOWLISTED",
        }:
            return False, "untrusted PR sandbox must deny network by default or use an allowlist"
    return True, "execution trust boundary recorded"


def _evidence_valid(
    case: dict[str, Any],
    expected_head: str | None,
    current_head: str | None,
    cwd: Path | None = None,
) -> tuple[bool, str]:
    evidence = case.get("evidence", {})
    if evidence.get("state") != "CURRENT":
        return False, f"evidence state is {evidence.get('state')!r}, not CURRENT"
    evidence_head = evidence.get("head_sha")
    reference = current_head or expected_head
    if not _heads_match(evidence_head, reference):
        return False, "evidence head does not match the expected/current head"
    if not evidence.get("manually_inspected", False):
        return False, "evidence artifacts were not manually inspected"
    manifest_path = evidence.get("manifest_path")
    manifest_sha = evidence.get("manifest_sha256")
    if not manifest_path or not manifest_sha:
        return False, "evidence bundle manifest identity is incomplete"
    if cwd is not None:
        path = Path(manifest_path).expanduser()
        if not path.is_absolute():
            path = (cwd / path).resolve()
        if not path.exists() or not path.is_file() or path.is_symlink():
            return False, f"evidence manifest is missing or unsafe: {path}"
        data = path.read_bytes()
        actual_sha = hashlib.sha256(data).hexdigest()
        if actual_sha != manifest_sha:
            return False, "evidence manifest SHA-256 does not match the durable case"
        try:
            manifest = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            return False, f"evidence manifest is malformed: {exc}"
        if not isinstance(manifest, dict) or not _heads_match(manifest.get("head_sha"), reference):
            return False, "evidence manifest head does not match the expected/current head"
    return True, "current-head evidence bundle is valid"


def _verification_valid(
    case: dict[str, Any], expected_head: str | None, current_head: str | None
) -> tuple[bool, str]:
    verification = case.get("verification", {})
    if not verification.get("required", False):
        if verification.get("state") not in {"NOT_REQUIRED", None}:
            return False, "verification is not required but its state is inconsistent"
        return True, "independent verification not required"
    if verification.get("state") != "PASSED":
        return False, f"required independent verification is {verification.get('state')!r}, not PASSED"
    creator = verification.get("creator")
    verifier = verification.get("verifier")
    if not creator or not verifier:
        return False, "required independent verification lacks creator or verifier identity"
    if creator == verifier:
        return False, "creator cannot independently verify the same contribution"
    reference = current_head or expected_head
    if not _heads_match(verification.get("verified_head_sha"), reference):
        return False, "independent verification is not bound to the expected/current head"
    return True, "required independent verification passed"


def evaluate_action(action: str, case: dict[str, Any], cwd: Path | None = None) -> Decision:
    if action == "benign":
        return Decision(True, action, "command is not a classified upstream mutation")
    if action == "unclassified_mutation":
        return Decision(False, action, "mutating GitHub API command is not safely classified; deny by default")

    authority = case.get("authority", {})
    required_authority = action
    if action == "open_ready_pr":
        if not authority.get("open_draft_pr") or not authority.get("ready_transition"):
            return Decision(False, action, "opening a ready PR requires both open_draft_pr and ready_transition authority")
    elif not authority.get(required_authority, False):
        return Decision(False, action, f"case does not grant {required_authority} authority")

    traffic = case.get("traffic", {})
    traffic_state = traffic.get("state")
    if traffic_state == "RED":
        return Decision(False, action, "repository traffic is RED")
    if action in {"ready_transition", "open_ready_pr"}:
        if traffic_state != "GREEN" or not traffic.get("ready_slots_available", False):
            return Decision(False, action, "Ready action requires GREEN traffic and an available review slot")

    valid, lease_reason = _lease_valid(case)
    if not valid:
        return Decision(False, action, lease_reason)

    valid, lever_reason = _shared_levers_valid(action, case)
    if not valid:
        return Decision(False, action, lever_reason)

    expected_head = case.get("expected_head_sha")
    current_head = _current_head(cwd)
    if expected_head and current_head and not _heads_match(current_head, expected_head):
        return Decision(False, action, f"current head {current_head} does not match expected {expected_head}")

    gates = case.get("gates", {})
    if action in HEAD_BOUND_ACTIONS:
        missing = [gate for gate in RISKY_GATES if not gates.get(gate, False)]
        if missing:
            return Decision(False, action, "required gates are incomplete: " + ", ".join(missing))

        valid, boundary_reason = _execution_boundary_valid(case)
        if not valid:
            return Decision(False, action, boundary_reason)

        valid, evidence_reason = _evidence_valid(case, expected_head, current_head, cwd)
        if not valid:
            return Decision(False, action, evidence_reason)

    if action in {"ready_transition", "open_ready_pr"}:
        ready_gates = ("ci_observed", "review_capacity_checked", "no_unresolved_changes_requested")
        missing = [gate for gate in ready_gates if not gates.get(gate, False)]
        if missing:
            return Decision(False, action, "Ready gates are incomplete: " + ", ".join(missing))
        valid, verification_reason = _verification_valid(case, expected_head, current_head)
        if not valid:
            return Decision(False, action, verification_reason)
    else:
        verification_reason = "verification not required for this action"

    reasons = [lease_reason, lever_reason]
    if action in HEAD_BOUND_ACTIONS:
        reasons.append("current-head evidence valid")
    if action in {"ready_transition", "open_ready_pr"}:
        reasons.append(verification_reason)
    return Decision(True, action, f"authority and gates permit {action}; " + "; ".join(reasons))


def evaluate_payload(payload: dict[str, Any], cwd: Path | None = None) -> Decision:
    command = extract_command(payload)
    action = classify_command(command)
    if action == "benign":
        return Decision(True, action, "command is not a classified upstream mutation")
    case_path = discover_case_file(cwd)
    if case_path is None or not case_path.exists():
        return Decision(False, action, "no durable OSS case file was found")
    try:
        case = load_case(case_path)
    except (OSError, json.JSONDecodeError) as exc:
        return Decision(False, action, f"cannot load durable case: {exc}")
    return evaluate_action(action, case, cwd)
