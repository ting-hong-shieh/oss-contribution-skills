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
    required = (
        "objective",
        "starting_state",
        "ending_state",
        "head_sha",
        "material_delta",
        "execution_mode",
        "trust_boundary",
        "next_action",
    )
    missing = [key for key in required if not record.get(key)]
    if missing:
        return False, "run record is missing: " + ", ".join(missing)
    for list_key in ("evidence_added", "files_changed", "public_actions"):
        if list_key not in record or not isinstance(record[list_key], list):
            return False, f"run record must explicitly list {list_key}, even when empty"
    if record["execution_mode"] == "STATIC_ONLY" and record.get("runtime_validated"):
        return False, "STATIC_ONLY run cannot claim runtime validation"
    return True, "bounded run record is complete"
