#!/usr/bin/env python3
"""Diagnostyka i bezpieczna naprawa środowiska piper-mat na Windows 11."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, asdict
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

@dataclass
class Check:
    id: str
    title: str
    status: str
    message: str
    repairable: bool = False


def run(command: list[str], cwd: Path | None = None, timeout: int = 120) -> tuple[int, str]:
    try:
        p = subprocess.run(command, cwd=str(cwd or ROOT), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return p.returncode, (p.stdout + "\n" + p.stderr).strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 999, str(exc)


def is_lfs_pointer(path: Path) -> bool:
    try:
        return path.read_bytes()[:80].startswith(b"version https://git-lfs.github.com/spec/v1")
    except OSError:
        return False


def refresh_path() -> None:
    if os.name != "nt":
        return
    try:
        machine = subprocess.check_output(
            ["powershell", "-NoProfile", "-Command", "[Environment]::GetEnvironmentVariable('Path','Machine')"],
            text=True, encoding="utf-8", errors="replace"
        ).strip()
        user = subprocess.check_output(
            ["powershell", "-NoProfile", "-Command", "[Environment]::GetEnvironmentVariable('Path','User')"],
            text=True, encoding="utf-8", errors="replace"
        ).strip()
        os.environ["PATH"] = machine + os.pathsep + user
    except Exception:
        pass


def check_all() -> list[Check]:
    checks: list[Check] = []
    checks.append(Check("windows", "Windows", "ok" if os.name == "nt" else "error",
                        "System Windows wykryty." if os.name == "nt" else "Ten zestaw napraw jest przeznaczony dla Windows."))

    if sys.version_info >= (3, 11):
        checks.append(Check("python", "Python", "ok", f"Python {sys.version.split()[0]} jest odpowiedni."))
    else:
        checks.append(Check("python", "Python", "error", f"Python {sys.version.split()[0]} jest za stary. Wymagany jest Python 3.11 lub nowszy."))

    git = shutil.which("git")
    if git:
        rc, out = run([git, "--version"])
        checks.append(Check("git", "Git", "ok" if rc == 0 else "error", out or "Git znaleziony."))
    else:
        checks.append(Check("git", "Git", "error", "Nie znaleziono Git for Windows w PATH."))

    if git:
        rc, out = run([git, "lfs", "version"])
        checks.append(Check("lfs", "Git LFS", "ok" if rc == 0 else "error",
                            out if rc == 0 else "Git LFS nie działa. Można spróbować naprawy.", True))

    try:
        free = shutil.disk_usage(ROOT).free / (1024 ** 3)
        status = "ok" if free >= MIN_FREE_GIB else "warning" if free >= 15 else "error"
        checks.append(Check("disk", "Wolne miejsce", status,
                            f"Wolne miejsce na dysku: {free:.1f} GiB. Zalecane minimum przed treningiem: {MIN_FREE_GIB:.0f} GiB."))
    except OSError as exc:
        checks.append(Check("disk", "Wolne miejsce", "warning", f"Nie udało się sprawdzić dysku: {exc}"))

    if (ROOT / ".git").is_dir():
        checks.append(Check("repo", "Repozytorium", "ok", "Folder jest prawidłowym repozytorium Git."))
        if git:
            rc, out = run([git, "status", "--porcelain=v1"], timeout=30)
            if rc != 0:
                checks.append(Check("repo_status", "Stan Git", "error", "Git nie potrafi odczytać stanu repozytorium."))
            elif out.strip():
                checks.append(Check("repo_status", "Stan Git", "warning", "W repozytorium są lokalne zmiany. Kreator ich nie usunie."))
            else:
                checks.append(Check("repo_status", "Stan Git", "ok", "Brak niezatwierdzonych zmian w śledzonych plikach."))
    else:
        checks.append(Check("repo", "Repozytorium", "error", "Ten folder nie zawiera katalogu .git."))

    if VENV_PYTHON.is_file():
        rc, _ = run([str(VENV_PYTHON), "-c", "import sys,pip; print(sys.version)"], timeout=30)
        checks.append(Check("venv", "Środowisko .venv", "ok" if rc == 0 else "error",
                            "Środowisko .venv działa." if rc == 0 else "Środowisko .venv jest uszkodzone lub niekompletne.", True))
    else:
        checks.append(Check("venv", "Środowisko .venv", "error", "Brak środowiska .venv.", True))

    if VENV_PYTHON.is_file():
        rc, _ = run([str(VENV_PYTHON), "-c", "import piper, lightning, tensorboard, librosa; print('OK')"], timeout=60)
        checks.append(Check("deps", "Biblioteki treningowe", "ok" if rc == 0 else "error",
                            "Biblioteki treningowe są dostępne." if rc == 0 else "Brakuje części bibliotek lub instalacja jest uszkodzona.", True))

        rc, out = run([str(VENV_PYTHON), "-c", "import torch; print(torch.__version__); print('CUDA', torch.cuda.is_available()); print(torch.version.cuda)"], timeout=60)
        if rc == 0:
            cuda_ok = "CUDA True" in out
            checks.append(Check("cuda", "PyTorch i CUDA", "ok" if cuda_ok else "warning",
                                out if cuda_ok else "PyTorch działa, ale nie widzi CUDA. Sprawdź sterownik NVIDIA i zgodność wersji PyTorch/CUDA."))
        else:
            checks.append(Check("cuda", "PyTorch i CUDA", "error", "Nie można uruchomić PyTorch.", True))

        rc, _ = run([str(VENV_PYTHON), "-c", "from piper.train.vits.monotonic_align import core; print('OK')"], timeout=30)
        checks.append(Check("align", "monotonic_align", "ok" if rc == 0 else "error",
                            "Moduł monotonic_align działa." if rc == 0 else "Moduł monotonic_align nie jest zbudowany.", True))

    if CONFIG.is_file():
        try:
            cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
            base = ROOT / cfg.get("training", {}).get("base_checkpoint", "")
            if base.is_file() and not is_lfs_pointer(base):
                checks.append(Check("checkpoint", "Bazowy checkpoint", "ok", f"Checkpoint jest pobrany: {base.name}."))
            elif base.is_file():
                checks.append(Check("checkpoint", "Bazowy checkpoint", "error", "Checkpoint jest tylko wskaźnikiem Git LFS.", True))
            else:
                checks.append(Check("checkpoint", "Bazowy checkpoint", "error", "Brak bazowego checkpointu.", True))
        except Exception as exc:
            checks.append(Check("config", "Konfiguracja", "error", f"Nie można odczytać konfiguracji: {exc}"))

    wav_dir = ROOT / "dataset" / "wavs"
    wavs = list(wav_dir.glob("*.wav")) if wav_dir.is_dir() else []
    if not wavs:
        checks.append(Check("audio", "Nagrania WAV", "error", "Brak nagrań WAV.", True))
    elif any(is_lfs_pointer(p) for p in wavs[:50]):
        checks.append(Check("audio", "Nagrania WAV", "error", "Część nagrań to nadal wskaźniki Git LFS.", True))
    else:
        checks.append(Check("audio", "Nagrania WAV", "ok", f"Znaleziono {len(wavs)} plików WAV."))
    return checks


def repair() -> list[str]:
    log: list[str] = []
    git = shutil.which("git")
    if git:
        rc, _ = run([git, "lfs", "version"])
        if rc != 0 and os.name == "nt" and shutil.which("winget"):
            rc, out = run(["winget", "install", "--id", "GitHub.GitLFS", "-e", "--source", "winget",
                           "--accept-package-agreements", "--accept-source-agreements"], timeout=1800)
            log.append(f"{'OK' if rc == 0 else 'BŁĄD'}: instalacja Git LFS przez winget: {out}")
            refresh_path()
        for cmd in ([git, "config", "--local", "core.longpaths", "true"], [git, "lfs", "install", "--local"]):
            rc, out = run(list(cmd), timeout=60)
            log.append(f"{'OK' if rc == 0 else 'BŁĄD'}: {' '.join(cmd[1:])}: {out}")
        if (ROOT / ".git").is_dir():
            rc, out = run([git, "lfs", "pull"], timeout=3600)
            log.append(f"{'OK' if rc == 0 else 'BŁĄD'}: git lfs pull: {out}")

    venv_broken = VENV.exists() and not VENV_PYTHON.is_file()
    if VENV_PYTHON.is_file():
        rc, _ = run([str(VENV_PYTHON), "-c", "import pip"], timeout=30)
        venv_broken = rc != 0
    if venv_broken:
        backup = ROOT / f".venv_broken_{datetime.now():%Y%m%d_%H%M%S}"
        suffix = 1
        while backup.exists():
            backup = ROOT / f".venv_broken_{datetime.now():%Y%m%d_%H%M%S}_{suffix}"
            suffix += 1
        VENV.rename(backup)
        log.append(f"OK: uszkodzone .venv przeniesiono do {backup.name}")

    if not VENV_PYTHON.is_file():
        rc, out = run([sys.executable, "-m", "venv", str(VENV)], timeout=180)
        log.append(f"{'OK' if rc == 0 else 'BŁĄD'}: utworzenie .venv: {out}")

    if VENV_PYTHON.is_file():
        cmds = [
            [str(VENV_PYTHON), "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"],
            [str(VENV_PYTHON), "-m", "pip", "install", "-e", ".[train]"],
        ]
        deps_ok = True
        for cmd in cmds:
            rc, out = run(cmd, timeout=3600)
            log.append(f"{'OK' if rc == 0 else 'BŁĄD'}: {' '.join(cmd[2:])}: {out}")
            if rc != 0:
                deps_ok = False
                break
        if deps_ok:
            src = ROOT / "src" / "piper" / "train" / "vits" / "monotonic_align"
            target = src / "monotonic_align"
            target.mkdir(exist_ok=True)
            rc, out = run([str(VENV_PYTHON), "-m", "Cython.Build.Cythonize", "-i", "core.pyx"], cwd=src, timeout=900)
            log.append(f"{'OK' if rc == 0 else 'BŁĄD'}: budowanie monotonic_align: {out}")
            if rc == 0:
                for built in src.glob("core*.pyd"):
                    dst = target / built.name
                    if dst.exists():
                        dst.unlink()
                    shutil.move(str(built), str(dst))
    return log


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repair", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    repair_log = repair() if args.repair else []
    checks = check_all()
    if args.json:
        print(json.dumps({"checks": [asdict(c) for c in checks], "repair_log": repair_log}, ensure_ascii=False, indent=2))
    else:
        for line in repair_log:
            print(line)
        for c in checks:
            print(f"[{c.status.upper():7}] {c.title}: {c.message}")
    return 2 if any(c.status == "error" for c in checks) else 0

if __name__ == "__main__":
    raise SystemExit(main())
