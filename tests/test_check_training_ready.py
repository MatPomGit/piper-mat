"""Testy kontroli pól ścieżek w konfiguracji treningu."""

import hashlib
import json
from pathlib import Path

import pytest

from scripts.check_training_ready import (
    read_path_field,
    validate_audio_files,
    validate_project_paths,
)

MISSING = object()


@pytest.mark.parametrize(
    ("value", "expected_error"),
    [
        (MISSING, "brak pola konfiguracji: dataset.metadata"),
        ("", "pole dataset.metadata nie może być pustym napisem"),
        (None, "pole dataset.metadata musi być niepustym napisem"),
        (123, "pole dataset.metadata musi być niepustym napisem"),
        (["metadata.csv"], "pole dataset.metadata musi być niepustym napisem"),
        ({"path": "metadata.csv"}, "pole dataset.metadata musi być niepustym napisem"),
    ],
    ids=["missing", "empty", "null", "number", "list", "object"],
)
def test_read_path_field_rejects_invalid_values(
    value: object,
    expected_error: str,
) -> None:
    """Odrzuć brakujące i niepoprawne wartości z pełną nazwą pola."""
    config = {} if value is MISSING else {"metadata": value}
    errors: list[str] = []

    result = read_path_field(config, "dataset.metadata", errors)

    assert result is None
    assert len(errors) == 1
    assert expected_error in errors[0]


@pytest.mark.parametrize("value", ["dataset/metadata.csv", Path("metadata.csv")])
def test_read_path_field_accepts_valid_path(value: str | Path) -> None:
    """Zwróć obiekt Path dla napisu i obiektu zgodnego z os.PathLike."""
    errors: list[str] = []

    result = read_path_field(
        {"metadata": value},
        "dataset.metadata",
        errors,
    )

    assert result == Path(value)
    assert errors == []


def test_validate_audio_files_checks_lfs_pointer_after_first_twenty(
    tmp_path: Path,
) -> None:
    """Wykryj wskaźnik Git LFS znajdujący się po pierwszych 20 plikach WAV."""
    for index in range(20):
        (tmp_path / f"{index:02}.wav").write_bytes(b"RIFF")
    pointer = tmp_path / "20.wav"
    pointer.write_bytes(
        b"version https://git-lfs.github.com/spec/v1\n"
        b"oid sha256:0000000000000000000000000000000000000000000000000000000000000000\n"
        b"size 123\n"
    )
    errors: list[str] = []

    validate_audio_files(tmp_path, errors)

    assert len(errors) == 1
    assert "wykryto 1" in errors[0]
    assert str(pointer) in errors[0]


def test_validate_audio_files_limits_lfs_pointer_examples(tmp_path: Path) -> None:
    """Podaj liczbę wskaźników Git LFS, ale ogranicz listę przykładów."""
    pointer_header = b"version https://git-lfs.github.com/spec/v1\n"
    pointers = [tmp_path / f"{index:02}.wav" for index in range(7)]
    for pointer in pointers:
        pointer.write_bytes(pointer_header)
    errors: list[str] = []

    validate_audio_files(tmp_path, errors)

    assert len(errors) == 1
    assert "wykryto 7" in errors[0]
    for pointer in pointers[:5]:
        assert str(pointer) in errors[0]
    for pointer in pointers[5:]:
        assert str(pointer) not in errors[0]


def project_paths(tmp_path: Path, splits: object = MISSING) -> tuple[dict, dict]:
    """Przygotuj istniejące ścieżki projektu i opcjonalny plik podziału."""
    metadata = tmp_path / "metadata.csv"
    metadata.write_text("recording.wav|Tekst\n", encoding="utf-8")
    audio_dir = tmp_path / "wavs"
    audio_dir.mkdir()
    checkpoint = tmp_path / "base.ckpt"
    checkpoint.touch()
    splits_path = tmp_path / "splits.json"
    if splits is not MISSING:
        splits_path.write_text(json.dumps(splits), encoding="utf-8")

    dataset = {
        "metadata": str(metadata),
        "audio_dir": str(audio_dir),
        "splits_path": str(splits_path),
    }
    training = {"base_checkpoint": str(checkpoint)}
    return dataset, training


def test_validate_project_paths_rejects_missing_splits_file(tmp_path: Path) -> None:
    """Zgłoś brak skonfigurowanego pliku podziału danych."""
    dataset, training = project_paths(tmp_path)
    errors: list[str] = []

    validate_project_paths(dataset, training, errors)

    assert len(errors) == 1
    assert "brak pliku podziału danych" in errors[0]


def test_validate_project_paths_rejects_invalid_splits_structure(
    tmp_path: Path,
) -> None:
    """Zgłoś brak wymaganych list i puste podstawowe podziały."""
    dataset, training = project_paths(
        tmp_path,
        {
            "metadata_sha256": "hash",
            "splits": {"train": [], "validation": "recording.wav"},
        },
    )
    errors: list[str] = []

    validate_project_paths(dataset, training, errors)

    assert any("splits.train nie może być pustą listą" in error for error in errors)
    assert any("splits.validation musi być listą" in error for error in errors)
    assert any("splits.test musi być listą" in error for error in errors)


def test_validate_project_paths_rejects_mismatched_metadata_hash(
    tmp_path: Path,
) -> None:
    """Zgłoś sumę kontrolną niezgodną z bieżącymi metadanymi."""
    dataset, training = project_paths(
        tmp_path,
        {
            "metadata_sha256": hashlib.sha256(b"inne metadane").hexdigest(),
            "splits": {
                "train": ["recording.wav"],
                "validation": ["validation.wav"],
                "test": [],
            },
        },
    )
    errors: list[str] = []

    validate_project_paths(dataset, training, errors)

    assert len(errors) == 1
    assert "nie odpowiada aktualnym metadanym" in errors[0]
