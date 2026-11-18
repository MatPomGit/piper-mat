"""Testy blokady równoległego uruchomienia sesji treningowych."""

import subprocess
import sys
from pathlib import Path

import pytest

from scripts.session_lock import training_session_lock


def test_lock_rejects_another_holder(tmp_path: Path) -> None:
    """Druga próba przejęcia blokady kończy się czytelnym błędem."""
    with training_session_lock(tmp_path):
        with pytest.raises(RuntimeError, match="Nie można uzyskać blokady"):
            with training_session_lock(tmp_path):
                pytest.fail("Drugi proces nie powinien otrzymać blokady")

    with training_session_lock(tmp_path):
        pass
    assert (tmp_path / ".train_sessions.lock").is_file()


def test_lock_rejects_competing_process(tmp_path: Path) -> None:
    """Rzeczywisty drugi proces nie może rozpocząć równoległej sesji."""
    script = """\
import sys
from pathlib import Path
from scripts.session_lock import training_session_lock
try:
    with training_session_lock(Path(sys.argv[1])):
        pass
except RuntimeError:
    sys.exit(3)
"""
    root = Path(__file__).resolve().parents[1]
    with training_session_lock(tmp_path):
        competing = subprocess.run(
            [sys.executable, "-c", script, str(tmp_path)],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
    available = subprocess.run(
        [sys.executable, "-c", script, str(tmp_path)],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert competing.returncode == 3, competing.stderr
    assert available.returncode == 0, available.stderr


def test_lock_released_after_body_exception(tmp_path: Path) -> None:
    """Błąd trenowania nie pozostawia aktywnej blokady."""
    with pytest.raises(ValueError, match="symulowany"):
        with training_session_lock(tmp_path):
            raise ValueError("symulowany")

    with training_session_lock(tmp_path):
        pass
