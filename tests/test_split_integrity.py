"""Regression tests for frozen training, validation and test partitions."""

from pathlib import Path

import pytest

from scripts.split_integrity import validate_split_membership


def check(tmp_path: Path, splits: object, counts: object = None) -> list[str]:
    """Return errors for a three-record example dataset."""
    metadata = tmp_path / "metadata.csv"
    metadata.write_text("a.wav|A\nb.wav|B\nc.wav|C\n", encoding="utf-8")
    payload = {"splits": splits}
    if counts is not None:
        payload["counts"] = counts
    errors: list[str] = []
    validate_split_membership(payload, metadata, errors)
    return errors


def test_accepts_complete_disjoint_splits(tmp_path: Path) -> None:
    """Accept a complete partition with consistent counters."""
    splits = {"train": ["a.wav"], "validation": ["b.wav"], "test": ["c.wav"]}
    counts = {"train": 1, "validation": 1, "test": 1}
    assert check(tmp_path, splits, counts) == []


@pytest.mark.parametrize(
    ("splits", "fragment"),
    [
        ({"train": ["a.wav"], "validation": ["a.wav"], "test": ["c.wav"]}, "występuje"),
        (
            {"train": ["a.wav", "a.wav"], "validation": ["b.wav"], "test": ["c.wav"]},
            "występuje",
        ),
        ({"train": ["a.wav"], "validation": ["b.wav"], "test": []}, "pomija"),
        (
            {"train": ["a.wav"], "validation": ["b.wav"], "test": ["z.wav"]},
            "spoza metadanych",
        ),
        ({"train": [], "validation": ["b.wav"], "test": ["c.wav"]}, "pustą listą"),
        ({"train": ["a.wav"], "validation": [" "], "test": ["c.wav"]}, "niepustych"),
        ({"train": ["a.wav"], "validation": "b.wav", "test": ["c.wav"]}, "listą"),
    ],
)
def test_rejects_invalid_splits(tmp_path: Path, splits: object, fragment: str) -> None:
    """Reject leakage, omitted and invented recordings, and malformed lists."""
    assert any(fragment in error for error in check(tmp_path, splits))


def test_rejects_wrong_counters(tmp_path: Path) -> None:
    """Verify counters against the actual number of recordings."""
    splits = {"train": ["a.wav"], "validation": ["b.wav"], "test": ["c.wav"]}
    errors = check(tmp_path, splits, {"train": 3, "validation": 1, "test": 1})
    assert any("counts.train" in error for error in errors)
