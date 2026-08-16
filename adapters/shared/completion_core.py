#!/usr/bin/env python3
"""Check whether a bounded OSS run recorded enough state to stop safely."""

from __future__ import annotations

import json
import os
from pathlib import Path


def check_completion() -> tuple[bool, str]:
    path_text = os.environ.get("OSS_RUN_RECORD")
    if not path_text:
        return True, "OSS_RUN_RECORD is not configured; completion gate is inactive"
    path = Path(path_text).expanduser()
    if not path.exists():
        return False, f"run record does not exist: {path}"
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return False, f"cannot read run record: {exc}"
    required = ("objective", "starting_state", "ending_state", "material_delta", "next_action")
    missing = [key for key in required if not record.get(key)]
    if missing:
        return False, "run record is missing: " + ", ".join(missing)
    if "public_actions" not in record:
        return False, "run record must explicitly list public_actions, even when empty"
    return True, "bounded run record is complete"
