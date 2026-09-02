#!/usr/bin/env python3
"""Diagnose and safely repair the piper-mat environment on Windows 11."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
VENV = ROOT / ".venv"
VENV_PYTHON = VENV / "Scripts" / "python.exe"
CONFIG = ROOT / "configs" / "pl_PL-mateusz-medium.json"
MIN_FREE_GIB = 30.0
COMMAND_FAILURE = 999


@dataclass
class Check:
    """Represent one diagnostic check result."""

    id: str
    title: str
    status: str
    message: str
    repairable: bool = False


def run(
    command: list[str],
    cwd: Path | None = None,
    timeout: int = 120,
) -> tuple[int, str]:
    """Run a command and return its exit code and combined output."""
    try:
        process = subprocess.run(
            command,
            cwd=str(cwd or ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return COMMAND_FAILURE, str(exc)

    output = (process.stdout + "\n" + process.stderr).strip()
    return process.returncode, output


def is_lfs_pointer(path: Path) -> bool:
    """Return whether a file contains a Git LFS pointer instead of real data."""
    try:
        return path.read_bytes()[:80].startswith(
            b"version https://git-lfs.github.com/spec/v1"
        )
    except OSError:
        return False


def refresh_path() -> None:
    """Reload machine and user PATH values into the current Windows process."""
    if os.name != "nt":
        return

    command_prefix = ["powershell", "-NoProfile", "-Command"]
    try:
        machine = subprocess.check_output(
            command_prefix
            + ["[Environment]::GetEnvironmentVariable('Path','Machine')"],
            text=True,
            encoding="utf-8",
            errors="replace",
        ).strip()
        user = subprocess.check_output(
            command_prefix
            + ["[Environment]::GetEnvironmentVariable('Path','User')"],
            text=True,
            encoding="utf-8",
            errors="replace",
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return

    os.environ["PATH"] = machine + os.pathsep + user


def check_windows() -> Check:
    """Check whether the script is running on Windows."""
    if os.name == "nt":
        return Check("windows", "Windows", "ok", "System Windows wykryty.")
    return Check(
        "windows",
        "Windows",
        "error",
        "Ten zestaw napraw jest przeznaczony dla Windows.",
    )


def check_python() -> Check:
    """Check whether the running Python version meets project requirements."""
    version = sys.version.split()[0]
    if sys.version_info >= (3, 11):
        return Check("python", "Python", "ok", f"Python {version} jest odpowiedni.")
    return Check(
        "python",
        "Python",
        "error",
        f"Python {version} jest za stary. Wymagany jest Python 3.11 lub nowszy.",
    )


def check_git() -> tuple[Check, str | None]:
    """Check Git availability and return its executable path when found."""
    git = shutil.which("git")
    if not git:
        return (
            Check("git", "Git", "error", "Nie znaleziono Git for Windows w PATH."),
            None,
        )

    return_code, output = run([git, "--version"])
    check = Check(
        "git",
        "Git",
        "ok" if return_code == 0 else "error",
        output or "Git znaleziony.",
    )
    return check, git


def check_git_lfs(git: str | None) -> Check | None:
    """Check Git LFS when Git is available."""
    if git is None:
        return None

    return_code, output = run([git, "lfs", "version"])
    if return_code == 0:
        return Check("lfs", "Git LFS", "ok", output)
    return Check(
        "lfs",
        "Git LFS",
        "error",
        "Git LFS nie działa. Można spróbować naprawy.",
        True,
    )


def check_disk_space() -> Check:
    """Check whether enough free disk space is available for training."""
    try:
        free_gib = shutil.disk_usage(ROOT).free / (1024**3)
    except OSError as exc:
        return Check(
            "disk",
            "Wolne miejsce",
            "warning",
            f"Nie udało się sprawdzić dysku: {exc}",
        )

    if free_gib >= MIN_FREE_GIB:
        status = "ok"
    elif free_gib >= 15:
        status = "warning"
    else:
        status = "error"

    return Check(
        "disk",
        "Wolne miejsce",
        status,
        (
            f"Wolne miejsce na dysku: {free_gib:.1f} GiB. Zalecane minimum "
            f"przed trenowaniem: {MIN_FREE_GIB:.0f} GiB."
        ),
    )


def check_repository(git: str | None) -> list[Check]:
    """Check repository presence and local working-tree status."""
    if not (ROOT / ".git").is_dir():
        return [
            Check(
                "repo",
                "Repozytorium",
                "error",
                "Ten folder nie zawiera katalogu .git.",
            )
        ]

    checks = [
        Check(
            "repo",
            "Repozytorium",
            "ok",
            "Folder jest prawidłowym repozytorium Git.",
        )
    ]
    if git is None:
        return checks

    return_code, output = run(
        [git, "status", "--porcelain=v1"],
        timeout=30,
    )
    if return_code != 0:
        checks.append(
            Check(
                "repo_status",
                "Stan Git",
                "error",
                "Git nie potrafi odczytać stanu repozytorium.",
            )
        )
    elif output.strip():
        checks.append(
            Check(
                "repo_status",
                "Stan Git",
                "warning",
                "W repozytorium są lokalne zmiany. Kreator ich nie usunie.",
            )
        )
    else:
        checks.append(
            Check(
                "repo_status",
                "Stan Git",
                "ok",
                "Brak niezatwierdzonych zmian w śledzonych plikach.",
            )
        )
    return checks


def check_venv() -> Check:
    """Check whether the project virtual environment is present and usable."""
    if not VENV_PYTHON.is_file():
        return Check(
            "venv",
            "Środowisko .venv",
            "error",
            "Brak środowiska .venv.",
            True,
        )

    return_code, _ = run(
        [str(VENV_PYTHON), "-c", "import sys, pip; print(sys.version)"],
        timeout=30,
    )
    if return_code == 0:
        return Check("venv", "Środowisko .venv", "ok", "Środowisko .venv działa.")
    return Check(
        "venv",
        "Środowisko .venv",
        "error",
        "Środowisko .venv jest uszkodzone lub niekompletne.",
        True,
    )


def check_training_dependencies() -> list[Check]:
    """Check training libraries, CUDA support, and monotonic_align."""
    if not VENV_PYTHON.is_file():
        return []

    checks: list[Check] = []
    return_code, _ = run(
        [
            str(VENV_PYTHON),
            "-c",
            "import piper, lightning, tensorboard, librosa; print('OK')",
        ],
        timeout=60,
    )
    checks.append(
        Check(
            "deps",
            "Biblioteki treningowe",
            "ok" if return_code == 0 else "error",
            (
                "Biblioteki treningowe są dostępne."
                if return_code == 0
                else "Brakuje części bibliotek lub instalacja jest uszkodzona."
            ),
            return_code != 0,
        )
    )

    return_code, output = run(
        [
            str(VENV_PYTHON),
            "-c",
            (
                "import torch; print(torch.__version__); "
                "print('CUDA', torch.cuda.is_available()); print(torch.version.cuda)"
            ),
        ],
        timeout=60,
    )
    if return_code == 0:
        cuda_ok = "CUDA True" in output
        checks.append(
            Check(
                "cuda",
                "PyTorch i CUDA",
                "ok" if cuda_ok else "warning",
                (
                    output
                    if cuda_ok
                    else "PyTorch działa, ale nie widzi CUDA. Sprawdź sterownik "
                    "NVIDIA i zgodność wersji PyTorch/CUDA."
                ),
            )
        )
    else:
        checks.append(
            Check(
                "cuda",
                "PyTorch i CUDA",
                "error",
                "Nie można uruchomić PyTorch.",
                True,
            )
        )

    return_code, _ = run(
        [
            str(VENV_PYTHON),
            "-c",
            "from piper.train.vits.monotonic_align import core; print('OK')",
        ],
        timeout=30,
    )
    checks.append(
        Check(
            "align",
            "monotonic_align",
            "ok" if return_code == 0 else "error",
            (
                "Moduł monotonic_align działa."
                if return_code == 0
                else "Moduł monotonic_align nie jest zbudowany."
            ),
            return_code != 0,
        )
    )
    return checks


def check_checkpoint() -> list[Check]:
    """Validate the configured base checkpoint and its Git LFS state."""
    if not CONFIG.is_file():
        return [
            Check(
                "config",
                "Konfiguracja",
                "error",
                f"Brak konfiguracji: {CONFIG.relative_to(ROOT)}",
            )
        ]

    try:
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        checkpoint_value = config.get("training", {}).get("base_checkpoint", "")
        checkpoint = ROOT / checkpoint_value
    except (OSError, json.JSONDecodeError, TypeError) as exc:
        return [
            Check(
                "config",
                "Konfiguracja",
                "error",
                f"Nie można odczytać konfiguracji: {exc}",
            )
        ]

    if checkpoint.is_file() and not is_lfs_pointer(checkpoint):
        return [
            Check(
                "checkpoint",
                "Bazowy punkt kontrolny",
                "ok",
                f"Punkt kontrolny jest pobrany: {checkpoint.name}.",
            )
        ]
    if checkpoint.is_file():
        return [
            Check(
                "checkpoint",
                "Bazowy punkt kontrolny",
                "error",
                "Punkt kontrolny jest tylko wskaźnikiem Git LFS.",
                True,
            )
        ]
    return [
        Check(
            "checkpoint",
            "Bazowy punkt kontrolny",
            "error",
            "Brak bazowego punktu kontrolnego.",
            True,
        )
    ]


def check_audio() -> Check:
    """Check whether WAV files are present and materialized from Git LFS."""
    wav_dir = ROOT / "dataset" / "wavs"
    wav_files = list(wav_dir.glob("*.wav")) if wav_dir.is_dir() else []
    if not wav_files:
        return Check(
            "audio",
            "Nagrania WAV",
            "error",
            "Brak nagrań WAV.",
            True,
        )
    if any(is_lfs_pointer(path) for path in wav_files[:50]):
        return Check(
            "audio",
            "Nagrania WAV",
            "error",
            "Część nagrań to nadal wskaźniki Git LFS.",
            True,
        )
    return Check(
        "audio",
        "Nagrania WAV",
        "ok",
        f"Znaleziono {len(wav_files)} plików WAV.",
    )


def check_all() -> list[Check]:
    """Run all diagnostics in a stable, user-facing order."""
    checks = [check_windows(), check_python()]

    git_check, git = check_git()
    checks.append(git_check)

    lfs_check = check_git_lfs(git)
    if lfs_check is not None:
        checks.append(lfs_check)

    checks.append(check_disk_space())
    checks.extend(check_repository(git))
    checks.append(check_venv())
    checks.extend(check_training_dependencies())
    checks.extend(check_checkpoint())
    checks.append(check_audio())
    return checks


def _log_result(log: list[str], label: str, return_code: int, output: str) -> None:
    """Append a normalized repair command result to the repair log."""
    status = "OK" if return_code == 0 else "BŁĄD"
    log.append(f"{status}: {label}: {output}")


def _repair_git_lfs(log: list[str], git: str | None) -> None:
    """Repair Git LFS configuration and download large files when possible."""
    if git is None:
        return

    return_code, _ = run([git, "lfs", "version"])
    if return_code != 0 and os.name == "nt" and shutil.which("winget"):
        return_code, output = run(
            [
                "winget",
                "install",
                "--id",
                "GitHub.GitLFS",
                "-e",
                "--source",
                "winget",
                "--accept-package-agreements",
                "--accept-source-agreements",
            ],
            timeout=1800,
        )
        _log_result(log, "instalacja Git LFS przez winget", return_code, output)
        refresh_path()
        git = shutil.which("git") or git

    commands = (
        [git, "config", "--local", "core.longpaths", "true"],
        [git, "lfs", "install", "--local"],
    )
    for command in commands:
        return_code, output = run(command, timeout=60)
        _log_result(log, " ".join(command[1:]), return_code, output)

    if (ROOT / ".git").is_dir():
        return_code, output = run([git, "lfs", "pull"], timeout=3600)
        _log_result(log, "git lfs pull", return_code, output)


def _venv_is_broken() -> bool:
    """Return whether an existing virtual environment cannot import pip."""
    if VENV.exists() and not VENV_PYTHON.is_file():
        return True
    if not VENV_PYTHON.is_file():
        return False

    return_code, _ = run(
        [str(VENV_PYTHON), "-c", "import pip"],
        timeout=30,
    )
    return return_code != 0


def _backup_broken_venv(log: list[str]) -> None:
    """Move a broken virtual environment to a timestamped backup directory."""
    if not _venv_is_broken():
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = ROOT / f".venv_broken_{timestamp}"
    suffix = 1
    while backup.exists():
        backup = ROOT / f".venv_broken_{timestamp}_{suffix}"
        suffix += 1

    VENV.rename(backup)
    log.append(f"OK: uszkodzone .venv przeniesiono do {backup.name}")


def _ensure_venv(log: list[str]) -> None:
    """Create the project virtual environment when it does not exist."""
    if VENV_PYTHON.is_file():
        return

    return_code, output = run(
        [sys.executable, "-m", "venv", str(VENV)],
        timeout=180,
    )
    _log_result(log, "utworzenie .venv", return_code, output)


def _install_dependencies(log: list[str]) -> bool:
    """Install training dependencies and return whether installation succeeded."""
    if not VENV_PYTHON.is_file():
        return False

    commands = (
        [
            str(VENV_PYTHON),
            "-m",
            "pip",
            "install",
            "--upgrade",
            "pip",
            "setuptools",
            "wheel",
        ],
        [str(VENV_PYTHON), "-m", "pip", "install", "-e", ".[train]"],
    )
    for command in commands:
        return_code, output = run(command, timeout=3600)
        _log_result(log, " ".join(command[2:]), return_code, output)
        if return_code != 0:
            return False
    return True


def _build_monotonic_align(log: list[str]) -> None:
    """Build monotonic_align and move the generated module into its package."""
    source = ROOT / "src" / "piper" / "train" / "vits" / "monotonic_align"
    target = source / "monotonic_align"
    target.mkdir(exist_ok=True)

    return_code, output = run(
        [
            str(VENV_PYTHON),
            "-m",
            "Cython.Build.Cythonize",
            "-i",
            "core.pyx",
        ],
        cwd=source,
        timeout=900,
    )
    _log_result(log, "budowanie monotonic_align", return_code, output)
    if return_code != 0:
        return

    for built in source.glob("core*.pyd"):
        destination = target / built.name
        if destination.exists():
            destination.unlink()
        shutil.move(str(built), str(destination))


def repair() -> list[str]:
    """Perform only repair operations designed to preserve user data."""
    log: list[str] = []
    git = shutil.which("git")

    _repair_git_lfs(log, git)
    _backup_broken_venv(log)
    _ensure_venv(log)
    if _install_dependencies(log):
        _build_monotonic_align(log)

    return log


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Diagnozuj i bezpiecznie napraw środowisko piper-mat."
    )
    parser.add_argument("--repair", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    """Run optional repairs, diagnostics, and the selected output format."""
    args = parse_args()
    repair_log = repair() if args.repair else []
    checks = check_all()

    if args.json:
        payload = {
            "checks": [asdict(check) for check in checks],
            "repair_log": repair_log,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for line in repair_log:
            print(line)
        for check in checks:
            print(f"[{check.status.upper():7}] {check.title}: {check.message}")

    return 2 if any(check.status == "error" for check in checks) else 0


if __name__ == "__main__":
    raise SystemExit(main())
