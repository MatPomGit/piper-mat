"""Testy sprawdzania konfiguracji w teście dymnym głosu."""

import argparse
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
