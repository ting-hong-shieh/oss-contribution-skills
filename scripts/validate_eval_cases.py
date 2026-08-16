#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "evals/schema/case.schema.json").read_text(encoding="utf-8"))


def main() -> int:
    errors: list[str] = []
    ids: set[str] = set()
    files = sorted((ROOT / "evals/cases").glob("*.yaml"))
    if len(files) < 8:
        errors.append(f"expected at least 8 eval cases, found {len(files)}")
    for path in files:
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            jsonschema.Draft202012Validator(SCHEMA).validate(data)
        except Exception as exc:
            errors.append(f"{path.relative_to(ROOT)}: {exc}")
            continue
        if data["id"] in ids:
            errors.append(f"duplicate eval id: {data['id']}")
        ids.add(data["id"])
        if path.stem != data["id"]:
            errors.append(f"{path.name}: filename must match id {data['id']}")
    if errors:
        print("Eval validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Validated {len(files)} eval cases + JSON Schema.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
