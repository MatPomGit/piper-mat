"""Testy weryfikacji punktów kontrolnych sesji treningowych."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import train_sessions  # noqa: E402


def test_accepts_new_last_checkpoint(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Zaakceptuj nowy last.ckpt kończący planowaną epokę."""
    previous = train_sessions.checkpoint_modification_times(tmp_path)
    checkpoint = tmp_path / "version_0" / "checkpoints" / "last.ckpt"
    checkpoint.parent.mkdir(parents=True)
    checkpoint.write_bytes(b"new")
    monkeypatch.setattr(train_sessions, "checkpoint_epoch", lambda path: 7)

    selected, epoch = train_sessions.validate_training_checkpoint(
        tmp_path,
        previous,
        target_max_epochs=8,
    )

    assert selected == checkpoint
    assert epoch == 7


def test_rejects_unchanged_last_checkpoint(tmp_path: Path) -> None:
    """Odrzuć last.ckpt istniejący bez zmian przed treningiem."""
    checkpoint = tmp_path / "last.ckpt"
    checkpoint.write_bytes(b"old")
    previous = train_sessions.checkpoint_modification_times(tmp_path)

    with pytest.raises(RuntimeError, match="nie utworzył ani nie zmienił"):
        train_sessions.validate_training_checkpoint(tmp_path, previous, 8)


def test_rejects_missing_new_checkpoint(tmp_path: Path) -> None:
    """Zgłoś błąd, jeżeli trening nie pozostawił last.ckpt."""
    previous = train_sessions.checkpoint_modification_times(tmp_path)

    with pytest.raises(RuntimeError, match="nie utworzył ani nie zmienił"):
        train_sessions.validate_training_checkpoint(tmp_path, previous, 8)


def test_rejects_checkpoint_before_planned_epoch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Odrzuć nowy checkpoint kończący się przed planowaną epoką."""
    previous = train_sessions.checkpoint_modification_times(tmp_path)
    checkpoint = tmp_path / "last.ckpt"
    checkpoint.write_bytes(b"new")
    monkeypatch.setattr(train_sessions, "checkpoint_epoch", lambda path: 6)

    with pytest.raises(RuntimeError, match="minimalna oczekiwana epoka to 7"):
        train_sessions.validate_training_checkpoint(tmp_path, previous, 8)
