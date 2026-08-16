#!/usr/bin/env python3
"""Claude Code PreToolUse adapter for the shared public-action gate."""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "shared"))
from gate_core import evaluate_payload  # noqa: E402


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        decision = {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": f"invalid hook JSON: {exc}"}}
        print(json.dumps(decision))
        return 0
    result = evaluate_payload(payload)
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow" if result.allow else "deny",
            "permissionDecisionReason": result.reason,
        }
    }
    print(json.dumps(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
