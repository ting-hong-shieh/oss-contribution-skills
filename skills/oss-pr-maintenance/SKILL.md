---
name: oss-pr-maintenance
description: Inspect an open-source pull request after it is opened and report only what changed: reviews, unresolved threads, CI, mergeability, main drift, competing work, draft/ready state, claim-evidence drift, and the smallest correct next action. Read-only by default; prepare concise responses or patches but do not push, comment, resolve threads, rerun CI, or change Ready state without exact authority.
---

# OSS PR Maintenance

Maintain an open contribution as a collaboration with upstream, not as an endless coding session.

## Default authority

`READ` only. Public replies, pushes, thread resolution, CI reruns, Ready transitions, closure, and merge each require separate authority.

Read [`../../protocol/review-capacity.md`](../../protocol/review-capacity.md), [`../../protocol/public-action-gates.md`](../../protocol/public-action-gates.md), and [`../../protocol/states.md`](../../protocol/states.md).

## One-run workflow

### 1. Load durable state

Read the case’s expected head/base, last observed review/CI snapshot, current queue state, authority, lease, and next trigger. If no durable state exists, create a read-only observation packet rather than inferring history from the session.

### 2. Verify identity and head

Confirm repository, PR number, author, open/draft state, head SHA, base SHA, and whether the head moved unexpectedly. Never apply a prepared patch to a different head without revalidation.

### 3. Compute the delta since the last check

Inspect only new or changed:

- maintainer/reviewer comments;
- review submissions and unresolved threads;
- requested changes;
- CI/check conclusions and actionable root causes;
- mergeability/conflicts;
- base/main drift;
- competing PRs or maintainer direction;
- draft/ready status;
- claims in the PR body that became stale after a new commit.

### 4. Reassess the queue

- `WAITING_ON_US` outranks new discovery in the same repository.
- Existing Ready PRs consume review capacity.
- A repository in `RED` permits observation and local repair only, not new public work.
- Do not make another Draft ready merely because its CI is green.

### 5. Choose one next action

Examples:

- `WAIT` — no material change or upstream response pending;
- `LOCAL_FIX` — prepare the smallest patch for a concrete review/CI issue;
- `REQUALIFY` — maintainer direction or scope changed;
- `REBASE_REVALIDATE` — base advanced and semantic conflict risk exists;
- `REPLY_READY` — concise evidence-backed response is prepared, not posted;
- `ABANDON/SUPERSEDED` — competing work or direction replaced the contribution.

### 6. Keep public replies short

A normal response should fit this structure:

```text
You're right. Fixed at <commit>.

Added <exact regression evidence> covering <exact boundary>.

Validation:
<one focused current-head result>

<Related behavior> remains out of scope because <one sentence>.
```

Do not narrate the entire investigation, repeat all prior history, or pitch a new PR in the review thread unless the maintainer requested it.

### 7. Persist and stop

Record the new snapshot, material delta, evidence, next action, next trigger, and authority needed. Release the lease. A scheduler or webhook may start a later bounded run; do not idle indefinitely waiting for upstream.

## Output

Produce a Maintenance Brief:

- PR and exact head/base;
- changes since last observation;
- current four-axis state;
- blockers and evidence;
- one recommended action;
- public draft text, if needed;
- authority required;
- next trigger.
