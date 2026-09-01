#!/usr/bin/env python3
"""Run a basic validity test for a Piper ONNX voice."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import wave
from pathlib import Path


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run a basic validity test for a Piper voice."
    )
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--config", type=Path)
    parser.add_argument(
        "--text",
        default="Zażółć gęślą jaźń. System syntezy mowy działa poprawnie.",
    )
    parser.add_argument("--min-duration", type=float, default=0.25)
    return parser.parse_args()


def main() -> int:
    """Synthesize a temporary WAV file and validate its basic properties."""
    args = parse_args()
    config = args.config or Path(str(args.model) + ".json")
    for path in (args.model, config):
        if not path.is_file():
            print(f"ERROR: missing file: {path}", file=sys.stderr)
            return 2

    try:
        parsed = json.loads(config.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: invalid config: {exc}", file=sys.stderr)
        return 2

    sample_rate = int(parsed.get("audio", {}).get("sample_rate", 0))
    if sample_rate <= 0:
        print("ERROR: voice config has no valid audio.sample_rate", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory(prefix="piper-smoke-") as tmp:
        output = Path(tmp) / "smoke.wav"
        command = [
            sys.executable,
            "-m",
            "piper",
            "--model",
            str(args.model),
            "--config",
            str(config),
            "--output-file",
            str(output),
        ]
        process = subprocess.run(
            command,
            input=args.text + "\n",
            text=True,
            capture_output=True,
            check=False,
        )
        if process.returncode != 0:
            print(process.stdout)
            print(process.stderr, file=sys.stderr)
            return process.returncode

        if not output.is_file() or output.stat().st_size <= 44:
            print("ERROR: synthesis produced no usable WAV", file=sys.stderr)
            return 1

        with wave.open(str(output), "rb") as wav_file:
            duration = wav_file.getnframes() / wav_file.getframerate()
            if wav_file.getframerate() != sample_rate:
                print(
                    f"ERROR: output rate {wav_file.getframerate()} "
                    f"!= config rate {sample_rate}",
                    file=sys.stderr,
                )
                return 1
            if duration < args.min_duration:
                print(
                    f"ERROR: output too short: {duration:.3f} s",
                    file=sys.stderr,
                )
                return 1

        print(
            f"OK: {duration:.3f} s, {sample_rate} Hz, "
            f"{output.stat().st_size} bytes"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
