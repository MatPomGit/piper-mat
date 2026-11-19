"""Regresje bramki gotowości oraz przebiegu sesji w GUI Windows."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.windows_setup_gui import WindowsSetupWizard


def wizard_for_project(tmp_path: Path) -> WindowsSetupWizard:
    """Utwórz kontroler kroków bez inicjalizacji ekranu Tk."""
    wizard = object.__new__(WindowsSetupWizard)
    wizard._repo_path = lambda: tmp_path
    python = tmp_path / ".venv" / "Scripts" / "python.exe"
    python.parent.mkdir(parents=True)
    python.touch()
    wizard._venv_python = lambda: python
    return wizard


def make_training_plan(tmp_path: Path, done: int = 0) -> Path:
    """Przygotuj konfigurację i stan zakończonych sesji."""
    config_path = tmp_path / "configs" / "pl_PL-mateusz-medium.json"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        json.dumps(
            {"training": {"sessions": {
                "state_dir": "output/training_state",
                "epochs_per_session": [2, 2],
            }}}
        ),
        encoding="utf-8",
    )
    if done:
        save_completed(tmp_path, done)
    return config_path


def save_completed(tmp_path: Path, count: int) -> None:
    """Zapisz licznik ukończonych sesji w testowym katalogu."""
    path = tmp_path / "output" / "training_state" / "state.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"completed_sessions": list(range(count))}),
        encoding="utf-8",
    )


def test_preflight_checks_project_after_windows_diagnostics(
    tmp_path: Path,
) -> None:
    """Sukces diagnostyki Windows nie oznacza automatycznie gotowości danych."""
    wizard = wizard_for_project(tmp_path)
    script = tmp_path / "scripts" / "check_training_ready.py"
    script.parent.mkdir()
    script.touch()
    wizard._diagnose = lambda: (True, "System działa")
    commands: list[list[str]] = []

    def fake_command(command: list[str], **kwargs: object) -> int:
        commands.append(command)
        return 2

    wizard._run_command = fake_command

    ready, message = wizard._action_check_ready()

    assert not ready
    assert "Kontrola danych" in message
    assert len(commands) == 1
    assert commands[0][1] == "scripts/check_training_ready.py"


def test_preflight_stops_after_failed_windows_diagnostics(
    tmp_path: Path,
) -> None:
    """Nie sprawdzaj kolejnych etapów, gdy diagnostyka Windows już zawiodła."""
    wizard = wizard_for_project(tmp_path)
    wizard._diagnose = lambda: (False, "Brak CUDA")
    wizard._run_command = lambda *args, **kwargs: pytest.fail("No subprocess")

    assert wizard._action_check_ready() == (False, "Brak CUDA")


def test_start_never_runs_training_after_failed_preflight(
    tmp_path: Path,
) -> None:
    """Odmowa z kontrolera gotowości blokuje uruchomienie trenowania."""
    wizard = wizard_for_project(tmp_path)
    wizard._action_check_ready = lambda: (False, "Brak podziału danych")
    wizard._run_command = lambda *args, **kwargs: pytest.fail("No training")

    ready, message = wizard._action_start_training()

    assert not ready
    assert "nie zostało uruchomione" in message


def test_start_does_not_repeat_completed_plan(tmp_path: Path) -> None:
    """Po wykonaniu planu GUI nie może zgłosić nowej zakończonej sesji."""
    wizard = wizard_for_project(tmp_path)
    make_training_plan(tmp_path, done=2)
    wizard._action_check_ready = lambda: (True, "Gotowe")
    wizard._run_command = lambda *args, **kwargs: pytest.fail("No training")

    success, message = wizard._action_start_training()

    assert success
    assert "Nie uruchomiono nowego treningu" in message


def test_start_requires_confirmed_progress_change(tmp_path: Path) -> None:
    """Kod zakończenia 0 bez aktualizacji state.json nie oznacza sukcesu."""
    wizard = wizard_for_project(tmp_path)
    make_training_plan(tmp_path)
    wizard._action_check_ready = lambda: (True, "Gotowe")
    wizard._run_command = lambda *args, **kwargs: 0

    success, message = wizard._action_start_training()

    assert not success
    assert "nie potwierdził ukończenia" in message


def test_start_accepts_one_completed_new_session(tmp_path: Path) -> None:
    """GUI zgłasza sukces dopiero po utrwaleniu nowego stanu sesji."""
    wizard = wizard_for_project(tmp_path)
    make_training_plan(tmp_path)
    wizard._action_check_ready = lambda: (True, "Gotowe")

    def fake_training(*args: object, **kwargs: object) -> int:
        save_completed(tmp_path, 1)
        return 0

    wizard._run_command = fake_training

    assert wizard._action_start_training() == (
        True, "Sesja zakończona i zapisana."
    )


def test_start_rejects_corrupted_state(tmp_path: Path) -> None:
    """Nie uruchamiaj GPU, jeśli pliku stanu nie można odczytać."""
    wizard = wizard_for_project(tmp_path)
    make_training_plan(tmp_path)
    state = tmp_path / "output" / "training_state" / "state.json"
    state.parent.mkdir(parents=True)
    state.write_text("{", encoding="utf-8")
    wizard._action_check_ready = lambda: (True, "Gotowe")
    wizard._run_command = lambda *args, **kwargs: pytest.fail("No training")

    success, message = wizard._action_start_training()
    assert not success
    assert "Nie można odczytać stanu treningu" in message

def test_preflight_accepts_completed_project_check(tmp_path: Path) -> None:
    """Pełna diagnostyka może dopuścić trenowanie po obu kontrolach."""
    wizard = wizard_for_project(tmp_path)
    script = tmp_path / "scripts" / "check_training_ready.py"
    script.parent.mkdir()
    script.touch()
    wizard._diagnose = lambda: (True, "System działa")
    wizard._run_command = lambda *args, **kwargs: 0

    ready, message = wizard._action_check_ready()

    assert ready
    assert "gotowe" in message
