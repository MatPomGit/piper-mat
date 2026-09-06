#!/usr/bin/env python3
"""Compatibility helpers for PyTorch/Lightning checkpoints across OSes."""

from __future__ import annotations

import os
import pathlib
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


@contextmanager
def checkpoint_path_compatibility() -> Iterator[None]:
    """Allow Windows to unpickle ``pathlib.PosixPath`` checkpoint values.

    Lightning checkpoints may contain ``Path`` objects in hyperparameters or
    callback state. A checkpoint created on Linux therefore serializes
    ``pathlib.PosixPath``. Constructing that class on Windows raises
    ``NotImplementedError`` before PyTorch can finish loading the checkpoint.

    While a checkpoint is being loaded on Windows, map the serialized
    ``PosixPath`` constructor to ``WindowsPath``. The original pathlib class is
    restored immediately afterwards.
    """
    if os.name != "nt":
        yield
        return

    original_posix_path = pathlib.PosixPath
    pathlib.PosixPath = pathlib.WindowsPath
    try:
        yield
    finally:
        pathlib.PosixPath = original_posix_path


def torch_load_checkpoint(path: Path, **kwargs: Any) -> Any:
    """Load a PyTorch checkpoint with cross-platform pathlib compatibility."""
    import torch

    with checkpoint_path_compatibility():
        return torch.load(path, **kwargs)
