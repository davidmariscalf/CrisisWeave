#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

MANIFEST = "MANIFEST.sha256"
PROVENANCE = "BUILD_PROVENANCE.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def files(root: Path):
    for path in sorted(root.rglob("*"), key=lambda p: p.as_posix()):
        if path.is_file() and path.name not in {MANIFEST, PROVENANCE}:
            yield path


def write_manifest(root: Path, lock_path: Path) -> None:
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    if lock.get("schema_version") != 1 or not isinstance(lock.get("components"), dict):
        raise SystemExit("invalid components.lock.json")

    provenance = {
        "schema_version": 1,
        "umbrella_repository": "davidmariscalf/CrisisWeave",
        "umbrella_commit": os.getenv("GITHUB_SHA") or None,
        "components": lock["components"],
        "artifact_manifest": MANIFEST,
        "note": "Hashes cover the generated E2E artifact, excluding the manifest and provenance files themselves.",
    }
    (root / PROVENANCE).write_text(
        json.dumps(provenance, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )

    lines = []
    for path in files(root):
        rel = path.relative_to(root).as_posix()
        lines.append(f"{sha256(path)}  {rel}")
    if not lines:
        raise SystemExit("artifact is empty")
    (root / MANIFEST).write_text("\n".join(lines) + "\n", encoding="utf-8")


def verify(root: Path) -> None:
    manifest = root / MANIFEST
    provenance = root / PROVENANCE
    if not manifest.is_file() or not provenance.is_file():
        raise SystemExit("artifact integrity files are missing")

    expected = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, sep, rel = line.partition("  ")
        if not sep or len(digest) != 64 or rel in expected:
            raise SystemExit("invalid artifact manifest")
        if rel.startswith("/") or ".." in Path(rel).parts:
            raise SystemExit("unsafe artifact manifest path")
        expected[rel] = digest

    actual_paths = {path.relative_to(root).as_posix() for path in files(root)}
    if actual_paths != set(expected):
        missing = sorted(set(expected) - actual_paths)
        extra = sorted(actual_paths - set(expected))
        raise SystemExit(f"artifact file set mismatch; missing={missing}, extra={extra}")

    for rel, digest in expected.items():
        if sha256(root / rel) != digest:
            raise SystemExit(f"artifact hash mismatch: {rel}")

    data = json.loads(provenance.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or len(data.get("components", {})) != 11:
        raise SystemExit("invalid build provenance")
    print(json.dumps({"ok": True, "files": len(expected), "components": 11}))


def main() -> int:
    parser = argparse.ArgumentParser(description="Seal or verify a CrisisWeave E2E artifact")
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--lock", type=Path, default=Path("components.lock.json"))
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    root = args.artifact.resolve()
    if not root.is_dir():
        raise SystemExit("artifact directory does not exist")
    if args.verify:
        verify(root)
    else:
        write_manifest(root, args.lock)
        verify(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
