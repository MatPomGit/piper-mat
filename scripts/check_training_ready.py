#!/usr/bin/env python3
"""Sprawdź, czy lokalne środowisko i pliki są gotowe do trenowania Piper."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys
from pathlib import Path
from typing import Any

DEFAULT_CONFIG = Path("configs/pl_PL-mateusz-medium.json")
REQUIRED_CONFIG_KEYS = (
    "voice_name",
    "sample_rate",
    "espeak_voice",
    "batch_size",
    "dataset",
    "training",
    "export",
)
REQUIRED_MODULES = ("torch", "lightning", "tensorboard", "librosa", "piper")


def is_lfs_pointer(path: Path) -> bool:
    """Sprawdź, czy plik jest wskaźnikiem Git LFS zamiast właściwego artefaktu."""
    try:
        head = path.read_bytes()[:200]
    except OSError:
        return False
    return head.startswith(b"version https://git-lfs.github.com/spec/v1")


def load_config(path: Path) -> dict[str, Any]:
    """Wczytaj i zweryfikuj podstawową strukturę konfiguracji JSON."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise RuntimeError(f"nie można odczytać konfiguracji {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"niepoprawny JSON w konfiguracji {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise RuntimeError("konfiguracja musi zawierać obiekt JSON")
    return data


def validate_required_keys(config: dict[str, Any], errors: list[str]) -> None:
    """Sprawdź wymagane pola najwyższego poziomu konfiguracji."""
    for key in REQUIRED_CONFIG_KEYS:
        if key not in config:
            errors.append(f"brak pola konfiguracji: {key}")


def validate_session_plan(training: Any, errors: list[str], warnings: list[str]) -> None:
    """Sprawdź plan dodatkowych epok dla kolejnych sesji."""
    if not isinstance(training, dict):
        errors.append("sekcja training musi być obiektem")
        return

    sessions = training.get("sessions")
    if not isinstance(sessions, dict):
        errors.append("brak sekcji training.sessions")
        return

    increments = sessions.get("epochs_per_session")
    if not isinstance(increments, list) or not increments:
        errors.append("training.sessions.epochs_per_session musi być niepustą listą")
        return

    invalid = any(
        isinstance(value, bool) or not isinstance(value, int) or value <= 0
        for value in increments
    )
    if invalid:
        errors.append("każda wartość epochs_per_session musi być dodatnią liczbą całkowitą")
        return

    if not 3 <= len(increments) <= 6:
        warnings.append(
            f"plan ma {len(increments)} sesji; typowy plan projektu zakłada 3-6 podejść"
        )


def validate_project_paths(
    dataset: Any,
    training: Any,
    errors: list[str],
) -> tuple[Path, Path, Path, bool]:
    """Sprawdź ścieżki zbioru danych i bazowego punktu kontrolnego."""
    dataset_dict = dataset if isinstance(dataset, dict) else {}
    training_dict = training if isinstance(training, dict) else {}

    metadata = Path(dataset_dict.get("metadata", ""))
    audio_dir = Path(dataset_dict.get("audio_dir", ""))
    base_checkpoint = Path(training_dict.get("base_checkpoint", ""))

    if not metadata.is_file():
        errors.append(f"brak metadanych: {metadata}")
    if not audio_dir.is_dir():
        errors.append(f"brak katalogu nagrań: {audio_dir}")

    checkpoint_is_pointer = False
    if not base_checkpoint.is_file():
        errors.append(f"brak bazowego punktu kontrolnego: {base_checkpoint}")
    else:
        checkpoint_is_pointer = is_lfs_pointer(base_checkpoint)
        if checkpoint_is_pointer:
            errors.append(
                f"punkt kontrolny jest tylko wskaźnikiem Git LFS: {base_checkpoint}; "
                "wykonaj `git lfs pull`"
            )

    return metadata, audio_dir, base_checkpoint, checkpoint_is_pointer


def validate_audio_files(audio_dir: Path, errors: list[str]) -> None:
    """Sprawdź obecność plików WAV i przykładowe wskaźniki Git LFS."""
    if not audio_dir.is_dir():
        return

    wavs = sorted(audio_dir.glob("*.wav"))
    if not wavs:
        errors.append(f"brak plików WAV w {audio_dir}")
        return

    lfs_samples = [path for path in wavs[:20] if is_lfs_pointer(path)]
    if lfs_samples:
        errors.append(
            "nagrania WAV są nadal wskaźnikami Git LFS; wykonaj `git lfs pull` "
            "przed treningiem"
        )


def validate_python_modules(errors: list[str]) -> set[str]:
    """Sprawdź moduły wymagane przez środowisko trenowania."""
    missing: set[str] = set()
    for module in REQUIRED_MODULES:
        if importlib.util.find_spec(module) is None:
            missing.add(module)
            errors.append(
                f"brak modułu Python: {module}; zainstaluj projekt przez "
                "`python -m pip install -e '.[train]'`"
            )
    return missing


def validate_checkpoint_load(
    base_checkpoint: Path,
    checkpoint_is_pointer: bool,
    missing_modules: set[str],
    errors: list[str],
) -> None:
    """Spróbuj zdeserializować bazowy punkt kontrolny i odczytać jego epokę."""
    if (
        "torch" in missing_modules
        or not base_checkpoint.is_file()
        or checkpoint_is_pointer
    ):
        return

    try:
        import torch

        checkpoint = torch.load(
            base_checkpoint,
            map_location="cpu",
            weights_only=False,
        )
    except (OSError, RuntimeError, ValueError, TypeError) as exc:
        errors.append(
            "nie można zdeserializować bazowego punktu kontrolnego na tym systemie: "
            f"{exc}. Nie rozpoczynaj treningu, dopóki aktywny punkt kontrolny "
            "nie przejdzie tej kontroli"
        )
        return

    if not isinstance(checkpoint, dict) or "epoch" not in checkpoint:
        errors.append(
            "bazowy punkt kontrolny można odczytać, ale nie zawiera pola `epoch`"
        )
        return

    print(f"Bazowy punkt kontrolny: epoka {int(checkpoint['epoch'])}")


def validate_espeak(warnings: list[str]) -> None:
    """Sprawdź, czy program eSpeak NG jest dostępny w PATH."""
    if shutil.which("espeak-ng") is None:
        warnings.append(
            "nie znaleziono `espeak-ng` w PATH; Piper może korzystać z dołączonych "
            "danych, ale warto zweryfikować lokalną instalację"
        )


def validate_monotonic_align(errors: list[str]) -> None:
    """Sprawdź dostępność skompilowanego rozszerzenia monotonic_align."""
    try:
        from piper.train.vits.monotonic_align import core  # noqa: F401
    except (ImportError, ModuleNotFoundError, OSError) as exc:
        errors.append(
            "rozszerzenie monotonic_align nie jest gotowe: "
            f"{exc}; uruchom build_monotonic_align.sh i setup.py build_ext --inplace"
        )


def validate_free_space(training: Any, warnings: list[str]) -> None:
    """Oceń ilość wolnego miejsca dla katalogu wynikowego."""
    training_dict = training if isinstance(training, dict) else {}
    output_dir = Path(training_dict.get("output_dir", "output"))
    probe_dir = output_dir if output_dir.exists() else output_dir.parent
    if not probe_dir.exists():
        probe_dir = Path(".")

    try:
        usage = shutil.disk_usage(probe_dir)
    except OSError as exc:
        warnings.append(f"nie udało się sprawdzić wolnego miejsca: {exc}")
        return

    free_gib = usage.free / (1024**3)
    if free_gib < 20:
        warnings.append(
            f"mało wolnego miejsca: {free_gib:.1f} GiB; wielosesyjny trening "
            "może wymagać znacznie więcej"
        )


def parse_args() -> argparse.Namespace:
    """Wczytaj argumenty interfejsu wiersza poleceń."""
    parser = argparse.ArgumentParser(
        description="Sprawdź gotowość projektu do treningu Piper"
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--skip-audio",
        action="store_true",
        help="Nie sprawdzaj, czy nagrania WAV są pobrane z Git LFS",
    )
    parser.add_argument(
        "--skip-checkpoint-load",
        action="store_true",
        help="Nie deserializuj pełnego checkpointu PyTorch",
    )
    return parser.parse_args()


def main() -> int:
    """Wykonaj wszystkie kontrole gotowości i zwróć kod stanu."""
    args = parse_args()
    errors: list[str] = []
    warnings: list[str] = []

    if not args.config.is_file():
        print(f"BŁĄD: brak konfiguracji {args.config}", file=sys.stderr)
        return 2

    try:
        config = load_config(args.config)
    except RuntimeError as exc:
        print(f"BŁĄD: {exc}", file=sys.stderr)
        return 2

    validate_required_keys(config, errors)
    training = config.get("training", {})
    dataset = config.get("dataset", {})
    validate_session_plan(training, errors, warnings)
    _, audio_dir, base_checkpoint, checkpoint_is_pointer = validate_project_paths(
        dataset,
        training,
        errors,
    )

    if not args.skip_audio:
        validate_audio_files(audio_dir, errors)

    missing_modules = validate_python_modules(errors)
    if not args.skip_checkpoint_load:
        validate_checkpoint_load(
            base_checkpoint,
            checkpoint_is_pointer,
            missing_modules,
            errors,
        )

    validate_espeak(warnings)
    if "piper" not in missing_modules:
        validate_monotonic_align(errors)
    validate_free_space(training, warnings)

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
