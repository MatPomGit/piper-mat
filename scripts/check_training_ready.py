#!/usr/bin/env python3
"""Sprawdź, czy lokalne środowisko i pliki projektu są gotowe do treningu."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys
from pathlib import Path


def is_lfs_pointer(path: Path) -> bool:
    try:
        head = path.read_bytes()[:200]
    except OSError:
        return False
    return head.startswith(b"version https://git-lfs.github.com/spec/v1")


def main() -> int:
    parser = argparse.ArgumentParser(description="Sprawdź gotowość projektu do treningu Piper")
    parser.add_argument("--config", type=Path, default=Path("configs/pl_PL-mateusz-medium.json"))
    parser.add_argument("--skip-audio", action="store_true", help="Nie sprawdzaj, czy nagrania WAV są pobrane z Git LFS")
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []

    if not args.config.is_file():
        print(f"BŁĄD: brak konfiguracji {args.config}")
        return 2
    config = json.loads(args.config.read_text(encoding="utf-8"))
    training = config.get("training", {})
    dataset = config.get("dataset", {})

    required_keys = ["voice_name", "sample_rate", "espeak_voice", "batch_size", "dataset", "training", "export"]
    for key in required_keys:
        if key not in config:
            errors.append(f"brak pola konfiguracji: {key}")

    metadata = Path(dataset.get("metadata", ""))
    audio_dir = Path(dataset.get("audio_dir", ""))
    base_checkpoint = Path(training.get("base_checkpoint", ""))
    if not metadata.is_file():
        errors.append(f"brak metadanych: {metadata}")
    if not audio_dir.is_dir():
        errors.append(f"brak katalogu nagrań: {audio_dir}")
    if not base_checkpoint.is_file():
        errors.append(f"brak bazowego punktu kontrolnego: {base_checkpoint}")
    elif is_lfs_pointer(base_checkpoint):
        errors.append(f"punkt kontrolny jest tylko wskaźnikiem Git LFS: {base_checkpoint}; wykonaj `git lfs pull`")

    sessions = training.get("sessions")
    if not isinstance(sessions, dict):
        errors.append("brak sekcji training.sessions")
    else:
        increments = sessions.get("epochs_per_session")
        if not isinstance(increments, list) or not increments:
            errors.append("training.sessions.epochs_per_session musi być niepustą listą")
        elif any(not isinstance(value, int) or value <= 0 for value in increments):
            errors.append("każda wartość epochs_per_session musi być dodatnią liczbą całkowitą")
        elif not 3 <= len(increments) <= 6:
            warnings.append(f"plan ma {len(increments)} sesji; typowy plan projektu zakłada 3-6 podejść")

    if not args.skip_audio and audio_dir.is_dir():
        wavs = sorted(audio_dir.glob("*.wav"))
        if not wavs:
            errors.append(f"brak plików WAV w {audio_dir}")
        else:
            lfs_samples = [path for path in wavs[:20] if is_lfs_pointer(path)]
            if lfs_samples:
                errors.append("nagrania WAV są nadal wskaźnikami Git LFS; wykonaj `git lfs pull` przed treningiem")

    for module in ("torch", "lightning", "tensorboard", "librosa", "piper"):
        if importlib.util.find_spec(module) is None:
            errors.append(f"brak modułu Python: {module}; zainstaluj projekt przez `python -m pip install -e '.[train]'`")

    if shutil.which("espeak-ng") is None:
        warnings.append("nie znaleziono `espeak-ng` w PATH; Piper może korzystać z dołączonych danych, ale warto zweryfikować lokalną instalację")

    try:
        from piper.train.vits.monotonic_align import core as _core  # noqa: F401
    except Exception as exc:  # noqa: BLE001
        errors.append(f"rozszerzenie monotonic_align nie jest gotowe: {exc}; uruchom build_monotonic_align.sh i setup.py build_ext --inplace")

    output_dir = Path(training.get("output_dir", "output"))
    probe_dir = output_dir if output_dir.exists() else output_dir.parent
    try:
        usage = shutil.disk_usage(probe_dir if probe_dir.exists() else Path("."))
        free_gib = usage.free / (1024 ** 3)
        if free_gib < 20:
            warnings.append(f"mało wolnego miejsca: {free_gib:.1f} GiB; wielosesyjny trening może wymagać znacznie więcej")
    except OSError:
        pass

    print("Kontrola gotowości treningu")
    for warning in warnings:
        print(f"OSTRZEŻENIE: {warning}")
    for error in errors:
        print(f"BŁĄD: {error}")

    if errors:
        print(f"Wynik: NIEGOTOWE ({len(errors)} błędów, {len(warnings)} ostrzeżeń)")
        return 2
    print(f"Wynik: GOTOWE ({len(warnings)} ostrzeżeń)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
