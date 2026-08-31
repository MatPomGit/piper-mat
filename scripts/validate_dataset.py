#!/usr/bin/env python3
"""Validate Piper metadata and WAV quality using only the standard library."""

from __future__ import annotations

import argparse
import csv
import math
import statistics
import sys
import wave
from array import array
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a Piper voice dataset")
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--audio-dir", type=Path, required=True)
    parser.add_argument("--sample-rate", type=int, default=22050)
    parser.add_argument("--skip-audio", action="store_true")
    parser.add_argument("--silence-dbfs", type=float, default=-40.0)
    parser.add_argument("--clipping-threshold", type=float, default=0.999)
    return parser.parse_args()


def inspect_pcm16(
    wav: wave.Wave_read, silence_dbfs: float, clipping_threshold: float
) -> tuple[float, float, float, float]:
    """Return RMS, peak, silence ratio and clipping ratio for mono PCM16 audio."""
    max_value = 32767.0
    silence_level = max_value * (10.0 ** (silence_dbfs / 20.0))
    clip_level = max_value * clipping_threshold
    sum_squares = 0.0
    sample_count = 0
    silent_count = 0
    clipped_count = 0
    peak = 0

    while True:
        raw = wav.readframes(65536)
        if not raw:
            break
        samples = array("h")
        samples.frombytes(raw)
        if sys.byteorder != "little":
            samples.byteswap()
        for sample in samples:
            value = abs(sample)
            peak = max(peak, value)
            sum_squares += float(sample) * float(sample)
            sample_count += 1
            if value <= silence_level:
                silent_count += 1
            if value >= clip_level:
                clipped_count += 1

    if sample_count == 0:
        return float("-inf"), float("-inf"), 1.0, 0.0
    rms = math.sqrt(sum_squares / sample_count)
    rms_dbfs = 20.0 * math.log10(rms / max_value) if rms > 0 else float("-inf")
    peak_dbfs = 20.0 * math.log10(peak / max_value) if peak > 0 else float("-inf")
    silence_ratio = silent_count / sample_count
    clipping_ratio = clipped_count / sample_count
    return rms_dbfs, peak_dbfs, silence_ratio, clipping_ratio


def main() -> int:
    args = parse_args()
    errors: list[str] = []
    warnings: list[str] = []
    durations: list[float] = []
    rms_values: list[float] = []
    peak_values: list[float] = []
    silence_ratios: list[float] = []
    clipping_ratios: list[float] = []

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

    audio_files = {p.name for p in args.audio_dir.iterdir() if p.is_file()}
    unreferenced = sorted(audio_files - seen)
    for filename in unreferenced:
        warnings.append(f"audio file not referenced by metadata: {filename}")

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

                if channels == 1 and width == 2:
                    wav.rewind()
                    rms_dbfs, peak_dbfs, silence_ratio, clipping_ratio = inspect_pcm16(
                        wav, args.silence_dbfs, args.clipping_threshold
                    )
                    if math.isfinite(rms_dbfs):
                        rms_values.append(rms_dbfs)
                    if math.isfinite(peak_dbfs):
                        peak_values.append(peak_dbfs)
                    silence_ratios.append(silence_ratio)
                    clipping_ratios.append(clipping_ratio)
                    if clipping_ratio > 0.001:
                        warnings.append(f"{filename}: clipping ratio {clipping_ratio:.4%}")
                    if silence_ratio > 0.60:
                        warnings.append(f"{filename}: high silence ratio {silence_ratio:.1%}")
                    if rms_dbfs < -45.0:
                        warnings.append(f"{filename}: very low RMS level {rms_dbfs:.1f} dBFS")
                elif width != 2:
                    warnings.append(f"{filename}: signal metrics currently require PCM16")
        except (wave.Error, EOFError) as exc:
            errors.append(f"{filename}: invalid WAV file ({exc})")

    print(f"utterances: {len(rows)}")
    print(f"unreferenced_audio_files: {len(unreferenced)}")
    if durations:
        print(f"duration_total_s: {sum(durations):.2f}")
        print(f"duration_median_s: {statistics.median(durations):.2f}")
        print(f"duration_min_s: {min(durations):.2f}")
        print(f"duration_max_s: {max(durations):.2f}")
    if rms_values:
        print(f"rms_median_dbfs: {statistics.median(rms_values):.2f}")
    if peak_values:
        print(f"peak_max_dbfs: {max(peak_values):.2f}")
    if silence_ratios:
        print(f"silence_ratio_median: {statistics.median(silence_ratios):.4f}")
    if clipping_ratios:
        print(f"clipping_ratio_max: {max(clipping_ratios):.6f}")
    print(f"warnings: {len(warnings)}")
    print(f"errors: {len(errors)}")

    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
