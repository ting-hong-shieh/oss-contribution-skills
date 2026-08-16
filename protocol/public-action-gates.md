# Public-action gates

Host hooks are enforcement adapters for rules that must not depend on the model remembering prose.

## Commands to classify

At minimum:

- `git push` and force-push variants;
- `gh pr create`, `gh pr ready`, `gh pr edit`, `gh pr close`, `gh pr merge`;
- `gh issue comment`, `gh pr comment`, `gh pr review`;
- mutating `gh api` or direct GitHub API calls;
- thread resolution and workflow reruns when exposed through tools rather than shell.

## Checks

For a risky action, fail closed unless the durable case proves:

1. exact authority for the action;
2. repository/branch/PR identity;
3. expected head SHA matches;
4. writer lease and action-scoped shared-lever leases are valid when required;
5. repository traffic permits the action;
6. the execution trust boundary is recorded;
7. current-head evidence is `CURRENT`, identified by a manifest, and manually inspected;
8. required independent verification passed at the same head;
9. action-specific gates passed;
10. the command is not broader than the grant.

## Scheduler separation

A cron entry, webhook, queued job, `workflow_dispatch`, resumed session, or model decision may make a run eligible. It never grants the authority required by this gate. Apply [`scheduler-vs-action-authorization.md`](scheduler-vs-action-authorization.md) before every side effect, including non-shell connector/API calls.

## Action gates

### Remote push / Draft PR

Require trust-boundary audit, upstream instructions read, local validation, generated-artifact audit, self-review, adversarial review, claim verification, and a current-head evidence bundle. Any shared lever required for the action must be held by the current agent.

### Ready transition

Also require CI observed, no unresolved requested changes, review capacity available, traffic `GREEN`, and required independent verification `PASSED` at the exact current head.

### Public speech

Require the exact case and authority. The prepared text should be concise, evidence-backed, and limited to the current contribution.

### Force-push, close, merge

Require a dedicated explicit grant. Never infer it from general push authority.

## Tool-level actions

Shell hooks cannot intercept connector/API tool calls outside the shell. Hosts or orchestrators must apply the same gate before invoking those tools. A safe architecture treats the gate core as a library, not only as a command-string filter.
