#!/usr/bin/env python3
"""Uruchom trening Piper na podstawie kanonicznej konfiguracji JSON projektu."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Uruchom trening głosu na podstawie konfiguracji projektu")
    parser.add_argument("--config", type=Path, default=Path("configs/pl_PL-mateusz-medium.json"))
    parser.add_argument("--dry-run", action="store_true", help="Pokaż polecenie bez uruchamiania treningu")
    args = parser.parse_args()

    config = json.loads(args.config.read_text(encoding="utf-8"))
    dataset = config["dataset"]
    training = config["training"]
    output_dir = Path(training["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    command = [
        "python", "-m", "piper.train", "fit",
        "--data.voice_name", str(config["voice_name"]),
        "--data.csv_path", str(dataset["metadata"]),
        "--data.audio_dir", str(dataset["audio_dir"]),
        "--model.sample_rate", str(config["sample_rate"]),
        "--data.espeak_voice", str(config["espeak_voice"]),
        "--data.cache_dir", str(training["cache_dir"]),
        "--data.config_path", str(output_dir / config["export"]["config_filename"]),
        "--data.batch_size", str(config["batch_size"]),
        "--ckpt_path", str(training["base_checkpoint"]),
    ]

    if training.get("seed") is not None:
        command.extend(["--seed_everything", str(training["seed"])])
    if training.get("max_epochs") is not None:
        command.extend(["--trainer.max_epochs", str(training["max_epochs"])])

    print("Polecenie treningowe:")
    print(" ".join(command))
    if args.dry_run:
        return 0
    return subprocess.run(command, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
