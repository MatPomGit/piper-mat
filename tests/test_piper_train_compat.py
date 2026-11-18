"""Testy izolacji samodzielnych uruchomień zgodnego trenera Piper."""

import json
import os
import subprocess
import sys
import time
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


def test_parent_delegation_prevents_nested_lock(tmp_path: Path) -> None:
    """Rzeczywisty podproces rodzica może korzystać z jego blokady."""
    config_path, state_dir = create_config(tmp_path)
    project_root = Path(__file__).resolve().parents[1]
    script = (
        "import sys; from scripts import piper_train_compat as m; "
        "m._run_compatible_training=lambda:19; "
        "sys.argv=['piper_train_compat.py','fit',"
        "'--piper-mat-config',sys.argv[1]]; "
        "sys.exit(m.main())"
    )
    with training_session_lock(state_dir):
        result = subprocess.run(
            [sys.executable, "-c", script, str(config_path)],
            env=locked_subprocess_environment(state_dir),
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )
    assert result.returncode == 19, result.stderr


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


def test_delegated_training_holds_worker_lock(tmp_path: Path) -> None:
    """Delegowany proces utrzymuje własną wyłączną blokadę."""
    config_path, state_dir = create_config(tmp_path)
    project_root = Path(__file__).resolve().parents[1]
    script = (
        "import sys; from pathlib import Path; "
        "from scripts import piper_train_compat as m; "
        "from scripts.session_lock import training_worker_lock; "
        "d=Path(sys.argv[2]); "
        "def_check = None; "
        "exec('def fake():\\n try:\\n  with training_worker_lock(d):"
        " return 23\\n except RuntimeError:\\n  return 0'); "
        "m._run_compatible_training=fake; "
        "sys.argv=['piper_train_compat.py','fit',"
        "'--piper-mat-config',sys.argv[1]]; "
        "sys.exit(m.main())"
    )
    with training_session_lock(state_dir):
        result = subprocess.run(
            [sys.executable, "-c", script, str(config_path), str(state_dir)],
            env=locked_subprocess_environment(state_dir),
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )
    assert result.returncode == 0, result.stderr
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
    monkeypatch.setenv("PIPER_MAT_LOCK_PARENT_PID", str(os.getppid()))
    monkeypatch.setenv("PIPER_MAT_LOCK_PARENT_DIR", str(state_dir))
    assert delegated_lock_directory() is None


def test_delegated_worker_lock_conflict_returns_code_two(
    tmp_path: Path,
) -> None:
    """Delegowany proces odmawia pracy, gdy blokada trenera jest zajęta."""
    config_path, state_dir = create_config(tmp_path)
    project_root = Path(__file__).resolve().parents[1]
    script = (
        "import sys; from scripts import piper_train_compat as m; "
        "m._run_compatible_training=lambda:75; "
        "sys.argv=['piper_train_compat.py','fit',"
        "'--piper-mat-config',sys.argv[1]]; "
        "sys.exit(m.main())"
    )
    with training_session_lock(state_dir):
        with training_worker_lock(state_dir):
            result = subprocess.run(
                [sys.executable, "-c", script, str(config_path)],
                env=locked_subprocess_environment(state_dir),
                cwd=project_root,
                capture_output=True,
                text=True,
                check=False,
            )
    assert result.returncode == 2, result.stderr
    assert "Nie można uzyskać blokady" in result.stderr


def test_missing_project_config_argument_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Zgłoś czytelny błąd, gdy opcja nie zawiera wymaganej ścieżki."""
    monkeypatch.setattr(
        sys, "argv", ["piper_train_compat.py", "fit", "--piper-mat-config"]
    )
    monkeypatch.setattr(
        piper_train_compat,
        "_run_compatible_training",
        lambda: pytest.fail("Nie wolno wywołać Lightning"),
    )
    assert piper_train_compat.main() == 2


def test_orphan_worker_remains_protected_across_processes(
    tmp_path: Path,
) -> None:
    """Osierocony podproces utrzymuje blokadę po zakończeniu rodzica."""
    project_root = Path(__file__).resolve().parents[1]
    worker_script = (
        "import sys,time; from pathlib import Path; "
        "from scripts.session_lock import training_worker_lock;\n"
        "with training_worker_lock(Path(sys.argv[1])):\n"
        " print('READY',flush=True); time.sleep(1.5)"
    )
    parent_script = (
        "import subprocess,sys,os; from pathlib import Path; "
        "from scripts.session_lock import "
        "training_session_lock,locked_subprocess_environment; "
        "d=Path(sys.argv[1]);\n"
        "with training_session_lock(d):\n"
        " p=subprocess.Popen([sys.executable,'-c',sys.argv[2],str(d)],"
        "env=locked_subprocess_environment(d),stdout=subprocess.PIPE,"
        "text=True,cwd=sys.argv[3]); "
        "assert p.stdout.readline().strip()=='READY'; "
        "print(p.pid,flush=True); os._exit(0)"
    )
    parent = subprocess.Popen(
        [
            sys.executable,
            "-u",
            "-c",
            parent_script,
            str(tmp_path),
            worker_script,
            str(project_root),
        ],
        cwd=project_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    assert parent.stdout is not None
    worker_pid = parent.stdout.readline().strip()
    assert worker_pid.isdigit()
    assert parent.wait(timeout=5) == 0

    with pytest.raises(RuntimeError, match="Nie można uzyskać blokady"):
        with training_session_lock(tmp_path):
            pass

    deadline = time.monotonic() + 5
    while True:
        try:
            with training_session_lock(tmp_path):
                break
        except RuntimeError:
            if time.monotonic() > deadline:
                raise
            time.sleep(0.05)
