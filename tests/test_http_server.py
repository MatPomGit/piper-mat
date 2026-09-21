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
    _alignment_info,
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


def test_alignment_info_reports_missing_onnx(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Report that alignment output cannot be added without onnx."""
    monkeypatch.setattr("importlib.util.find_spec", lambda name: None)

    alignment_info = _alignment_info()

    assert alignment_info["available"] is False
    assert "onnx package is required" in alignment_info["error"]


def test_dynamic_voice_uses_shared_load_options_and_alignments(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Load default and dynamic voices alike and retain dynamic alignments."""
    from flask import Flask

    from piper.http_server import PiperVoice, main

    default_path = tmp_path / "default.onnx"
    dynamic_path = tmp_path / "dynamic.onnx"
    default_path.touch()
    dynamic_path.touch()
    load_calls = []
    responses = {}

    class FakeVoice:
        config = SimpleNamespace(
            default_speaker_id=0,
            espeak_voice="en-us",
            length_scale=1.0,
            noise_scale=0.667,
            noise_w_scale=0.8,
            num_speakers=1,
            sample_rate=22_050,
            speaker_id_map={},
        )

        def synthesize(self, text, syn_config, include_alignments=False):
            del text, syn_config
            assert include_alignments is True
            yield SimpleNamespace(
                audio_int16_bytes=b"\x00\x00",
                phoneme_alignments=[SimpleNamespace(phoneme="a", num_samples=2205)],
                phonemes=["a"],
                sample_channels=1,
                sample_rate=22_050,
                sample_width=2,
            )

    def fake_load(model_path, **kwargs):
        load_calls.append((Path(model_path), kwargs))
        return FakeVoice()

    def test_run(app: Flask, **kwargs) -> None:
        del kwargs
        with app.test_client() as client:
            responses["synthesis"] = client.post(
                "/synthesize", json={"text": "Test", "voice": "dynamic"}
            )
            responses["info"] = client.get("/info")

    monkeypatch.setattr(PiperVoice, "load", fake_load)
    monkeypatch.setattr(Flask, "run", test_run)
    monkeypatch.setattr("importlib.util.find_spec", lambda name: None)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "piper-http-server",
            "--model",
            str(default_path),
            "--data-dir",
            str(tmp_path),
            "--download-dir",
            str(tmp_path),
            "--cuda",
        ],
    )

    main()

    assert responses["synthesis"].status_code == 200
    assert [call[0] for call in load_calls] == [default_path, dynamic_path]
    assert (
        load_calls[0][1]
        == load_calls[1][1]
        == {
            "download_dir": tmp_path,
            "include_alignments": True,
            "use_cuda": True,
        }
    )
    assert responses["info"].json["last"]["alignments"] == [
        {"phoneme": "a", "seconds": 0.1}
    ]
    assert responses["info"].json["alignments"]["available"] is False
    assert "onnx package is required" in responses["info"].json["alignments"]["error"]


def test_synthesize_without_voice_uses_default(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Use the default voice only when the voice field is absent."""
    from flask import Flask

    from piper.http_server import PiperVoice, main

    default_path = tmp_path / "default.onnx"
    default_path.touch()
    load_calls = []
    responses = {}

    class FakeVoice:
        config = SimpleNamespace(
            default_speaker_id=0,
            espeak_voice="en-us",
            length_scale=1.0,
            noise_scale=0.667,
            noise_w_scale=0.8,
            num_speakers=1,
            sample_rate=22_050,
            speaker_id_map={},
        )

        def synthesize(self, text, syn_config, include_alignments=False):
            del text, syn_config
            assert include_alignments is True
            yield SimpleNamespace(
                audio_int16_bytes=b"\x00\x00",
                phoneme_alignments=[],
                phonemes=[],
                sample_channels=1,
                sample_rate=22_050,
                sample_width=2,
            )

    def fake_load(model_path, **kwargs):
        del kwargs
        load_calls.append(Path(model_path))
        return FakeVoice()

    def test_run(app: Flask, **kwargs) -> None:
        del kwargs
        with app.test_client() as client:
            responses["synthesis"] = client.post(
                "/synthesize", json={"text": "Default voice"}
            )
            responses["info"] = client.get("/info")

    monkeypatch.setattr(PiperVoice, "load", fake_load)
    monkeypatch.setattr(Flask, "run", test_run)
    monkeypatch.setattr(
        sys,
        "argv",
        ["piper-http-server", "--model", str(default_path)],
    )

    main()

    assert responses["synthesis"].status_code == 200
    assert responses["info"].json["last"]["text"] == "Default voice"
    assert load_calls == [default_path]


def test_unknown_voice_returns_not_found_without_updating_state(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Reject an unknown explicit voice without caching the failed choice."""
    from flask import Flask

    from piper.http_server import PiperVoice, main

    default_path = tmp_path / "default.onnx"
    unknown_path = tmp_path / "unknown.onnx"
    default_path.touch()
    load_calls = []
    responses = {}

    class FakeVoice:
        config = SimpleNamespace(
            default_speaker_id=0,
            espeak_voice="en-us",
            length_scale=1.0,
            noise_scale=0.667,
            noise_w_scale=0.8,
            num_speakers=1,
            sample_rate=22_050,
            speaker_id_map={},
        )

        def synthesize(self, text, syn_config, include_alignments=False):
            del text, syn_config
            assert include_alignments is True
            yield SimpleNamespace(
                audio_int16_bytes=b"\x00\x00",
                phoneme_alignments=[],
                phonemes=[],
                sample_channels=1,
                sample_rate=22_050,
                sample_width=2,
            )

    def fake_load(model_path, **kwargs):
        del kwargs
        load_calls.append(Path(model_path))
        return FakeVoice()

    def test_run(app: Flask, **kwargs) -> None:
        del kwargs
        with app.test_client() as client:
            successful_response = client.post(
                "/synthesize", json={"text": "Successful synthesis"}
            )
            assert successful_response.status_code == 200

            responses["unknown"] = client.post(
                "/synthesize", json={"text": "Must fail", "voice": "unknown"}
            )
            responses["info_after_failure"] = client.get("/info")

            unknown_path.touch()
            responses["available_later"] = client.post(
                "/synthesize", json={"text": "Now available", "voice": "unknown"}
            )

    monkeypatch.setattr(PiperVoice, "load", fake_load)
    monkeypatch.setattr(Flask, "run", test_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "piper-http-server",
            "--model",
            str(default_path),
            "--data-dir",
            str(tmp_path),
        ],
    )

    main()

    assert responses["unknown"].status_code == 404
    assert "unknown" in responses["unknown"].get_data(as_text=True)
    assert responses["info_after_failure"].json["last"]["text"] == (
        "Successful synthesis"
    )
    assert responses["available_later"].status_code == 200
    assert load_calls == [default_path, unknown_path]


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
