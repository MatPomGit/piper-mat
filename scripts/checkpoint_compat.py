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
    """Allow Windows to load trusted checkpoints created on POSIX systems.

    Linux-created Lightning checkpoints may contain ``pathlib.PosixPath``.
    Windows cannot instantiate that class. PyTorch 2.6+ also uses
    ``weights_only=True`` in Lightning's checkpoint pre-parser, so merely
    monkey-patching ``pathlib.PosixPath`` is insufficient: the serialized
    global must also be explicitly allowlisted.

    On Windows this context maps the serialized global name
    ``pathlib.PosixPath`` to ``pathlib.WindowsPath`` in PyTorch's restricted
    unpickler and temporarily maps the pathlib attribute itself to
    ``WindowsPath``. This keeps both ``weights_only=True`` and normal pickle
    loading compatible with the trusted project checkpoint.
    """
    if os.name != "nt":
        yield
        return

    original_posix_path = pathlib.PosixPath
    windows_path = pathlib.WindowsPath

    try:
        import torch
    except ImportError:
        torch = None  # type: ignore[assignment]

    safe_globals_context = None
    if torch is not None:
        serialization = getattr(torch, "serialization", None)
        safe_globals_factory = getattr(serialization, "safe_globals", None)
        if safe_globals_factory is not None:
            # PyTorch 2.6+ accepts (callable, serialized_full_name) tuples.
            # The checkpoint names pathlib.PosixPath, but on Windows it must
            # actually construct pathlib.WindowsPath.
            safe_globals_context = safe_globals_factory(
                [
                    windows_path,
                    (windows_path, "pathlib.PosixPath"),
                ]
            )
            safe_globals_context.__enter__()

    pathlib.PosixPath = windows_path
    try:
        yield
    finally:
        pathlib.PosixPath = original_posix_path
        if safe_globals_context is not None:
            safe_globals_context.__exit__(None, None, None)


def torch_load_checkpoint(path: Path, **kwargs: Any) -> Any:
    """Load a trusted PyTorch checkpoint with cross-platform path support."""
    import torch

    with checkpoint_path_compatibility():
        return torch.load(path, **kwargs)
