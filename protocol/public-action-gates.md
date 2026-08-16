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
4. lease is valid when required;
5. repository traffic permits the action;
6. action-specific gates passed;
7. the command is not broader than the grant.

## Action gates

### Remote push / Draft PR

Require upstream instructions read, local validation, generated-artifact audit, self-review, adversarial review, and claim verification.

### Ready transition

Also require CI observed, no unresolved requested changes, review capacity available, and traffic `GREEN`.

### Public speech

Require the exact case and authority. The prepared text should be concise, evidence-backed, and limited to the current contribution.

### Force-push, close, merge

Require a dedicated explicit grant. Never infer it from general push authority.

## Tool-level actions

Shell hooks cannot intercept connector/API tool calls outside the shell. Hosts or orchestrators must apply the same gate before invoking those tools. A safe architecture treats the gate core as a library, not only as a command-string filter.
