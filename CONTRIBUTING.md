# Contributing

Contributions are welcome when they reduce maintainer burden and preserve the protocol's conservative defaults.

## Before opening a pull request

- Open an issue first for new authority types, state-machine changes, or host adapters.
- Add or update an eval for every behavioral rule.
- Run `python scripts/validate_repo.py`.
- Keep host-specific mechanics under `adapters/`; keep `skills/` and `protocol/` portable.
- Do not include real credentials, private repository state, or identifiable upstream conflict transcripts.

Pull requests should start as drafts and describe the problem, change, exact validation command, evidence boundary, and known limitations.
