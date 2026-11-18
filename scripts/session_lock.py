"""Blokada międzyprocesowa dla wielosesyjnego trenowania głosu."""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

LOCK_PARENT_PID_ENV = "PIPER_MAT_LOCK_PARENT_PID"
LOCK_PARENT_DIR_ENV = "PIPER_MAT_LOCK_PARENT_DIR"


def locked_subprocess_environment(state_dir: Path) -> dict[str, str]:
    """Przekaż podprocesowi identyfikator właściciela aktywnej blokady."""
    environment = dict(os.environ)
    environment[LOCK_PARENT_PID_ENV] = str(os.getpid())
    environment[LOCK_PARENT_DIR_ENV] = str(state_dir.resolve())
    return environment


def delegated_lock_directory() -> Path | None:
    """Rozpoznaj podproces uruchomiony bezpośrednio przez właściciela blokady."""
    parent_pid = os.environ.get(LOCK_PARENT_PID_ENV)
    parent_dir = os.environ.get(LOCK_PARENT_DIR_ENV)
    if parent_pid != str(os.getppid()) or not parent_dir:
        return None
    return Path(parent_dir)


@contextmanager
def training_session_lock(state_dir: Path) -> Iterator[None]:
    """Wyklucz równoczesne sesje korzystające z jednego katalogu stanu."""
    state_dir.mkdir(parents=True, exist_ok=True)
    lock_path = state_dir / ".train_sessions.lock"

    # Nie usuwaj pliku blokady: drugi proces mógł go już otworzyć.
    with lock_path.open("a+b") as handle:
        if os.name == "nt":
            import msvcrt

            handle.seek(0)
            if not handle.read(1):
                handle.write(b"\0")
                handle.flush()
            handle.seek(0)
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                raise RuntimeError(
                    f"Nie można uzyskać blokady treningu: {lock_path}. "
                    "Sprawdź, czy nie działa już inna sesja."
                ) from exc
        else:
            import fcntl

            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                raise RuntimeError(
                    f"Nie można uzyskać blokady treningu: {lock_path}. "
                    "Sprawdź, czy nie działa już inna sesja."
                ) from exc

        try:
            yield
        finally:
            if os.name == "nt":
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
