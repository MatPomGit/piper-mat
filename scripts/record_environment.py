#!/usr/bin/env python3
"""Zapisz środowisko wykonawcze eksperymentu do pliku JSON."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def command_output(command: list[str]) -> str | None:
    if not shutil.which(command[0]):
        return None
    try:
        result = subprocess.run(command, check=False, capture_output=True, text=True, timeout=10)
    except OSError:
        return None
    text = (result.stdout or result.stderr).strip()
    return text or None


def package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Zapisz wersje oprogramowania i identyfikatory danych użytych w eksperymencie")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=Path("configs/pl_PL-mateusz-medium.json"))
    parser.add_argument("--metadata", type=Path, default=Path("dataset/metadata.csv"))
    parser.add_argument("--splits", type=Path, default=Path("dataset/splits.json"))
    args = parser.parse_args()

    record = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python": sys.version,
        },
        "software": {
            "piper_tts": package_version("piper-tts"),
            "torch": package_version("torch"),
            "pytorch_lightning": package_version("pytorch-lightning"),
            "onnxruntime": package_version("onnxruntime"),
            "espeak_ng": command_output(["espeak-ng", "--version"]),
            "nvidia_smi": command_output(["nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"]),
        },
        "git": {
            "commit": command_output(["git", "rev-parse", "HEAD"]),
            "status": command_output(["git", "status", "--porcelain"]),
        },
        "inputs": {
            "config": {"path": str(args.config), "sha256": sha256(args.config)},
            "metadata": {"path": str(args.metadata), "sha256": sha256(args.metadata)},
            "splits": {"path": str(args.splits), "sha256": sha256(args.splits)},
        },
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Zapisano rekord środowiska: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
