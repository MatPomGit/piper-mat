#!/usr/bin/env python3
"""Lekkie kontrole integralności repozytorium odpowiednie dla CI."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "pl_PL-mateusz-medium.json"

REQUIRED = [
    ROOT / "COPYING",
    ROOT / "dataset" / "DATASET_CARD.md",
    ROOT / "models" / "pl_PL-mateusz-medium" / "MODEL_CARD.md",
    ROOT / "docs" / "ROADMAP.md",
    ROOT / "docs" / "STAGED_TRAINING.md",
    ROOT / "dataset" / "metadata.csv",
    ROOT / "train.sh",
    ROOT / "train.ps1",
    ROOT / "scripts" / "train_voice.py",
    ROOT / "scripts" / "train_sessions.py",
    ROOT / "scripts" / "report_training_session.py",
    ROOT / "scripts" / "check_training_ready.py",
    ROOT / "scripts" / "record_environment.py",
    ROOT / "scripts" / "validate_dataset.py",
]


def main() -> int:
    errors: list[str] = []

    for path in REQUIRED:
        if not path.exists():
            errors.append(f"brak wymaganej ścieżki: {path.relative_to(ROOT)}")

    if not CONFIG.is_file():
        errors.append("brak konfiguracji głosu: configs/pl_PL-mateusz-medium.json")
    else:
        try:
            data = json.loads(CONFIG.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"niepoprawna konfiguracja JSON: {exc}")
        else:
            expected = {
                "language": "pl_PL",
                "quality": "medium",
                "sample_rate": 22050,
                "espeak_voice": "pl",
            }
            for key, value in expected.items():
                if data.get(key) != value:
                    errors.append(f"config {key!r}: oczekiwano {value!r}, otrzymano {data.get(key)!r}")
            export = data.get("export", {})
            if export.get("model_filename") != "pl_PL-mateusz-medium.onnx":
                errors.append("nieoczekiwana nazwa pliku modelu ONNX w konfiguracji")
            if export.get("config_filename") != "pl_PL-mateusz-medium.onnx.json":
                errors.append("nieoczekiwana nazwa pliku JSON modelu ONNX w konfiguracji")

            training = data.get("training", {})
            sessions = training.get("sessions", {})
            epochs = sessions.get("epochs_per_session")
            if not isinstance(epochs, list) or not epochs:
                errors.append("brak planu training.sessions.epochs_per_session")
            elif any(not isinstance(value, int) or value <= 0 for value in epochs):
                errors.append("epochs_per_session musi zawierać wyłącznie dodatnie liczby całkowite")
            for key in ("runs_dir", "state_dir", "reports_dir"):
                if not sessions.get(key):
                    errors.append(f"brak training.sessions.{key}")

    if (ROOT / "LICENSE").exists():
        errors.append("istnieje niejednoznaczny plik LICENSE; licencja kodu GPL-3.0-or-later znajduje się w COPYING")

    for error in errors:
        print(f"BŁĄD: {error}", file=sys.stderr)
    if errors:
        return 1

    print("Kontrole integralności projektu zakończone powodzeniem.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
