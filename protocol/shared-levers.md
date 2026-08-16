# Shared lever leases

A writer lease protects one contribution case. It does not protect shared external
resources such as a production deployment, staging environment, release tag, remote
branch, DNS record, secret rotation, billing action, or rollback authority.

Represent each shared resource as a separate lever lease:

```yaml
shared_levers:
  - id: rocketpy-fork-branch
    kind: REMOTE_BRANCH
    required_for: [remote_push, force_push]
    state: HELD
    owner: claude-code:session-a
    acquired_at: 2026-08-17T03:00:00Z
    expires_at: 2026-08-17T03:45:00Z
```

## States

```text
UNCLAIMED
HELD
RELEASED
BLOCKED
```

## Rules

- only one active holder for an exclusive lever;
- a lever may be required for one or more exact action classes;
- the holder must match the current agent when `OSS_AGENT_ID` is available;
- expired leases do not authorize use;
- acquire before touching the resource and release after the bounded transition;
- do not infer permission to access secrets from a lever record;
- a conflicting or unavailable lever moves the case to `WAIT`/`BLOCKED`, not to a
  workaround.

The public-action gate denies a classified action when a lever required for that action
is missing, unheld, expired, or held by a different agent.
