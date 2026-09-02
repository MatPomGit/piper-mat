#!/usr/bin/env python3
"""Check whether a voice candidate meets minimum release requirements."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

DEFAULT_MODEL = Path("output/pl_PL-mateusz-medium.onnx")
DEFAULT_SPLITS = Path("dataset/splits.json")
DEFAULT_METADATA = Path("dataset/metadata.csv")
DEFAULT_EVALUATION = Path("evaluations/pl_PL-mateusz-medium.json")
DATASET_CARD = Path("dataset/DATASET_CARD.md")
MODEL_CARD = Path("models/pl_PL-mateusz-medium/MODEL_CARD.md")
REQUIRED_METRICS = ("wer", "cer")


def sha256_file(path: Path) -> str:
    """Return the SHA-256 checksum of a file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path, errors: list[str], label: str) -> dict[str, Any] | None:
    """Load a JSON object and append a readable error on failure."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"Nie można odczytać {label}: {path}: {exc}")
        return None

    if not isinstance(data, dict):
        errors.append(f"{label.capitalize()} musi zawierać obiekt JSON: {path}")
        return None

    return data


def check_required_files(paths: list[Path], errors: list[str]) -> None:
    """Check that all required release files exist."""
    for path in paths:
        if not path.is_file():
            errors.append(f"Brak wymaganego pliku: {path}")


def check_cards(errors: list[str]) -> None:
    """Reject incomplete data and model cards containing TODO markers."""
    for card in (DATASET_CARD, MODEL_CARD):
        if not card.is_file():
            continue
        try:
            content = card.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(f"Nie można odczytać karty: {card}: {exc}")
            continue
        if "TODO" in content:
            errors.append(f"Niewypełnione pola TODO: {card}")


def check_split_integrity(
    splits_path: Path,
    metadata_path: Path,
    errors: list[str],
) -> None:
    """Verify that the frozen split matches the current metadata file."""
    if not splits_path.is_file() or not metadata_path.is_file():
        return

    split_data = load_json(splits_path, errors, "plik podziału danych")
    if split_data is None:
        return

    expected = split_data.get("metadata_sha256")
    if not isinstance(expected, str) or not expected:
        errors.append(
            f"Brak metadata_sha256 w pliku podziału danych: {splits_path}"
        )
        return

    try:
        actual = sha256_file(metadata_path)
    except OSError as exc:
        errors.append(f"Nie można obliczyć SHA-256 {metadata_path}: {exc}")
        return

    if expected != actual:
        errors.append(
            "dataset/splits.json nie odpowiada aktualnemu metadata.csv"
        )


def check_evaluation(path: Path, errors: list[str]) -> None:
    """Verify that the evaluation record contains required metrics."""
    if not path.is_file():
        errors.append(f"Brak rekordu oceny: {path}")
        return

    evaluation = load_json(path, errors, "rekord oceny")
    if evaluation is None:
        return

    metrics = evaluation.get("metrics", evaluation)
    if not isinstance(metrics, dict):
        errors.append(f"Pole metrics musi być obiektem JSON: {path}")
        return

    for metric in REQUIRED_METRICS:
        if metric not in metrics:
            errors.append(
                f"Brak metryki {metric.upper()} w rekordzie oceny"
            )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Sprawdź kompletność kandydata do wydania głosu."
    )
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--evaluation", type=Path, default=DEFAULT_EVALUATION)
    return parser.parse_args()


def main() -> int:
    """Run release-readiness checks and return a process exit code."""
    args = parse_args()
    errors: list[str] = []

    model_config = Path(str(args.model) + ".json")
    check_required_files(
        [
            args.model,
            model_config,
            args.splits,
            args.metadata,
            DATASET_CARD,
            MODEL_CARD,
        ],
        errors,
    )
    check_cards(errors)
    check_split_integrity(args.splits, args.metadata, errors)
    check_evaluation(args.evaluation, errors)

    if errors:
        print("Projekt nie jest jeszcze gotowy do wydania:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Kandydat spełnia minimalne automatyczne kryteria wydania.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
