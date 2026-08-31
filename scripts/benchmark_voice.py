#!/usr/bin/env python3
"""Zmierz czas syntezy i RTF dla głosu Piper."""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import subprocess
import tempfile
import time
import wave
from pathlib import Path


def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as wav:
        return wav.getnframes() / float(wav.getframerate())


def main() -> int:
    parser = argparse.ArgumentParser(description="Zmierz RTF modelu Piper na bieżącej maszynie")
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--text", default="To jest powtarzalny test wydajności polskiego modelu głosu Piper.")
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--warmup", type=int, default=1)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if args.runs < 1 or args.warmup < 0:
        raise SystemExit("Liczba pomiarów musi być dodatnia, a liczba rozgrzewek nieujemna")
    config = Path(str(args.model) + ".json")
    if not args.model.is_file() or not config.is_file():
        raise SystemExit("Brak pary model ONNX + plik JSON")

    timings: list[dict[str, float]] = []
    with tempfile.TemporaryDirectory() as tmp:
        wav_path = Path(tmp) / "benchmark.wav"
        for iteration in range(args.warmup + args.runs):
            start = time.perf_counter()
            proc = subprocess.run(
                ["piper", "--model", str(args.model), "--output_file", str(wav_path), "--", args.text],
                capture_output=True,
                text=True,
                check=False,
            )
            elapsed = time.perf_counter() - start
            if proc.returncode != 0:
                raise SystemExit(proc.stderr or proc.stdout or "Synteza Piper zakończyła się błędem")
            duration = wav_duration(wav_path)
            if iteration >= args.warmup:
                timings.append({"elapsed_s": elapsed, "audio_s": duration, "rtf": elapsed / duration})

    rtfs = [item["rtf"] for item in timings]
    result = {
        "schema_version": 1,
        "model": str(args.model),
        "text": args.text,
        "runs": args.runs,
        "warmup": args.warmup,
        "platform": {"system": platform.system(), "machine": platform.machine(), "processor": platform.processor()},
        "measurements": timings,
        "summary": {
            "rtf_mean": statistics.mean(rtfs),
            "rtf_median": statistics.median(rtfs),
            "rtf_min": min(rtfs),
            "rtf_max": max(rtfs),
        },
    }
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
        print(f"Zapisano benchmark: {args.output}")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
