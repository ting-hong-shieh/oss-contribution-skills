# Review capacity and upstream traffic

The bottleneck in OSS is often reviewer attention, not local implementation throughput.

## Default ready limit

The default is one Ready PR per contributor per upstream repository. A repository policy may explicitly override the number.

Drafts and local branches do not automatically consume the same review slot, but repeated pushes, comments, or requests can still create churn.

## Traffic states

### GREEN

- ready slots are available;
- no unresolved requested changes are waiting on the contributor;
- no public-action burst or duplicate agent lease exists.

One candidate may advance after all technical gates pass.

### YELLOW

- a Ready PR already consumes the slot;
- a maintainer is actively reviewing another contribution;
- or several drafts exist and should be serialized.

Allow observation, local work, and repair. Do not create another review request or Ready transition.

### RED

Examples:

- ready limit exceeded;
- requested changes are waiting while new work is being pushed;
- repeated public updates without material progress;
- two agents act on the same case;
- authority/head/evidence is inconsistent.

Freeze new public contribution actions. Observation and local recovery remain allowed.

## Priority rule

`WAITING_ON_US` review work outranks new discovery in the same repository unless the owner explicitly chooses otherwise.

## Capacity gate record

Before Ready, record:

- Ready count and limit;
- other open drafts by the contributor;
- current requested changes/unresolved threads;
- recent public-action count/window;
- maintainer activity on another PR;
- resulting traffic state and decision.
