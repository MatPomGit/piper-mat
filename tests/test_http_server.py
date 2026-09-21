"""Tests for the Piper HTTP server."""

from pathlib import Path

import pytest

from piper.http_server import _model_id_from_path


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
