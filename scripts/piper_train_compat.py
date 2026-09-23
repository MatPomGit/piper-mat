#!/usr/bin/env python3
"""Run piper.train with compatibility for trusted legacy Piper checkpoints."""

from __future__ import annotations

import inspect
import logging
import runpy
import sys
import tempfile
from pathlib import Path
from typing import Any

from checkpoint_compat import checkpoint_path_compatibility, torch_load_checkpoint

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
        name
        for name in sanitized
        if isinstance(name, str) and name not in valid_names
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


def main() -> int:
    """Execute Piper training with legacy-checkpoint compatibility."""
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


if __name__ == "__main__":
    raise SystemExit(main())
