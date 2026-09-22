"""Testy kontroli pól ścieżek w konfiguracji treningu."""

from pathlib import Path

import pytest

from scripts.check_training_ready import read_path_field


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
