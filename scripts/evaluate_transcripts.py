#!/usr/bin/env python3
"""Compute WER and CER from reference/hypothesis text pairs."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).lower()
    text = re.sub(r"[^\wąćęłńóśźż]+", " ", text, flags=re.UNICODE)
    return " ".join(text.split())


def distance(a: list[str], b: list[str]) -> int:
    previous = list(range(len(b) + 1))
    for i, item_a in enumerate(a, start=1):
        current = [i]
        for j, item_b in enumerate(b, start=1):
            current.append(min(
                current[-1] + 1,
                previous[j] + 1,
                previous[j - 1] + (item_a != item_b),
            ))
        previous = current
    return previous[-1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate ASR transcripts of synthetic speech")
    parser.add_argument("input", type=Path, help="JSONL with reference and hypothesis fields")
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    word_errors = word_total = char_errors = char_total = 0
    utterances = 0

    with args.input.open("r", encoding="utf-8") as handle:
        for line_no, raw in enumerate(handle, start=1):
            if not raw.strip():
                continue
            row = json.loads(raw)
            if "reference" not in row or "hypothesis" not in row:
                raise ValueError(f"line {line_no}: expected reference and hypothesis")
            reference = normalize(str(row["reference"]))
            hypothesis = normalize(str(row["hypothesis"]))
            ref_words, hyp_words = reference.split(), hypothesis.split()
            ref_chars, hyp_chars = list(reference.replace(" ", "")), list(hypothesis.replace(" ", ""))
            word_errors += distance(ref_words, hyp_words)
            word_total += len(ref_words)
            char_errors += distance(ref_chars, hyp_chars)
            char_total += len(ref_chars)
            utterances += 1

    result = {
        "utterances": utterances,
        "word_errors": word_errors,
        "reference_words": word_total,
        "wer": word_errors / word_total if word_total else None,
        "character_errors": char_errors,
        "reference_characters": char_total,
        "cer": char_errors / char_total if char_total else None,
    }
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
