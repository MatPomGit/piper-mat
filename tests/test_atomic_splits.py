"""Testy bezpiecznego, atomowego zapisu pliku podziału danych."""

import json
from pathlib import Path

import pytest

from scripts.create_splits import write_splits_atomic


def test_atomic_write_creates_output_and_cleans_up(tmp_path: Path) -> None:
    """Utwórz brakujący katalog i usuń tymczasowy po sukcesie."""
    output = tmp_path / "nested" / "splits.json"

    write_splits_atomic(output, {"splits": {"train": ["a.wav"]}})

    assert json.loads(output.read_text(encoding="utf-8")) == {
        "splits": {"train": ["a.wav"]}
    }
    assert list(output.parent.iterdir()) == [output]


def test_atomic_write_replaces_existing_split(tmp_path: Path) -> None:
    """Zastąp poprzedni podział gotowym plikiem JSON."""
    output = tmp_path / "splits.json"
    output.write_text("old", encoding="utf-8")

    write_splits_atomic(output, {"splits": {"train": ["b.wav"]}})

    assert json.loads(output.read_text(encoding="utf-8")) == {
        "splits": {"train": ["b.wav"]}
    }


def test_atomic_write_preserves_old_split_on_replace_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Nie niszcz poprzedniego podziału przy błędzie publikacji."""
    output = tmp_path / "splits.json"
    output.write_bytes(b"original data")
    original_replace = Path.replace

    def fail_replace(source: Path, destination: Path) -> Path:
        if destination == output:
            raise OSError("symulowany blad zapisu")
        return original_replace(source, destination)

    monkeypatch.setattr(Path, "replace", fail_replace)

    with pytest.raises(OSError, match="symulowany blad zapisu"):
        write_splits_atomic(output, {"splits": {"train": ["b.wav"]}})

    assert output.read_bytes() == b"original data"
    assert sorted(path.name for path in tmp_path.iterdir()) == ["splits.json"]
