"""Testy izolacji samodzielnych uruchomień zgodnego trenera Piper."""

import json
import sys
from pathlib import Path

import pytest

from scripts import piper_train_compat
from scripts.session_lock import (
    delegated_lock_directory,
    locked_subprocess_environment,
    training_session_lock,
    training_worker_lock,
)


def create_config(tmp_path: Path) -> tuple[Path, Path]:
    """Zapisz minimalną konfigurację z dedykowanym katalogiem blokady."""
    state_dir = tmp_path / "state"
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps(
            {"training": {"sessions": {"state_dir": str(state_dir)}}}
        ),
        encoding="utf-8",
    )
    return path, state_dir


def test_direct_compat_refuses_running_session(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Nie uruchamiaj Lightning, gdy istnieje aktywna sesja."""
    config_path, state_dir = create_config(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        ["piper_train_compat.py", "fit", "--piper-mat-config", str(config_path)],
    )
    called = []
    monkeypatch.setattr(
        piper_train_compat, "_run_compatible_training", lambda: called.append(1)
    )

    with training_session_lock(state_dir):
        assert piper_train_compat.main() == 2
    assert called == []
    assert "--piper-mat-config" not in sys.argv
    assert "Nie można uzyskać blokady" in capsys.readouterr().err


def test_direct_compat_holds_lock_until_training_exits(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Nie zwalniaj blokady podczas pracy Lightning."""
    config_path, state_dir = create_config(tmp_path)
    monkeypatch.setattr(
        sys, "argv", ["piper_train_compat.py", "fit", "--piper-mat-config="
                      + str(config_path)],
    )

    def fake_training() -> int:
        with pytest.raises(RuntimeError, match="Nie można uzyskać blokady"):
            with training_session_lock(state_dir):
                pass
        return 0

    monkeypatch.setattr(
        piper_train_compat, "_run_compatible_training", fake_training
    )
    assert piper_train_compat.main() == 0
    with training_session_lock(state_dir):
        pass


def test_parent_delegation_prevents_nested_lock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Podproces prawidłowego menedżera może pracować pod jego blokadą."""
    config_path, state_dir = create_config(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        ["piper_train_compat.py", "fit", "--piper-mat-config", str(config_path)],
    )
    environment = locked_subprocess_environment(state_dir)
    monkeypatch.setenv(
        "PIPER_MAT_LOCK_PARENT_DIR", environment["PIPER_MAT_LOCK_PARENT_DIR"]
    )
    # Symulacja odrębnego procesu, którego rodzicem jest właściciel blokady.
    monkeypatch.setenv(
        "PIPER_MAT_LOCK_PARENT_PID", str(__import__("os").getppid())
    )
    monkeypatch.setattr(
        piper_train_compat, "_run_compatible_training", lambda: 19
    )
    with training_session_lock(state_dir):
        assert delegated_lock_directory() == state_dir.resolve()
        assert piper_train_compat.main() == 19


def test_invalid_parent_marker_does_not_bypass_lock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Nie ufaj znacznikowi z innym numerem procesu nadrzędnego."""
    config_path, state_dir = create_config(tmp_path)
    monkeypatch.setenv("PIPER_MAT_LOCK_PARENT_PID", "-1")
    monkeypatch.setenv("PIPER_MAT_LOCK_PARENT_DIR", str(state_dir))
    monkeypatch.setattr(
        sys,
        "argv",
        ["piper_train_compat.py", "fit", "--piper-mat-config", str(config_path)],
    )
    monkeypatch.setattr(
        piper_train_compat, "_run_compatible_training", lambda: 0
    )
    with training_session_lock(state_dir):
        assert piper_train_compat.main() == 2


def test_custom_project_flag_is_removed_before_lightning(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Opcja projektu nie może trafić do parsera biblioteki Lightning."""
    config_path, state_dir = create_config(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        ["piper_train_compat.py", "fit", "--piper-mat-config", str(config_path)],
    )

    def fake_training() -> int:
        assert "--piper-mat-config" not in sys.argv
        assert str(config_path) not in sys.argv
        return 0

    monkeypatch.setattr(
        piper_train_compat, "_run_compatible_training", fake_training
    )
    assert piper_train_compat.main() == 0
    assert (state_dir / ".train_sessions.lock").exists()


def test_missing_project_config_fails_without_training(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Błędna konfiguracja nie może uruchamiać treningu bez blokady."""
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "piper_train_compat.py",
            "fit",
            "--piper-mat-config",
            str(tmp_path / "missing.json"),
        ],
    )
    monkeypatch.setattr(
        piper_train_compat,
        "_run_compatible_training",
        lambda: pytest.fail("Nie wolno uruchomić treningu"),
    )
    assert piper_train_compat.main() == 2


def test_orphan_worker_prevents_new_session(tmp_path: Path) -> None:
    """Po awarii menedżera nie pozwól wznowić przy aktywnym trenerze."""
    state_dir = tmp_path / "state"
    with training_worker_lock(state_dir):
        with pytest.raises(RuntimeError, match="Nie można uzyskać blokady"):
            with training_session_lock(state_dir):
                pytest.fail("Nowa sesja nie może wyprzedzić trenera")
    with training_session_lock(state_dir):
        pass


def test_delegated_training_holds_worker_lock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Właściwy trening utrzymuje własną blokadę do końca pracy."""
    config_path, state_dir = create_config(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        ["piper_train_compat.py", "fit", "--piper-mat-config", str(config_path)],
    )
    monkeypatch.setenv("PIPER_MAT_LOCK_PARENT_PID", str(__import__("os").getppid()))
    monkeypatch.setenv("PIPER_MAT_LOCK_PARENT_DIR", str(state_dir.resolve()))

    def fake_training() -> int:
        with pytest.raises(RuntimeError, match="Nie można uzyskać blokady"):
            with training_worker_lock(state_dir):
                pass
        return 0

    monkeypatch.setattr(
        piper_train_compat, "_run_compatible_training", fake_training
    )
    with training_session_lock(state_dir):
        assert piper_train_compat.main() == 0
    with training_worker_lock(state_dir):
        pass


def test_parent_marker_without_active_lock_is_ignored(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Sam identyfikator rodzica nie wystarcza do pominięcia blokady."""
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    (state_dir / ".train_sessions.lock").touch()
    monkeypatch.setenv("PIPER_MAT_LOCK_PARENT_PID", str(__import__("os").getppid()))
    monkeypatch.setenv("PIPER_MAT_LOCK_PARENT_DIR", str(state_dir))
    assert delegated_lock_directory() is None
