"""Testy zarządzania wielosesyjnym treningiem."""

import json
import sys
from pathlib import Path

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
