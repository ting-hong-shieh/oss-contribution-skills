# Decision policy

Every Contribution Brief ends with exactly one decision.

## `GO`

Use only when all of the following are true:

- state is `CLAIMABLE`;
- the problem/work is still relevant;
- no known active competing effort makes duplication likely;
- upstream intent is explicit or sufficiently supported by repository policy/current context;
- the repository's AI/LLM contribution policy permits the contribution as it will actually be produced;
- expected scope is reviewable;
- no discussion/approval gate is currently unmet;
- confidence is at least `Medium`.

`GO` authorizes nothing. It recommends handing the target to the next workflow.

## `ASK`

Use when a specific human or maintainer decision would resolve the main uncertainty.

Examples:

- repository policy says “discuss before implementing”;
- two plausible designs exist and maintainer preference matters;
- issue wording conflicts with current code or recent maintainer direction;
- the proposed contribution changes public API/behavior and intent is not established.

State is usually `QUALIFIED` or `BLOCKED`.

The next action should identify **what must be clarified**, not automatically post a message.

## `WAIT`

Use when the right next move is to observe an existing dependency rather than create new work.

Examples:

- another contributor has an active PR;
- maintainer response is already pending;
- a prerequisite patch is in review;
- a recent competing implementation may resolve the issue.

State is usually `BLOCKED` or, if duplication is highly likely, `SUPERSEDED`.

## `SKIP`

Use when current evidence says the target should not consume contribution effort now.

Typical states:

- `SUPERSEDED`;
- `STALE`;
- `NOT_WORTH_IT`.

A repository whose AI policy forbids the intended production method is `NOT_WORTH_IT` for that method, even when the change itself is wanted. Record the policy, not only the decision, so a future run can tell whether the policy or the plan changed.

A skip is contextual, not permanent. Record the reason so a future run can tell what changed.

## Tie-break rules

When evidence supports more than one decision:

1. Prefer the action that reduces uncertainty with the least maintainer burden.
2. Prefer `WAIT` over duplicate implementation.
3. Prefer `ASK` over guessing maintainer intent.
4. Prefer `SKIP` over a high-burden speculative contribution.
5. Use `GO` only when the remaining uncertainty is normal implementation uncertainty, not upstream-coordination uncertainty.
