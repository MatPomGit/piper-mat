#!/usr/bin/env python3
"""Verify checkpoint identity against checkpoints/manifest.json."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

LFS_OID_RE = re.compile(r"^oid sha256:([0-9a-f]{64})$", re.MULTILINE)
LFS_SIZE_RE = re.compile(r"^size (\d+)$", re.MULTILINE)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("checkpoint", type=Path)
    parser.add_argument("--manifest", type=Path, default=Path("checkpoints/manifest.json"))
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    entry = manifest["checkpoints"].get(args.checkpoint.name)
    if entry is None:
        print(f"ERROR: {args.checkpoint.name} is not listed in {args.manifest}", file=sys.stderr)
        return 2
    if not args.checkpoint.is_file():
        print(f"ERROR: checkpoint not found: {args.checkpoint}", file=sys.stderr)
        return 2

    expected_hash = entry["sha256"]
    expected_size = int(entry["size_bytes"])

    raw = args.checkpoint.read_bytes()
    if raw.startswith(b"version https://git-lfs.github.com/spec/v1"):
        text = raw.decode("utf-8")
        oid = LFS_OID_RE.search(text)
        size = LFS_SIZE_RE.search(text)
        if not oid or not size:
            print("ERROR: malformed Git LFS pointer", file=sys.stderr)
            return 1
        if oid.group(1) != expected_hash or int(size.group(1)) != expected_size:
            print("ERROR: Git LFS pointer does not match manifest", file=sys.stderr)
            return 1
        print(f"OK: LFS pointer matches {args.checkpoint.name}")
        return 0

    actual_size = args.checkpoint.stat().st_size
    actual_hash = sha256_file(args.checkpoint)
    if actual_size != expected_size:
        print(f"ERROR: size mismatch: expected {expected_size}, got {actual_size}", file=sys.stderr)
        return 1
    if actual_hash != expected_hash:
        print(f"ERROR: SHA-256 mismatch: expected {expected_hash}, got {actual_hash}", file=sys.stderr)
        return 1

    print(f"OK: checkpoint verified: {args.checkpoint}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
