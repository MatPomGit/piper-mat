"""Tests for the Piper HTTP server."""

import io
from pathlib import Path
import struct
import sys
from types import SimpleNamespace
import wave

import pytest
from werkzeug.exceptions import BadRequest

from piper.http_server import (
    _model_id_from_path,
    _select_speaker_id,
    _validate_speaker_id,
)

NUM_SPEAKERS = 3
_TEST_VOICE = Path(__file__).parent / "test_voice.onnx"


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


def test_select_speaker_id_preserves_zero_from_command_line():
    """Prefer speaker zero from the command line over a nonzero default."""
    args = SimpleNamespace(speaker=0)
    voice = SimpleNamespace(
        config=SimpleNamespace(
            default_speaker_id=2,
            num_speakers=NUM_SPEAKERS,
            speaker_id_map={},
        )
    )

    assert _select_speaker_id({}, voice, args) == 0


@pytest.mark.parametrize("value", ["-0.1", "nan", "inf", "-inf"])
def test_server_rejects_invalid_sentence_silence(
    monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    """Reject non-finite and negative silence while parsing server options."""
    from piper.http_server import main

    monkeypatch.setattr(
        sys,
        "argv",
        ["piper-http-server", "--model", "unused.onnx", "--sentence-silence", value],
    )

    with pytest.raises(SystemExit) as error:
        main()

    assert error.value.code == 2


@pytest.mark.parametrize("sentence_silence", [0.15, 0.25, 0.45, 0.75])
def test_sentence_silence_even_byte_count(
    monkeypatch: pytest.MonkeyPatch, sentence_silence: float
) -> None:
    """Write whole silence samples between chunks from the HTTP endpoint."""
    from flask import Flask

    from piper.http_server import main

    responses = []

    def test_run(app: Flask, **kwargs) -> None:
        del kwargs
        with app.test_client() as client:
            responses.append(
                client.post(
                    "/synthesize",
                    json={"text": "This is a test. This is another."},
                )
            )

    monkeypatch.setattr(Flask, "run", test_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "piper-http-server",
            "--model",
            str(_TEST_VOICE),
            "--sentence-silence",
            str(sentence_silence),
        ],
    )

    main()

    assert len(responses) == 1
    response = responses[0]
    assert response.status_code == 200
    with wave.open(io.BytesIO(response.data), "rb") as wav_input:
        assert wav_input.getsampwidth() == 2
        assert wav_input.getnchannels() == 1

    data_idx = response.data.find(b"data")
    data_size = struct.unpack("<I", response.data[data_idx + 4 : data_idx + 8])[0]
    sample_rate = 22_050
    silence_samples = int(sample_rate * sentence_silence)
    expected_bytes = (sample_rate * 2 * 2) + (silence_samples * 2)

    assert data_size % 2 == 0
    assert data_size == expected_bytes
