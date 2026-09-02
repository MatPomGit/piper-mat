#!/usr/bin/env python3
"""Utwórz powtarzalny podział zbioru danych Piper."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
from random import Random

CHUNK_SIZE = 1024 * 1024


def parse_args() -> argparse.Namespace:
    """Odczytaj argumenty interfejsu wiersza poleceń."""
    parser = argparse.ArgumentParser(
        description="Utwórz powtarzalny podział zbioru danych."
    )
    parser.add_argument(
        "--metadata",
        type=Path,
        default=Path("dataset/metadata.csv"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("dataset/splits.json"),
    )
    parser.add_argument("--seed", type=int, default=20260831)
    parser.add_argument("--validation-ratio", type=float, default=0.05)
    parser.add_argument("--test-ratio", type=float, default=0.05)
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    """Oblicz sumę kontrolną SHA-256 pliku."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_ids(path: Path) -> list[str]:
    """Wczytaj unikalne identyfikatory nagrań z pliku metadanych."""
    identifiers: list[str] = []
    seen: set[str] = set()

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, delimiter="|")
        for line_number, row in enumerate(reader, start=1):
            if len(row) < 2:
                raise ValueError(
                    f"wiersz {line_number}: oczekiwano co najmniej dwóch kolumn"
                )

            identifier = row[0].strip()
            if not identifier:
                raise ValueError(
                    f"wiersz {line_number}: pusty identyfikator nagrania"
                )
            if identifier in seen:
                raise ValueError(
                    f"wiersz {line_number}: zduplikowany identyfikator {identifier}"
                )

            seen.add(identifier)
            identifiers.append(identifier)

    if not identifiers:
        raise ValueError("plik metadanych nie zawiera żadnych rekordów")

    return identifiers


def validate_ratios(validation_ratio: float, test_ratio: float) -> None:
    """Sprawdź poprawność udziałów zbiorów walidacyjnego i testowego."""
    for name, value in (
        ("validation_ratio", validation_ratio),
        ("test_ratio", test_ratio),
    ):
        if not 0.0 <= value < 1.0:
            raise ValueError(f"{name} musi należeć do przedziału [0, 1)")

    if validation_ratio + test_ratio >= 1.0:
        raise ValueError(
            "suma validation_ratio i test_ratio musi być mniejsza niż 1"
        )


def build_payload(
    identifiers: list[str],
    *,
    seed: int,
    validation_ratio: float,
    test_ratio: float,
    metadata_hash: str,
) -> dict[str, object]:
    """Zbuduj deterministyczny opis podziału zbioru danych."""
    shuffled = identifiers.copy()
    Random(seed).shuffle(shuffled)

    total = len(shuffled)
    test_count = round(total * test_ratio)
    validation_count = round(total * validation_ratio)

    test = sorted(shuffled[:test_count])
    validation = sorted(
        shuffled[test_count : test_count + validation_count]
    )
    train = sorted(shuffled[test_count + validation_count :])

    return {
        "schema_version": 1,
        "metadata_sha256": metadata_hash,
        "seed": seed,
        "ratios": {
            "train": 1.0 - validation_ratio - test_ratio,
            "validation": validation_ratio,
            "test": test_ratio,
        },
        "counts": {
            "train": len(train),
            "validation": len(validation),
            "test": len(test),
        },
        "splits": {
            "train": train,
            "validation": validation,
            "test": test,
        },
    }


def main() -> int:
    """Utwórz i zapisz deterministyczny podział zbioru danych."""
    args = parse_args()

    try:
        validate_ratios(args.validation_ratio, args.test_ratio)
        identifiers = load_ids(args.metadata)
        payload = build_payload(
            identifiers,
            seed=args.seed,
            validation_ratio=args.validation_ratio,
            test_ratio=args.test_ratio,
            metadata_hash=sha256_file(args.metadata),
        )
    except (OSError, csv.Error, ValueError) as exc:
        print(f"BŁĄD: {exc}", file=sys.stderr)
        return 2

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    counts = payload["counts"]
    assert isinstance(counts, dict)
    print(f"Zapisano: {args.output}")
    print(
        "trening={train} walidacja={validation} test={test}".format(**counts)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
