# Compatibility and adapters

The canonical `SKILL.md` files use only `name` and `description` frontmatter. Host-specific invocation controls, hooks, plugin metadata, and tool schemas stay under `adapters/` or host manifests.

This separation prevents Claude- or Codex-specific behavior from becoming accidental protocol policy. The same skill text can be copied or linked into either host, while deterministic public-action enforcement is installed independently.

Hook examples are intentionally conservative and require a durable runtime case. They do not intercept non-shell connector calls; orchestrators must invoke the shared gate core for those actions.
