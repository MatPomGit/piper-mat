#!/usr/bin/env python3
"""Run ``piper.train`` with compatibility for older Piper checkpoints."""

from __future__ import annotations

import inspect
import runpy
from typing import Any

from checkpoint_compat import checkpoint_path_compatibility

# Older Piper checkpoints stored these model hyperparameters directly in
# ``hyper_parameters``.  The current VitsModel accepts arbitrary **kwargs at
# runtime, but LightningCLI validates checkpoint hyperparameters against the
# introspected constructor signature before model construction.  Registering
# the removed parameters in the signature lets Lightning resume a trusted old
# checkpoint without rewriting the checkpoint or discarding optimizer state.
_LEGACY_MODEL_PARAMETERS: dict[str, tuple[Any, type[Any] | Any]] = {
    # Older checkpoints may contain a dataset path in model hyperparameters.
    # Dataset configuration now belongs to the data module, but LightningCLI
    # still validates checkpoint metadata before constructing VitsModel.
    # ``object`` deliberately accepts pathlib.Path values serialized by older
    # Linux training runs as well as plain strings.
    "dataset_dir": (None, object),
    # Legacy Piper checkpoints may also persist how often training wrote
    # checkpoints. This is a training/Trainer concern in current Piper, but
    # LightningCLI validates the old value as a model hyperparameter while
    # restoring --ckpt_path, so expose it only for compatibility.
    "checkpoint_epochs": (None, int | None),
    "sample_bytes": (2, int),
    "channels": (1, int),
    "num_workers": (1, int),
    "seed": (1234, int),
    "num_test_examples": (5, int),
    "validation_split": (0.1, float),
    "max_phoneme_ids": (None, int | None),
}


def enable_legacy_checkpoint_hyperparameters() -> None:
    """Expose removed Piper model arguments to LightningCLI's parser.

    ``VitsModel.__init__`` still has ``**kwargs``, so no model implementation
    change is required.  We only extend the public signature used by
    jsonargparse/LightningCLI when it pre-parses ``--ckpt_path`` metadata.
    """
    from piper.train.vits.lightning import VitsModel

    current = inspect.signature(VitsModel.__init__)
    if all(name in current.parameters for name in _LEGACY_MODEL_PARAMETERS):
        return

    parameters: list[inspect.Parameter] = []
    inserted = False
    for parameter in current.parameters.values():
        if parameter.kind is inspect.Parameter.VAR_KEYWORD and not inserted:
            for name, (default, annotation) in _LEGACY_MODEL_PARAMETERS.items():
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
    enable_legacy_checkpoint_hyperparameters()
    with checkpoint_path_compatibility():
        runpy.run_module("piper.train", run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
