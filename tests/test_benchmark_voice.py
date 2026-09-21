"""Testy benchmarku syntezy głosu."""

from types import SimpleNamespace
import wave

import pytest

from scripts import benchmark_voice


def _write_wav(path):
    """Zapisać krótki, poprawny plik WAV."""
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16_000)
        wav_file.writeframes(b"\x00\x00" * 160)


def test_collect_measurements_does_not_reuse_previous_wav(monkeypatch):
    """Odrzucić przebieg, który nie utworzył własnego pliku WAV."""
    output_paths = []

    def fake_process(command, **kwargs):
        """Utworzyć wynik tylko w pierwszym przebiegu atrapy procesu."""
        wav_path = benchmark_voice.Path(command[command.index("--output-file") + 1])
        output_paths.append(wav_path)
        if len(output_paths) == 1:
            _write_wav(wav_path)
        return SimpleNamespace(returncode=0, stderr="", stdout="")

    monkeypatch.setattr(benchmark_voice.subprocess, "run", fake_process)

    with pytest.raises(RuntimeError, match="bieżącym przebiegu"):
        benchmark_voice.collect_measurements(
            model=benchmark_voice.Path("voice.onnx"),
            text="Test",
            runs=2,
            warmup=0,
        )

    assert len(output_paths) == 2
    assert output_paths[0] != output_paths[1]


def test_collect_measurements_reports_damaged_wav(monkeypatch):
    """Zgłosić czytelny błąd dla uszkodzonego pliku WAV."""

    def fake_process(command, **kwargs):
        """Zapisać dane, które nie są plikiem WAV."""
        wav_path = benchmark_voice.Path(command[command.index("--output-file") + 1])
        wav_path.write_bytes(b"uszkodzony plik" * 4)
        return SimpleNamespace(returncode=0, stderr="", stdout="")

    monkeypatch.setattr(benchmark_voice.subprocess, "run", fake_process)

    with pytest.raises(RuntimeError, match="uszkodzony plik WAV"):
        benchmark_voice.collect_measurements(
            model=benchmark_voice.Path("voice.onnx"),
            text="Test",
            runs=1,
            warmup=0,
        )


def test_main_reports_output_write_error_without_traceback(monkeypatch, capsys):
    """Zwrócić kod 2 i czytelny komunikat, gdy zapis wyniku zawiedzie."""
    output_path = benchmark_voice.Path("niedozwolony/wynik.json")
    args = SimpleNamespace(
        model=benchmark_voice.Path("voice.onnx"),
        text="Test",
        runs=1,
        warmup=0,
        output=output_path,
    )
    measurements = [{"elapsed_s": 0.1, "audio_s": 1.0, "rtf": 0.1}]

    monkeypatch.setattr(benchmark_voice, "parse_args", lambda: args)
    monkeypatch.setattr(
        benchmark_voice,
        "validate_args",
        lambda parsed_args: benchmark_voice.Path("voice.onnx.json"),
    )
    monkeypatch.setattr(
        benchmark_voice,
        "collect_measurements",
        lambda *unused_args: measurements,
    )

    def deny_write(path, *args, **kwargs):
        """Zasymulować odmowę zapisu pliku wynikowego."""
        raise OSError("brak uprawnień")

    monkeypatch.setattr(benchmark_voice.Path, "write_text", deny_write)

    assert benchmark_voice.main() == 2

    captured = capsys.readouterr()
    assert str(output_path) in captured.err
    assert "brak uprawnień" in captured.err
    assert "Traceback" not in captured.err
