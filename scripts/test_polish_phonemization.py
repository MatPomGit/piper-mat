#!/usr/bin/env python3
"""Smoke-test Polish text phonemization with system eSpeak NG."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sentences", type=Path, default=Path("tests/polish_sentences.txt"))
    parser.add_argument("--voice", default="pl")
    args = parser.parse_args()

    executable = shutil.which("espeak-ng")
    if executable is None:
        print("ERROR: espeak-ng executable not found", file=sys.stderr)
        return 2
    if not args.sentences.is_file():
        print(f"ERROR: sentence corpus not found: {args.sentences}", file=sys.stderr)
        return 2

    sentences = [line.strip() for line in args.sentences.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not sentences:
        print("ERROR: regression corpus is empty", file=sys.stderr)
        return 2

    failures: list[str] = []
    for index, sentence in enumerate(sentences, start=1):
        proc = subprocess.run(
            [executable, "-q", "--ipa=3", "-v", args.voice, sentence],
            text=True,
            capture_output=True,
            check=False,
        )
        phonemes = proc.stdout.strip()
        if proc.returncode != 0 or not phonemes:
            failures.append(f"line {index}: {sentence}")

    print(f"sentences: {len(sentences)}")
    print(f"failures: {len(failures)}")
    for failure in failures:
        print(f"ERROR: {failure}", file=sys.stderr)

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
