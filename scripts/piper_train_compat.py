#!/usr/bin/env python3
"""Run piper.train with compatibility for trusted legacy Piper checkpoints."""

from __future__ import annotations

import inspect
import json
import logging
import runpy
import sys
import tempfile
from pathlib import Path
from typing import Any

if __package__:
    from .checkpoint_compat import (
        checkpoint_path_compatibility,
        torch_load_checkpoint,
    )
    from .session_lock import delegated_lock_directory, training_session_lock
    from .train_voice import state_dir_for_config
else:
    from checkpoint_compat import checkpoint_path_compatibility, torch_load_checkpoint
    from session_lock import delegated_lock_directory, training_session_lock
    from train_voice import state_dir_for_config

PROJECT_CONFIG_DEFAULT = Path("configs/pl_PL-mateusz-medium.json")

_LOGGER = logging.getLogger("piper_mat.checkpoint_compat")


def _checkpoint_path_from_argv(argv: list[str] | None = None) -> Path | None:
    """Extract --ckpt_path from the LightningCLI command line."""
    args = list(sys.argv[1:] if argv is None else argv)
    for index, argument in enumerate(args):
        if argument == "--ckpt_path" and index + 1 < len(args):
            return Path(args[index + 1])
        if argument.startswith("--ckpt_path="):
            return Path(argument.split("=", 1)[1])
    return None


def _replace_checkpoint_path(path: Path, argv: list[str] | None = None) -> None:
    """Replace --ckpt_path in-place with a compatibility checkpoint path."""
    args = sys.argv if argv is None else argv
    for index, argument in enumerate(args):
        if argument == "--ckpt_path" and index + 1 < len(args):
            args[index + 1] = str(path)
            return
        if argument.startswith("--ckpt_path="):
            args[index] = f"--ckpt_path={path}"
            return


def _ensure_full_checkpoint_restore(argv: list[str] | None = None) -> None:
    """Tell Lightning to restore the trusted checkpoint with weights_only=False."""
    args = sys.argv if argv is None else argv
    if "--weights_only" in args or any(
        argument.startswith("--weights_only=") for argument in args
    ):
        return
    args.extend(["--weights_only", "false"])


def _valid_model_hyperparameter_names() -> set[str]:
    """Return explicit VitsModel constructor parameters accepted by jsonargparse."""
    from piper.train.vits.lightning import VitsModel

    signature = inspect.signature(VitsModel.__init__)
    return {
        name
        for name, parameter in signature.parameters.items()
        if name != "self"
        and parameter.kind
        not in {
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        }
    }


def _sanitize_hyperparameters(
    hyperparameters: dict[str, Any],
    valid_names: set[str],
) -> tuple[dict[str, Any], list[str]]:
    """Remove legacy model arguments rejected by current LightningCLI."""
    sanitized = dict(hyperparameters)
    removed = sorted(
        name for name in sanitized if isinstance(name, str) and name not in valid_names
    )
    for name in removed:
        sanitized.pop(name, None)
    return sanitized, removed


def _prepare_checkpoint_for_lightning(path: Path) -> tuple[Path, Path | None]:
    """Create a temporary parser-compatible copy of a trusted old checkpoint.

    New Lightning versions inspect hyper_parameters before constructing the
    model and reject historical Piper options such as sample_bytes or
    checkpoint_epochs. The checkpoint is loaded explicitly with
    weights_only=False because this repository controls and trusts the project
    checkpoint. Model weights, optimizer state, scheduler state and epoch
    counters are preserved unchanged; only obsolete constructor
    hyperparameters are removed.
    """
    if not path.is_file():
        return path, None

    checkpoint = torch_load_checkpoint(
        path,
        map_location="cpu",
        weights_only=False,
    )
    if not isinstance(checkpoint, dict):
        return path, None

    hyperparameters = checkpoint.get("hyper_parameters")
    if not isinstance(hyperparameters, dict):
        return path, None

    sanitized, removed = _sanitize_hyperparameters(
        hyperparameters,
        _valid_model_hyperparameter_names(),
    )
    if not removed:
        return path, None

    checkpoint = dict(checkpoint)
    checkpoint["hyper_parameters"] = sanitized

    import torch

    handle = tempfile.NamedTemporaryFile(
        prefix="piper_mat_compat_",
        suffix=".ckpt",
        delete=False,
    )
    temporary_path = Path(handle.name)
    handle.close()

    try:
        torch.save(checkpoint, temporary_path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise

    _LOGGER.info(
        "Usunięto nieaktualne hiperparametry checkpointu: %s",
        ", ".join(removed),
    )
    _LOGGER.info(
        "Utworzono tymczasowy checkpoint zgodności: %s",
        temporary_path,
    )
    return temporary_path, temporary_path


def _take_project_config_arg(argv: list[str] | None = None) -> Path:
    """Usuń opcję projektu przed wywołaniem parsera biblioteki Lightning."""
    args = sys.argv if argv is None else argv
    config_path = PROJECT_CONFIG_DEFAULT
    for index in range(1, len(args)):
        argument = args[index]
        if argument == "--piper-mat-config":
            if index + 1 >= len(args):
                raise ValueError("brak ścieżki po --piper-mat-config")
            config_path = Path(args[index + 1])
            del args[index : index + 2]
            return config_path
        if argument.startswith("--piper-mat-config="):
            config_path = Path(argument.split("=", 1)[1])
            del args[index]
            return config_path
    return config_path


def _state_dir_from_project_file(path: Path) -> Path:
    """Wczytaj katalog blokady z konfiguracji tego samego projektu."""
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(config, dict):
            raise ValueError("konfiguracja musi być obiektem JSON")
        return state_dir_for_config(config)
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise ValueError(
            f"nie można ustalić blokady na podstawie {path}: {exc}"
        ) from exc


def _run_compatible_training() -> int:
    """Wykonaj właściwe trenowanie po ustaleniu wyłączności sesji."""
    logging.basicConfig(level=logging.INFO)
    checkpoint_path = _checkpoint_path_from_argv()
    temporary_path: Path | None = None

    try:
        if checkpoint_path is not None:
            compatible_path, temporary_path = _prepare_checkpoint_for_lightning(
                checkpoint_path
            )
            _replace_checkpoint_path(compatible_path)
            _ensure_full_checkpoint_restore()

        with checkpoint_path_compatibility():
            runpy.run_module("piper.train", run_name="__main__")
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    return 0


def main() -> int:
    """Uruchom trening bezpośredni pod tą samą blokadą co menedżer."""
    try:
        config_path = _take_project_config_arg()
        if delegated_lock_directory() is not None:
            return _run_compatible_training()

        if "--help" in sys.argv or "-h" in sys.argv:
            return _run_compatible_training()

        state_dir = _state_dir_from_project_file(config_path)
    except ValueError as exc:
        print(f"BŁĄD: {exc}", file=sys.stderr)
        return 2

    try:
        with training_session_lock(state_dir):
            return _run_compatible_training()
    except RuntimeError as exc:
        if "Nie można uzyskać blokady treningu" not in str(exc):
            raise
        print(f"BŁĄD: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
