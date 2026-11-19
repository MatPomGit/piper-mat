"""Testy bezpiecznej wymiany natywnego modułu w narzędziu naprawczym."""

from __future__ import annotations

from pathlib import Path

import pytest

from tools import windows_doctor


def test_doctor_preserves_previous_module_on_replace_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Nie niszcz starego modułu, jeśli nowego nie można opublikować."""
    monkeypatch.setattr(windows_doctor, "ROOT", tmp_path)
    monkeypatch.setattr(windows_doctor, "VENV_PYTHON", tmp_path / "python.exe")
    source = tmp_path / "src" / "piper" / "train" / "vits" / "monotonic_align"
    target = source / "monotonic_align"
    target.mkdir(parents=True)
    name = "core.cp312-win_amd64.pyd"
    previous = target / name
    previous.write_bytes(b"valid module")
    built = source / name
    original_replace = Path.replace

    def fail_replace(path: Path, destination: Path) -> Path:
        if path == built and destination == previous:
            raise OSError("testowy brak uprawnień")
        return original_replace(path, destination)

    monkeypatch.setattr(Path, "replace", fail_replace)

    def fake_run(command: list[str], **kwargs: object) -> tuple[int, str]:
        built.write_bytes(b"new model")
        return 0, "ok"

    monkeypatch.setattr(windows_doctor, "run", fake_run)
    log: list[str] = []
    windows_doctor._build_monotonic_align(log)

    assert previous.read_bytes() == b"valid module"
    assert any("nie można zachować modułu" in line for line in log)
