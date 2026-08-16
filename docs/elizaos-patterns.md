# Patterns studied from elizaOS

This project reviewed `elizaOS/eliza` through commit
[`d53100a07e6f02d3eac18af36f01401f1ca18bd5`](https://github.com/elizaOS/eliza/tree/d53100a07e6f02d3eac18af36f01401f1ca18bd5)
on 2026-08-17. The main source surfaces were:

- `.github/FLEET.md`;
- `.github/ISSUE_TEMPLATE/agent_work_item.md`;
- `packages/skills/skills/contribute-to-eliza/SKILL.md` and its evidence rubric;
- `packages/core/src/types/service.ts`;
- `packages/core/src/types/task.ts`;
- `packages/core/src/types/plugin.ts` and `runtime.ts`.

The implementation here is an independent adaptation of operational ideas. No elizaOS
source code is copied.

## Patterns adopted

### Scoped work owns acceptance and evidence

elizaOS makes a work item the durable owner of scope, acceptance criteria, status, and
proof instead of treating a chat context as the project record. We adapt that into a
contribution case. A Claude or Codex session performs a bounded transition, records its
evidence, releases its lease, and stops.

### Scheduling and action authorization are different gates

The elizaOS task contract separates scheduler eligibility (`shouldRun`) from action-time
authorization (`canExecute`). We apply the same distinction:

- a scheduler may decide that a read-only monitor or maintenance run is due;
- only the durable case plus the public-action gate may authorize a push, comment, Ready
  transition, close, or merge.

A scheduled run is therefore never evidence of permission. See
[`../protocol/scheduler-vs-action-authorization.md`](../protocol/scheduler-vs-action-authorization.md).

### Agent verification is separate from creator review

Their fleet flow has a separate agent-verification stage before owner/human acceptance.
We model this as a verification axis and forbid a creator from independently verifying
the same current head when verification is required. Self-review and adversarial review
remain necessary, but they are not independent acceptance.

### Shared resources need explicit claims

Their coordination guide distinguishes ordinary work claims from exclusive shared
resources such as deployment, staging, DNS, secrets, physical devices, and release
operations. We generalize that into expiring shared-lever leases. A case writer lease
does not silently reserve a remote branch, deployment, release, or rollback authority.

### Contribution content is untrusted

Their contribution skill treats issue/PR text, diffs, changed tests, manifests, logs,
and linked artifacts as attacker-controlled data. It separates trusted inspection from
execution of an untrusted PR head and requires disposable isolation without ordinary
credentials or network by default. We adopt a host-neutral control-checkout /
disposable-sandbox boundary and a static-only fallback.

### Evidence is a structured acceptance record

Their workflow binds proof to the exact contribution revision and requires reviewers to
inspect the artifact rather than trusting a link or green badge. We adapt those
principles into deterministic evidence bundles, exact-head freshness, manual inspection,
and explicit claim scope. A captured-but-unread artifact is not proof.

### Coordination is an event stream, not one giant conversation

The fleet guide separates durable work cards, evidence-bearing PRs, and coordination
threads. We use append-only run/reconciliation events and generated projections instead
of asking agents to recover operational truth from a long chat transcript.

### Runtime, services, tasks, and capability packs stay separate

The elizaOS core keeps a central runtime distinct from long-lived services, durable task
records, and plugin-provided capabilities. Our mapping is deliberately smaller:

| elizaOS concept | This project |
| --- | --- |
| Task | durable contribution case |
| Task worker | one bounded state-transition run |
| Service | GitHub observer, reconciler, renderer, or host adapter |
| Plugin/capability bundle | installable `oss-*` skill and adapter package |
| Runtime | private control plane coordinating state, never inventing authority |

See [`control-plane-architecture.md`](control-plane-architecture.md).

## Patterns deliberately not copied as universal policy

- Mandatory public AI model attribution is repository-specific, not a universal rule.
  This protocol records bounded internal provenance and follows each upstream project's
  disclosure policy.
- Public `CLAIMING:` comments are appropriate only where the repository explicitly uses
  that coordination mechanism. This protocol never recommends a claim merely to reserve
  an issue.
- Reward mechanics, lane signatures, and project-board mutations are elizaOS-specific.
- A scheduler, memory record, agent identity, or shared-lever lease never creates public
  authority by implication.
- Surface-specific evidence requirements are configured per repository/case rather than
  requiring screenshots or live-model traces for every contribution.
- We do not keep one autonomous chat session alive for the whole OSS lifecycle. Durable
  cases survive; sessions remain bounded and replaceable.
