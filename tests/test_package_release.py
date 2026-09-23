"""Testy atomowego przygotowywania katalogu wydania."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from scripts import package_release


def create_inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Utwórz minimalny zestaw plików wejściowych wydania."""
    model = tmp_path / "voice.onnx"
    config = tmp_path / "voice.onnx.json"
    model_card = tmp_path / "MODEL_CARD.md"
    model.write_bytes(b"model")
    config.write_text("{}\n", encoding="utf-8")
    model_card.write_text("# Model\n", encoding="utf-8")
    return model, config, model_card


def run_main(
    monkeypatch: pytest.MonkeyPatch,
    model: Path,
    config: Path,
    model_card: Path,
    output: Path,
) -> int:
    """Uruchom funkcję główną z opcją zastąpienia wydania."""
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "package_release.py",
            "--model",
            str(model),
            "--config",
            str(config),
            "--model-card",
            str(model_card),
            "--samples",
            str(output.parent / "missing-samples"),
            "--output",
            str(output),
            "--overwrite",
        ],
    )
    return package_release.main()


def snapshot(directory: Path) -> dict[str, bytes]:
    """Zwróć zawartość wszystkich plików w katalogu."""
    return {
        path.relative_to(directory).as_posix(): path.read_bytes()
        for path in directory.rglob("*")
        if path.is_file()
    }


def assert_no_temporary_directories(output: Path) -> None:
    """Sprawdź, czy obok wydania nie pozostały katalogi tymczasowe."""
    prefixes = (f".{output.name}.working-", f".{output.name}.backup-")
    assert not any(path.name.startswith(prefixes) for path in output.parent.iterdir())


def test_copy_failure_preserves_existing_release(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Nie zmieniaj starego wydania po błędzie kopiowania."""
    model, config, model_card = create_inputs(tmp_path)
    output = tmp_path / "release"
    output.mkdir()
    (output / "old.txt").write_bytes(b"old release")
    before = snapshot(output)

    def fail_copy(source: Path, target: Path) -> None:
        raise OSError("kontrolowany błąd kopiowania")

    monkeypatch.setattr(package_release.shutil, "copy2", fail_copy)

    assert run_main(monkeypatch, model, config, model_card, output) == 1
    assert snapshot(output) == before
    assert_no_temporary_directories(output)


def test_manifest_write_failure_preserves_existing_release(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Nie zmieniaj starego wydania po błędzie zapisu manifestu."""
    model, config, model_card = create_inputs(tmp_path)
    output = tmp_path / "release"
    output.mkdir()
    (output / "old.txt").write_bytes(b"old release")
    before = snapshot(output)
    original_write_text = Path.write_text

    def fail_manifest_write(
        path: Path,
        data: str,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> int:
        if path.name == package_release.MANIFEST_NAME:
            raise OSError("kontrolowany błąd zapisu manifestu")
        return original_write_text(path, data, encoding, errors, newline)

    monkeypatch.setattr(Path, "write_text", fail_manifest_write)

    assert run_main(monkeypatch, model, config, model_card, output) == 1
    assert snapshot(output) == before
    assert_no_temporary_directories(output)


def test_publish_failure_restores_existing_release(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Przywróć stare wydanie po błędzie publikacji nowego katalogu."""
    output = tmp_path / "release"
    output.mkdir()
    (output / "old.txt").write_bytes(b"old release")
    before = snapshot(output)
    model, config, model_card = create_inputs(tmp_path)
    original_rename = Path.rename

    def fail_working_rename(path: Path, target: Path) -> Path:
        if path.name.startswith(f".{output.name}.working-"):
            raise OSError("kontrolowany błąd publikacji")
        return original_rename(path, target)

    monkeypatch.setattr(Path, "rename", fail_working_rename)

    assert run_main(monkeypatch, model, config, model_card, output) == 1
    assert snapshot(output) == before
    assert_no_temporary_directories(output)
