"""Testy zachowania podglądu i budowania polecenia trenowania."""

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import train_voice
from scripts.session_lock import training_session_lock


def voice_config(tmp_path: Path) -> tuple[Path, Path]:
    """Zapisz minimalną konfigurację polecenia bez faktycznego treningu."""
    output_dir = tmp_path / "generated-model"
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "voice_name": "mateusz",
                "sample_rate": 22050,
                "espeak_voice": "pl",
                "batch_size": 8,
                "dataset": {
                    "metadata": "dataset/metadata.csv",
                    "audio_dir": "dataset/wavs",
                    "splits_path": "dataset/splits.json",
                },
                "training": {
                    "output_dir": str(output_dir),
                    "base_checkpoint": "checkpoints/base.ckpt",
                    "cache_dir": "cache",
                },
                "export": {"config_filename": "voice.onnx.json"},
            }
        ),
        encoding="utf-8",
    )
    return config_path, output_dir


def test_dry_run_cli_does_not_create_output_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Podgląd CLI nie może modyfikować systemu plików."""
    config_path, output_dir = voice_config(tmp_path)
    monkeypatch.setattr(
        sys, "argv", ["train_voice.py", "--config", str(config_path), "--dry-run"]
    )

    assert train_voice.main() == 0
    assert not output_dir.exists()


def test_regular_command_builder_creates_output_directory(tmp_path: Path) -> None:
    """Zachowaj przygotowanie katalogu przy rzeczywistym treningu."""
    config_path, output_dir = voice_config(tmp_path)

    command = train_voice.build_command(config_path)

    assert output_dir.is_dir()
    assert str(output_dir / "voice.onnx.json") in command


def config_with_sessions(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Dodaj do konfiguracji wspólny katalog stanu sesji."""
    config_path, output_dir = voice_config(tmp_path)
    state_dir = tmp_path / "training-state"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["training"]["sessions"] = {"state_dir": str(state_dir)}
    config_path.write_text(json.dumps(config), encoding="utf-8")
    return config_path, state_dir, output_dir


def set_cli_args(
    monkeypatch: pytest.MonkeyPatch,
    config_path: Path,
    *flags: str,
) -> None:
    """Przekaż programowi argumenty bez uruchamiania treningu GPU."""
    monkeypatch.setattr(
        sys, "argv", ["train_voice.py", "--config", str(config_path), *flags]
    )


def test_direct_training_refuses_active_session(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Nie uruchamiaj procesu, gdy menedżer ma już blokadę."""
    config_path, state_dir, output_dir = config_with_sessions(tmp_path)
    set_cli_args(monkeypatch, config_path)
    called: list[bool] = []
    monkeypatch.setattr(
        train_voice.subprocess,
        "run",
        lambda *args, **kwargs: called.append(True),
    )

    with training_session_lock(state_dir):
        assert train_voice.main() == 2

    assert not called
    assert not output_dir.exists()
    assert "Nie można uzyskać blokady treningu" in capsys.readouterr().err


def test_direct_training_holds_lock_until_process_exits(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Trzymaj blokadę podczas całego wywołania treningu."""
    config_path, state_dir, output_dir = config_with_sessions(tmp_path)
    set_cli_args(monkeypatch, config_path)

    def fake_run(
        command: list[str], *, check: bool, env: dict[str, str]
    ) -> SimpleNamespace:
        assert output_dir.is_dir()
        assert not check
        assert "--ckpt_path" in command
        assert env["PIPER_MAT_LOCK_PARENT_PID"]
        assert Path(env["PIPER_MAT_LOCK_PARENT_DIR"]) == state_dir.resolve()
        with pytest.raises(RuntimeError, match="Nie można uzyskać blokady"):
            with training_session_lock(state_dir):
                pass
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(train_voice.subprocess, "run", fake_run)
    assert train_voice.main() == 0
    with training_session_lock(state_dir):
        pass


def test_dry_run_does_not_lock_or_create_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Podgląd działa również w trakcie zablokowanej sesji."""
    config_path, state_dir, output_dir = config_with_sessions(tmp_path)
    set_cli_args(monkeypatch, config_path, "--dry-run")

    with training_session_lock(state_dir):
        assert train_voice.main() == 0

    assert not output_dir.exists()


def test_legacy_config_without_sessions_uses_output_local_lock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Starsza konfiguracja bez sekcji sessions zachowuje zgodność."""
    config_path, output_dir = voice_config(tmp_path)
    state_dir = output_dir / "training_state"
    set_cli_args(monkeypatch, config_path)

    def fake_run(
        command: list[str], *, check: bool, env: dict[str, str]
    ) -> SimpleNamespace:
        assert not check
        assert Path(env["PIPER_MAT_LOCK_PARENT_DIR"]) == state_dir.resolve()
        with pytest.raises(RuntimeError, match="Nie można uzyskać blokady"):
            with training_session_lock(state_dir):
                pass
        return SimpleNamespace(returncode=7)

    monkeypatch.setattr(train_voice.subprocess, "run", fake_run)
    assert train_voice.main() == 7
    assert (state_dir / ".train_sessions.lock").is_file()


def test_direct_training_reports_subprocess_error_and_unlocks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Obsłuż błąd procesu treningowego bez pozostawienia blokady."""
    config_path, state_dir, _ = config_with_sessions(tmp_path)
    set_cli_args(monkeypatch, config_path)

    def fail_run(
        command: list[str], *, check: bool, env: dict[str, str]
    ) -> None:
        assert Path(env["PIPER_MAT_LOCK_PARENT_DIR"]) == state_dir.resolve()
        raise OSError("testowy błąd uruchomienia")

    monkeypatch.setattr(train_voice.subprocess, "run", fail_run)
    assert train_voice.main() == 2
    assert "testowy błąd uruchomienia" in capsys.readouterr().err
    with training_session_lock(state_dir):
        pass
