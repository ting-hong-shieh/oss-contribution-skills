# Evidence bundles

Evidence should be inspectable, current, and bound to the exact code that produced it.
A prose summary is not the evidence record.

## One run, one bundle

A validation run may produce a deterministic bundle:

```text
evidence/<run-id>/
├── manifest.json
├── meta.json
├── logs/
├── reports/
├── screenshots/
├── video/
└── trajectories/
```

Use `scripts/build_evidence_bundle.py` with an explicit JSON spec to construct the bundle without following instructions embedded in artifacts.

`meta.json` records the exact commit, branch, runner class, bounded environment
fingerprint, start/end time, and commands. `manifest.json` lists every artifact with a
bundle-relative path, byte count, SHA-256, kind, producer, and optional lane.

## Required properties

- paths are relative, normalized, and cannot escape the bundle;
- symlinks are rejected;
- manifest output is canonical and byte-stable;
- only a small environment allowlist is recorded; never dump the whole environment;
- `run_id` and `head_sha` are reserved and cannot be overridden by free-form metadata;
- artifact `source` and `produced_by` are explicit bounded labels; local absolute paths are not used as public provenance defaults;
- artifacts are hashed as stored;
- `absent` is distinct from `present but empty`;
- validation fails loudly on malformed metadata rather than silently repairing it;
- every artifact intended as proof is opened or otherwise manually inspected before
  publication;
- the bundle head must equal the contribution's expected/current head.

## Evidence state

```text
NONE
COLLECTING
CURRENT
STALE
INVALID
```

A new commit makes head-bound evidence `STALE`. Reusing an earlier command result is
allowed only when the claim is explicitly limited to the earlier commit; it cannot
validate the current head.

## Minimal case record

```yaml
evidence:
  state: CURRENT
  head_sha: <40-char-sha>
  manifest_path: .oss-control/evidence/<run-id>/manifest.json
  manifest_sha256: <64-char-sha256>
  artifacts: 4
  manually_inspected: true
  limitations:
    - full GPU lane not run
```

The public-action gate uses this record for publication/Ready actions. It does not treat
a green CI icon, uploaded file, or captured-but-unread screenshot as sufficient proof.

## Surface-specific evidence

Do not require every surface to produce every artifact type. Define applicable rows and
keep non-applicable rows visible with a specific reason. Examples:

- UI: before/after screenshots, walkthrough, console/network logs;
- agent/model/prompt: real or explicitly deterministic trajectories;
- packaging: built artifact metadata and install/import smoke evidence;
- data/domain change: the produced record, file, row, or protocol output;
- test-only change: regression/ablation evidence and exact suite scope.
