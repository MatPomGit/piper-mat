#!/usr/bin/env python3
"""Uruchom trening Piper na podstawie kanonicznej konfiguracji JSON projektu."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def build_command(
    config_path: Path,
    *,
    checkpoint: Path | None = None,
    max_epochs: int | None = None,
    default_root_dir: Path | None = None,
) -> list[str]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    dataset = config["dataset"]
    training = config["training"]
    output_dir = Path(training["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    resume_checkpoint = checkpoint or Path(training["base_checkpoint"])
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
        "--ckpt_path", str(resume_checkpoint),
    ]

    if training.get("seed") is not None:
        command.extend(["--seed_everything", str(training["seed"])])

    effective_max_epochs = max_epochs if max_epochs is not None else training.get("max_epochs")
    if effective_max_epochs is not None:
        command.extend(["--trainer.max_epochs", str(effective_max_epochs)])

    if default_root_dir is not None:
        command.extend(["--trainer.default_root_dir", str(default_root_dir)])

    return command


def main() -> int:
    parser = argparse.ArgumentParser(description="Uruchom trening głosu na podstawie konfiguracji projektu")
    parser.add_argument("--config", type=Path, default=Path("configs/pl_PL-mateusz-medium.json"))
    parser.add_argument("--checkpoint", type=Path, help="Punkt kontrolny użyty do wznowienia lub startu treningu")
    parser.add_argument("--max-epochs", type=int, help="Bezwzględny limit epok Lightning dla tego uruchomienia")
    parser.add_argument("--default-root-dir", type=Path, help="Katalog logów i punktów kontrolnych tej sesji")
    parser.add_argument("--dry-run", action="store_true", help="Pokaż polecenie bez uruchamiania treningu")
    args = parser.parse_args()

    command = build_command(
        args.config,
        checkpoint=args.checkpoint,
        max_epochs=args.max_epochs,
        default_root_dir=args.default_root_dir,
    )

    print("Polecenie treningowe:")
    print(" ".join(command))
    if args.dry_run:
        return 0
    return subprocess.run(command, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
