#!/usr/bin/env python3
"""Zarządzaj wielosesyjnym treningiem Piper z bezpiecznym wznowieniem."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from train_voice import build_command

CONFIG_DEFAULT = Path("configs/pl_PL-mateusz-medium.json")
STATE_SCHEMA_VERSION = 1
SESSION_METADATA_SCHEMA_VERSION = 1


def utc_now() -> str:
    """Zwróć bieżący czas UTC w formacie ISO 8601."""
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    """Wczytaj obiekt JSON i zgłoś czytelny błąd dla niepoprawnego pliku."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise RuntimeError(f"Nie można odczytać pliku {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Niepoprawny JSON w pliku {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise RuntimeError(f"Plik {path} musi zawierać obiekt JSON")
    return data


def write_json_atomic(path: Path, data: dict[str, Any]) -> None:
    """Zapisz obiekt JSON atomowo, aby ograniczyć ryzyko uszkodzenia stanu."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(path)


def load_config(path: Path) -> dict[str, Any]:
    """Wczytaj konfigurację projektu."""
    return load_json(path)


def get_session_increments(config: dict[str, Any]) -> list[int]:
    """Zwróć i zweryfikuj plan dodatkowych epok dla kolejnych sesji."""
    try:
        increments = config["training"]["sessions"]["epochs_per_session"]
    except (KeyError, TypeError) as exc:
        raise RuntimeError(
            "Brak training.sessions.epochs_per_session w konfiguracji"
        ) from exc

    if not isinstance(increments, list) or not increments:
        raise RuntimeError(
            "training.sessions.epochs_per_session musi być niepustą listą"
        )
    if any(
        isinstance(value, bool) or not isinstance(value, int) or value <= 0
        for value in increments
    ):
        raise RuntimeError(
            "training.sessions.epochs_per_session musi zawierać dodatnie liczby całkowite"
        )
    return increments


def checkpoint_epoch(path: Path) -> int:
    """Odczytaj numer epoki zapisany w punkcie kontrolnym PyTorch."""
    try:
        import torch
    except ImportError as exc:
        raise RuntimeError("Brak modułu PyTorch potrzebnego do odczytu checkpointu") from exc

    try:
        checkpoint = torch.load(path, map_location="cpu", weights_only=False)
    except (OSError, RuntimeError, ValueError) as exc:
        raise RuntimeError(f"Nie można odczytać punktu kontrolnego {path}: {exc}") from exc

    if not isinstance(checkpoint, dict) or "epoch" not in checkpoint:
        raise RuntimeError(f"Punkt kontrolny nie zawiera pola 'epoch': {path}")
    return int(checkpoint["epoch"])


def newest_last_checkpoint(root: Path) -> Path:
    """Znajdź najnowszy plik last.ckpt w katalogu sesji."""
    matches = list(root.rglob("last.ckpt"))
    if not matches:
        raise RuntimeError(f"Nie znaleziono last.ckpt po treningu w {root}")
    return max(matches, key=lambda path: path.stat().st_mtime_ns)


def checkpoint_candidates(root: Path) -> list[Path]:
    """Zwróć punkty kontrolne sesji uporządkowane według czasu modyfikacji."""
    return sorted(
        root.rglob("*.ckpt"),
        key=lambda path: path.stat().st_mtime_ns,
    )


def choose_best_by_filename(
    checkpoints: list[Path],
    token: str,
    mode: str,
) -> Path | None:
    """Wybierz punkt kontrolny na podstawie wartości metryki zapisanej w nazwie."""
    if mode not in {"min", "max"}:
        raise ValueError("mode musi mieć wartość 'min' albo 'max'")

    values: list[tuple[float, Path]] = []
    marker = f"{token}="
    for path in checkpoints:
        if marker not in path.name:
            continue
        try:
            value = float(path.name.split(marker, 1)[1].split(".ckpt", 1)[0])
        except ValueError:
            continue
        values.append((value, path))

    if not values:
        return None
    selector = min if mode == "min" else max
    return selector(values, key=lambda item: item[0])[1]


def archive_file(source: Path, destination: Path) -> None:
    """Zarchiwizuj plik przez twarde dowiązanie lub kopię zapasową."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.unlink(missing_ok=True)
    try:
        os.link(source, destination)
    except OSError:
        shutil.copy2(source, destination)


def session_paths(
    config: dict[str, Any],
    number: int,
) -> tuple[Path, Path, Path]:
    """Zwróć katalog uruchomienia, archiwum i raportu dla sesji."""
    sessions = config["training"]["sessions"]
    session_name = f"session_{number:02d}"
    return (
        Path(sessions["runs_dir"]) / session_name,
        Path(sessions["state_dir"]) / session_name,
        Path(sessions["reports_dir"]) / session_name,
    )


def state_path(config: dict[str, Any]) -> Path:
    """Zwróć ścieżkę głównego pliku stanu sesji."""
    return Path(config["training"]["sessions"]["state_dir"]) / "state.json"


def load_state(config: dict[str, Any]) -> dict[str, Any] | None:
    """Wczytaj stan sesji, jeżeli został już utworzony."""
    path = state_path(config)
    if not path.is_file():
        return None
    return load_json(path)


def save_state(config: dict[str, Any], state: dict[str, Any]) -> None:
    """Zapisz stan sesji atomowo."""
    write_json_atomic(state_path(config), state)


def initialize_state(config: dict[str, Any]) -> dict[str, Any]:
    """Utwórz początkowy stan planu na podstawie bazowego checkpointu."""
    base = Path(config["training"]["base_checkpoint"])
    if not base.is_file():
        raise RuntimeError(f"Brak bazowego punktu kontrolnego: {base}")

    state = {
        "schema_version": STATE_SCHEMA_VERSION,
        "created_at": utc_now(),
        "initial_checkpoint": str(base),
        "initial_epoch": checkpoint_epoch(base),
        "latest_checkpoint": str(base),
        "completed_sessions": [],
    }
    save_state(config, state)
    return state


def validate_state(state: dict[str, Any]) -> None:
    """Sprawdź minimalną strukturę pliku stanu przed użyciem."""
    required = {
        "initial_checkpoint",
        "initial_epoch",
        "latest_checkpoint",
        "completed_sessions",
    }
    missing = required - state.keys()
    if missing:
        raise RuntimeError(
            "Plik stanu jest niekompletny. Brak pól: " + ", ".join(sorted(missing))
        )
    if not isinstance(state["completed_sessions"], list):
        raise RuntimeError("Pole completed_sessions w stanie musi być listą")


def print_status(config: dict[str, Any], state: dict[str, Any] | None) -> None:
    """Wyświetl postęp planu wielosesyjnego."""
    increments = get_session_increments(config)
    if state is None:
        print(f"Stan: jeszcze nie rozpoczęto. Zaplanowane sesje: {len(increments)}")
        print(f"Dodatkowe epoki na sesję: {increments}")
        return

    validate_state(state)
    completed = len(state["completed_sessions"])
    print(f"Ukończone sesje: {completed}/{len(increments)}")
    print(
        f"Punkt startowy: epoka {state['initial_epoch']} "
        f"({state['initial_checkpoint']})"
    )
    print(f"Ostatni punkt kontrolny: {state['latest_checkpoint']}")
    if completed < len(increments):
        print(
            f"Następna sesja: {completed + 1}, "
            f"dodatkowe epoki: {increments[completed]}"
        )
    else:
        print("Plan wszystkich sesji został zakończony.")


def cleanup_checkpoints(run_dir: Path) -> None:
    """Usuń tymczasowe checkpointy z katalogu zakończonej sesji."""
    for path in run_dir.rglob("*.ckpt"):
        path.unlink(missing_ok=True)


def write_session_metadata(path: Path, metadata: dict[str, Any]) -> None:
    """Zapisz metadane sesji atomowo."""
    write_json_atomic(path, metadata)


def archive_session_checkpoints(
    run_dir: Path,
    archive_dir: Path,
    sessions: dict[str, Any],
) -> dict[str, str]:
    """Zarchiwizuj ostatni i opcjonalnie najlepsze checkpointy sesji."""
    last = newest_last_checkpoint(run_dir)
    candidates = checkpoint_candidates(run_dir)
    best_mel = (
        choose_best_by_filename(candidates, "val_mel", "min")
        if sessions.get("archive_best_val_mel", True)
        else None
    )
    best_mos = (
        choose_best_by_filename(candidates, "val_mos", "max")
        if sessions.get("archive_best_val_mos", True)
        else None
    )

    archive_dir.mkdir(parents=True, exist_ok=True)
    archived_last = archive_dir / "last.ckpt"
    archive_file(last, archived_last)
    archived = {"last": str(archived_last)}

    if best_mel is not None:
        target = archive_dir / "best_val_mel.ckpt"
        archive_file(best_mel, target)
        archived["best_val_mel"] = str(target)
    if best_mos is not None:
        target = archive_dir / "best_val_mos.ckpt"
        archive_file(best_mos, target)
        archived["best_val_mos"] = str(target)

    return archived


def generate_report(run_dir: Path, report_dir: Path, metadata_path: Path) -> int:
    """Uruchom generator raportu bieżącym interpreterem Pythona."""
    command = [
        sys.executable,
        "scripts/report_training_session.py",
        "--session-dir",
        str(run_dir),
        "--output-dir",
        str(report_dir),
        "--metadata",
        str(metadata_path),
    ]
    return subprocess.run(command, check=False).returncode


def run_next(config_path: Path, dry_run: bool) -> int:
    """Uruchom następną niezakończoną sesję treningową."""
    config = load_config(config_path)
    increments = get_session_increments(config)
    sessions = config["training"]["sessions"]

    state = load_state(config) or initialize_state(config)
    validate_state(state)
    completed = len(state["completed_sessions"])
    if completed >= len(increments):
        print("Wszystkie zaplanowane sesje są już ukończone.")
        return 0

    number = completed + 1
    run_dir, archive_dir, report_dir = session_paths(config, number)
    resume_checkpoint = Path(state["latest_checkpoint"])
    if not resume_checkpoint.is_file():
        raise RuntimeError(f"Brak punktu wznowienia: {resume_checkpoint}")

    cumulative_extra = sum(increments[:number])
    target_max_epochs = int(state["initial_epoch"]) + 1 + cumulative_extra
    run_dir.mkdir(parents=True, exist_ok=True)

    metadata: dict[str, Any] = {
        "schema_version": SESSION_METADATA_SCHEMA_VERSION,
        "session": number,
        "planned_sessions": len(increments),
        "additional_epochs_this_session": increments[completed],
        "cumulative_additional_epochs": cumulative_extra,
        "initial_epoch": state["initial_epoch"],
        "target_max_epochs": target_max_epochs,
        "resume_checkpoint": str(resume_checkpoint),
        "started_at": utc_now(),
    }
    metadata_path = run_dir / "session.json"
    write_session_metadata(metadata_path, metadata)

    command = build_command(
        config_path,
        checkpoint=resume_checkpoint,
        max_epochs=target_max_epochs,
        default_root_dir=run_dir,
    )
    print(f"Sesja {number}/{len(increments)}")
    print("Polecenie:")
    print(subprocess.list2cmdline(command))
    if dry_run:
        return 0

    result = subprocess.run(command, check=False)
    metadata["finished_at"] = utc_now()
    metadata["return_code"] = result.returncode
    write_session_metadata(metadata_path, metadata)
    if result.returncode != 0:
        print(
            "Trening zakończył się błędem. Stan nie został przesunięty do następnej sesji.",
            file=sys.stderr,
        )
        return result.returncode

    archived = archive_session_checkpoints(run_dir, archive_dir, sessions)
    archived_last = Path(archived["last"])
    metadata["archived_checkpoints"] = archived
    metadata["completed_epoch"] = checkpoint_epoch(archived_last)
    write_session_metadata(metadata_path, metadata)

    report_return_code = generate_report(run_dir, report_dir, metadata_path)
    if report_return_code != 0:
        print(
            "Ostrzeżenie: trening zakończył się poprawnie, ale generowanie raportu nie powiodło się.",
            file=sys.stderr,
        )

    if sessions.get("cleanup_temporary_checkpoints", True):
        cleanup_checkpoints(run_dir)

    report_path = report_dir / "REPORT.md"
    state["latest_checkpoint"] = str(archived_last)
    state["completed_sessions"].append(
        {
            "session": number,
            "checkpoint": str(archived_last),
            "completed_epoch": metadata["completed_epoch"],
            "report": str(report_path),
            "finished_at": metadata["finished_at"],
        }
    )
    save_state(config, state)

    print(f"Sesja {number} zakończona. Można bezpiecznie wyłączyć komputer.")
    print(f"Punkt wznowienia: {archived_last}")
    print(f"Raport: {report_path}")
    return 0


def parse_args() -> argparse.Namespace:
    """Wczytaj argumenty interfejsu wiersza poleceń."""
    parser = argparse.ArgumentParser(
        description="Wielosesyjny trening Piper z automatycznym wznowieniem"
    )
    parser.add_argument("--config", type=Path, default=CONFIG_DEFAULT)
    parser.add_argument(
        "--status",
        action="store_true",
        help="Pokaż stan planu treningowego",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Pokaż następną sesję bez jej uruchamiania",
    )
    return parser.parse_args()


def main() -> int:
    """Obsłuż polecenie programu."""
    args = parse_args()
    try:
        config = load_config(args.config)
        if args.status:
            print_status(config, load_state(config))
            return 0
        return run_next(args.config, args.dry_run)
    except (KeyError, TypeError, ValueError, RuntimeError) as exc:
        print(f"BŁĄD: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
