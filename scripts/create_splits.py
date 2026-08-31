#!/usr/bin/env python3
"""Tworzy powtarzalny podział danych Piper na zbiory treningowy, walidacyjny i testowy."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Utwórz powtarzalny podział zbioru danych")
    parser.add_argument("--metadata", type=Path, default=Path("dataset/metadata.csv"))
    parser.add_argument("--output", type=Path, default=Path("dataset/splits.json"))
    parser.add_argument("--seed", type=int, default=20260831)
    parser.add_argument("--validation-ratio", type=float, default=0.05)
    parser.add_argument("--test-ratio", type=float, default=0.05)
    return parser.parse_args()


def metadata_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_ids(path: Path) -> list[str]:
    ids: list[str] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for line_no, row in enumerate(csv.reader(handle, delimiter="|"), start=1):
            if len(row) < 2 or not row[0].strip():
                raise ValueError(f"nieprawidłowe metadane w wierszu {line_no}")
            ids.append(row[0].strip())
    if len(ids) != len(set(ids)):
        raise ValueError("metadane zawierają zduplikowane identyfikatory plików dźwiękowych")
    return ids


def main() -> int:
    args = parse_args()
    if args.validation_ratio < 0 or args.test_ratio < 0:
        raise ValueError("udziały podziału nie mogą być ujemne")
    if args.validation_ratio + args.test_ratio >= 1:
        raise ValueError("suma validation_ratio i test_ratio musi być mniejsza niż 1")

    ids = load_ids(args.metadata)
    shuffled = ids.copy()
    random.Random(args.seed).shuffle(shuffled)

    n_total = len(shuffled)
    n_test = round(n_total * args.test_ratio)
    n_validation = round(n_total * args.validation_ratio)

    test = sorted(shuffled[:n_test])
    validation = sorted(shuffled[n_test : n_test + n_validation])
    train = sorted(shuffled[n_test + n_validation :])

    payload = {
        "schema_version": 1,
        "metadata_sha256": metadata_sha256(args.metadata),
        "seed": args.seed,
        "ratios": {
            "train": 1.0 - args.validation_ratio - args.test_ratio,
            "validation": args.validation_ratio,
            "test": args.test_ratio,
        },
        "counts": {"train": len(train), "validation": len(validation), "test": len(test)},
        "splits": {"train": train, "validation": validation, "test": test},
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"zapisano: {args.output}")
    print(f"trening={len(train)} walidacja={len(validation)} test={len(test)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
