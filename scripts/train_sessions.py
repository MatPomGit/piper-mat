#!/usr/bin/env python3
"""Zarządzaj wielosesyjnym treningiem Piper z bezpiecznym wznowieniem i raportami."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import torch

from train_voice import build_command


CONFIG_DEFAULT = Path("configs/pl_PL-mateusz-medium.json")


def load_config(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def checkpoint_epoch(path: Path) -> int:
    checkpoint = torch.load(path, map_location="cpu", weights_only=False)
    epoch = checkpoint.get("epoch")
    if epoch is None:
        raise RuntimeError(f"Punkt kontrolny nie zawiera pola 'epoch': {path}")
    return int(epoch)


def newest_last_checkpoint(root: Path) -> Path:
    matches = list(root.rglob("last.ckpt"))
    if not matches:
        raise RuntimeError(f"Nie znaleziono last.ckpt po treningu w {root}")
    return max(matches, key=lambda path: path.stat().st_mtime_ns)


def checkpoint_candidates(root: Path) -> list[Path]:
    return sorted(root.rglob("*.ckpt"), key=lambda path: path.stat().st_mtime_ns)


def choose_best_by_filename(checkpoints: list[Path], token: str, mode: str) -> Path | None:
    values: list[tuple[float, Path]] = []
    for path in checkpoints:
        name = path.name
        marker = f"{token}="
        if marker not in name:
            continue
        try:
            value = float(name.split(marker, 1)[1].split(".ckpt", 1)[0])
        except ValueError:
            continue
        values.append((value, path))
    if not values:
        return None
    return (min if mode == "min" else max)(values, key=lambda item: item[0])[1]


def archive_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        destination.unlink()
    try:
        os.link(source, destination)
    except OSError:
        shutil.copy2(source, destination)


def session_paths(config: dict, number: int) -> tuple[Path, Path, Path]:
    sessions = config["training"]["sessions"]
    session_name = f"session_{number:02d}"
    return (
        Path(sessions["runs_dir"]) / session_name,
        Path(sessions["state_dir"]) / session_name,
        Path(sessions["reports_dir"]) / session_name,
    )


def state_path(config: dict) -> Path:
    return Path(config["training"]["sessions"]["state_dir"]) / "state.json"


def load_state(config: dict) -> dict | None:
    path = state_path(config)
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(config: dict, state: dict) -> None:
    path = state_path(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def initialize_state(config: dict) -> dict:
    base = Path(config["training"]["base_checkpoint"])
    if not base.is_file():
        raise RuntimeError(f"Brak bazowego punktu kontrolnego: {base}")
    initial_epoch = checkpoint_epoch(base)
    state = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "initial_checkpoint": str(base),
        "initial_epoch": initial_epoch,
        "latest_checkpoint": str(base),
        "completed_sessions": [],
    }
    save_state(config, state)
    return state


def print_status(config: dict, state: dict | None) -> None:
    increments = config["training"]["sessions"]["epochs_per_session"]
    if state is None:
        print(f"Stan: jeszcze nie rozpoczęto. Zaplanowane sesje: {len(increments)}")
        print(f"Dodatkowe epoki na sesję: {increments}")
        return
    completed = len(state["completed_sessions"])
    print(f"Ukończone sesje: {completed}/{len(increments)}")
    print(f"Punkt startowy: epoka {state['initial_epoch']} ({state['initial_checkpoint']})")
    print(f"Ostatni punkt kontrolny: {state['latest_checkpoint']}")
    if completed < len(increments):
        print(f"Następna sesja: {completed + 1}, dodatkowe epoki: {increments[completed]}")
    else:
        print("Plan wszystkich sesji został zakończony.")


def cleanup_checkpoints(run_dir: Path, preserved_sources: set[Path]) -> None:
    for path in run_dir.rglob("*.ckpt"):
        if path not in preserved_sources:
            path.unlink(missing_ok=True)


def run_next(config_path: Path, dry_run: bool) -> int:
    config = load_config(config_path)
    training = config["training"]
    sessions = training["sessions"]
    increments = sessions["epochs_per_session"]
    if not increments or any(int(value) <= 0 for value in increments):
        raise RuntimeError("training.sessions.epochs_per_session musi zawierać dodatnie liczby epok")

    state = load_state(config) or initialize_state(config)
    completed = len(state["completed_sessions"])
    if completed >= len(increments):
        print("Wszystkie zaplanowane sesje są już ukończone.")
        return 0

    number = completed + 1
    run_dir, archive_dir, report_dir = session_paths(config, number)
    resume_checkpoint = Path(state["latest_checkpoint"])
    cumulative_extra = sum(int(value) for value in increments[:number])
    # Lightning zapisuje epoch jako indeks ostatniej ukończonej epoki. Aby wykonać
    # N dodatkowych epok po checkpointcie E, max_epochs musi wynosić E + 1 + N.
    target_max_epochs = int(state["initial_epoch"]) + 1 + cumulative_extra

    run_dir.mkdir(parents=True, exist_ok=True)
    metadata = {
        "schema_version": 1,
        "session": number,
        "planned_sessions": len(increments),
        "additional_epochs_this_session": int(increments[completed]),
        "cumulative_additional_epochs": cumulative_extra,
        "initial_epoch": state["initial_epoch"],
        "target_max_epochs": target_max_epochs,
        "resume_checkpoint": str(resume_checkpoint),
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    metadata_path = run_dir / "session.json"
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    command = build_command(
        config_path,
        checkpoint=resume_checkpoint,
        max_epochs=target_max_epochs,
        default_root_dir=run_dir,
    )
    print(f"Sesja {number}/{len(increments)}")
    print("Polecenie:")
    print(" ".join(command))
    if dry_run:
        return 0

    result = subprocess.run(command, check=False)
    metadata["finished_at"] = datetime.now(timezone.utc).isoformat()
    metadata["return_code"] = result.returncode
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if result.returncode != 0:
        print("Trening zakończył się błędem. Stan nie został przesunięty do następnej sesji.", file=sys.stderr)
        return result.returncode

    last = newest_last_checkpoint(run_dir)
    all_checkpoints = checkpoint_candidates(run_dir)
    best_mel = choose_best_by_filename(all_checkpoints, "val_mel", "min") if sessions.get("archive_best_val_mel", True) else None
    best_mos = choose_best_by_filename(all_checkpoints, "val_mos", "max") if sessions.get("archive_best_val_mos", True) else None

    archive_dir.mkdir(parents=True, exist_ok=True)
    archived_last = archive_dir / "last.ckpt"
    archive_file(last, archived_last)
    preserved_sources = {last}
    archived = {"last": str(archived_last)}

    if best_mel is not None:
        target = archive_dir / "best_val_mel.ckpt"
        archive_file(best_mel, target)
        preserved_sources.add(best_mel)
        archived["best_val_mel"] = str(target)
    if best_mos is not None:
        target = archive_dir / "best_val_mos.ckpt"
        archive_file(best_mos, target)
        preserved_sources.add(best_mos)
        archived["best_val_mos"] = str(target)

    metadata["archived_checkpoints"] = archived
    metadata["completed_epoch"] = checkpoint_epoch(archived_last)
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report_result = subprocess.run(
        [
            "python",
            "scripts/report_training_session.py",
            "--session-dir", str(run_dir),
            "--output-dir", str(report_dir),
            "--metadata", str(metadata_path),
        ],
        check=False,
    )
    if report_result.returncode != 0:
        print("Ostrzeżenie: trening zakończył się poprawnie, ale generowanie raportu nie powiodło się.", file=sys.stderr)

    if sessions.get("cleanup_temporary_checkpoints", True):
        cleanup_checkpoints(run_dir, preserved_sources)

    state["latest_checkpoint"] = str(archived_last)
    state["completed_sessions"].append(
        {
            "session": number,
            "checkpoint": str(archived_last),
            "completed_epoch": metadata["completed_epoch"],
            "report": str(report_dir / "REPORT.md"),
            "finished_at": metadata["finished_at"],
        }
    )
    save_state(config, state)
    print(f"Sesja {number} zakończona. Można bezpiecznie wyłączyć komputer.")
    print(f"Punkt wznowienia: {archived_last}")
    print(f"Raport: {report_dir / 'REPORT.md'}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Wielosesyjny trening Piper z automatycznym wznowieniem")
    parser.add_argument("--config", type=Path, default=CONFIG_DEFAULT)
    parser.add_argument("--status", action="store_true", help="Pokaż stan planu treningowego")
    parser.add_argument("--dry-run", action="store_true", help="Pokaż następną sesję bez jej uruchamiania")
    args = parser.parse_args()

    config = load_config(args.config)
    if args.status:
        print_status(config, load_state(config))
        return 0
    return run_next(args.config, args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
