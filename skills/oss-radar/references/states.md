# Radar states

- `DISCOVERED` — target exists; evidence is insufficient.
- `QUALIFIED` — work appears real and relevant, but one coordination uncertainty remains.
- `CLAIMABLE` — current evidence supports that work is wanted, not known to be superseded, and reviewably scoped.
- `BLOCKED` — a dependency, decision, or active competing effort prevents work now.
- `SUPERSEDED` — already solved, replaced, or actively covered elsewhere.
- `STALE` — current relevance lacks support; age alone is not enough.
- `NOT_WORTH_IT` — expected value is low relative to uncertainty, conflict, or review burden.

`APPROVED` is forbidden in `oss-radar`; it records a later human authority transition.
