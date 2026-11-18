"""Tests of small-dataset allocation and WAV discovery."""

from pathlib import Path

import pytest

from scripts.create_splits import build_payload
from scripts.validate_dataset import ValidationResult, find_unreferenced_audio


def make_split(n: int, validation_ratio: float, test_ratio: float) -> dict:
    """Build an illustrative split of the requested size."""
    return build_payload(
        [f"{index}.wav" for index in range(n)],
        seed=1,
        validation_ratio=validation_ratio,
        test_ratio=test_ratio,
        metadata_hash="test",
    )


@pytest.mark.parametrize(
    ("size", "validation_ratio", "test_ratio", "message"),
    [
        (3, 0.05, 0.0, "walidacyjny"),
        (3, 0.34, 0.05, "testowy"),
        (2, 0.49, 0.49, "treningowym"),
    ],
)
def test_split_rejects_empty_required_partitions(
    size: int, validation_ratio: float, test_ratio: float, message: str
) -> None:
    """Reject rounded allocations that leave a required partition empty."""
    with pytest.raises(ValueError, match=message):
        make_split(size, validation_ratio, test_ratio)


def test_split_accepts_sufficiently_large_dataset() -> None:
    """Keep the usual 80/10/10 allocation unchanged."""
    payload = make_split(20, 0.1, 0.1)
    assert payload["counts"] == {"train": 16, "validation": 2, "test": 2}


def test_non_wav_files_are_not_counted_as_unused_recordings(tmp_path: Path) -> None:
    """Ignore unrelated files and report only unreferenced WAV recordings."""
    (tmp_path / "a.wav").write_bytes(b"audio")
    (tmp_path / "b.WAV").write_bytes(b"audio")
    (tmp_path / "notes.txt").write_text("notes", encoding="utf-8")
    result = ValidationResult(rows=[("a.wav", "tekst")])

    find_unreferenced_audio(tmp_path, result)

    assert result.unreferenced_audio_files == ["b.WAV"]
    assert len(result.warnings) == 1
    assert "b.WAV" in result.warnings[0]
