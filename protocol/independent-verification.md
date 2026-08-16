# Independent verification

Self-review and adversarial review improve a contribution, but they are not independent
acceptance. Medium- and high-risk work should pass through a separate verifier before a
Ready transition when repository policy or the durable case requires it.

## Verification state

```text
NOT_REQUIRED
PENDING
IN_PROGRESS
PASSED
FAILED
BLOCKED
```

A verifier may be another agent, a human, or a repository-provided reviewer workflow.
The verifier must read the exact head and evidence packet rather than the creator's
session summary alone.

## Separation rules

- `creator` and `verifier` must differ when verification is required.
- A creator may repair findings but cannot mark the repaired head independently
  verified.
- A new head invalidates `PASSED` until the verifier reviews that head or explicitly
  scopes the prior result to unchanged content.
- Verification does not grant public authority or upstream approval.
- No agent approves, merges, or marks its own upstream repair as independently accepted.

## Minimum record

```yaml
verification:
  required: true
  state: PASSED
  creator: claude-code:session-a
  verifier: codex:session-b
  verified_head_sha: <40-char-sha>
  completed_at: 2026-08-17T04:20:00Z
  findings:
    - no blocking findings
```

## When to require it

Default to required for:

- concurrency, persistence, security boundary, authentication, sandbox, release, or
  migration changes;
- claims based on many measurements or complex evidence;
- a PR that already produced repeated review churn;
- a repository that explicitly uses an agent-verification stage;
- any case the operator marks medium/high risk.

Low-risk documentation or narrowly mechanical changes may use `NOT_REQUIRED`, but the
reason should be explicit in the case.
