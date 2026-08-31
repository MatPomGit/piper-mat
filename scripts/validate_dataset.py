#!/usr/bin/env python3
"""Validate Piper metadata and basic WAV properties using only the standard library."""

from __future__ import annotations

import argparse
import csv
import statistics
import sys
import wave
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a Piper voice dataset")
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--audio-dir", type=Path, required=True)
    parser.add_argument("--sample-rate", type=int, default=22050)
    parser.add_argument("--skip-audio", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    errors: list[str] = []
    warnings: list[str] = []
    durations: list[float] = []

    if not args.metadata.is_file():
        print(f"ERROR: metadata file not found: {args.metadata}", file=sys.stderr)
        return 2
    if not args.audio_dir.is_dir():
        print(f"ERROR: audio directory not found: {args.audio_dir}", file=sys.stderr)
        return 2

    rows: list[tuple[str, str]] = []
    seen: set[str] = set()
    with args.metadata.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, delimiter="|")
        for line_no, row in enumerate(reader, start=1):
            if len(row) < 2:
                errors.append(f"line {line_no}: expected at least 2 columns separated by '|'")
                continue
            filename, text = row[0].strip(), row[-1].strip()
            if not filename:
                errors.append(f"line {line_no}: empty audio filename")
                continue
            if not text:
                errors.append(f"line {line_no}: empty transcription for {filename}")
            if filename in seen:
                errors.append(f"line {line_no}: duplicate audio entry {filename}")
            seen.add(filename)
            rows.append((filename, text))

    for filename, _ in rows:
        path = args.audio_dir / filename
        if not path.is_file():
            errors.append(f"missing audio file: {path}")
            continue
        if args.skip_audio:
            continue
        if path.suffix.lower() != ".wav":
            warnings.append(f"audio inspection skipped for non-WAV file: {filename}")
            continue
        try:
            with wave.open(str(path), "rb") as wav:
                channels = wav.getnchannels()
                rate = wav.getframerate()
                frames = wav.getnframes()
                width = wav.getsampwidth()
                duration = frames / rate if rate else 0.0
                durations.append(duration)
                if channels != 1:
                    errors.append(f"{filename}: expected mono, got {channels} channels")
                if rate != args.sample_rate:
                    errors.append(f"{filename}: expected {args.sample_rate} Hz, got {rate} Hz")
                if width not in (2, 3, 4):
                    warnings.append(f"{filename}: unusual sample width: {width * 8} bit")
                if duration < 0.25:
                    warnings.append(f"{filename}: very short utterance ({duration:.2f} s)")
                if duration > 20.0:
                    warnings.append(f"{filename}: long utterance ({duration:.2f} s)")
        except (wave.Error, EOFError) as exc:
            errors.append(f"{filename}: invalid WAV file ({exc})")

    print(f"utterances: {len(rows)}")
    if durations:
        print(f"duration_total_s: {sum(durations):.2f}")
        print(f"duration_median_s: {statistics.median(durations):.2f}")
        print(f"duration_min_s: {min(durations):.2f}")
        print(f"duration_max_s: {max(durations):.2f}")
    print(f"warnings: {len(warnings)}")
    print(f"errors: {len(errors)}")

    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
