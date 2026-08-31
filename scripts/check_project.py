#!/usr/bin/env python3
"""Lightweight repository integrity checks suitable for CI."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "pl_PL-mateusz-medium.json"

REQUIRED = [
    ROOT / "COPYING",
    ROOT / "dataset" / "DATASET_CARD.md",
    ROOT / "models" / "pl_PL-mateusz-medium" / "MODEL_CARD.md",
    ROOT / "docs" / "ROADMAP.md",
    ROOT / "dataset" / "metadata.csv",
    ROOT / "train.sh",
]


def main() -> int:
    errors: list[str] = []

    for path in REQUIRED:
        if not path.exists():
            errors.append(f"missing required path: {path.relative_to(ROOT)}")

    if not CONFIG.is_file():
        errors.append("missing voice config: configs/pl_PL-mateusz-medium.json")
    else:
        try:
            data = json.loads(CONFIG.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"invalid JSON config: {exc}")
        else:
            expected = {
                "language": "pl_PL",
                "quality": "medium",
                "sample_rate": 22050,
                "espeak_voice": "pl",
            }
            for key, value in expected.items():
                if data.get(key) != value:
                    errors.append(f"config {key!r}: expected {value!r}, got {data.get(key)!r}")
            export = data.get("export", {})
            if export.get("model_filename") != "pl_PL-mateusz-medium.onnx":
                errors.append("unexpected ONNX model filename in config")
            if export.get("config_filename") != "pl_PL-mateusz-medium.onnx.json":
                errors.append("unexpected ONNX JSON filename in config")

    if (ROOT / "LICENSE").exists():
        errors.append("ambiguous top-level LICENSE exists; code licence is GPL-3.0-or-later in COPYING")

    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if errors:
        return 1

    print("Project integrity checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
