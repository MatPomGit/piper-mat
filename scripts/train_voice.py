#!/usr/bin/env python3
"""Run Piper training from the project's canonical JSON configuration."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

DEFAULT_CONFIG_PATH = Path("configs/pl_PL-mateusz-medium.json")


def load_config(config_path: Path) -> dict[str, Any]:
    """Load a training configuration from a UTF-8 JSON file."""
    return json.loads(config_path.read_text(encoding="utf-8"))


def build_command(
    config_path: Path,
    *,
    checkpoint: Path | None = None,
    max_epochs: int | None = None,
    default_root_dir: Path | None = None,
) -> list[str]:
    """Build the Piper training command for one invocation."""
    config = load_config(config_path)
    dataset = config["dataset"]
    training = config["training"]

    output_dir = Path(training["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    resume_checkpoint = checkpoint or Path(training["base_checkpoint"])
    command = [
        sys.executable,
        "-m",
        "piper.train",
        "fit",
        "--data.voice_name",
        str(config["voice_name"]),
        "--data.csv_path",
        str(dataset["metadata"]),
        "--data.audio_dir",
        str(dataset["audio_dir"]),
        "--model.sample_rate",
        str(config["sample_rate"]),
        "--data.espeak_voice",
        str(config["espeak_voice"]),
        "--data.cache_dir",
        str(training["cache_dir"]),
        "--data.config_path",
        str(output_dir / config["export"]["config_filename"]),
        "--data.batch_size",
        str(config["batch_size"]),
        "--ckpt_path",
        str(resume_checkpoint),
    ]

    seed = training.get("seed")
    if seed is not None:
        command.extend(["--seed_everything", str(seed)])

    effective_max_epochs = (
        max_epochs if max_epochs is not None else training.get("max_epochs")
    )
    if effective_max_epochs is not None:
        command.extend(["--trainer.max_epochs", str(effective_max_epochs)])

    if default_root_dir is not None:
        command.extend(
            ["--trainer.default_root_dir", str(default_root_dir)]
        )

    return command


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Uruchom trenowanie głosu na podstawie kanonicznej "
            "konfiguracji projektu."
        )
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Ścieżka do konfiguracji JSON projektu.",
    )
    parser.add_argument(
        "--checkpoint",
        type=Path,
        help="Punkt kontrolny użyty do wznowienia lub rozpoczęcia trenowania.",
    )
    parser.add_argument(
        "--max-epochs",
        type=int,
        help="Bezwzględny limit epok Lightning dla tego uruchomienia.",
    )
    parser.add_argument(
        "--default-root-dir",
        type=Path,
        help="Katalog logów i punktów kontrolnych tej sesji.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Pokaż polecenie bez uruchamiania trenowania.",
    )
    return parser.parse_args()


def main() -> int:
    """Build and optionally execute the canonical training command."""
    args = parse_args()

    try:
        command = build_command(
            args.config,
            checkpoint=args.checkpoint,
            max_epochs=args.max_epochs,
            default_root_dir=args.default_root_dir,
        )
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        print(f"BŁĄD: nie można zbudować polecenia treningowego: {exc}")
        return 2

    print("Polecenie treningowe:")
    print(subprocess.list2cmdline(command))

    if args.dry_run:
        return 0

    return subprocess.run(command, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
