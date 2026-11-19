"""Testy odczytu i odzyskiwania checkpointów po awarii procesu."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import train_sessions  # noqa: E402
from checkpoint_recovery import (  # noqa: E402
    recoverable_session_archive,
    sha256_file,
    validate_resume_checkpoint,
)


def write_checkpoint(path: Path, epoch: int = 11) -> None:
    """Zapisz mały, kompletny checkpoint Lightning na CPU."""
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "epoch": epoch,
            "global_step": 100,
            "state_dict": {"weight": torch.ones(2)},
            "optimizer_states": [{"state": {}}],
            "loops": {"fit_loop": {}},
        },
        path,
    )


def recovery_metadata(tmp_path: Path) -> tuple[Path, Path]:
    """Zapisz archiwum i kompletny dziennik zakończonej sesji."""
    checkpoint = tmp_path / "last.ckpt"
    write_checkpoint(checkpoint)
    metadata_path = tmp_path / "session.json"
    metadata_path.write_text(
        json.dumps(
            {
                "session": 2,
                "resume_checkpoint": "previous.ckpt",
                "target_max_epochs": 12,
                "return_code": 0,
                "archived_checkpoints": {"last": str(checkpoint)},
                "archive_last_sha256": sha256_file(checkpoint),
                "completed_epoch": 11,
                "finished_at": "2026-11-19T09:46:00+00:00",
            }
        ),
        encoding="utf-8",
    )
    return checkpoint, metadata_path


def recover(checkpoint: Path, metadata_path: Path):
    """Wywołaj odzyskiwanie z poprawną identyfikacją sesji."""
    return recoverable_session_archive(
        metadata_path,
        checkpoint,
        session=2,
        previous_checkpoint=Path("previous.ckpt"),
        target_max_epochs=12,
    )


def test_valid_checkpoint_contains_resume_state(tmp_path: Path) -> None:
    """Odczytaj model, optymalizator i stan pętli z poprawnej migawki."""
    path = tmp_path / "valid.ckpt"
    write_checkpoint(path)
    assert validate_resume_checkpoint(path, 11) == 11


def test_truncated_checkpoint_is_rejected(tmp_path: Path) -> None:
    """Odrzuć urwany zapis punktu kontrolnego."""
    path = tmp_path / "partial.ckpt"
    write_checkpoint(path)
    path.write_bytes(path.read_bytes()[:10])
    with pytest.raises(RuntimeError):
        validate_resume_checkpoint(path, 11)


def test_checkpoint_without_optimizer_is_rejected(tmp_path: Path) -> None:
    """Nie uznawaj za pełny pliku bez stanu optymalizatora."""
    path = tmp_path / "incomplete.ckpt"
    torch.save(
        {
            "epoch": 11,
            "global_step": 100,
            "state_dict": {"weight": torch.ones(2)},
            "optimizer_states": [],
            "loops": {},
        },
        path,
    )
    with pytest.raises(RuntimeError, match="optymalizatora"):
        validate_resume_checkpoint(path, 11)


def test_checkpoint_from_earlier_epoch_is_rejected(tmp_path: Path) -> None:
    """Nie przechodź do kolejnej sesji po niedostatecznej liczbie epok."""
    path = tmp_path / "too_early.ckpt"
    write_checkpoint(path, epoch=10)
    with pytest.raises(RuntimeError, match="epokę"):
        validate_resume_checkpoint(path, 11)


def test_recovery_from_verified_archive(tmp_path: Path) -> None:
    """Przyjmij pełny checkpoint z pasującą sumą kontrolną."""
    checkpoint, metadata = recovery_metadata(tmp_path)
    recovered = recover(checkpoint, metadata)
    assert recovered is not None
    epoch, payload = recovered
    assert epoch == 11
    assert payload["session"] == 2


def test_modified_archive_stops_recovery(tmp_path: Path) -> None:
    """Nie używaj zmienionego checkpointu mimo poprawnego pliku JSON."""
    checkpoint, metadata = recovery_metadata(tmp_path)
    checkpoint.write_bytes(b"CORRUPTED")
    with pytest.raises(RuntimeError, match="SHA-256"):
        recover(checkpoint, metadata)


def test_missing_journal_means_no_recovery(tmp_path: Path) -> None:
    """Nie zatwierdzaj niezarejestrowanego pliku checkpointu."""
    assert recover(tmp_path / "last.ckpt", tmp_path / "missing.json") is None


def test_incomplete_journal_is_not_promoted(tmp_path: Path) -> None:
    """Brak sumy kontrolnej wyklucza odzyskanie zakończonej sesji."""
    checkpoint, metadata = recovery_metadata(tmp_path)
    payload = json.loads(metadata.read_text(encoding="utf-8"))
    payload.pop("archive_last_sha256")
    metadata.write_text(json.dumps(payload), encoding="utf-8")
    assert recover(checkpoint, metadata) is None


def test_unrelated_journal_is_not_promoted(tmp_path: Path) -> None:
    """Nie odzyskuj sesji zapisanej dla innego punktu wznowienia."""
    checkpoint, metadata = recovery_metadata(tmp_path)
    assert recoverable_session_archive(
        metadata,
        checkpoint,
        session=2,
        previous_checkpoint=Path("other.ckpt"),
        target_max_epochs=12,
    ) is None


def test_epoch_mismatch_stops_recovery(tmp_path: Path) -> None:
    """Nie uznawaj za poprawne metadanych z inną epoką końcową."""
    checkpoint, metadata = recovery_metadata(tmp_path)
    payload = json.loads(metadata.read_text(encoding="utf-8"))
    payload["completed_epoch"] = 999
    metadata.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(RuntimeError, match="Metadane epoki"):
        recover(checkpoint, metadata)


def test_missing_finished_at_stops_recovery(tmp_path: Path) -> None:
    """Zatrzymaj odzyskiwanie niepełnych metadanych."""
    checkpoint, metadata = recovery_metadata(tmp_path)
    payload = json.loads(metadata.read_text(encoding="utf-8"))
    del payload["finished_at"]
    metadata.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(RuntimeError, match="czasu zakończenia"):
        recover(checkpoint, metadata)


def setup_training(tmp_path: Path) -> tuple[Path, dict]:
    """Przygotuj sesję z bazowym checkpointem i plikiem stanu."""
    base = tmp_path / "base.ckpt"
    write_checkpoint(base, epoch=9)
    config = {
        "training": {
            "base_checkpoint": str(base),
            "sessions": {
                "epochs_per_session": [2],
                "runs_dir": str(tmp_path / "runs"),
                "state_dir": str(tmp_path / "state"),
                "reports_dir": str(tmp_path / "reports"),
            },
        }
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    train_sessions.save_state(
        config,
        {
            "schema_version": 1,
            "initial_checkpoint": str(base),
            "initial_epoch": 9,
            "latest_checkpoint": str(base),
            "completed_sessions": [],
        },
    )
    return config_path, config


def test_crash_before_state_commit_recovers_without_retraining(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Dziennik zakończonej sesji pozwala wznowić po awarii raportu."""
    config_path, config = setup_training(tmp_path)
    run_dir = tmp_path / "runs" / "session_01"

    monkeypatch.setattr(
        train_sessions,
        "build_command",
        lambda *args, **kwargs: ["fake-train"],
    )

    def train_once(*args: object, **kwargs: object) -> int:
        write_checkpoint(run_dir / "last.ckpt", epoch=11)
        return 0

    monkeypatch.setattr(train_sessions, "run_training_command", train_once)

    def interrupt_report(*args: object, **kwargs: object) -> int:
        raise KeyboardInterrupt("symulowana awaria przed state.json")

    monkeypatch.setattr(train_sessions, "generate_report", interrupt_report)
    with pytest.raises(KeyboardInterrupt):
        train_sessions.run_next(config_path, False)

    state = train_sessions.load_state(config)
    assert state is not None
    assert state["completed_sessions"] == []

    def fail_if_retrained(*args: object, **kwargs: object) -> int:
        pytest.fail("Nie należy ponownie trenować zakończonej sesji")

    monkeypatch.setattr(
        train_sessions, "run_training_command", fail_if_retrained
    )
    assert train_sessions.run_next(config_path, False) == 0
    recovered_state = train_sessions.load_state(config)
    assert recovered_state is not None
    assert len(recovered_state["completed_sessions"]) == 1
    assert Path(recovered_state["latest_checkpoint"]).is_file()


def test_cleanup_failure_does_not_undo_completed_session(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Nieudane sprzątanie nie cofa zatwierdzonego checkpointu."""
    config_path, config = setup_training(tmp_path)
    run_dir = tmp_path / "runs" / "session_01"
    monkeypatch.setattr(
        train_sessions, "build_command", lambda *args, **kwargs: ["fake-train"]
    )

    def train_once(*args: object, **kwargs: object) -> int:
        write_checkpoint(run_dir / "last.ckpt", epoch=11)
        return 0

    monkeypatch.setattr(train_sessions, "run_training_command", train_once)
    monkeypatch.setattr(train_sessions, "generate_report", lambda *args: 0)

    def fail_cleanup(*args: object) -> None:
        raise OSError("odmowa dostępu")

    monkeypatch.setattr(train_sessions, "cleanup_checkpoints", fail_cleanup)
    assert train_sessions.run_next(config_path, False) == 0
    state = train_sessions.load_state(config)
    assert state is not None
    assert len(state["completed_sessions"]) == 1
    assert Path(state["latest_checkpoint"]).is_file()
