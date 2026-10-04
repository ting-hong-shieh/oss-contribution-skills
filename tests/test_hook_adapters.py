from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOSTS = ("claude-code", "codex")


def run_adapter(script: Path, payload: dict | None, env: dict[str, str], cwd: str) -> str:
    result = subprocess.run(
        [sys.executable, str(script)],
        input=json.dumps(payload) if payload is not None else "",
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
        check=True,
    )
    return result.stdout.strip()


class AdapterOutputTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.env = {key: value for key, value in os.environ.items() if not key.startswith("OSS_")}

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_allowed_command_produces_no_decision(self) -> None:
        # An explicit "allow" would bypass the host's own permission prompt.
        for host in HOSTS:
            with self.subTest(host=host):
                script = ROOT / "adapters" / host / "public_action_gate.py"
                out = run_adapter(script, {"tool_input": {"command": "rm -rf build"}}, self.env, self.tmp.name)
                self.assertEqual(out, "")

    def test_denied_command_reports_deny(self) -> None:
        for host in HOSTS:
            with self.subTest(host=host):
                script = ROOT / "adapters" / host / "public_action_gate.py"
                out = run_adapter(script, {"tool_input": {"command": "git -C repo push"}}, self.env, self.tmp.name)
                decision = json.loads(out)["hookSpecificOutput"]
                self.assertEqual(decision["permissionDecision"], "deny")

    def test_completion_gate_is_silent_when_inactive_and_blocks_on_missing_record(self) -> None:
        for host in HOSTS:
            with self.subTest(host=host):
                script = ROOT / "adapters" / host / "completion_gate.py"
                self.assertEqual(run_adapter(script, None, self.env, self.tmp.name), "")
                env = {**self.env, "OSS_RUN_RECORD": str(Path(self.tmp.name) / "missing.json")}
                self.assertEqual(json.loads(run_adapter(script, None, env, self.tmp.name))["decision"], "block")

    def test_hook_examples_use_python3(self) -> None:
        # Ubuntu ships no `python`; a hook that fails to start does not block the command.
        examples = (
            ROOT / "adapters/claude-code/settings.example.json",
            ROOT / "adapters/codex/hooks.example.json",
        )
        for path in examples:
            hooks = json.loads(path.read_text(encoding="utf-8"))["hooks"]
            for groups in hooks.values():
                for group in groups:
                    for hook in group["hooks"]:
                        with self.subTest(path=path.name, command=hook["command"]):
                            self.assertTrue(hook["command"].startswith("python3 "))


if __name__ == "__main__":
    unittest.main()
