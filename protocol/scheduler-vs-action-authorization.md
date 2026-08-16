# Scheduler eligibility versus action authorization

A scheduled task answers **whether a run should start**. It does not answer **whether a
side effect may occur**.

## Eligibility gate (`shouldRun`)

The scheduler may start a bounded run when, for example:

- the read-only GitHub inventory is due;
- CI or review state may have changed;
- an external trigger named by the case occurred;
- a lease expired and cleanup is needed;
- a case has a deterministic `WAITING_ON_US` signal;
- independent verification is pending and a verifier is available.

Eligibility is derived from time, observation, queue state, and capacity. It can only
launch a run with the authority already present in the durable case.

## Action gate (`canExecute`)

Before every local or public side effect, re-evaluate:

1. exact case identity;
2. exact action class;
3. explicit action authority;
4. expected versus current head SHA;
5. writer and required shared-lever ownership;
6. current evidence and verification state;
7. repository traffic and review capacity;
8. unresolved review/CI blockers;
9. host and upstream policy.

The action is denied when any required input is missing, stale, unknown, or inconsistent.

## Consequences

- `workflow_dispatch`, cron, a webhook, or a resumed session is not permission to post.
- A monitor can prepare a reply draft while `public_speech: false`, but it cannot publish
  it.
- A scheduled maintenance run can repair locally while `remote_push: false`, but it must
  stop at a local evidence packet.
- Memory, prior conversation, model identity, or a successful earlier run cannot replace
  current durable authority.
- A scheduler must never broaden authority to avoid being blocked.
