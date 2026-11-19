#!/usr/bin/env python3
"""Zarządzaj wielosesyjnym treningiem Piper z bezpiecznym wznowieniem."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from checkpoint_compat import torch_load_checkpoint
from checkpoint_recovery import (
    recoverable_session_archive,
    sha256_file,
    validate_resume_checkpoint,
)
from session_lock import locked_subprocess_environment, training_session_lock
from train_voice import build_command

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

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
    """Zapisz JSON atomowo bez wspólnego pliku tymczasowego."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=f".{path.name}.working-", dir=path.parent
    ) as working_dir:
        temporary_path = Path(working_dir) / path.name
        with temporary_path.open("w", encoding="utf-8") as stream:
            stream.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
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
        import torch  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(
            "Brak modułu PyTorch potrzebnego do odczytu checkpointu"
        ) from exc

    try:
        checkpoint = torch_load_checkpoint(
            path,
            map_location="cpu",
            weights_only=False,
        )
    except (OSError, RuntimeError, ValueError, NotImplementedError) as exc:
        raise RuntimeError(
            f"Nie można odczytać punktu kontrolnego {path}: {exc}"
        ) from exc

    if not isinstance(checkpoint, dict) or "epoch" not in checkpoint:
        raise RuntimeError(f"Punkt kontrolny nie zawiera pola 'epoch': {path}")
    return int(checkpoint["epoch"])


def checkpoint_modification_times(root: Path) -> dict[Path, int]:
    """Zapisz czasy modyfikacji istniejących punktów kontrolnych."""
    return {path: path.stat().st_mtime_ns for path in root.rglob("*.ckpt")}


def newest_updated_last_checkpoint(
    root: Path,
    previous_modification_times: dict[Path, int],
) -> Path:
    """Znajdź last.ckpt utworzony lub zmieniony podczas treningu."""
    matches = [
        path
        for path in root.rglob("last.ckpt")
        if previous_modification_times.get(path) != path.stat().st_mtime_ns
    ]
    if not matches:
        raise RuntimeError(
            f"Trening nie utworzył ani nie zmienił pliku last.ckpt w {root}"
        )
    return max(matches, key=lambda path: path.stat().st_mtime_ns)


def minimum_expected_epoch(target_max_epochs: int) -> int:
    """Wyznacz ostatnią epokę dla limitu max_epochs biblioteki Lightning."""
    # Lightning numeruje epoki od zera, więc limit N kończy się epoką N - 1.
    return target_max_epochs - 1


def validate_training_checkpoint(
    root: Path,
    previous_modification_times: dict[Path, int],
    target_max_epochs: int,
) -> tuple[Path, int]:
    """Sprawdź pochodzenie i osiągniętą epokę końcowego checkpointu."""
    last = newest_updated_last_checkpoint(root, previous_modification_times)
    completed_epoch = checkpoint_epoch(last)
    expected_epoch = minimum_expected_epoch(target_max_epochs)
    if completed_epoch < expected_epoch:
        raise RuntimeError(
            f"Punkt kontrolny {last} kończy się na epoce {completed_epoch}, "
            f"ale minimalna oczekiwana epoka to {expected_epoch} "
            f"dla max_epochs={target_max_epochs}"
        )
    return last, completed_epoch


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
    """Archiwizuj punkt kontrolny bez usuwania poprzedniego przy błędzie."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=f".{destination.name}.working-", dir=destination.parent
    ) as working_dir:
        staged = Path(working_dir) / destination.name
        try:
            os.link(source, staged)
        except OSError:
            shutil.copy2(source, staged)
        staged.replace(destination)


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


def commit_completed_session(
    config: dict[str, Any],
    state: dict[str, Any],
    number: int,
    checkpoint: Path,
    epoch: int,
    report: Path,
    finished_at: str,
) -> None:
    """Zapisz trwały postęp dopiero po potwierdzeniu checkpointu."""
    new_state = dict(state)
    new_state["latest_checkpoint"] = str(checkpoint)
    new_state["completed_sessions"] = [
        *state["completed_sessions"],
        {
            "session": number,
            "checkpoint": str(checkpoint),
            "completed_epoch": epoch,
            "report": str(report),
            "finished_at": finished_at,
        },
    ]
    save_state(config, new_state)
    state.update(new_state)


def try_recover_completed_session(
    config: dict[str, Any],
    state: dict[str, Any],
    number: int,
    archive_dir: Path,
    report_dir: Path,
    metadata_path: Path,
    target_max_epochs: int,
) -> bool:
    """Odzyskaj zweryfikowaną sesję po przerwaniu przed zapisem stanu."""
    archived_last = archive_dir / "last.ckpt"
    recovered = recoverable_session_archive(
        metadata_path,
        archived_last,
        session=number,
        previous_checkpoint=Path(state["latest_checkpoint"]),
        target_max_epochs=target_max_epochs,
    )
    if recovered is None:
        return False
    epoch, metadata = recovered
    commit_completed_session(
        config,
        state,
        number,
        archived_last,
        epoch,
        report_dir / "REPORT.md",
        metadata["finished_at"],
    )
    print(
        f"Odzyskano zakończoną sesję {number} z checkpointu "
        f"{archived_last}. Trenowanie nie zostało powtórzone."
    )
    return True


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


def verify_committed_checkpoint(
    config: dict[str, Any],
    state: dict[str, Any],
) -> None:
    """Sprawdź punkt wznowienia i dziennik ostatniej zakończonej sesji."""
    completed = state["completed_sessions"]
    if not completed:
        return

    previous = completed[-1]
    if not isinstance(previous, dict):
        raise RuntimeError("Ostatnia zakończona sesja ma niepoprawną strukturę.")
    checkpoint = Path(state["latest_checkpoint"])
    if previous.get("checkpoint") != str(checkpoint):
        raise RuntimeError(
            "Punkt wznowienia jest niezgodny z ostatnią zakończoną sesją."
        )

    expected_epoch = previous.get("completed_epoch")
    if type(expected_epoch) is not int or expected_epoch < 0:
        raise RuntimeError("Brak poprawnej epoki zakończonej sesji.")

    actual_epoch = validate_resume_checkpoint(checkpoint, expected_epoch)
    if actual_epoch != expected_epoch:
        raise RuntimeError(
            "Checkpoint ma inną epokę niż zatwierdzona w state.json."
        )

    sessions = config["training"]["sessions"]
    previous_log = (
        Path(sessions["runs_dir"])
        / f"session_{len(completed):02d}"
        / "session.json"
    )
    if previous_log.is_file():
        journal = load_json(previous_log)
        expected_hash = journal.get("archive_last_sha256")
        if isinstance(expected_hash, str) and expected_hash:
            if sha256_file(checkpoint) != expected_hash:
                raise RuntimeError(
                    "Punkt wznowienia ma niezgodną sumę SHA-256 "
                    "w porównaniu z dziennikiem poprzedniej sesji."
                )


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
    last: Path,
) -> dict[str, str]:
    """Zarchiwizuj ostatni i opcjonalnie najlepsze checkpointy sesji."""
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

    for label, source in (
        ("best_val_mel", best_mel),
        ("best_val_mos", best_mos),
    ):
        if source is None:
            continue
        target = archive_dir / f"{label}.ckpt"
        try:
            validate_resume_checkpoint(source, 0)
            archive_file(source, target)
            validate_resume_checkpoint(target, 0)
        except (RuntimeError, OSError) as exc:
            print(
                f"Ostrzeżenie: pominięto niepoprawny opcjonalny "
                f"checkpoint {label}: {exc}",
                file=sys.stderr,
            )
            continue
        archived[label] = str(target)

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


def format_process_return_code(return_code: int) -> str:
    """Sformatuj kod procesu także jako wartość NTSTATUS/hex, gdy ma to sens."""
    unsigned = return_code & 0xFFFFFFFF
    if return_code < 0 or unsigned >= 0x80000000:
        return f"{return_code} (0x{unsigned:08X})"
    if return_code >= 256:
        return f"{return_code} (0x{return_code:08X})"
    return str(return_code)


def run_training_command(
    command: list[str], log_path: Path, state_dir: Path
) -> int:
    """Uruchom trening, pokazuj wyjście na żywo i zachowaj pełny log."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    environment = locked_subprocess_environment(state_dir)
    environment.update(
        {
            "PYTHONIOENCODING": "utf-8",
            "PYTHONUTF8": "1",
            "PYTHONUNBUFFERED": "1",
            "PYTHONFAULTHANDLER": "1",
        }
    )

    with log_path.open("w", encoding="utf-8", errors="replace") as log_file:
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                env=environment,
            )
        except OSError as exc:
            raise RuntimeError(
                f"Nie można uruchomić procesu treningowego: {exc}"
            ) from exc

        if process.stdout is None:
            process.kill()
            process.wait()
            raise RuntimeError("Nie można odczytać wyjścia procesu treningowego")

        for line in process.stdout:
            log_file.write(line)
            log_file.flush()
            print(line, end="", flush=True)

        return process.wait()


def run_next(config_path: Path, dry_run: bool) -> int:
    """Uruchom sesję pod blokadą albo wykonaj podgląd bez zapisu."""
    config = load_config(config_path)
    if dry_run:
        return _run_next_with_config(config_path, dry_run, config)

    state_dir = Path(config["training"]["sessions"]["state_dir"])
    with training_session_lock(state_dir):
        return _run_next_with_config(config_path, dry_run, config)


def _run_next_with_config(
    config_path: Path,
    dry_run: bool,
    config: dict[str, Any],
) -> int:
    """Przetwórz następną sesję po przejęciu blokady lub w trybie próbnym."""
    increments = get_session_increments(config)
    sessions = config["training"]["sessions"]

    state = load_state(config)
    if state is None:
        if dry_run:
            base_checkpoint = Path(config["training"]["base_checkpoint"])
            if not base_checkpoint.is_file():
                raise RuntimeError(
                    f"Brak bazowego punktu kontrolnego: {base_checkpoint}"
                )
            initial_epoch = checkpoint_epoch(base_checkpoint)
            state = {
                "initial_checkpoint": str(base_checkpoint),
                "initial_epoch": initial_epoch,
                "latest_checkpoint": str(base_checkpoint),
                "completed_sessions": [],
            }
        else:
            state = initialize_state(config)
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

    if not dry_run and try_recover_completed_session(
        config,
        state,
        number,
        archive_dir,
        report_dir,
        metadata_path,
        target_max_epochs,
    ):
        return 0

    if not dry_run:
        verify_committed_checkpoint(config, state)

    command = build_command(
        config_path,
        checkpoint=resume_checkpoint,
        max_epochs=target_max_epochs,
        default_root_dir=run_dir,
        create_output_dir=not dry_run,
    )
    print(f"Sesja {number}/{len(increments)}")
    print("Polecenie:")
    print(subprocess.list2cmdline(command))
    if dry_run:
        return 0

    run_dir.mkdir(parents=True, exist_ok=True)
    training_log_path = run_dir / "training.log"
    metadata["training_log"] = str(training_log_path)
    write_session_metadata(metadata_path, metadata)

    previous_modification_times = checkpoint_modification_times(run_dir)
    return_code = run_training_command(
        command, training_log_path, Path(sessions["state_dir"])
    )
    metadata["finished_at"] = utc_now()
    metadata["return_code"] = return_code
    write_session_metadata(metadata_path, metadata)
    if return_code != 0:
        formatted_code = format_process_return_code(return_code)
        print(
            "Trening zakończył się błędem. "
            f"Kod procesu: {formatted_code}. "
            "Stan nie został przesunięty do następnej sesji.\n"
            f"Pełny log: {training_log_path}",
            file=sys.stderr,
        )
        return return_code

    last, completed_epoch = validate_training_checkpoint(
        run_dir,
        previous_modification_times,
        target_max_epochs,
    )
    archived = archive_session_checkpoints(run_dir, archive_dir, sessions, last)
    archived_last = Path(archived["last"])
    verified_epoch = validate_resume_checkpoint(
        archived_last, minimum_expected_epoch(target_max_epochs)
    )
    if verified_epoch != completed_epoch:
        raise RuntimeError(
            "Epoka zarchiwizowanego checkpointu różni się od epoki "
            "punktu źródłowego."
        )
    metadata["archived_checkpoints"] = archived
    metadata["completed_epoch"] = verified_epoch
    metadata["archive_last_sha256"] = sha256_file(archived_last)
    write_session_metadata(metadata_path, metadata)

    report_return_code = generate_report(run_dir, report_dir, metadata_path)
    if report_return_code != 0:
        print(
            "Ostrzeżenie: trening zakończył się poprawnie, ale generowanie raportu nie powiodło się.",
            file=sys.stderr,
        )

    report_path = report_dir / "REPORT.md"
    commit_completed_session(
        config,
        state,
        number,
        archived_last,
        verified_epoch,
        report_path,
        metadata["finished_at"],
    )

    if sessions.get("cleanup_temporary_checkpoints", True):
        try:
            cleanup_checkpoints(run_dir)
        except OSError as exc:
            print(
                f"Ostrzeżenie: nie udało się usunąć plików roboczych: {exc}",
                file=sys.stderr,
            )

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
    except (KeyError, TypeError, ValueError, RuntimeError, OSError) as exc:
        print(f"BŁĄD: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
