"""Tests for converting phonemes to identifiers."""

import pytest

from piper.const import BOS, EOS, PAD
from piper.phoneme_ids import DEFAULT_PHONEME_ID_MAP, phonemes_to_ids


def test_none_uses_default_map() -> None:
    """Use the default map only when no map is supplied."""
    assert phonemes_to_ids(["a"], None) == [1, 0, 14, 0, 2]


def test_empty_map_is_rejected() -> None:
    """Reject an explicitly supplied empty map."""
    with pytest.raises(ValueError, match="must not be empty"):
        phonemes_to_ids(["a"], {})


@pytest.mark.parametrize("missing_symbol", [BOS, EOS, PAD])
def test_missing_special_symbol_is_rejected(missing_symbol: str) -> None:
    """Reject a map that omits a required special symbol."""
    id_map = {
        symbol: identifiers
        for symbol, identifiers in DEFAULT_PHONEME_ID_MAP.items()
        if symbol != missing_symbol
    }

    with pytest.raises(ValueError) as error:
        phonemes_to_ids(["a"], id_map)

    assert repr(missing_symbol) in str(error.value)


def test_custom_map_is_used() -> None:
    """Convert phonemes with a valid custom map."""
    id_map = {BOS: [10], EOS: [11], PAD: [12], "a": [20, 21]}

    assert phonemes_to_ids(["a"], id_map) == [10, 12, 20, 21, 12, 11]


@pytest.mark.parametrize("invalid_ids", [[], [-1], [1.5], [True], "1"])
def test_invalid_map_value_is_rejected(invalid_ids: object) -> None:
    """Reject empty sequences and values that are not valid identifiers."""
    id_map = {BOS: [1], EOS: [2], PAD: [0], "a": invalid_ids}

    with pytest.raises(ValueError, match="map value"):
        phonemes_to_ids(["a"], id_map)  # type: ignore[arg-type]
