"""Validate that frozen train, validation and test splits are disjoint."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

SPLIT_NAMES = ("train", "validation", "test")


def validate_split_membership(
    payload: dict[str, Any],
    metadata_path: Path | None,
    errors: list[str],
) -> None:
    """Check split identifiers, counts and coverage of the metadata records."""
    splits = payload.get("splits")
    if not isinstance(splits, dict):
        errors.append("brak obiektu splits w pliku podziału danych")
        return

    assigned: dict[str, str] = {}
    valid_lists = True
    for name in SPLIT_NAMES:
        identifiers = splits.get(name)
        if not isinstance(identifiers, list) or not all(
            isinstance(item, str) and bool(item.strip()) for item in identifiers
        ):
            errors.append(f"splits.{name} musi być listą niepustych identyfikatorów")
            valid_lists = False
            continue
        if name in ("train", "validation") and not identifiers:
            errors.append(f"splits.{name} nie może być pustą listą")

        for identifier in identifiers:
            previous = assigned.get(identifier)
            if previous is not None:
                errors.append(
                    f"nagranie {identifier!r} występuje w splits.{previous} "
                    f"oraz splits.{name}"
                )
            else:
                assigned[identifier] = name

    if not valid_lists:
        return

    counts = payload.get("counts")
    if counts is not None:
        if not isinstance(counts, dict):
            errors.append("pole counts musi być obiektem JSON")
        else:
            for name in SPLIT_NAMES:
                actual = counts.get(name)
                if isinstance(actual, bool) or not isinstance(actual, int):
                    errors.append(f"counts.{name} musi być liczbą całkowitą")
                elif actual != len(splits[name]):
                    errors.append(f"counts.{name} nie zgadza się z splits.{name}")

    if metadata_path is None or not metadata_path.is_file():
        return

    metadata_ids: set[str] = set()
    try:
        with metadata_path.open("r", encoding="utf-8-sig", newline="") as handle:
            for line_number, row in enumerate(csv.reader(handle, delimiter="|"), 1):
                if len(row) < 2 or not row[0].strip():
                    errors.append(f"niepoprawne metadane w wierszu {line_number}")
                    continue
                identifier = row[0].strip()
                if identifier in metadata_ids:
                    errors.append(
                        f"powtórzony identyfikator w metadanych: {identifier}"
                    )
                metadata_ids.add(identifier)
    except (OSError, UnicodeError, csv.Error) as exc:
        errors.append(f"nie można zweryfikować identyfikatorów metadanych: {exc}")
        return

    unknown = set(assigned) - metadata_ids
    missing = metadata_ids - set(assigned)
    if unknown:
        errors.append(
            f"podział zawiera {len(unknown)} identyfikatorów spoza metadanych: "
            + ", ".join(sorted(unknown)[:5])
        )
    if missing:
        errors.append(
            f"podział pomija {len(missing)} nagrań z metadanych: "
            + ", ".join(sorted(missing)[:5])
        )
