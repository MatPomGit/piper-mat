#!/usr/bin/env python3
"""Sprawdź, czy projekt spełnia minimalne kryteria wydania głosu."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes())
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Sprawdź kompletność kandydata do wydania")
    parser.add_argument("--model", type=Path, default=Path("output/pl_PL-mateusz-medium.onnx"))
    parser.add_argument("--splits", type=Path, default=Path("dataset/splits.json"))
    parser.add_argument("--metadata", type=Path, default=Path("dataset/metadata.csv"))
    parser.add_argument("--evaluation", type=Path, default=Path("evaluations/pl_PL-mateusz-medium.json"))
    args = parser.parse_args()

    errors: list[str] = []
    model_config = Path(str(args.model) + ".json")
    required_files = [args.model, model_config, args.splits, args.metadata, Path("dataset/DATASET_CARD.md"), Path("models/pl_PL-mateusz-medium/MODEL_CARD.md")]
    for path in required_files:
        if not path.is_file():
            errors.append(f"Brak wymaganego pliku: {path}")

    for card in [Path("dataset/DATASET_CARD.md"), Path("models/pl_PL-mateusz-medium/MODEL_CARD.md")]:
        if card.is_file() and "TODO" in card.read_text(encoding="utf-8"):
            errors.append(f"Niewypełnione pola TODO: {card}")

    if args.splits.is_file() and args.metadata.is_file():
        split_data = json.loads(args.splits.read_text(encoding="utf-8"))
        expected = split_data.get("metadata_sha256")
        actual = sha256(args.metadata)
        if expected != actual:
            errors.append("dataset/splits.json nie odpowiada aktualnemu metadata.csv")

    if not args.evaluation.is_file():
        errors.append(f"Brak rekordu ewaluacji: {args.evaluation}")
    else:
        evaluation = json.loads(args.evaluation.read_text(encoding="utf-8"))
        metrics = evaluation.get("metrics", evaluation)
        for metric in ("wer", "cer"):
            if metric not in metrics:
                errors.append(f"Brak metryki {metric.upper()} w rekordzie ewaluacji")

    if errors:
        print("Projekt nie jest jeszcze gotowy do wydania:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Kandydat spełnia minimalne automatyczne kryteria wydania.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
