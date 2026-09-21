"""Tests for the Piper HTTP server."""

from pathlib import Path

import pytest
from werkzeug.exceptions import BadRequest

from piper.http_server import _model_id_from_path, _validate_speaker_id

NUM_SPEAKERS = 3


@pytest.mark.parametrize(
    ("path", "suffix", "expected_model_id"),
    [
        (Path("axon.onnx"), ".onnx", "axon"),
        (Path("voice-x.onnx"), ".onnx", "voice-x"),
        (Path("json.onnx.json"), ".onnx.json", "json"),
        (
            Path("pl_PL-mateusz-medium.onnx.json"),
            ".onnx.json",
            "pl_PL-mateusz-medium",
        ),
    ],
)
def test_model_id_removes_exact_suffix(path, suffix, expected_model_id):
    """Preserve every character belonging to the model identifier."""
    assert _model_id_from_path(path, suffix) == expected_model_id


def test_model_id_rejects_path_without_expected_suffix():
    """Reject a path that does not have the expected suffix."""
    with pytest.raises(ValueError, match="must end with"):
        _model_id_from_path(Path("voice.json"), ".onnx.json")


@pytest.mark.parametrize("speaker_id", [0, NUM_SPEAKERS - 1])
def test_validate_speaker_id_accepts_range_boundaries(speaker_id):
    """Accept the first and last identifiers in the configured range."""
    assert _validate_speaker_id(speaker_id, NUM_SPEAKERS) == speaker_id


@pytest.mark.parametrize("speaker_id", [-1, NUM_SPEAKERS, "1", 1.0, True])
def test_validate_speaker_id_rejects_invalid_value(speaker_id):
    """Reject out-of-range identifiers and values of an invalid type."""
    with pytest.raises(BadRequest) as error:
        _validate_speaker_id(speaker_id, NUM_SPEAKERS)

    assert error.value.code == 400
    assert f"0 <= speaker_id < {NUM_SPEAKERS}" in error.value.description
