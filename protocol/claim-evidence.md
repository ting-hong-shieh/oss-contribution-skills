# Claim–Evidence Matrix

Public OSS prose is part of the engineering artifact. Every quantitative, absolute, causal, or guarantee-like claim must be bound to evidence before publication.

## Trigger

Audit proactively when text includes or implies:

- counts, percentages, coverage, benchmark, duration, memory, tolerance, version range;
- `all`, `every`, `exactly`, `only`, `none`;
- `guarantee`, `always`, `never`, `fully`, `complete`;
- “no behavior change,” “CI unaffected,” “works in serial and parallel”;
- “each fix was reverted independently,” “all tests pass,” or similar completeness claims.

The trigger does not mean the claim is wrong. It means the claim must be traceable.

## Required fields

```yaml
claim: "works in serial and parallel"
evidence:
  - "pytest tests/... -q"
head_sha: "..."
scope: "serial interruption and cooperative fake-worker parallel cleanup"
status: PARTIAL
limitations:
  - "does not exercise a real stuck process"
publication_text: "covers serial interruption and cooperative parallel cleanup"
```

Statuses:

- `VERIFIED` — direct current-head evidence supports the exact claim and scope.
- `PARTIAL` — evidence supports a narrower claim.
- `UNSUPPORTED` — no adequate evidence exists.
- `NOT_APPLICABLE` — the statement is not an empirical/engineering claim.

## Resolution

- `VERIFIED`: keep, while preserving scope and current head.
- `PARTIAL`: narrow and name exclusions.
- `UNSUPPORTED`: remove or state uncertainty; do not manufacture tests or references.
- New commit: reassess head-bound claims.

## Evidence hierarchy

Direct current-head command/CI output > code/tests/configuration at current head > pinned external measurement or implementation > historical nearby result > inference.

A deterministic regression proves that the defined path remains stable; it does not by itself establish physical, external, or universal correctness.
