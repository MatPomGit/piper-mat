#!/usr/bin/env python3
"""Pobierz punkt kontrolny z manifestu i zweryfikuj SHA-256."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import urllib.request
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Pobierz zweryfikowany punkt kontrolny z checkpoints/manifest.json")
    parser.add_argument("name", nargs="?", default="base.ckpt")
    parser.add_argument("--manifest", type=Path, default=Path("checkpoints/manifest.json"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    entry = manifest["checkpoints"].get(args.name)
    if not entry:
        raise SystemExit(f"Nieznany punkt kontrolny: {args.name}")
    source = entry.get("source") or {}
    url = source.get("url")
    if not url:
        raise SystemExit(f"Brak zweryfikowanego źródła dla: {args.name}")

    output = args.output or Path("checkpoints") / args.name
    temp = output.with_suffix(output.suffix + ".part")
    output.parent.mkdir(parents=True, exist_ok=True)

    print(f"Pobieranie: {url}")
    with urllib.request.urlopen(url) as response, temp.open("wb") as handle:
        shutil.copyfileobj(response, handle)

    actual_size = temp.stat().st_size
    actual_sha = sha256(temp)
    if actual_size != entry["size_bytes"] or actual_sha != entry["sha256"]:
        temp.unlink(missing_ok=True)
        raise SystemExit(
            f"Weryfikacja nie powiodła się: rozmiar={actual_size}, sha256={actual_sha}"
        )

    temp.replace(output)
    print(f"Zweryfikowano i zapisano: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
