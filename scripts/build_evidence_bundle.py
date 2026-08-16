#!/usr/bin/env python3
"""Build a deterministic evidence bundle from an explicit JSON spec."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import stat
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any


RESERVED_META_KEYS = {"run_id", "head_sha"}
ARTIFACT_KINDS = {
    "log",
    "report",
    "screenshot",
    "video",
    "trajectory",
    "test-output",
    "benchmark",
    "other",
}


def canonical_json(data: Any) -> bytes:
    return (json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_bundle_path(value: str) -> PurePosixPath:
    if "\\" in value:
        raise ValueError(f"bundle path must use POSIX separators: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"unsafe bundle path: {value!r}")
    if path.parts[0] in {"manifest.json", "meta.json"}:
        raise ValueError(f"bundle path collides with reserved metadata: {value!r}")
    return path


def regular_file(path: Path) -> None:
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode):
        raise ValueError(f"symlink artifacts are not allowed: {path}")
    if not stat.S_ISREG(info.st_mode):
        raise ValueError(f"artifact is not a regular file: {path}")


def required_string(artifact: dict[str, Any], key: str, index: int) -> str:
    value = artifact.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"artifact[{index}].{key} must be a non-empty string")
    return value.strip()


def build(spec: dict[str, Any], output: Path) -> tuple[Path, str]:
    run_id = spec.get("run_id")
    head_sha = spec.get("head_sha")
    meta = spec.get("meta")
    artifacts = spec.get("artifacts")
    if not isinstance(run_id, str) or not run_id:
        raise ValueError("run_id must be a non-empty string")
    if not isinstance(head_sha, str) or len(head_sha) != 40 or any(
        ch not in "0123456789abcdef" for ch in head_sha
    ):
        raise ValueError("head_sha must be a lowercase 40-character SHA")
    if not isinstance(meta, dict):
        raise ValueError("meta must be an object")
    reserved = sorted(RESERVED_META_KEYS.intersection(meta))
    if reserved:
        raise ValueError(f"meta cannot override reserved fields: {reserved}")
    if not isinstance(artifacts, list):
        raise ValueError("artifacts must be a list")
    if output.exists() or output.is_symlink():
        raise ValueError(f"output already exists: {output}")

    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=output.name + ".", dir=output.parent))
    try:
        meta_payload = {**meta, "run_id": run_id, "head_sha": head_sha}
        meta_bytes = canonical_json(meta_payload)
        (staging / "meta.json").write_bytes(meta_bytes)

        entries: list[dict[str, Any]] = []
        seen: set[str] = set()
        for index, artifact in enumerate(artifacts):
            if not isinstance(artifact, dict):
                raise ValueError(f"artifact[{index}] must be an object")

            source_value = artifact.get("source_path")
            if not isinstance(source_value, str) or not source_value:
                raise ValueError(f"artifact[{index}].source_path must be a non-empty string")
            source_path = Path(source_value).expanduser()
            regular_file(source_path)

            bundle_path = safe_bundle_path(str(artifact.get("bundle_path", "")))
            bundle_text = bundle_path.as_posix()
            if bundle_text in seen:
                raise ValueError(f"duplicate bundle path: {bundle_text}")
            seen.add(bundle_text)

            kind = artifact.get("kind", "other")
            if kind not in ARTIFACT_KINDS:
                raise ValueError(f"artifact[{index}].kind is unsupported: {kind!r}")
            source = required_string(artifact, "source", index)
            produced_by = required_string(artifact, "produced_by", index)
            lane = artifact.get("lane")
            if lane is not None and (not isinstance(lane, str) or not lane.strip()):
                raise ValueError(f"artifact[{index}].lane must be null or a non-empty string")

            destination = staging.joinpath(*bundle_path.parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            data = source_path.read_bytes()
            destination.write_bytes(data)
            entries.append(
                {
                    "path": bundle_text,
                    "sha256": sha256_bytes(data),
                    "bytes": len(data),
                    "kind": kind,
                    "source": source,
                    "produced_by": produced_by,
                    "lane": lane.strip() if isinstance(lane, str) else None,
                }
            )

        entries.sort(key=lambda item: item["path"])
        manifest = {
            "schema": 1,
            "run_id": run_id,
            "head_sha": head_sha,
            "meta_sha256": sha256_bytes(meta_bytes),
            "artifacts": entries,
        }
        manifest_bytes = canonical_json(manifest)
        manifest_path = staging / "manifest.json"
        manifest_path.write_bytes(manifest_bytes)
        staging.replace(output)
        return output / "manifest.json", sha256_bytes(manifest_bytes)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    if not isinstance(spec, dict):
        raise SystemExit("spec must contain a JSON object")
    try:
        manifest, digest = build(spec, args.output)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(f"evidence bundle failed: {exc}") from exc
    print(f"Built {manifest} sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
