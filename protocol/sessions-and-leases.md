# Sessions, durable cases, and leases

A session is a worker. A contribution case is the durable source of truth.

## Why sessions should stop

An OSS lifecycle may wait hours or days for CI, review, or a maintainer decision. Keeping one context alive encourages drift, stale assumptions, duplicate work, and unclear authority.

A normal run:

```text
load case
→ acquire writer and required shared-lever leases
→ verify head and trigger
→ perform one bounded transition
→ record evidence/material delta/next action
→ release lease
→ stop
```

## Lease fields

```yaml
lease:
  required: true
  owner: claude-code:session-id
  acquired_at: 2026-08-17T03:00:00Z
  expires_at: 2026-08-17T03:45:00Z
```

Rules:

- only one active writer lease per case;
- shared external resources use separate lever leases; see [`shared-levers.md`](shared-levers.md);
- read-only monitors may run concurrently but cannot mutate;
- expired leases are not silently reused;
- the writer renews only while making material progress;
- release before waiting on an external trigger.

## Run record

Every run should persist:

```yaml
objective: "address review request about rollback"
starting_state: "CHANGES_REQUESTED"
ending_state: "RESPONSE_READY"
material_delta: "added a regression test and bounded the claim"
evidence_added:
  - "pytest ... at <sha>"
files_changed:
  - "..."
public_actions: []
next_action: "request approval to push"
next_trigger: "owner approval"
```

## Stop-loss rules

- two cycles without material delta: `STOP_AND_REPORT`;
- reproduction timebox exceeded: `BLOCKED`;
- scope expands beyond contract: `REQUALIFY`;
- competing PR appears: `WAIT` or `SUPERSEDED`;
- another active lease exists: do not write;
- repository traffic `RED`: no new public action;
- head differs from expected: mark evidence and verification stale, refresh, and revalidate.
- untrusted execution lacks a suitable sandbox: static review only.
