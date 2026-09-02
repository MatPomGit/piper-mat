#!/usr/bin/env python3
"""Oblicz WER i CER dla par transkrypcji referencyjnych i rozpoznanych."""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path


def normalize(text: str) -> str:
    """Ujednolić tekst przed obliczeniem metryk błędów."""
    normalized = unicodedata.normalize("NFKC", text).lower()
    normalized = re.sub(
        r"[^\wąćęłńóśźż]+",
        " ",
        normalized,
        flags=re.UNICODE,
    )
    return " ".join(normalized.split())


def levenshtein_distance(reference: list[str], hypothesis: list[str]) -> int:
    """Oblicz odległość Levenshteina między dwiema sekwencjami."""
    previous = list(range(len(hypothesis) + 1))

    for reference_index, reference_item in enumerate(reference, start=1):
        current = [reference_index]
        for hypothesis_index, hypothesis_item in enumerate(hypothesis, start=1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[hypothesis_index] + 1,
                    previous[hypothesis_index - 1]
                    + (reference_item != hypothesis_item),
                )
            )
        previous = current

    return previous[-1]


def parse_args() -> argparse.Namespace:
    """Odczytaj argumenty interfejsu wiersza poleceń."""
    parser = argparse.ArgumentParser(
        description="Oblicz WER i CER dla transkrypcji mowy syntetycznej."
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Plik JSONL z polami reference i hypothesis.",
    )
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def load_pairs(path: Path) -> list[tuple[str, str]]:
    """Wczytaj i zwaliduj pary reference/hypothesis z pliku JSONL."""
    pairs: list[tuple[str, str]] = []

    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            if not raw_line.strip():
                continue

            try:
                row = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"wiersz {line_number}: niepoprawny JSON: {exc.msg}"
                ) from exc

            if not isinstance(row, dict):
                raise ValueError(
                    f"wiersz {line_number}: oczekiwano obiektu JSON"
                )
            if "reference" not in row or "hypothesis" not in row:
                raise ValueError(
                    f"wiersz {line_number}: brak pola reference lub hypothesis"
                )

            pairs.append(
                (
                    normalize(str(row["reference"])),
                    normalize(str(row["hypothesis"])),
                )
            )

    if not pairs:
        raise ValueError("plik wejściowy nie zawiera żadnych par transkrypcji")

    return pairs


def evaluate_pairs(pairs: list[tuple[str, str]]) -> dict[str, int | float | None]:
    """Oblicz współczynnik błędów słów i znaków dla podanych par."""
    word_errors = 0
    word_total = 0
    character_errors = 0
    character_total = 0

    for reference, hypothesis in pairs:
        reference_words = reference.split()
        hypothesis_words = hypothesis.split()
        reference_characters = list(reference.replace(" ", ""))
        hypothesis_characters = list(hypothesis.replace(" ", ""))

        word_errors += levenshtein_distance(
            reference_words,
            hypothesis_words,
        )
        word_total += len(reference_words)
        character_errors += levenshtein_distance(
            reference_characters,
            hypothesis_characters,
        )
        character_total += len(reference_characters)

    return {
        "utterances": len(pairs),
        "word_errors": word_errors,
        "reference_words": word_total,
        "wer": word_errors / word_total if word_total else None,
        "character_errors": character_errors,
        "reference_characters": character_total,
        "cer": (
            character_errors / character_total
            if character_total
            else None
        ),
    }


def main() -> int:
    """Wczytaj transkrypcje, oblicz WER/CER i zapisz wynik."""
    args = parse_args()

    try:
        pairs = load_pairs(args.input)
        result = evaluate_pairs(pairs)
    except (OSError, ValueError) as exc:
        print(f"BŁĄD: {exc}", file=sys.stderr)
        return 2

    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    print(rendered)

    if args.output is not None:
        try:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered + "\n", encoding="utf-8")
        except OSError as exc:
            print(f"BŁĄD: nie można zapisać wyniku: {exc}", file=sys.stderr)
            return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
