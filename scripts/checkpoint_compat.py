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
    """Allow Windows to load checkpoints created on POSIX systems.

    Lightning checkpoints may contain ``pathlib.PosixPath`` values. On Windows,
    constructing ``PosixPath`` raises ``NotImplementedError``. PyTorch 2.6+
    additionally defaults ``torch.load`` to ``weights_only=True`` in several
    Lightning code paths, which rejects ``PosixPath`` unless explicitly
    allowlisted.

    This context therefore does two things on Windows:
    1. maps the serialized ``PosixPath`` constructor to ``WindowsPath``;
    2. temporarily adds the original serialized ``PosixPath`` global to
       PyTorch's safe-globals allowlist when that API is available.

    The compatibility scope is intentionally limited to trusted project
    checkpoints and all global state is restored afterwards.
    """
    if os.name != "nt":
        yield
        return

    original_posix_path = pathlib.PosixPath

    try:
        import torch
    except ImportError:
        torch = None  # type: ignore[assignment]

    safe_globals = None
    if torch is not None:
        serialization = getattr(torch, "serialization", None)
        safe_globals_factory = getattr(serialization, "safe_globals", None)
        if safe_globals_factory is not None:
            safe_globals = safe_globals_factory([original_posix_path])
            safe_globals.__enter__()

    pathlib.PosixPath = pathlib.WindowsPath
    try:
        yield
    finally:
        pathlib.PosixPath = original_posix_path
        if safe_globals is not None:
            safe_globals.__exit__(None, None, None)


def torch_load_checkpoint(path: Path, **kwargs: Any) -> Any:
    """Load a trusted PyTorch checkpoint with cross-platform path support."""
    import torch

    with checkpoint_path_compatibility():
        return torch.load(path, **kwargs)
