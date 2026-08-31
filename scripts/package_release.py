#!/usr/bin/env python3
"""Build a reproducible release directory and SHA-256 manifest for a Piper voice."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--model-card", type=Path, default=Path("models/pl_PL-mateusz-medium/MODEL_CARD.md"))
    parser.add_argument("--samples", type=Path, default=Path("samples/pl_PL-mateusz-medium"))
    parser.add_argument("--output", type=Path, default=Path("dist/pl_PL-mateusz-medium"))
    args = parser.parse_args()

    required = [args.model, args.config, args.model_card]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        for path in missing:
            print(f"ERROR: missing required release input: {path}", file=sys.stderr)
        return 2

    args.output.mkdir(parents=True, exist_ok=True)
    copied: list[Path] = []
    for source in required:
        target = args.output / source.name
        shutil.copy2(source, target)
        copied.append(target)

    if args.samples.is_dir():
        sample_dir = args.output / "samples"
        sample_dir.mkdir(exist_ok=True)
        for source in sorted(args.samples.glob("*.wav")):
            target = sample_dir / source.name
            shutil.copy2(source, target)
            copied.append(target)

    records = []
    for path in sorted(copied):
        records.append({
            "file": path.relative_to(args.output).as_posix(),
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        })

    manifest = {
        "schema_version": 1,
        "voice": "pl_PL-mateusz-medium",
        "files": records,
    }
    (args.output / "release-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (args.output / "checksums.txt").write_text(
        "".join(f"{item['sha256']}  {item['file']}\n" for item in records),
        encoding="utf-8",
    )

    print(f"release_dir: {args.output}")
    print(f"files: {len(records)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
