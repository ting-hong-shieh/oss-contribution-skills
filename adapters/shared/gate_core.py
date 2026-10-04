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
import shlex
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
        # An argv list such as ["bash", "-lc", "git push"] must keep its word
        # boundaries; a plain space join would hide the script from the classifier.
        return shlex.join(_flatten_command(item) for item in value)
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


# Shell operators that start a new command. Newlines count: collapsing them into
# spaces would hide a second command on the next line. Quoted text is preserved.
_PUNCTUATION = ";&|()`\n"
_ENV_ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
_WRAPPERS = {"env", "sudo", "command", "builtin", "exec", "nohup", "time", "nice", "stdbuf", "xargs"}
_WRAPPER_OPTIONS_WITH_VALUE = {"-u", "-g", "-C", "-n", "--unset", "--chdir", "--user", "--group"}
_SHELLS = {"sh", "bash", "zsh", "dash", "ksh"}
_GIT_OPTIONS_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--super-prefix", "--config-env"}
_GH_OPTIONS_WITH_VALUE = {"-R", "--repo", "--hostname"}
_GH_READ_ONLY_GROUPS = {"search", "auth", "help", "version", "completion", "browse", "status"}
_GH_READ_ONLY_SUBCOMMANDS = {"view", "list", "status", "diff", "checks", "checkout", "clone", "download", "watch", "get"}
_GH_PR_CREATE_OPTIONS_WITH_VALUE = {
    "-t", "--title", "-b", "--body", "-F", "--body-file", "-B", "--base", "-H", "--head",
    "-l", "--label", "-a", "--assignee", "-r", "--reviewer", "-m", "--milestone",
    "-p", "--project", "-T", "--template", "-R", "--repo",
}
_HTTP_CLIENTS = {"curl", "wget", "http", "https", "xh"}
_MUTATING_METHODS = {"POST", "PATCH", "PUT", "DELETE"}
_MAX_NESTING = 4


def _split_segments(command: str) -> list[list[str]] | None:
    """Split a shell command into argv lists, or return None if it cannot be parsed."""
    lexer = shlex.shlex(command, posix=True, punctuation_chars=_PUNCTUATION)
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    segments: list[list[str]] = [[]]
    try:
        for token in lexer:
            if token and all(char in _PUNCTUATION for char in token):
                segments.append([])
            else:
                segments[-1].append(token)
    except ValueError:
        return None
    return [segment for segment in segments if segment]


def _strip_wrappers(argv: list[str]) -> list[str]:
    index = 0
    while index < len(argv):
        token = argv[index]
        if _ENV_ASSIGNMENT.match(token):
            index += 1
        elif Path(token).name in _WRAPPERS:
            index += 1
            while index < len(argv) and argv[index].startswith("-"):
                index += 2 if argv[index] in _WRAPPER_OPTIONS_WITH_VALUE else 1
        else:
            break
    return argv[index:]


def _method_and_body(args: list[str], method_flags: set[str], body_prefixes: tuple[str, ...]) -> tuple[str | None, bool]:
    method: str | None = None
    has_body = False
    for index, token in enumerate(args):
        if token in method_flags:
            method = args[index + 1] if index + 1 < len(args) else ""
        elif token.startswith("-X") and len(token) > 2:
            method = token[2:]
        elif token.startswith(("--method=", "--request=")):
            method = token.split("=", 1)[1]
        elif token.startswith(body_prefixes):
            has_body = True
    return method, has_body


def _classify_git(args: list[str]) -> str:
    index = 0
    while index < len(args) and args[index].startswith("-"):
        index += 2 if args[index] in _GIT_OPTIONS_WITH_VALUE else 1
    if index >= len(args) or args[index] != "push":
        return "benign"
    action = "remote_push"
    for token in args[index + 1:]:
        if token.startswith(("--delete", "--mirror", "--prune")) or token.startswith(":"):
            return "unclassified_mutation"
        if token.startswith("--"):
            if token.startswith(("--force", "--force-with-lease", "--force-if-includes")):
                action = "force_push"
        elif token.startswith("-"):
            if "d" in token[1:]:
                return "unclassified_mutation"
            if "f" in token[1:]:
                action = "force_push"
        elif token.startswith("+"):
            action = "force_push"
    return action


def _classify_gh_pr_create(args: list[str]) -> str:
    draft = False
    index = 0
    while index < len(args):
        token = args[index]
        if token in _GH_PR_CREATE_OPTIONS_WITH_VALUE:
            index += 2
            continue
        if token in ("-d", "--draft", "--draft=true"):
            draft = True
        elif token == "--draft=false":
            draft = False
        index += 1
    return "open_draft_pr" if draft else "open_ready_pr"


def _classify_gh_api(args: list[str]) -> str:
    field_flags = ("-f", "-F", "--field", "--raw-field")
    fields: list[str] = []
    has_input = False
    is_graphql = False
    for index, token in enumerate(args):
        if token in field_flags:
            fields.append(args[index + 1] if index + 1 < len(args) else "")
        elif token.startswith(("--field=", "--raw-field=")) or (token[:2] in ("-f", "-F") and len(token) > 2):
            fields.append(token)
        elif token == "--input" or token.startswith("--input="):
            has_input = True
        elif token in ("graphql", "/graphql"):
            is_graphql = True
    method, _ = _method_and_body(args, {"-X", "--method"}, ())
    if is_graphql:
        if has_input or any("mutation" in field.lower() for field in fields):
            return "unclassified_mutation"
        return "benign"
    effective = (method or ("POST" if fields or has_input else "GET")).upper()
    return "unclassified_mutation" if effective in _MUTATING_METHODS else "benign"


def _classify_gh(args: list[str]) -> str:
    positional: list[str] = []
    index = 0
    while index < len(args) and len(positional) < 2:
        token = args[index]
        if token in _GH_OPTIONS_WITH_VALUE:
            index += 2
            continue
        if not token.startswith("-"):
            positional.append(token)
        index += 1
    if not positional:
        return "benign"
    group = positional[0]
    sub = positional[1] if len(positional) > 1 else ""
    if group == "api":
        return _classify_gh_api(args[args.index("api") + 1:])
    if group in _GH_READ_ONLY_GROUPS or sub in _GH_READ_ONLY_SUBCOMMANDS:
        return "benign"
    if group in ("pr", "issue"):
        rest = args[args.index(sub) + 1:] if sub else []
        if group == "pr" and sub == "create":
            return _classify_gh_pr_create(rest)
        if group == "pr" and sub == "ready":
            return "ready_transition"
        if sub in ("comment", "edit") or (group == "pr" and sub == "review") or (group == "issue" and sub == "create"):
            return "public_speech"
        if sub in ("close", "merge"):
            return "close_or_merge"
    # Any other gh subcommand may mutate GitHub state; deny until it is classified.
    return "unclassified_mutation"


def _classify_http(args: list[str]) -> str:
    if not any("github.com" in token for token in args):
        return "benign"
    method, has_body = _method_and_body(
        args,
        {"-X", "--request", "--method"},
        ("-d", "--data", "--json", "-F", "--form", "-T", "--upload-file", "--post-data", "--post-file", "--body-data", "--body-file"),
    )
    effective = (method or ("POST" if has_body else "GET")).upper()
    return "unclassified_mutation" if effective in _MUTATING_METHODS else "benign"


def _classify_argv(argv: list[str], depth: int) -> str:
    argv = _strip_wrappers(argv)
    if not argv:
        return "benign"
    program = Path(argv[0]).name
    if program in _SHELLS:
        for index, token in enumerate(argv[1:], start=1):
            if token.startswith("-") and not token.startswith("--") and "c" in token[1:]:
                script = argv[index + 1] if index + 1 < len(argv) else ""
                return _classify(script, depth + 1)
        return "benign"
    if program == "eval":
        return _classify(" ".join(argv[1:]), depth + 1)
    if program == "git":
        return _classify_git(argv[1:])
    if program == "gh":
        return _classify_gh(argv[1:])
    if program in _HTTP_CLIENTS:
        return _classify_http(argv[1:])
    return "benign"


def _classify(command: str, depth: int) -> str:
    if depth > _MAX_NESTING:
        return "unclassified_mutation"
    segments = _split_segments(command)
    if segments is None:
        # Unbalanced quoting: fail closed if a GitHub-capable tool appears at all.
        if re.search(r"\b(git|gh|curl|wget)\b", command):
            return "unclassified_mutation"
        return "benign"
    actions = {_classify_argv(segment, depth) for segment in segments} - {"benign"}
    if not actions:
        return "benign"
    if len(actions) == 1:
        return actions.pop()
    # One command line asking for several public actions needs several grants;
    # deny and let each action run, and be checked, on its own.
    return "unclassified_mutation"


def classify_command(command: str) -> str:
    """Classify a shell command into one authority class, benign, or unclassified_mutation.

    Commands are tokenized like a shell would split them, including wrappers such as
    `env` and `bash -c`, and any GitHub mutation that cannot be mapped to a single
    authority class is reported as `unclassified_mutation` so the gate denies it.
    String classification cannot see git aliases, scripts, or other programs that
    call GitHub on their own; treat this gate as a guardrail, not a sandbox.
    """
    return _classify(command, 0)


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
