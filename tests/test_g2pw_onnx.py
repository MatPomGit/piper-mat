"""Tests for the torch-free g2pW ONNX feature builder."""

import pytest

from piper.g2pw_onnx import FeatureBuildError, _FeatureBuilder


class _Tokenizer:
    """Minimal tokenizer which can reject selected input text."""

    def __init__(self, rejected: set[str]) -> None:
        self.rejected = rejected

    def tokenize(self, text: str) -> list[str]:
        """Return a single token unless the text is rejected."""
        if text in self.rejected:
            raise ValueError(f"cannot tokenize {text}")
        return [text]

    @staticmethod
    def convert_tokens_to_ids(tokens: list[str]) -> list[int]:
        """Give each test token a stable, distinct identifier."""
        return [sum(ord(char) for char in token) for token in tokens]


def _builder(texts: list[str], rejected: set[str]) -> _FeatureBuilder:
    """Create a feature builder for one query character per text."""
    return _FeatureBuilder(
        tokenizer=_Tokenizer(rejected),
        labels=["a"],
        char2phonemes={text: [0] for text in texts},
        chars=texts,
        texts=texts,
        query_ids=[0] * len(texts),
    )


def test_failed_item_is_not_replaced_with_next_item() -> None:
    """Keep valid samples distinct when the sample between them fails."""
    builder = _builder(["a", "b", "c"], {"b"})

    first = builder[0]
    with pytest.raises(FeatureBuildError) as error_info:
        builder[1]
    third = builder[2]

    assert error_info.value.index == 1
    assert error_info.value.text == "b"
    assert isinstance(error_info.value.__cause__, ValueError)
    assert "cannot tokenize b" in str(error_info.value)
    assert first["char_id"] == 0
    assert third["char_id"] == 2


def test_batch_with_only_failed_items_raises_without_recursion() -> None:
    """Report the first failed item when no sample in a batch is usable."""
    builder = _builder(["a", "b"], {"a", "b"})

    with pytest.raises(FeatureBuildError, match="index 0.*'a'.*cannot tokenize a"):
        [builder[index] for index in range(len(builder))]
