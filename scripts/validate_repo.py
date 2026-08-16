#!/usr/bin/env python3
"""Validate skills, protocols, evals, adapters, and tests."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def validate_skills(errors: list[str]) -> None:
    names: set[str] = set()
    for path in sorted((ROOT / "skills").glob("*/SKILL.md")):
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---\n"):
            fail(errors, f"{path.relative_to(ROOT)}: missing frontmatter")
            continue
        parts = text.split("---\n", 2)
        if len(parts) < 3:
            fail(errors, f"{path.relative_to(ROOT)}: unclosed frontmatter")
            continue
        keys: dict[str, str] = {}
        for line in parts[1].splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                keys[key.strip()] = value.strip()
        if set(keys) != {"name", "description"}:
            fail(errors, f"{path.relative_to(ROOT)}: frontmatter must contain only name and description")
        name = keys.get("name", "")
        if name != path.parent.name:
            fail(errors, f"{path.relative_to(ROOT)}: name must match directory")
        if name in names:
            fail(errors, f"duplicate skill name: {name}")
        names.add(name)
        if len(keys.get("description", "")) < 80:
            fail(errors, f"{path.relative_to(ROOT)}: description is too weak for skill discovery")
    expected = {"oss-radar", "oss-contribute", "oss-pr-maintenance"}
    if names != expected:
        fail(errors, f"skill set is {sorted(names)}, expected {sorted(expected)}")


def validate_links(errors: list[str]) -> None:
    pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for path in ROOT.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        for target in pattern.findall(text):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            local = target.split("#", 1)[0]
            if not (path.parent / local).resolve().exists():
                fail(errors, f"{path.relative_to(ROOT)} links to missing {target}")


def validate_json(errors: list[str]) -> None:
    for path in ROOT.rglob("*.json"):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            fail(errors, f"{path.relative_to(ROOT)}: invalid JSON: {exc}")
    claude = json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
    codex = json.loads((ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
    for key in ("name", "version", "description", "license"):
        if claude.get(key) != codex.get(key):
            fail(errors, f"Claude and Codex manifests disagree on {key}")


def run(errors: list[str], label: str, command: list[str]) -> None:
    result = subprocess.run(command, cwd=ROOT, check=False, capture_output=True, text=True)
    output = (result.stdout + result.stderr).strip()
    if result.returncode:
        fail(errors, f"{label} failed:\n{output}")
    elif output:
        print(output)


def main() -> int:
    errors: list[str] = []
    validate_skills(errors)
    validate_links(errors)
    validate_json(errors)
    run(errors, "eval validation", [sys.executable, "scripts/validate_eval_cases.py"])
    py_files = [str(path.relative_to(ROOT)) for path in ROOT.rglob("*.py")]
    run(errors, "Python compile", [sys.executable, "-m", "py_compile", *py_files])
    run(errors, "gate tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"])
    if errors:
        print("Repository validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Repository validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
