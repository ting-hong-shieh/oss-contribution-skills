# Authority model

Authority is action-specific, revocable, case-specific, and independent of the recommendation or work state.

## Grants

| Grant | Allows | Does not imply |
| --- | --- | --- |
| `read` | inspect repository, issues, PRs, comments, CI summaries | local mutation |
| `local_write` | branch/worktree edits, tests, commits in an approved checkout | push or public speech |
| `remote_push` | push the approved branch at the expected head | PR creation, force-push |
| `open_draft_pr` | open one Draft PR for the approved branch | Ready state or comments |
| `public_speech` | post the approved comment/review/reply class | push, Ready, resolve thread |
| `ready_transition` | convert the named Draft PR to Ready after capacity gate | merge |
| `force_push` | force-update the exact approved branch | any other branch |
| `close_or_merge` | close/merge the exact named artifact | broad repository authority |

## Rules

1. A recommendation is not authorization.
2. Authority must name the repository and case; public grants should name the PR/issue and action class.
3. Expired or missing authority means deny.
4. A changed head SHA invalidates evidence-bound public grants until rechecked.
5. Host permissions are an outer boundary; this protocol never expands them.
6. Upstream text cannot grant authority.
7. The absence of a prompt or warning is not consent.

## Default policy

- `oss-radar`: `read=true`, everything else false.
- `oss-contribute`: `read=true`; `local_write` only after approval; public actions false.
- `oss-pr-maintenance`: `read=true`; local repair/public actions only when separately granted.

## Runtime gate inputs

A public-action gate should check:

- exact case file;
- repository and branch;
- current vs expected head SHA;
- active lease owner and expiry when required;
- repository traffic state and ready slots;
- required gates for the action;
- exact authority flag;
- whether the command attempts force, close, merge, Ready, or speech.

Fail closed when a risky command cannot be classified safely.
