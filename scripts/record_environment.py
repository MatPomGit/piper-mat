#!/usr/bin/env python3
"""Zapisz środowisko wykonawcze eksperymentu do pliku JSON."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import re
import shutil
import stat
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

CHUNK_SIZE = 1024 * 1024
COMMAND_TIMEOUT_SECONDS = 10
FULL_GIT_SHA_PATTERN = re.compile(r"[0-9a-f]{40}")
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")


class InputFileError(ValueError):
    """Sygnalizuj, że wymaganego pliku wejściowego nie można zidentyfikować."""


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


def sha256_file(path: Path) -> str:
    """Zwróć SHA-256 wymaganego, zwykłego pliku.

    Brak pliku, niewłaściwy typ ścieżki i błąd odczytu są zgłaszane osobno,
    aby wywołujący nie pomylił ich z poprawnie obliczoną sumą.
    """
    try:
        path_stat = path.stat()
    except FileNotFoundError as exc:
        raise InputFileError(f"wymagany plik nie istnieje: {path}") from exc
    except OSError as exc:
        raise InputFileError(
            f"nie można sprawdzić wymaganego pliku {path}: {exc}"
        ) from exc

    if not stat.S_ISREG(path_stat.st_mode):
        raise InputFileError(f"wymagana ścieżka nie jest plikiem: {path}")

    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(CHUNK_SIZE), b""):
                digest.update(chunk)
    except OSError as exc:
        raise InputFileError(
            f"nie można odczytać wymaganego pliku {path}: {exc}"
        ) from exc

    checksum = digest.hexdigest()
    if SHA256_PATTERN.fullmatch(checksum) is None:
        raise InputFileError(f"niepoprawna suma SHA-256 pliku: {path}")
    return checksum


def command_output(
    command: list[str], warnings: list[str]
) -> dict[str, bool | int | str | None]:
    """Uruchom polecenie i zwróć uporządkowany rekord wyniku."""
    command_name = command[0]
    if shutil.which(command[0]) is None:
        error = f"program {command_name!r} nie jest dostępny"
        warnings.append(error)
        return {
            "available": False,
            "exit_code": None,
            "stdout": None,
            "error": error,
        }

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
    except subprocess.TimeoutExpired:
        error = (
            f"polecenie {command_name!r} przekroczyło limit "
            f"{COMMAND_TIMEOUT_SECONDS} s"
        )
        warnings.append(error)
        return {
            "available": False,
            "exit_code": None,
            "stdout": None,
            "error": error,
        }
    except OSError as exc:
        error = f"nie udało się uruchomić programu {command_name!r}: {exc}"
        warnings.append(error)
        return {
            "available": False,
            "exit_code": None,
            "stdout": None,
            "error": error,
        }

    stdout = result.stdout.strip() or None
    stderr = result.stderr.strip() or None
    if result.returncode != 0:
        error = stderr or (
            f"polecenie {command_name!r} zakończyło się kodem "
            f"{result.returncode}"
        )
        warnings.append(error)
        return {
            "available": False,
            "exit_code": result.returncode,
            "stdout": stdout,
            "error": error,
        }

    return {
        "available": True,
        "exit_code": result.returncode,
        "stdout": stdout,
        "error": stderr,
    }


def git_commit_record(warnings: list[str]) -> dict[str, bool | int | str | None]:
    """Zwróć rekord pełnego identyfikatora zatwierdzenia Git."""
    result = command_output(["git", "rev-parse", "HEAD"], warnings)
    commit = result["stdout"]
    if result["available"] and (
        not isinstance(commit, str) or FULL_GIT_SHA_PATTERN.fullmatch(commit) is None
    ):
        error = "Git nie zwrócił pełnego, 40-znakowego skrótu SHA"
        warnings.append(error)
        result["available"] = False
        result["error"] = error
    return result


def package_version(name: str) -> str | None:
    """Zwróć wersję zainstalowanego pakietu Pythona."""
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def input_record(path: Path) -> dict[str, str]:
    """Zbuduj rekord identyfikujący plik wejściowy eksperymentu."""
    return {
        "path": str(path),
        "sha256": sha256_file(path),
    }


def build_record(args: argparse.Namespace) -> dict[str, object]:
    """Zbuduj rekord środowiska i wejść eksperymentu."""
    inputs = {
        "config": input_record(args.config),
        "metadata": input_record(args.metadata),
        "splits": input_record(args.splits),
    }
    warnings: list[str] = []
    return {
        "schema_version": 2,
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
            "espeak_ng": command_output(["espeak-ng", "--version"], warnings),
            "nvidia_smi": command_output(
                [
                    "nvidia-smi",
                    "--query-gpu=name,driver_version,memory.total",
                    "--format=csv,noheader",
                ],
                warnings,
            ),
        },
        "git": {
            "commit": git_commit_record(warnings),
            "status": command_output(["git", "status", "--porcelain"], warnings),
        },
        "inputs": inputs,
        "warnings": warnings,
    }


def main() -> int:
    """Zapisz rekord środowiska eksperymentu."""
    args = parse_args()
    try:
        record = build_record(args)
    except InputFileError as exc:
        print(f"BŁĄD: {exc}", file=sys.stderr)
        return 2

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
