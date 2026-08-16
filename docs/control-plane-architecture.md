# Control-plane architecture

The system is designed around durable contribution cases and short-lived agent runs.
It borrows the useful separation between runtime, services, tasks, and capability packs
without turning a chat model into an all-powerful daemon.

## Components

### Durable case

The case is the source of operational truth for one issue/PR contribution. It owns:

- exact repository, issue/PR, branch, base, and expected head identity;
- work, upstream, queue, evidence, and verification state;
- exact authority grants;
- writer/shared-lever leases;
- next action and next external trigger.

A case outlives every Claude, Codex, or human session.

### Bounded transition worker

A worker acquires one case lease, performs one explicit transition, records evidence and
material delta, releases its leases, and stops. It must not wait indefinitely for CI or
a maintainer inside the same model context.

### Read-only services

GitHub inventory, CI/review observation, drift detection, dashboard rendering, and alert
classification are services. They may run on a schedule and update private observed
state, but they cannot infer public authority from what they observe.

### Host adapters

Claude Code and Codex adapters translate host hooks and tool calls into the canonical
protocol. They are enforcement surfaces, not separate policy forks.

### Skills

`oss-radar`, `oss-contribute`, and `oss-pr-maintenance` are portable capability bundles.
They define how to decide and prepare work; the private control plane decides which case
is active and which exact action is authorized.

## Two gates

Every automated run separates:

1. **Eligibility (`shouldRun`)** — Is a read, refresh, local repair, or verification run
   due for this case?
2. **Authorization (`canExecute`)** — Is this exact side effect allowed now, at this
   exact head, by this exact agent, with all current gates and leases satisfied?

Eligibility can schedule a run. It cannot grant authorization.

## Event and projection model

State-changing runs append a compact event. `STATUS.md`, issue dashboards, and static
HTML are projections generated from cases plus read-only observations. A projection can
be rebuilt; authority and evidence cannot be reconstructed from presentation alone.

## Failure behavior

- missing or partial GitHub observations lower confidence or block a transition;
- a head move invalidates head-bound assurance;
- a stalled worker stops and reports instead of extending its own scope;
- a conflicting lease blocks the action rather than selecting a winner implicitly;
- an unavailable verifier keeps verification pending;
- an unavailable sandbox limits review to static evidence.
