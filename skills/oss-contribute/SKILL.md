---
name: oss-contribute
description: Execute an explicitly approved open-source contribution locally: read upstream instructions, reproduce the problem, define a minimal scope, implement, test, self-review, run an adversarial review, audit generated artifacts and public claims, and prepare a Draft PR packet. Use only after a target is approved. Public GitHub actions remain blocked unless the durable case grants the exact authority.
---

# OSS Contribute

Turn an approved Contribution Brief into the smallest evidence-backed change that a maintainer can review cheaply.

## Preconditions

Stop unless all are available:

1. an exact repository and target;
2. a Contribution Brief or equivalent scope contract;
3. explicit approval for `LOCAL` work;
4. a durable case with no conflicting active lease;
5. repository traffic is not `RED`;
6. the current checkout/worktree and branch are identified;
7. the repository's AI/LLM contribution policy permits the contribution as it will be produced, including any disclosure it requires.

Read [`../../protocol/authority.md`](../../protocol/authority.md), [`../../protocol/states.md`](../../protocol/states.md), [`../../protocol/claim-evidence.md`](../../protocol/claim-evidence.md), and [`../../protocol/sessions-and-leases.md`](../../protocol/sessions-and-leases.md).

## Workflow

### 1. Orient to upstream before editing

Read the nearest `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, templates, test guidance, changelog rules, commit conventions, and in-repo skills. Record what was read and anything unavailable. Prefer upstream-provided reviewer or simulation/domain skills at the final gate.

### 2. Confirm checkout safety

- Verify repository, remote, branch, base, and worktree.
- Inspect `git status --short` before any edit.
- Do not overwrite unexplained changes.
- Acquire the case lease before modifying files.

### 3. Reproduce or bound the problem

Record the literal command, environment, input/fixture, observed result, and head/base SHA. If reproduction is impossible within the timebox, move the case to `BLOCKED` rather than speculating.

### 4. Freeze the scope contract

State:

- behavior being changed;
- behavior deliberately not changed;
- likely files/subsystems;
- required regression evidence;
- upstream policy decisions that remain unresolved.

If implementation expands materially beyond this contract, stop and return to qualification (`REQUALIFY`).

### 5. Implement minimally

Follow established repository patterns. Avoid unrelated cleanup, mass reformatting, speculative abstractions, and broad refactors. Optimize for **minimum upstream burden**, not cleverness.

### 6. Validate at the current head

Run focused regression tests first, then the broader relevant checks required by the repository. Record exact commands and raw outcomes at the current head SHA. Earlier-commit results do not validate the final head.

### 7. Audit generated artifacts and staging

Before committing:

```bash
git status --short
git diff --stat
git diff --name-status
```

Before staging, list explicit intended paths. Do not default to `git add -A`. Inspect any logs, snapshots, coverage files, caches, generated text, or temporary data created by tests.

### 8. Self-review the complete diff

Check correctness, regression risk, API/behavior compatibility, scope, weak assertions, cleanup paths, exception boundaries, concurrency timing, partial writes, environment differences, and test-double assumptions.

### 9. Run an adversarial review

Use an independent read-only context when available. Ask:

> Assume this contribution is wrong. Find a concrete input, timing boundary, exception type, state transition, concurrency interleaving, environment difference, generated artifact, or test-double assumption that falsifies one of its claims.

Resolve or explicitly bound each material finding. Do not let the adversarial reviewer push or comment.

### 10. Build the Claim–Evidence Matrix

Audit every quantitative, absolute, or guarantee-like public claim. Mark each `VERIFIED`, `PARTIAL`, or `UNSUPPORTED`. Narrow or remove unsupported wording.

### 11. Prepare, do not silently publish

Produce a Draft PR packet containing:

- exact problem and minimal change;
- scope and exclusions;
- current-head validation;
- claim-evidence summary;
- known limitations;
- branch/head/base;
- requested next authority.

`DRAFT_READY` is the normal endpoint. `git push` or opening a Draft PR requires the corresponding durable authority and the public-action gate. A ready-for-review PR requires a later review-capacity gate.

## Hard stops

- No public action merely because code is complete.
- No Ready transition while another PR consumes the repository review slot.
- No force-push unless explicitly granted for this exact case.
- No “all tests pass,” “no behavior change,” “guarantees,” or equivalent without direct current-head evidence.
- No second agent editing a case with an active lease.
- Two cycles without material evidence or state progress: stop and report.
