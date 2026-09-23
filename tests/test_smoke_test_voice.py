"""Testy sprawdzania konfiguracji w teście dymnym głosu."""

import argparse
import os
import wave
from pathlib import Path

import pytest

from scripts import smoke_test_voice


@pytest.mark.parametrize(
    ("config_text", "field_name"),
    [
        ("[]", "config"),
        ('{"audio": null}', "audio"),
        ('{"audio": {}}', "audio.sample_rate"),
        ('{"audio": {"sample_rate": "22050"}}', "audio.sample_rate"),
        ('{"audio": {"sample_rate": 22050.0}}', "audio.sample_rate"),
        ('{"audio": {"sample_rate": true}}', "audio.sample_rate"),
        ('{"audio": {"sample_rate": 0}}', "audio.sample_rate"),
        ('{"audio": {"sample_rate": -1}}', "audio.sample_rate"),
    ],
    ids=[
        "top-level-list",
        "null-audio",
        "missing-sample-rate",
        "string-sample-rate",
        "float-sample-rate",
        "boolean-sample-rate",
        "zero-sample-rate",
        "negative-sample-rate",
    ],
)
def test_main_rejects_invalid_config_without_traceback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    config_text: str,
    field_name: str,
) -> None:
    """Odrzuć niepoprawne pola konfiguracji bez śladu stosu."""
    model = tmp_path / "voice.onnx"
    config = tmp_path / "voice.onnx.json"
    model.touch()
    config.write_text(config_text, encoding="utf-8")
    monkeypatch.setattr(
        smoke_test_voice,
        "parse_args",
        lambda: argparse.Namespace(
            model=model,
            config=config,
            text="Test.",
            min_duration=0.25,
        ),
    )

    assert smoke_test_voice.main() == 2
    captured = capsys.readouterr()
    assert field_name in captured.err
    assert "Traceback" not in captured.err


def test_main_accepts_positive_integer_sample_rate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Zaakceptuj dodatnią całkowitą częstotliwość próbkowania."""
    model = tmp_path / "voice.onnx"
    config = tmp_path / "voice.onnx.json"
    model.touch()
    config.write_text('{"audio": {"sample_rate": 22050}}', encoding="utf-8")
    monkeypatch.setattr(
        smoke_test_voice,
        "parse_args",
        lambda: argparse.Namespace(
            model=model,
            config=config,
            text="Test.",
            min_duration=0.25,
        ),
    )

    synthesis_started = False

    def stop_after_validation(*args, **kwargs):
        """Zarejestruj rozpoczęcie syntezy po kontroli konfiguracji."""
        nonlocal synthesis_started
        synthesis_started = True
        return argparse.Namespace(returncode=7, stdout="", stderr="")

    monkeypatch.setattr(smoke_test_voice.subprocess, "run", stop_after_validation)

    assert smoke_test_voice.main() == 7
    assert synthesis_started


def run_with_synthesized_wav(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    wav_data: bytes,
) -> int:
    """Uruchom test dymny z podaną zawartością pliku wynikowego WAV."""
    model = tmp_path / "voice.onnx"
    config = tmp_path / "voice.onnx.json"
    model.touch()
    config.write_text('{"audio": {"sample_rate": 22050}}', encoding="utf-8")
    monkeypatch.setattr(
        smoke_test_voice,
        "parse_args",
        lambda: argparse.Namespace(
            model=model,
            config=config,
            text="Test.",
            min_duration=0.0,
        ),
    )

    def synthesize(command, **kwargs):
        """Zapisz przygotowany plik zamiast uruchamiać syntezę."""
        output = Path(command[command.index("--output-file") + 1])
        output.write_bytes(wav_data)
        return argparse.Namespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(smoke_test_voice.subprocess, "run", synthesize)
    return smoke_test_voice.main()


@pytest.mark.parametrize(
    "wav_data",
    [
        pytest.param(os.urandom(64), id="random-data"),
        pytest.param(b"RIFF\x24\x00\x00\x00WAVEfmt ", id="truncated-header"),
    ],
)
def test_main_rejects_invalid_wav_data(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    wav_data: bytes,
) -> None:
    """Zwróć błąd syntezy dla uszkodzonych danych WAV."""
    assert run_with_synthesized_wav(tmp_path, monkeypatch, wav_data) == 1
    assert "ERROR:" in capsys.readouterr().err


def test_main_rejects_wav_without_audio_frames(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Zwróć błąd syntezy dla pliku WAV bez ramek dźwięku."""
    wav_path = tmp_path / "empty.wav"
    with wave.open(str(wav_path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(22_050)
    wav_data = wav_path.read_bytes() + b"JUNK"

    assert run_with_synthesized_wav(tmp_path, monkeypatch, wav_data) == 1
    assert "invalid output WAV" in capsys.readouterr().err


def test_main_accepts_valid_wav(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Zaakceptuj prawidłowy plik WAV zawierający dane dźwiękowe."""
    wav_path = tmp_path / "valid.wav"
    with wave.open(str(wav_path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(22_050)
        wav_file.writeframes(b"\x00\x00" * 2205)

    assert run_with_synthesized_wav(tmp_path, monkeypatch, wav_path.read_bytes()) == 0
    assert "OK: 0.100 s" in capsys.readouterr().out
