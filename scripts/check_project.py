#!/usr/bin/env python3
"""Run lightweight repository integrity checks suitable for CI."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "pl_PL-mateusz-medium.json"

REQUIRED_PATHS = (
    ROOT / "COPYING",
    ROOT / "dataset" / "DATASET_CARD.md",
    ROOT / "models" / "pl_PL-mateusz-medium" / "MODEL_CARD.md",
    ROOT / "docs" / "ROADMAP.md",
    ROOT / "docs" / "STAGED_TRAINING.md",
    ROOT / "docs" / "WINDOWS_GUI.md",
    ROOT / "dataset" / "metadata.csv",
    ROOT / "train.sh",
    ROOT / "train.ps1",
    ROOT / "START_PIPER_MAT_GUI.bat",
    ROOT / "tools" / "windows_setup_gui.py",
    ROOT / "tools" / "start_windows_gui.ps1",
    ROOT / "tools" / "windows_doctor.py",
    ROOT / "scripts" / "train_voice.py",
    ROOT / "scripts" / "train_sessions.py",
    ROOT / "scripts" / "report_training_session.py",
    ROOT / "scripts" / "check_training_ready.py",
    ROOT / "scripts" / "record_environment.py",
    ROOT / "scripts" / "validate_dataset.py",
)

EXPECTED_CONFIG_VALUES = {
    "language": "pl_PL",
    "quality": "medium",
    "sample_rate": 22050,
    "espeak_voice": "pl",
}

EXPECTED_EXPORT_FILENAMES = {
    "model_filename": "pl_PL-mateusz-medium.onnx",
    "config_filename": "pl_PL-mateusz-medium.onnx.json",
}

SESSION_PATH_FIELDS = ("runs_dir", "state_dir", "reports_dir")


def load_config(errors: list[str]) -> dict[str, Any] | None:
    """Load the canonical project configuration and report parse errors."""
    if not CONFIG_PATH.is_file():
        errors.append(
            "brak konfiguracji głosu: configs/pl_PL-mateusz-medium.json"
        )
        return None

    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"niepoprawna konfiguracja JSON: {exc}")
        return None


def check_required_paths(errors: list[str]) -> None:
    """Check that required project files and directories exist."""
    for path in REQUIRED_PATHS:
        if not path.exists():
            errors.append(
                f"brak wymaganej ścieżki: {path.relative_to(ROOT)}"
            )


def check_config_values(config: dict[str, Any], errors: list[str]) -> None:
    """Validate fixed voice properties in the canonical configuration."""
    for key, expected in EXPECTED_CONFIG_VALUES.items():
        actual = config.get(key)
        if actual != expected:
            errors.append(
                f"config {key!r}: oczekiwano {expected!r}, "
                f"otrzymano {actual!r}"
            )


def check_export_config(config: dict[str, Any], errors: list[str]) -> None:
    """Validate exported model file names."""
    export_config = config.get("export", {})
    if not isinstance(export_config, dict):
        errors.append("pole export w konfiguracji musi być obiektem JSON")
        return

    for key, expected in EXPECTED_EXPORT_FILENAMES.items():
        actual = export_config.get(key)
        if actual != expected:
            errors.append(
                f"export.{key}: oczekiwano {expected!r}, otrzymano {actual!r}"
            )


def check_training_sessions(
    config: dict[str, Any],
    errors: list[str],
) -> None:
    """Validate the staged-training session configuration."""
    training = config.get("training", {})
    if not isinstance(training, dict):
        errors.append("pole training w konfiguracji musi być obiektem JSON")
        return

    sessions = training.get("sessions", {})
    if not isinstance(sessions, dict):
        errors.append(
            "pole training.sessions w konfiguracji musi być obiektem JSON"
        )
        return

    epochs = sessions.get("epochs_per_session")
    if not isinstance(epochs, list) or not epochs:
        errors.append("brak planu training.sessions.epochs_per_session")
    elif any(
        not isinstance(epoch, int) or isinstance(epoch, bool) or epoch <= 0
        for epoch in epochs
    ):
        errors.append(
            "epochs_per_session musi zawierać wyłącznie dodatnie "
            "liczby całkowite"
        )

    for field_name in SESSION_PATH_FIELDS:
        value = sessions.get(field_name)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"brak training.sessions.{field_name}")


def check_license_layout(errors: list[str]) -> None:
    """Reject an ambiguous root LICENSE file next to canonical COPYING."""
    if (ROOT / "LICENSE").exists():
        errors.append(
            "istnieje niejednoznaczny plik LICENSE; licencja kodu "
            "GPL-3.0-or-later znajduje się w COPYING"
        )


def main() -> int:
    """Run project integrity checks and return a process exit code."""
    errors: list[str] = []

    check_required_paths(errors)
    config = load_config(errors)
    if config is not None:
        check_config_values(config, errors)
        check_export_config(config, errors)
        check_training_sessions(config, errors)

    check_license_layout(errors)

    for error in errors:
        print(f"BŁĄD: {error}", file=sys.stderr)

    if errors:
        return 1

    print("Kontrole integralności projektu zakończone powodzeniem.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
