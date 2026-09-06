#!/usr/bin/env python3
"""Run ``piper.train`` with cross-platform checkpoint path compatibility."""

from __future__ import annotations

import runpy

from checkpoint_compat import checkpoint_path_compatibility


def main() -> int:
    """Execute Piper's training CLI while Windows can load POSIX checkpoints."""
    with checkpoint_path_compatibility():
        runpy.run_module("piper.train", run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
