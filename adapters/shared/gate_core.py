#!/usr/bin/env python3
"""Shared, host-neutral public action gate.

The gate is intentionally conservative. It does not grant GitHub authority; it checks
whether a durable case already grants the exact action and whether action-specific
state is consistent.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


RISKY_GATES = (
    "upstream_instructions_read",
    "local_validation",
    "generated_artifacts_checked",
    "self_review",
    "adversarial_review",
    "claims_verified",
)


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
        if any(token in lower for token in (" -x post", " -x patch", " -x put", " -x delete", "--method post", "--method patch", "--method put", "--method delete", " -f ", " --field ")):
            return "unclassified_mutation"
    if "api.github.com" in lower and any(token in lower for token in ("-x post", "-x patch", "-x put", "-x delete", "--request post", "--request patch", "--request put", "--request delete")):
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


def _lease_valid(case: dict[str, Any], now: dt.datetime | None = None) -> tuple[bool, str]:
    lease = case.get("lease")
    if not lease or not lease.get("required", False):
        return True, "lease not required"
    owner = lease.get("owner")
    expected_owner = os.environ.get("OSS_AGENT_ID")
    if not owner:
        return False, "writer lease is required but no owner is recorded"
    if expected_owner and owner != expected_owner:
        return False, f"lease belongs to {owner!r}, not {expected_owner!r}"
    expires_at = lease.get("expires_at")
    if not expires_at:
        return False, "writer lease has no expiry"
    try:
        expires = dt.datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    except ValueError:
        return False, "writer lease expiry is invalid"
    moment = now or dt.datetime.now(dt.timezone.utc)
    if expires <= moment:
        return False, "writer lease is expired"
    return True, "lease valid"


def evaluate_action(action: str, case: dict[str, Any], cwd: Path | None = None) -> Decision:
    if action == "benign":
        return Decision(True, action, "command is not a classified upstream mutation")
    if action == "unclassified_mutation":
        return Decision(False, action, "mutating GitHub API command is not safely classified; deny by default")

    authority = case.get("authority", {})
    required_authority = action
    if action == "open_ready_pr":
        # Creating a non-draft PR consumes review capacity immediately.
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

    expected_head = case.get("expected_head_sha")
    current_head = _current_head(cwd)
    if expected_head and current_head and not current_head.startswith(expected_head) and not expected_head.startswith(current_head):
        return Decision(False, action, f"current head {current_head} does not match expected {expected_head}")

    gates = case.get("gates", {})
    if action in {"remote_push", "force_push", "open_draft_pr", "open_ready_pr", "ready_transition"}:
        missing = [gate for gate in RISKY_GATES if not gates.get(gate, False)]
        if missing:
            return Decision(False, action, "required gates are incomplete: " + ", ".join(missing))
    if action in {"ready_transition", "open_ready_pr"}:
        ready_gates = ("ci_observed", "review_capacity_checked", "no_unresolved_changes_requested")
        missing = [gate for gate in ready_gates if not gates.get(gate, False)]
        if missing:
            return Decision(False, action, "Ready gates are incomplete: " + ", ".join(missing))
    return Decision(True, action, f"authority and gates permit {action}; {lease_reason}")


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
