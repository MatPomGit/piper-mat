#!/usr/bin/env python3
"""Measure process-level synthesis time and RTF for a Piper voice."""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import subprocess
import sys
import tempfile
import time
import wave
from pathlib import Path

DEFAULT_TEXT = (
    "To jest powtarzalny test wydajności polskiego modelu głosu Piper."
)


def wav_duration(path: Path) -> float:
    """Return the duration of a WAV file in seconds."""
    with wave.open(str(path), "rb") as wav_file:
        return wav_file.getnframes() / float(wav_file.getframerate())


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Zmierz procesowy RTF modelu Piper na bieżącej maszynie. "
            "Każdy pomiar obejmuje uruchomienie procesu i wczytanie modelu."
        )
    )
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--text", default=DEFAULT_TEXT)
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--warmup", type=int, default=1)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> Path:
    """Validate benchmark arguments and return the model config path."""
    if args.runs < 1:
        raise ValueError("Liczba pomiarów musi być dodatnia.")
    if args.warmup < 0:
        raise ValueError("Liczba przebiegów rozgrzewkowych nie może być ujemna.")

    config_path = Path(str(args.model) + ".json")
    if not args.model.is_file() or not config_path.is_file():
        raise FileNotFoundError("Brak zgodnej pary model ONNX i plik JSON.")

    return config_path


def run_synthesis(model: Path, text: str, wav_path: Path) -> float:
    """Run one Piper CLI synthesis and return elapsed process time."""
    start = time.perf_counter()
    process = subprocess.run(
        [
            sys.executable,
            "-m",
            "piper",
            "--model",
            str(model),
            "--output-file",
            str(wav_path),
            "--",
            text,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    elapsed = time.perf_counter() - start

    if process.returncode != 0:
        detail = process.stderr or process.stdout or "nieznany błąd syntezy"
        raise RuntimeError(f"Synteza Piper zakończyła się błędem: {detail.strip()}")

    return elapsed


def collect_measurements(
    model: Path,
    text: str,
    runs: int,
    warmup: int,
) -> list[dict[str, float]]:
    """Collect process-level synthesis measurements."""
    measurements: list[dict[str, float]] = []

    with tempfile.TemporaryDirectory(prefix="piper-benchmark-") as temp_dir:
        wav_path = Path(temp_dir) / "benchmark.wav"

        for iteration in range(warmup + runs):
            elapsed = run_synthesis(model, text, wav_path)
            audio_duration = wav_duration(wav_path)
            if audio_duration <= 0:
                raise RuntimeError("Piper wygenerował pusty plik WAV.")

            if iteration >= warmup:
                measurements.append(
                    {
                        "elapsed_s": elapsed,
                        "audio_s": audio_duration,
                        "rtf": elapsed / audio_duration,
                    }
                )

    return measurements


def build_result(
    model: Path,
    config_path: Path,
    text: str,
    runs: int,
    warmup: int,
    measurements: list[dict[str, float]],
) -> dict[str, object]:
    """Build a serializable benchmark result."""
    rtfs = [measurement["rtf"] for measurement in measurements]
    return {
        "schema_version": 2,
        "benchmark_scope": "process_level_cli",
        "includes_process_startup": True,
        "includes_model_loading": True,
        "model": str(model),
        "config": str(config_path),
        "text": text,
        "runs": runs,
        "warmup": warmup,
        "platform": {
            "system": platform.system(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python": platform.python_version(),
        },
        "measurements": measurements,
        "summary": {
            "rtf_mean": statistics.mean(rtfs),
            "rtf_median": statistics.median(rtfs),
            "rtf_min": min(rtfs),
            "rtf_max": max(rtfs),
        },
    }


def main() -> int:
    """Run the benchmark and print or save the result as JSON."""
    args = parse_args()

    try:
        config_path = validate_args(args)
        measurements = collect_measurements(
            args.model,
            args.text,
            args.runs,
            args.warmup,
        )
    except (FileNotFoundError, OSError, RuntimeError, ValueError) as exc:
        print(f"BŁĄD: {exc}", file=sys.stderr)
        return 2

    result = build_result(
        args.model,
        config_path,
        args.text,
        args.runs,
        args.warmup,
        measurements,
    )
    rendered = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
        print(f"Zapisano wynik benchmarku: {args.output}")
    else:
        print(rendered)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
