"""Testy zachowania podglądu i budowania polecenia trenowania."""

import json
import sys
from pathlib import Path

import pytest

from scripts import train_voice


def voice_config(tmp_path: Path) -> tuple[Path, Path]:
    """Zapisz minimalną konfigurację polecenia bez faktycznego treningu."""
    output_dir = tmp_path / "generated-model"
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "voice_name": "mateusz",
                "sample_rate": 22050,
                "espeak_voice": "pl",
                "batch_size": 8,
                "dataset": {
                    "metadata": "dataset/metadata.csv",
                    "audio_dir": "dataset/wavs",
                    "splits_path": "dataset/splits.json",
                },
                "training": {
                    "output_dir": str(output_dir),
                    "base_checkpoint": "checkpoints/base.ckpt",
                    "cache_dir": "cache",
                },
                "export": {"config_filename": "voice.onnx.json"},
            }
        ),
        encoding="utf-8",
    )
    return config_path, output_dir


def test_dry_run_cli_does_not_create_output_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Podgląd CLI nie może modyfikować systemu plików."""
    config_path, output_dir = voice_config(tmp_path)
    monkeypatch.setattr(
        sys, "argv", ["train_voice.py", "--config", str(config_path), "--dry-run"]
    )

    assert train_voice.main() == 0
    assert not output_dir.exists()


def test_regular_command_builder_creates_output_directory(tmp_path: Path) -> None:
    """Zachowaj przygotowanie katalogu przy rzeczywistym treningu."""
    config_path, output_dir = voice_config(tmp_path)

    command = train_voice.build_command(config_path)

    assert output_dir.is_dir()
    assert str(output_dir / "voice.onnx.json") in command
