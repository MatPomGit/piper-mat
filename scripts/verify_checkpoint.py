#!/usr/bin/env python3
"""Zweryfikuj punkt kontrolny względem checkpoints/manifest.json."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

CHUNK_SIZE = 1024 * 1024
LFS_POINTER_PREFIX = b"version https://git-lfs.github.com/spec/v1"
LFS_OID_RE = re.compile(r"^oid sha256:([0-9a-f]{64})$", re.MULTILINE)
LFS_SIZE_RE = re.compile(r"^size (\d+)$", re.MULTILINE)


def parse_args() -> argparse.Namespace:
    """Odczytaj argumenty interfejsu wiersza poleceń."""
    parser = argparse.ArgumentParser(
        description="Zweryfikuj punkt kontrolny względem manifestu."
    )
    parser.add_argument("checkpoint", type=Path)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("checkpoints/manifest.json"),
    )
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    """Oblicz sumę kontrolną SHA-256 pliku."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_entry(manifest_path: Path, checkpoint_name: str) -> dict[str, object]:
    """Wczytaj i zwaliduj wpis punktu kontrolnego z manifestu."""
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"nie można odczytać manifestu: {exc}") from exc

    checkpoints = manifest.get("checkpoints")
    if not isinstance(checkpoints, dict):
        raise ValueError("manifest nie zawiera obiektu checkpoints")

    entry = checkpoints.get(checkpoint_name)
    if not isinstance(entry, dict):
        raise ValueError(
            f"{checkpoint_name} nie jest wymieniony w {manifest_path}"
        )

    expected_hash = entry.get("sha256")
    expected_size = entry.get("size_bytes")
    if not isinstance(expected_hash, str) or len(expected_hash) != 64:
        raise ValueError(f"niepoprawne sha256 dla {checkpoint_name}")
    if not isinstance(expected_size, int) or expected_size < 0:
        raise ValueError(f"niepoprawne size_bytes dla {checkpoint_name}")

    return entry


def read_lfs_pointer(path: Path) -> tuple[str, int] | None:
    """Odczytaj SHA-256 i rozmiar z pliku wskaźnika Git LFS."""
    try:
        with path.open("rb") as handle:
            head = handle.read(1024)
    except OSError as exc:
        raise ValueError(f"nie można odczytać pliku: {exc}") from exc

    if not head.startswith(LFS_POINTER_PREFIX):
        return None

    try:
        text = head.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("niepoprawne kodowanie wskaźnika Git LFS") from exc

    oid_match = LFS_OID_RE.search(text)
    size_match = LFS_SIZE_RE.search(text)
    if oid_match is None or size_match is None:
        raise ValueError("niepoprawny wskaźnik Git LFS")

    return oid_match.group(1), int(size_match.group(1))


def verify_pointer(
    pointer: tuple[str, int],
    *,
    expected_hash: str,
    expected_size: int,
) -> bool:
    """Sprawdź zgodność wskaźnika Git LFS z manifestem."""
    actual_hash, actual_size = pointer
    return actual_hash == expected_hash and actual_size == expected_size


def main() -> int:
    """Zweryfikuj plik punktu kontrolnego lub jego wskaźnik Git LFS."""
    args = parse_args()

    if not args.checkpoint.is_file():
        print(
            f"BŁĄD: nie znaleziono punktu kontrolnego: {args.checkpoint}",
            file=sys.stderr,
        )
        return 2

    try:
        entry = load_entry(args.manifest, args.checkpoint.name)
        expected_hash = str(entry["sha256"])
        expected_size = int(entry["size_bytes"])
        pointer = read_lfs_pointer(args.checkpoint)
    except ValueError as exc:
        print(f"BŁĄD: {exc}", file=sys.stderr)
        return 2

    if pointer is not None:
        if not verify_pointer(
            pointer,
            expected_hash=expected_hash,
            expected_size=expected_size,
        ):
            print(
                "BŁĄD: wskaźnik Git LFS nie odpowiada manifestowi",
                file=sys.stderr,
            )
            return 1
        print(f"OK: wskaźnik Git LFS odpowiada {args.checkpoint.name}")
        return 0

    try:
        actual_size = args.checkpoint.stat().st_size
        actual_hash = sha256_file(args.checkpoint)
    except OSError as exc:
        print(f"BŁĄD: nie można odczytać punktu kontrolnego: {exc}", file=sys.stderr)
        return 2

    if actual_size != expected_size:
        print(
            f"BŁĄD: niezgodny rozmiar: oczekiwano {expected_size}, "
            f"otrzymano {actual_size}",
            file=sys.stderr,
        )
        return 1
    if actual_hash != expected_hash:
        print(
            f"BŁĄD: niezgodna SHA-256: oczekiwano {expected_hash}, "
            f"otrzymano {actual_hash}",
            file=sys.stderr,
        )
        return 1

    print(f"OK: zweryfikowano punkt kontrolny: {args.checkpoint}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
