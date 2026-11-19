"""Testy odczytu ostatniej sesji oraz weryfikacji archiwów best_*."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import train_sessions  # noqa: E402
from checkpoint_recovery import sha256_file  # noqa: E402


def save_checkpoint(path: Path, epoch: int = 11) -> None:
    """Zapisz mały poprawny punkt wznowienia."""
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "epoch": epoch,
            "global_step": 100,
            "state_dict": {"weight": torch.ones(1)},
            "optimizer_states": [{"state": {}}],
            "loops": {"fit_loop": {}},
        },
        path,
    )


def completed_session(tmp_path: Path) -> tuple[dict, dict, Path]:
    """Przygotuj plik stanu i punkt końcowy poprzedniej sesji."""
    last = tmp_path / "state" / "session_01" / "last.ckpt"
    save_checkpoint(last)
    config = {
        "training": {
            "sessions": {
                "state_dir": str(tmp_path / "state"),
                "runs_dir": str(tmp_path / "runs"),
                "reports_dir": str(tmp_path / "reports"),
                "epochs_per_session": [2, 2],
            }
        }
    }
    state = {
        "schema_version": 1,
        "initial_checkpoint": str(tmp_path / "base.ckpt"),
        "initial_epoch": 9,
        "latest_checkpoint": str(last),
        "completed_sessions": [
            {
                "session": 1,
                "checkpoint": str(last),
                "completed_epoch": 11,
            }
        ],
    }
    previous_log = tmp_path / "runs" / "session_01" / "session.json"
    previous_log.parent.mkdir(parents=True)
    previous_log.write_text(
        json.dumps({"archive_last_sha256": sha256_file(last)}),
        encoding="utf-8",
    )
    return config, state, last


def test_previous_checkpoint_is_validated_before_next_session(
    tmp_path: Path,
) -> None:
    """Dopuść pełny checkpoint zgodny z epoką i SHA-256."""
    config, state, _ = completed_session(tmp_path)
    train_sessions.verify_committed_checkpoint(config, state)


def test_modified_previous_checkpoint_is_rejected(tmp_path: Path) -> None:
    """Nie uruchamiaj kolejnej sesji, jeśli punkt wznowienia zmieniono."""
    config, state, path = completed_session(tmp_path)
    save_checkpoint(path, epoch=11)
    with pytest.raises(RuntimeError, match="SHA-256"):
        train_sessions.verify_committed_checkpoint(config, state)


def test_wrong_epoch_in_state_is_rejected(tmp_path: Path) -> None:
    """Nie uznawaj checkpointu z inną epoką niż w state.json."""
    config, state, _ = completed_session(tmp_path)
    state["completed_sessions"][-1]["completed_epoch"] = 12
    with pytest.raises(RuntimeError, match="epokę"):
        train_sessions.verify_committed_checkpoint(config, state)


def test_input_checkpoint_with_missing_optimizer_is_rejected(
    tmp_path: Path,
) -> None:
    """Istnienie pliku nie wystarcza do rozpoczęcia nowej sesji."""
    config, state, path = completed_session(tmp_path)
    torch.save(
        {
            "epoch": 11,
            "global_step": 100,
            "state_dict": {"weight": torch.ones(1)},
            "optimizer_states": [],
            "loops": {},
        },
        path,
    )
    with pytest.raises(RuntimeError, match="optymalizatora"):
        train_sessions.verify_committed_checkpoint(config, state)


def test_next_run_never_builds_command_with_bad_checkpoint(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Uszkodzony punkt wznowienia blokuje kosztowne obliczenia."""
    config, state, path = completed_session(tmp_path)
    path.write_bytes(b"TRUNCATED")
    train_sessions.save_state(config, state)
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    def fail_if_called(*args: object, **kwargs: object) -> int:
        pytest.fail("Nie wolno uruchamiać GPU z uszkodzonego checkpointu")

    monkeypatch.setattr(train_sessions, "build_command", fail_if_called)
    monkeypatch.setattr(train_sessions, "run_training_command", fail_if_called)
    with pytest.raises(RuntimeError):
        train_sessions.run_next(config_path, False)


def test_legacy_journal_without_sha_still_validates_checkpoint(
    tmp_path: Path,
) -> None:
    """Stary dziennik bez SHA nie wyłącza kontroli struktury checkpointu."""
    config, state, _ = completed_session(tmp_path)
    log = tmp_path / "runs" / "session_01" / "session.json"
    log.write_text(json.dumps({"session": 1}), encoding="utf-8")
    train_sessions.verify_committed_checkpoint(config, state)


def test_damaged_optional_model_is_skipped_without_losing_last(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Uszkodzony best_val_mel nie blokuje poprawnego last.ckpt."""
    run_dir = tmp_path / "run"
    archive = tmp_path / "archive"
    last = run_dir / "last.ckpt"
    save_checkpoint(last, epoch=11)
    invalid = run_dir / "epoch=11-val_mel=0.1234.ckpt"
    invalid.write_bytes(b"BROKEN")
    best_mos = run_dir / "epoch=11-val_mos=0.7000.ckpt"
    save_checkpoint(best_mos, epoch=11)

    archived = train_sessions.archive_session_checkpoints(
        run_dir, archive, {}, last
    )

    assert Path(archived["last"]).is_file()
    assert "best_val_mel" not in archived
    assert Path(archived["best_val_mos"]).is_file()
    assert "pominięto" in capsys.readouterr().err
