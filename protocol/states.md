# Contribution state model

One state string cannot represent engineering progress, upstream presentation, queue position, and authority. Every durable case records four independent axes.

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

`APPROVED` must come from an explicit user/owner authority transition; `oss-radar` cannot emit it.

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

## Normal path

```text
APPROVED
→ REPRODUCED
→ IMPLEMENTED
→ LOCAL_VALIDATED
→ SELF_REVIEWED
→ ADVERSARIAL_REVIEWED
→ CLAIMS_VERIFIED
→ DRAFT_READY
→ DRAFT_OPEN
→ CI_OBSERVED
→ REVIEW_CAPACITY_CHECKED
→ READY_FOR_REVIEW
→ IN_REVIEW
→ MERGED / CLOSED / SUPERSEDED
```

`CI_OBSERVED` and `REVIEW_CAPACITY_CHECKED` are gates recorded in evidence; they need not be permanent work-state enum values.

## Transition rules

- A later state does not imply earlier evidence exists; the case must record the gates.
- A new head SHA invalidates head-bound validation, self-review, adversarial review, and claim verification until rerun or explicitly scoped.
- Material scope expansion returns to `QUALIFIED`/`REQUALIFY`.
- A competing implementation may move a case to `SUPERSEDED` without code failure.
- Sessions release their lease when a transition completes or the case waits on an external trigger.
