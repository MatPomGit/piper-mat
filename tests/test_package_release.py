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


def test_duplicate_required_target_is_rejected_before_copying(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Odrzuć model i konfigurację o tej samej nazwie docelowej."""
    model_dir = tmp_path / "model"
    config_dir = tmp_path / "config"
    model_dir.mkdir()
    config_dir.mkdir()
    model = model_dir / "voice.data"
    config = config_dir / "voice.data"
    model.write_bytes(b"model")
    config.write_bytes(b"config")
    model_card = tmp_path / "MODEL_CARD.md"
    model_card.write_text("# Model\n", encoding="utf-8")
    output = tmp_path / "release"

    def fail_copy(source: Path, target: Path) -> None:
        raise AssertionError(f"nieoczekiwane kopiowanie {source} do {target}")

    monkeypatch.setattr(package_release.shutil, "copy2", fail_copy)

    assert run_main(monkeypatch, model, config, model_card, output) == 1
    assert not output.exists()
    assert "tę samą ścieżkę docelową voice.data" in capsys.readouterr().err
    assert_no_temporary_directories(output)


def test_build_records_rejects_duplicate_relative_paths(tmp_path: Path) -> None:
    """Odrzuć powtórzoną ścieżkę podczas budowania manifestu."""
    output = tmp_path / "release"
    output.mkdir()
    release_file = output / "voice.onnx"
    release_file.write_bytes(b"model")

    with pytest.raises(ValueError, match="powtórzone ścieżki"):
        package_release.build_records([release_file, release_file], output)
