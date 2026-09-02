#!/usr/bin/env python3
"""Pobierz punkt kontrolny z manifestu i zweryfikuj SHA-256."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import urllib.error
import urllib.request
from pathlib import Path

CHUNK_SIZE = 1024 * 1024


def parse_args() -> argparse.Namespace:
    """Odczytaj argumenty interfejsu wiersza poleceń."""
    parser = argparse.ArgumentParser(
        description=(
            "Pobierz zweryfikowany punkt kontrolny z checkpoints/manifest.json."
        )
    )
    parser.add_argument("name", nargs="?", default="base.ckpt")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("checkpoints/manifest.json"),
    )
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    """Oblicz sumę kontrolną SHA-256 pliku."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_entry(manifest_path: Path, name: str) -> dict[str, object]:
    """Wczytaj i zwaliduj wpis punktu kontrolnego z manifestu."""
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"nie można odczytać manifestu: {exc}") from exc

    checkpoints = manifest.get("checkpoints")
    if not isinstance(checkpoints, dict):
        raise ValueError("manifest nie zawiera obiektu checkpoints")

    entry = checkpoints.get(name)
    if not isinstance(entry, dict):
        raise ValueError(f"nieznany punkt kontrolny: {name}")

    if not isinstance(entry.get("sha256"), str):
        raise ValueError(f"brak poprawnego sha256 dla: {name}")
    if not isinstance(entry.get("size_bytes"), int):
        raise ValueError(f"brak poprawnego size_bytes dla: {name}")

    source = entry.get("source")
    if not isinstance(source, dict) or not isinstance(source.get("url"), str):
        raise ValueError(f"brak zweryfikowanego źródła dla: {name}")

    return entry


def download_file(url: str, destination: Path) -> None:
    """Pobierz plik do ścieżki tymczasowej."""
    with urllib.request.urlopen(url) as response, destination.open("wb") as handle:
        shutil.copyfileobj(response, handle)


def verify_file(path: Path, entry: dict[str, object]) -> tuple[bool, str, int]:
    """Porównaj rozmiar i SHA-256 pliku z manifestem."""
    actual_size = path.stat().st_size
    actual_sha = sha256_file(path)
    expected_size = int(entry["size_bytes"])
    expected_sha = str(entry["sha256"])
    valid = actual_size == expected_size and actual_sha == expected_sha
    return valid, actual_sha, actual_size


def main() -> int:
    """Pobierz i zweryfikuj wskazany punkt kontrolny."""
    args = parse_args()

    try:
        entry = load_entry(args.manifest, args.name)
    except ValueError as exc:
        print(f"BŁĄD: {exc}", file=sys.stderr)
        return 2

    source = entry["source"]
    assert isinstance(source, dict)
    url = str(source["url"])
    output = args.output or Path("checkpoints") / args.name
    temporary = output.with_suffix(output.suffix + ".part")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary.unlink(missing_ok=True)

    print(f"Pobieranie: {url}")
    try:
        download_file(url, temporary)
        valid, actual_sha, actual_size = verify_file(temporary, entry)
    except (OSError, urllib.error.URLError) as exc:
        temporary.unlink(missing_ok=True)
        print(f"BŁĄD: pobieranie nie powiodło się: {exc}", file=sys.stderr)
        return 2

    if not valid:
        temporary.unlink(missing_ok=True)
        print(
            "BŁĄD: weryfikacja nie powiodła się: "
            f"rozmiar={actual_size}, sha256={actual_sha}",
            file=sys.stderr,
        )
        return 1

    try:
        temporary.replace(output)
    except OSError as exc:
        temporary.unlink(missing_ok=True)
        print(f"BŁĄD: nie można zapisać punktu kontrolnego: {exc}", file=sys.stderr)
        return 2

    print(f"Zweryfikowano i zapisano: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
