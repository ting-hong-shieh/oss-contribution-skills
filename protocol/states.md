# Contribution state model

One state string cannot represent engineering progress, upstream presentation, queue
position, authority, verification, and evidence freshness. Every durable case records
four operational axes plus two assurance axes.

## Work state

```text
DISCOVERED
QUALIFIED
APPROVED
REPRODUCING
REPRODUCED
IMPLEMENTING
IMPLEMENTED
LOCAL_VALIDATED
SELF_REVIEWED
ADVERSARIAL_REVIEWED
CLAIMS_VERIFIED
DRAFT_READY
RESPONSE_READY
BLOCKED
SUPERSEDED
ABANDONED
COMPLETE
```

`APPROVED` must come from an explicit user/owner authority transition; `oss-radar`
cannot emit it.

## Upstream state

```text
NOT_OPENED
DRAFT_OPEN
READY_FOR_REVIEW
IN_REVIEW
CHANGES_REQUESTED
APPROVED_UPSTREAM
MERGED
CLOSED
```

`DRAFT_OPEN` is not `READY_FOR_REVIEW`.

## Queue state

```text
ACTIVE_LOCAL
WAITING_ON_US
WAITING_UPSTREAM
WAITING_CI
WAITING_DEPENDENCY
PAUSED_CAPACITY
STALLED
DONE
```

A case can be technically complete while waiting upstream and holding no active session.

## Authority state

This is derived from the current action grants, not from work progress:

```text
READ_ONLY
LOCAL_ALLOWED
REMOTE_PUSH_ALLOWED
DRAFT_PUBLICATION_ALLOWED
PUBLIC_SPEECH_ALLOWED
READY_TRANSITION_ALLOWED
CLOSE_OR_MERGE_ALLOWED
```

## Verification state

```text
NOT_REQUIRED
PENDING
IN_PROGRESS
PASSED
FAILED
BLOCKED
```

Verification is independent from self-review and upstream approval. See
[`independent-verification.md`](independent-verification.md).

## Evidence state

```text
NONE
COLLECTING
CURRENT
STALE
INVALID
```

Evidence is current only for the head recorded in the evidence packet. See
[`evidence-bundles.md`](evidence-bundles.md).

## Normal path

```text
APPROVED
→ REPRODUCED
→ IMPLEMENTED
→ LOCAL_VALIDATED
→ SELF_REVIEWED
→ ADVERSARIAL_REVIEWED
→ CLAIMS_VERIFIED
→ evidence CURRENT
→ DRAFT_READY
→ DRAFT_OPEN
→ CI_OBSERVED
→ independent verification PASSED (when required)
→ REVIEW_CAPACITY_CHECKED
→ READY_FOR_REVIEW
→ IN_REVIEW
→ MERGED / CLOSED / SUPERSEDED
```

`CI_OBSERVED` and `REVIEW_CAPACITY_CHECKED` are gates recorded in evidence; they
need not be permanent work-state enum values.

## Transition rules

- A later state does not imply earlier evidence exists; the case must record the gates.
- A new head SHA invalidates head-bound validation, executable-surface audit,
  self-review, adversarial review, claim verification, evidence freshness, and
  independent verification until rerun or explicitly scoped.
- Material scope expansion returns to `QUALIFIED`/`REQUALIFY`.
- A competing implementation may move a case to `SUPERSEDED` without code failure.
- Sessions release their writer and shared-lever leases when a transition completes or
  the case waits on an external trigger.
