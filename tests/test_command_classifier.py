from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "adapters/shared"))
from gate_core import classify_command, extract_command  # noqa: E402

# Commands that used to be classified as benign or as a weaker action.
BYPASSES = {
    "git -C ../repo push origin feat": "remote_push",
    "git --no-pager push origin feat": "remote_push",
    "echo ok\ngit push origin feat": "remote_push",
    "bash -c 'git push origin feat'": "remote_push",
    "env X=1 git push origin feat": "remote_push",
    "git push origin +feat": "force_push",
    "git push -uf origin feat": "force_push",
    "git push origin --delete main": "unclassified_mutation",
    "git push origin :main": "unclassified_mutation",
    "git push --mirror": "unclassified_mutation",
    "gh pr create --draft=false --title x": "open_ready_pr",
    "gh pr create --title x --body '--draft'": "open_ready_pr",
    "gh issue create --title x --body y": "public_speech",
    "gh pr reopen 5": "unclassified_mutation",
    "gh run rerun 123": "unclassified_mutation",
    "gh api repos/o/r/issues/1/comments --input body.json": "unclassified_mutation",
    "gh api -XPOST repos/o/r/issues/1/comments": "unclassified_mutation",
    "gh api --method=POST repos/o/r/pulls": "unclassified_mutation",
    "gh api graphql -f query='mutation{addStar(input:{}){clientMutationId}}'": "unclassified_mutation",
    "curl -d '{}' https://api.github.com/repos/o/r/issues": "unclassified_mutation",
    "git push origin x && gh pr create --draft": "unclassified_mutation",
}

# Existing classifications that must not change.
KEPT = {
    "git push origin feat": "remote_push",
    "git push origin fix-flaky": "remote_push",
    "(cd repo; git push)": "remote_push",
    "git push --force-with-lease origin feature": "force_push",
    "gh pr create --draft --title x": "open_draft_pr",
    "gh pr create --body \"multi\nline\" --draft": "open_draft_pr",
    "gh pr ready 5": "ready_transition",
    "gh pr comment 5 --body ok": "public_speech",
    "gh pr merge 5": "close_or_merge",
}

# Read-only or local commands that must not be denied.
BENIGN = [
    "pytest -q",
    "git status && git log --format='%h (%s)'",
    "git commit -m 'push it'",
    "echo 'git push origin main'",
    "gh pr view 5 --json title",
    "gh pr checks 19 -R o/r",
    "gh search prs --author me",
    "gh api repos/o/r/pulls",
    "gh api -X GET repos/o/r/pulls -f per_page=100",
    "gh api graphql -f query='query{viewer{login}}'",
    "curl -s https://api.github.com/repos/o/r",
]


class ClassifierTests(unittest.TestCase):
    def test_former_bypasses_are_classified(self) -> None:
        for command, expected in BYPASSES.items():
            with self.subTest(command=command):
                self.assertEqual(classify_command(command), expected)

    def test_existing_classifications_hold(self) -> None:
        for command, expected in KEPT.items():
            with self.subTest(command=command):
                self.assertEqual(classify_command(command), expected)

    def test_read_only_commands_stay_benign(self) -> None:
        for command in BENIGN:
            with self.subTest(command=command):
                self.assertEqual(classify_command(command), "benign")

    def test_argv_list_payload_keeps_word_boundaries(self) -> None:
        payload = {"tool_input": {"command": ["bash", "-lc", "git push origin feat"]}}
        self.assertEqual(classify_command(extract_command(payload)), "remote_push")

    def test_unbalanced_quotes_fail_closed_for_github_tools(self) -> None:
        self.assertEqual(classify_command("gh pr comment 5 --body 'oops"), "unclassified_mutation")
        self.assertEqual(classify_command("echo 'oops"), "benign")


if __name__ == "__main__":
    unittest.main()
