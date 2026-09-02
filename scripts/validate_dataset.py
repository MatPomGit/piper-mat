#!/usr/bin/env python3
"""Waliduj metadane Piper i podstawową jakość plików WAV."""

from __future__ import annotations

import argparse
import csv
import math
import statistics
import sys
import wave
from array import array
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ValidationResult:
    """Przechowuj wyniki walidacji zbioru danych."""

    rows: list[tuple[str, str]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    durations: list[float] = field(default_factory=list)
    rms_values: list[float] = field(default_factory=list)
    peak_values: list[float] = field(default_factory=list)
    silence_ratios: list[float] = field(default_factory=list)
    clipping_ratios: list[float] = field(default_factory=list)
    unreferenced_audio_files: list[str] = field(default_factory=list)


def parse_args() -> argparse.Namespace:
    """Wczytaj argumenty interfejsu wiersza poleceń."""
    parser = argparse.ArgumentParser(
        description="Waliduj zbiór danych głosu Piper"
    )
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--audio-dir", type=Path, required=True)
    parser.add_argument("--sample-rate", type=int, default=22050)
    parser.add_argument("--skip-audio", action="store_true")
    parser.add_argument("--silence-dbfs", type=float, default=-40.0)
    parser.add_argument("--clipping-threshold", type=float, default=0.999)
    return parser.parse_args()


def validate_thresholds(
    sample_rate: int,
    clipping_threshold: float,
) -> None:
    """Sprawdź poprawność podstawowych parametrów analizy sygnału."""
    if sample_rate <= 0:
        raise ValueError("częstotliwość próbkowania musi być dodatnia")
    if not 0.0 < clipping_threshold <= 1.0:
        raise ValueError("clipping-threshold musi należeć do przedziału (0, 1]")


def inspect_pcm16(
    wav_file: wave.Wave_read,
    silence_dbfs: float,
    clipping_threshold: float,
) -> tuple[float, float, float, float]:
    """Zwróć RMS, szczyt, udział ciszy i udział przesterowanych próbek PCM16."""
    max_value = 32767.0
    silence_level = max_value * (10.0 ** (silence_dbfs / 20.0))
    clipping_level = max_value * clipping_threshold
    sum_squares = 0.0
    sample_count = 0
    silent_count = 0
    clipped_count = 0
    peak = 0

    while True:
        raw = wav_file.readframes(65536)
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
            if value >= clipping_level:
                clipped_count += 1

    if sample_count == 0:
        return float("-inf"), float("-inf"), 1.0, 0.0

    rms = math.sqrt(sum_squares / sample_count)
    rms_dbfs = (
        20.0 * math.log10(rms / max_value)
        if rms > 0
        else float("-inf")
    )
    peak_dbfs = (
        20.0 * math.log10(peak / max_value)
        if peak > 0
        else float("-inf")
    )
    return (
        rms_dbfs,
        peak_dbfs,
        silent_count / sample_count,
        clipped_count / sample_count,
    )


def load_metadata(path: Path, result: ValidationResult) -> None:
    """Wczytaj metadata.csv i wykryj puste lub powtarzające się wpisy."""
    seen: set[str] = set()
    try:
        handle = path.open("r", encoding="utf-8-sig", newline="")
    except OSError as exc:
        result.errors.append(f"nie można odczytać pliku metadanych: {exc}")
        return

    with handle:
        reader = csv.reader(handle, delimiter="|")
        for line_number, row in enumerate(reader, start=1):
            if len(row) < 2:
                result.errors.append(
                    f"wiersz {line_number}: oczekiwano co najmniej 2 kolumn "
                    "oddzielonych znakiem '|'"
                )
                continue

            filename = row[0].strip()
            text = row[-1].strip()
            if not filename:
                result.errors.append(
                    f"wiersz {line_number}: pusta nazwa pliku dźwiękowego"
                )
                continue
            if not text:
                result.errors.append(
                    f"wiersz {line_number}: pusta transkrypcja dla {filename}"
                )
            if filename in seen:
                result.errors.append(
                    f"wiersz {line_number}: powtórzony wpis pliku {filename}"
                )

            seen.add(filename)
            result.rows.append((filename, text))


def find_unreferenced_audio(
    audio_dir: Path,
    result: ValidationResult,
) -> None:
    """Znajdź pliki dźwiękowe, które nie występują w metadata.csv."""
    referenced = {filename for filename, _ in result.rows}
    audio_files = {
        path.name
        for path in audio_dir.iterdir()
        if path.is_file()
    }
    result.unreferenced_audio_files = sorted(audio_files - referenced)
    for filename in result.unreferenced_audio_files:
        result.warnings.append(
            f"plik dźwiękowy nie jest używany w metadanych: {filename}"
        )


def inspect_audio_file(
    path: Path,
    expected_sample_rate: int,
    silence_dbfs: float,
    clipping_threshold: float,
    result: ValidationResult,
) -> None:
    """Sprawdź format WAV i podstawowe parametry sygnału."""
    filename = path.name
    if path.suffix.lower() != ".wav":
        result.warnings.append(
            f"pominięto analizę pliku innego niż WAV: {filename}"
        )
        return

    try:
        wav_context = wave.open(str(path), "rb")
    except (wave.Error, EOFError, OSError) as exc:
        result.errors.append(f"{filename}: niepoprawny plik WAV ({exc})")
        return

    with wav_context as wav_file:
        channels = wav_file.getnchannels()
        sample_rate = wav_file.getframerate()
        frames = wav_file.getnframes()
        sample_width = wav_file.getsampwidth()
        duration = frames / sample_rate if sample_rate else 0.0
        result.durations.append(duration)

        if channels != 1:
            result.errors.append(
                f"{filename}: oczekiwano sygnału mono, otrzymano {channels} kanały"
            )
        if sample_rate != expected_sample_rate:
            result.errors.append(
                f"{filename}: oczekiwano {expected_sample_rate} Hz, "
                f"otrzymano {sample_rate} Hz"
            )
        if sample_width not in (2, 3, 4):
            result.warnings.append(
                f"{filename}: nietypowa głębia próbki: {sample_width * 8} bitów"
            )
        if duration < 0.25:
            result.warnings.append(
                f"{filename}: bardzo krótka wypowiedź ({duration:.2f} s)"
            )
        if duration > 20.0:
            result.warnings.append(
                f"{filename}: długa wypowiedź ({duration:.2f} s)"
            )

        if channels == 1 and sample_width == 2:
            wav_file.rewind()
            rms_dbfs, peak_dbfs, silence_ratio, clipping_ratio = inspect_pcm16(
                wav_file,
                silence_dbfs,
                clipping_threshold,
            )
            if math.isfinite(rms_dbfs):
                result.rms_values.append(rms_dbfs)
            if math.isfinite(peak_dbfs):
                result.peak_values.append(peak_dbfs)
            result.silence_ratios.append(silence_ratio)
            result.clipping_ratios.append(clipping_ratio)

            if clipping_ratio > 0.001:
                result.warnings.append(
                    f"{filename}: udział przesterowanych próbek {clipping_ratio:.4%}"
                )
            if silence_ratio > 0.60:
                result.warnings.append(
                    f"{filename}: wysoki udział ciszy {silence_ratio:.1%}"
                )
            if rms_dbfs < -45.0:
                result.warnings.append(
                    f"{filename}: bardzo niski poziom RMS {rms_dbfs:.1f} dBFS"
                )
        elif sample_width != 2:
            result.warnings.append(
                f"{filename}: metryki sygnału są obecnie liczone wyłącznie dla PCM16"
            )


def inspect_referenced_audio(
    audio_dir: Path,
    expected_sample_rate: int,
    silence_dbfs: float,
    clipping_threshold: float,
    result: ValidationResult,
) -> None:
    """Sprawdź wszystkie pliki wymienione w metadanych."""
    for filename, _ in result.rows:
        path = audio_dir / filename
        if not path.is_file():
            result.errors.append(f"brak pliku dźwiękowego: {path}")
            continue
        inspect_audio_file(
            path,
            expected_sample_rate,
            silence_dbfs,
            clipping_threshold,
            result,
        )


def print_summary(result: ValidationResult) -> None:
    """Wyświetl statystyki i komunikaty walidatora."""
    print(f"utterances: {len(result.rows)}")
    print(
        "unreferenced_audio_files: "
        f"{len(result.unreferenced_audio_files)}"
    )
    if result.durations:
        print(f"duration_total_s: {sum(result.durations):.2f}")
        print(
            f"duration_median_s: {statistics.median(result.durations):.2f}"
        )
        print(f"duration_min_s: {min(result.durations):.2f}")
        print(f"duration_max_s: {max(result.durations):.2f}")
    if result.rms_values:
        print(
            f"rms_median_dbfs: {statistics.median(result.rms_values):.2f}"
        )
    if result.peak_values:
        print(f"peak_max_dbfs: {max(result.peak_values):.2f}")
    if result.silence_ratios:
        print(
            "silence_ratio_median: "
            f"{statistics.median(result.silence_ratios):.4f}"
        )
    if result.clipping_ratios:
        print(f"clipping_ratio_max: {max(result.clipping_ratios):.6f}")

    print(f"warnings: {len(result.warnings)}")
    print(f"errors: {len(result.errors)}")
    for warning in result.warnings:
        print(f"OSTRZEŻENIE: {warning}")
    for error in result.errors:
        print(f"BŁĄD: {error}", file=sys.stderr)


def main() -> int:
    """Wykonaj walidację zbioru danych i zwróć kod stanu."""
    args = parse_args()
    try:
        validate_thresholds(args.sample_rate, args.clipping_threshold)
    except ValueError as exc:
        print(f"BŁĄD: {exc}", file=sys.stderr)
        return 2

    if not args.metadata.is_file():
        print(
            f"BŁĄD: nie znaleziono pliku metadanych: {args.metadata}",
            file=sys.stderr,
        )
        return 2
    if not args.audio_dir.is_dir():
        print(
            f"BŁĄD: nie znaleziono katalogu nagrań: {args.audio_dir}",
            file=sys.stderr,
        )
        return 2

    result = ValidationResult()
    load_metadata(args.metadata, result)
    find_unreferenced_audio(args.audio_dir, result)

    if not args.skip_audio:
        inspect_referenced_audio(
            args.audio_dir,
            args.sample_rate,
            args.silence_dbfs,
            args.clipping_threshold,
            result,
        )

    print_summary(result)
    return 1 if result.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
