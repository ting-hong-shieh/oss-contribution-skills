#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "shared"))
from completion_core import check_completion  # noqa: E402

ok, reason = check_completion()
if ok:
    print(json.dumps({"decision": "allow", "reason": reason}))
else:
    print(json.dumps({"decision": "block", "reason": reason}))
