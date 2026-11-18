"""Testy zarządzania wielosesyjnym treningiem."""

import json
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import train_sessions  # noqa: E402


def test_dry_run_does_not_create_state_or_session_files(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Nie zapisuj stanu ani metadanych podczas podglądu pierwszej sesji."""
    base_checkpoint = tmp_path / "base.ckpt"
    base_checkpoint.touch()
    state_dir = tmp_path / "state"
    runs_dir = tmp_path / "runs"
    reports_dir = tmp_path / "reports"
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "training": {
                    "base_checkpoint": str(base_checkpoint),
                    "sessions": {
                        "epochs_per_session": [5],
                        "state_dir": str(state_dir),
                        "runs_dir": str(runs_dir),
                        "reports_dir": str(reports_dir),
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(train_sessions, "checkpoint_epoch", lambda path: 9)
    monkeypatch.setattr(
        train_sessions,
        "build_command",
        lambda *args, **kwargs: ["train", "--max-epochs", "15"],
    )

    result = train_sessions.run_next(config_path, dry_run=True)

    assert result == 0
    assert not state_dir.exists()
    assert not runs_dir.exists()
    assert not reports_dir.exists()
    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "base.ckpt",
        "config.json",
    ]


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


def test_dry_run_with_actual_command_builder_does_not_create_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Nie twórz katalogu modelu przy podglądzie rzeczywistego polecenia."""
    base_checkpoint = tmp_path / "base.ckpt"
    base_checkpoint.touch()
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
                    "metadata": str(tmp_path / "metadata.csv"),
                    "audio_dir": str(tmp_path / "wavs"),
                    "splits_path": str(tmp_path / "splits.json"),
                },
                "training": {
                    "base_checkpoint": str(base_checkpoint),
                    "output_dir": str(output_dir),
                    "cache_dir": str(tmp_path / "cache"),
                    "sessions": {
                        "epochs_per_session": [5],
                        "state_dir": str(tmp_path / "state"),
                        "runs_dir": str(tmp_path / "runs"),
                        "reports_dir": str(tmp_path / "reports"),
                    },
                },
                "export": {"config_filename": "voice.onnx.json"},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(train_sessions, "checkpoint_epoch", lambda path: 9)

    assert train_sessions.run_next(config_path, dry_run=True) == 0
    assert not output_dir.exists()
    assert not (tmp_path / "state").exists()
    assert not (tmp_path / "runs").exists()

def test_archive_copy_failure_preserves_previous_checkpoint(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Nie nadpisuj poprzedniego checkpointu przy częściowej kopii."""
    source = tmp_path / "new.ckpt"
    target = tmp_path / "archive" / "last.ckpt"
    source.write_bytes(b"new checkpoint")
    target.parent.mkdir()
    target.write_bytes(b"previous valid checkpoint")

    def fail_link(*_args: object) -> None:
        raise OSError("cross-device link")

    def fail_copy(source_path: Path, target_path: Path) -> None:
        target_path.write_bytes(b"partial checkpoint")
        raise OSError("disk full")

    monkeypatch.setattr(train_sessions.os, "link", fail_link)
    monkeypatch.setattr(train_sessions.shutil, "copy2", fail_copy)

    with pytest.raises(OSError, match="disk full"):
        train_sessions.archive_file(source, target)

    assert target.read_bytes() == b"previous valid checkpoint"
    assert list(target.parent.iterdir()) == [target]


def test_archive_success_replaces_checkpoint(tmp_path: Path) -> None:
    """Poprawna archiwizacja zastępuje checkpoint niezależnie od systemu."""
    source = tmp_path / "new.ckpt"
    target = tmp_path / "archive" / "last.ckpt"
    source.write_bytes(b"new valid checkpoint")
    target.parent.mkdir()
    target.write_bytes(b"old checkpoint")

    train_sessions.archive_file(source, target)

    assert target.read_bytes() == source.read_bytes()
    assert list(target.parent.iterdir()) == [target]


def test_archive_copy_fallback_replaces_checkpoint(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Po błędzie dowiązania skopiuj plik i zastąp nim stary checkpoint."""
    source = tmp_path / "new.ckpt"
    target = tmp_path / "archive" / "last.ckpt"
    source.write_bytes(b"new valid checkpoint")
    target.parent.mkdir()
    target.write_bytes(b"old checkpoint")

    def fail_link(*_args: object) -> None:
        raise OSError("cross-device link")

    monkeypatch.setattr(train_sessions.os, "link", fail_link)
    train_sessions.archive_file(source, target)

    assert target.read_bytes() == source.read_bytes()
    assert list(target.parent.iterdir()) == [target]


def test_archive_replace_failure_preserves_checkpoint(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Nie usuń starszego checkpointu po awarii końcowego zastąpienia."""
    source = tmp_path / "new.ckpt"
    target = tmp_path / "archive" / "last.ckpt"
    source.write_bytes(b"new checkpoint")
    target.parent.mkdir()
    target.write_bytes(b"previous checkpoint")
    original_replace = Path.replace

    def fail_replace(staged: Path, destination: Path) -> Path:
        if destination == target:
            raise OSError("permission denied")
        return original_replace(staged, destination)

    monkeypatch.setattr(Path, "replace", fail_replace)
    with pytest.raises(OSError, match="permission denied"):
        train_sessions.archive_file(source, target)

    assert target.read_bytes() == b"previous checkpoint"
    assert list(target.parent.iterdir()) == [target]


def test_state_save_success_replaces_existing_json(tmp_path: Path) -> None:
    """Wymień stary plik stanu dopiero po pełnym zapisie nowego."""
    path = tmp_path / "state.json"
    path.write_text('{"epoch": 11}', encoding="utf-8")

    train_sessions.write_json_atomic(path, {"epoch": 12})

    assert json.loads(path.read_text(encoding="utf-8")) == {"epoch": 12}
    assert list(tmp_path.iterdir()) == [path]


def test_state_save_failure_preserves_previous_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Po błędzie końcowej podmiany pozostaw poprzedni plik bez zmian."""
    path = tmp_path / "state.json"
    path.write_text('{"epoch": 11}', encoding="utf-8")
    original_replace = Path.replace

    def fail_replace(staged: Path, destination: Path) -> Path:
        if destination == path:
            raise OSError("permission denied")
        return original_replace(staged, destination)

    monkeypatch.setattr(Path, "replace", fail_replace)
    with pytest.raises(OSError, match="permission denied"):
        train_sessions.write_json_atomic(path, {"epoch": 12})

    assert json.loads(path.read_text(encoding="utf-8")) == {"epoch": 11}
    assert list(tmp_path.iterdir()) == [path]


def test_overlapping_state_saves_have_distinct_temporary_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Dwa przeplatane zapisy nie mogą usuwać sobie pliku tymczasowego."""
    path = tmp_path / "state.json"
    original_replace = Path.replace
    inner_done = False

    def interleaved_replace(staged: Path, destination: Path) -> Path:
        nonlocal inner_done
        if destination == path and not inner_done:
            inner_done = True
            train_sessions.write_json_atomic(path, {"epoch": 2})
        return original_replace(staged, destination)

    monkeypatch.setattr(Path, "replace", interleaved_replace)
    train_sessions.write_json_atomic(path, {"epoch": 3})

    assert json.loads(path.read_text(encoding="utf-8")) == {"epoch": 3}
    assert list(tmp_path.iterdir()) == [path]
