# Codex adapter

The canonical skills can be linked into `.agents/skills/` or `~/.agents/skills/`. The hook example applies the shared public-action gate to shell commands.

## Install cautiously

1. Link/copy the skills.
2. Copy `hooks.example.json` to `.codex/hooks.json` (or translate it into the current Codex hook configuration used by your installation) and replace `/ABSOLUTE/PATH`.
3. Export `OSS_CASE_FILE`, and `OSS_AGENT_ID` when a lease is required.
4. Run the gate unit tests and dry-run denied commands before enabling it in an active worktree.

The hook only adds denials. For a command it allows, it prints nothing, so the host's approval policy still apply. It classifies command text, so it cannot see git aliases, scripts, or other programs that call GitHub on their own: treat it as a guardrail, not a sandbox. The deny output follows the Claude Code hook format; confirm that your Codex version reads it before relying on it.

Non-shell GitHub tools still require the orchestrator to call the gate core directly.
