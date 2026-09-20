#!/usr/bin/env python3
"""Run piper.train with compatibility for older Piper checkpoints."""

from __future__ import annotations

import inspect
import runpy
import sys
from pathlib import Path
from typing import Any

from checkpoint_compat import checkpoint_path_compatibility, torch_load_checkpoint

_LEGACY_MODEL_PARAMETERS: dict[str, tuple[Any, type[Any] | Any]] = {
    "dataset_dir": (None, Any),
    "checkpoint_epochs": (None, Any),
    "quality": (None, Any),
    "sample_bytes": (None, Any),
    "channels": (None, Any),
    "num_workers": (None, Any),
    "seed": (None, Any),
    "num_test_examples": (None, Any),
    "validation_split": (None, Any),
    "max_phoneme_ids": (None, Any),
}


def _checkpoint_path_from_argv(argv: list[str] | None = None) -> Path | None:
    """Extract --ckpt_path from the LightningCLI command line."""
    args = list(sys.argv[1:] if argv is None else argv)
    for index, argument in enumerate(args):
        if argument == "--ckpt_path" and index + 1 < len(args):
            return Path(args[index + 1])
        if argument.startswith("--ckpt_path="):
            return Path(argument.split("=", 1)[1])
    return None


def _checkpoint_hyperparameters(path: Path | None) -> dict[str, Any]:
    """Read legacy model hyperparameters from a trusted checkpoint."""
    if path is None or not path.is_file():
        return {}

    try:
        checkpoint = torch_load_checkpoint(
            path,
            map_location="cpu",
            weights_only=False,
        )
    except (OSError, RuntimeError, ValueError, TypeError):
        return {}

    if not isinstance(checkpoint, dict):
        return {}
    hyperparameters = checkpoint.get("hyper_parameters", {})
    return hyperparameters if isinstance(hyperparameters, dict) else {}


def _compatibility_parameters(path: Path | None) -> dict[str, tuple[Any, Any]]:
    """Build a complete set of synthetic parameters accepted by LightningCLI."""
    parameters = dict(_LEGACY_MODEL_PARAMETERS)
    for name in _checkpoint_hyperparameters(path):
        if not isinstance(name, str) or not name.isidentifier():
            continue
        parameters.setdefault(name, (None, Any))
    return parameters


def enable_legacy_checkpoint_hyperparameters(
    checkpoint_path: Path | None = None,
) -> None:
    """Expose obsolete checkpoint fields to LightningCLI's model parser.

    Old Piper checkpoints can contain a snapshot of many CLI arguments under
    hyper_parameters. Newer Piper/Lightning versions validate those keys
    against VitsModel.__init__ before restoring --ckpt_path. Rather than fixing
    failures one key at a time, inspect the checkpoint and expose every obsolete
    top-level key as a synthetic keyword-only parameter.

    VitsModel already accepts **kwargs, so this changes parser compatibility
    only; it does not rewrite the checkpoint and does not discard optimizer state.
    """
    from piper.train.vits.lightning import VitsModel

    current = inspect.signature(VitsModel.__init__)
    compatibility = _compatibility_parameters(checkpoint_path)
    if all(name in current.parameters for name in compatibility):
        return

    parameters: list[inspect.Parameter] = []
    inserted = False
    for parameter in current.parameters.values():
        if parameter.kind is inspect.Parameter.VAR_KEYWORD and not inserted:
            for name, (default, annotation) in compatibility.items():
                if name in current.parameters:
                    continue
                parameters.append(
                    inspect.Parameter(
                        name,
                        kind=inspect.Parameter.KEYWORD_ONLY,
                        default=default,
                        annotation=annotation,
                    )
                )
            inserted = True
        parameters.append(parameter)

    VitsModel.__init__.__signature__ = current.replace(parameters=parameters)


def main() -> int:
    """Execute Piper's training CLI with checkpoint compatibility enabled."""
    checkpoint_path = _checkpoint_path_from_argv()
    enable_legacy_checkpoint_hyperparameters(checkpoint_path)
    with checkpoint_path_compatibility():
        runpy.run_module("piper.train", run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
