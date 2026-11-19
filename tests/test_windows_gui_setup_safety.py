"""Testy ochrony danych podczas kroków instalacyjnych kreatora Windows."""

from __future__ import annotations

import queue
from datetime import datetime
from pathlib import Path

import pytest

from tools import windows_setup_gui


def setup_wizard(tmp_path: Path) -> windows_setup_gui.WindowsSetupWizard:
    """Przygotuj kontroler bez uruchamiania okna Tk."""
    wizard = object.__new__(windows_setup_gui.WindowsSetupWizard)
    wizard._repo_path = lambda: tmp_path
    wizard._venv_python = lambda: tmp_path / ".venv" / "Scripts" / "python.exe"
    wizard.log_queue = queue.Queue()
    (tmp_path / ".git").mkdir()
    return wizard


def test_venv_backup_avoids_existing_backup_name(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Nie zastępuj wcześniejszej kopii uszkodzonego środowiska."""
    wizard = setup_wizard(tmp_path)
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv" / "marker.txt").write_text("old", encoding="utf-8")
    stamp = "20261119_083400"
    existing = tmp_path / f".venv_broken_{stamp}"
    existing.mkdir()
    (existing / "previous.txt").write_text("keep", encoding="utf-8")

    class FixedDatetime:
        """Zachowaj deterministyczną godzinę w teście kopii."""

        @staticmethod
        def now() -> datetime:
            return datetime(2026, 11, 19, 8, 34)

    monkeypatch.setattr(windows_setup_gui, "datetime", FixedDatetime)

    def fake_command(*args: object, **kwargs: object) -> int:
        path = wizard._venv_python()
        path.parent.mkdir(parents=True)
        path.touch()
        return 0

    wizard._run_command = fake_command
    success, _ = wizard._action_create_venv()

    assert success
    assert (existing / "previous.txt").read_text(encoding="utf-8") == "keep"
    assert (
        tmp_path / f".venv_broken_{stamp}_1" / "marker.txt"
    ).read_text(encoding="utf-8") == "old"


def test_lfs_initialization_failure_stops_download(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Nie zgłaszaj pobrania WAV, gdy inicjalizacja LFS się nie udała."""
    wizard = setup_wizard(tmp_path)
    monkeypatch.setattr(windows_setup_gui.shutil, "which", lambda name: "git")
    calls: list[list[str]] = []

    def fake_command(command: list[str], **kwargs: object) -> int:
        calls.append(command)
        return 2 if command[1:3] == ["lfs", "install"] else 0

    wizard._run_command = fake_command
    success, message = wizard._action_git_lfs_pull()

    assert not success
    assert "zainicjalizować" in message
    assert not any("pull" in command for command in calls)


def test_missing_venv_does_not_modify_extension_folder(tmp_path: Path) -> None:
    """Brak Pythona nie powinien tworzyć katalogów modułów."""
    wizard = setup_wizard(tmp_path)
    source = tmp_path / "src" / "piper" / "train" / "vits" / "monotonic_align"
    source.mkdir(parents=True)
    success, message = wizard._action_build_extension()

    assert not success
    assert "Brak .venv" in message
    assert not (source / "monotonic_align").exists()


def test_extension_replace_error_preserves_existing_binary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Nie usuwaj działającego .pyd, gdy publikacja nowego pliku zawiedzie."""
    wizard = setup_wizard(tmp_path)
    python = wizard._venv_python()
    python.parent.mkdir(parents=True)
    python.touch()
    source = tmp_path / "src" / "piper" / "train" / "vits" / "monotonic_align"
    target = source / "monotonic_align"
    target.mkdir(parents=True)
    name = "core.cp312-win_amd64.pyd"
    original = target / name
    original.write_bytes(b"previous working module")
    built = source / name
    original_replace = Path.replace

    def fail_replace(path: Path, destination: Path) -> Path:
        if path == built and destination == original:
            raise OSError("symulowany błąd kopiowania")
        return original_replace(path, destination)

    monkeypatch.setattr(Path, "replace", fail_replace)

    def fake_command(command: list[str], **kwargs: object) -> int:
        if "core.pyx" in command:
            built.write_bytes(b"new module")
        return 0

    wizard._run_command = fake_command
    success, message = wizard._action_build_extension()

    assert not success
    assert "bezpiecznie zainstalować" in message
    assert original.read_bytes() == b"previous working module"


def test_missing_new_extension_is_not_reported_as_success(
    tmp_path: Path,
) -> None:
    """Nie akceptuj starej biblioteki jako rezultatu nowej kompilacji."""
    wizard = setup_wizard(tmp_path)
    python = wizard._venv_python()
    python.parent.mkdir(parents=True)
    python.touch()
    source = tmp_path / "src" / "piper" / "train" / "vits" / "monotonic_align"
    target = source / "monotonic_align"
    target.mkdir(parents=True)
    (target / "core.cp312-win_amd64.pyd").write_bytes(b"old")
    wizard._run_command = lambda *args, **kwargs: 0

    success, message = wizard._action_build_extension()
    assert not success
    assert "Kompilator nie utworzył" in message
