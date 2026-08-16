# Contribution Brief v1

Produce this structure for each target. Keep it compact but evidence-backed.

```markdown
# Contribution Brief

## Summary
- Target: owner/repo#123
- Decision: GO | ASK | WAIT | SKIP
- State: DISCOVERED | QUALIFIED | CLAIMABLE | BLOCKED | SUPERSEDED | STALE | NOT_WORTH_IT
- Confidence: High | Medium | Low
- Evidence checked through: YYYY-MM-DD

## Problem
One short paragraph describing the actual work item, not merely copying the issue title.

## Current status
- Open/closed/draft state
- Last meaningful activity date
- Current assignee/labels if relevant
- Whether the requested behavior still appears current

## Competition
- Linked PRs checked: ...
- Assignees checked: ...
- Recent work-claim comments checked: ...
- PR search performed: ...
- Result: no competing work found / active work found / uncertain

Use “no competing work found in the checks performed,” never “there is no competing work.”

## Maintainer signals
### Explicit
Only statements/policies that directly support upstream intent.

### Pattern evidence
Similar accepted/rejected work, clearly labeled as inference.

### Unknowns
Anything not established.

## Contributor eligibility
- AI/LLM policy: none found | permits with disclosure | restricts some work | forbids the intended method
- Governing text: quote the deciding sentence, with file/URL and date
- Intended production method: ...
- Result: permitted | not permitted | unknown

## Scope and feasibility
- Likely subsystem: ...
- Expected surfaces/files: ... or Unknown
- Reproduction: Confirmed | Likely | Unknown | Not applicable
- Test burden: Low | Medium | High | Unknown
- Maintainer review burden: Low | Medium | High | Unknown

## Value profile
- Engineering: High | Medium | Low | Unknown
- Learning: High | Medium | Low | Unknown
- Portfolio: High | Medium | Low | Unknown
- Upstream relationship: High | Medium | Low | Unknown

## Merge likelihood
High | Medium | Low | Unknown

Explain the evidence; do not present this as a statistical probability.

## Risks
List only the main risks that could change the decision.

## Recommended next action
Exactly one concrete next step.

## Authority
- Exercised: READ only
- Not exercised: LOCAL, PUBLIC
- Additional authority required for next action: None | LOCAL approval | PUBLIC approval

## Main uncertainty
The single most important thing that could make this brief wrong.
```

## Decision/state consistency

- `GO` should normally pair with `CLAIMABLE`.
- `ASK` should normally pair with `QUALIFIED` or `BLOCKED`.
- `WAIT` should normally pair with `BLOCKED` or `SUPERSEDED`.
- `SKIP` should normally pair with `SUPERSEDED`, `STALE`, or `NOT_WORTH_IT`.

If you intentionally use a different pairing, explain why.
