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

CHUNK_SIZE = 1024 * 1024
COMMAND_TIMEOUT_SECONDS = 10


def parse_args() -> argparse.Namespace:
    """Odczytaj argumenty interfejsu wiersza poleceń."""
    parser = argparse.ArgumentParser(
        description=(
            "Zapisz wersje oprogramowania i identyfikatory danych "
            "użytych w eksperymencie."
        )
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/pl_PL-mateusz-medium.json"),
    )
    parser.add_argument(
        "--metadata",
        type=Path,
        default=Path("dataset/metadata.csv"),
    )
    parser.add_argument(
        "--splits",
        type=Path,
        default=Path("dataset/splits.json"),
    )
    return parser.parse_args()


def sha256_file(path: Path) -> str | None:
    """Zwróć SHA-256 pliku lub None, jeżeli plik nie istnieje."""
    if not path.is_file():
        return None

    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(CHUNK_SIZE), b""):
                digest.update(chunk)
    except OSError:
        return None
    return digest.hexdigest()


def command_output(command: list[str]) -> str | None:
    """Uruchom krótkie polecenie diagnostyczne i zwróć jego tekst."""
    if shutil.which(command[0]) is None:
        return None

    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=COMMAND_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None

    text = (result.stdout or result.stderr).strip()
    return text or None


def package_version(name: str) -> str | None:
    """Zwróć wersję zainstalowanego pakietu Pythona."""
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def input_record(path: Path) -> dict[str, str | None]:
    """Zbuduj rekord identyfikujący plik wejściowy eksperymentu."""
    return {
        "path": str(path),
        "sha256": sha256_file(path),
    }


def build_record(args: argparse.Namespace) -> dict[str, object]:
    """Zbuduj rekord środowiska i wejść eksperymentu."""
    return {
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
            "nvidia_smi": command_output(
                [
                    "nvidia-smi",
                    "--query-gpu=name,driver_version,memory.total",
                    "--format=csv,noheader",
                ]
            ),
        },
        "git": {
            "commit": command_output(["git", "rev-parse", "HEAD"]),
            "status": command_output(["git", "status", "--porcelain"]),
        },
        "inputs": {
            "config": input_record(args.config),
            "metadata": input_record(args.metadata),
            "splits": input_record(args.splits),
        },
    }


def main() -> int:
    """Zapisz rekord środowiska eksperymentu."""
    args = parse_args()
    record = build_record(args)

    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(record, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        print(f"BŁĄD: nie można zapisać rekordu środowiska: {exc}", file=sys.stderr)
        return 2

    print(f"Zapisano rekord środowiska: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
