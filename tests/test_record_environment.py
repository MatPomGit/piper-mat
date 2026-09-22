"""Testy zapisywania informacji o środowisku wykonawczym."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts import record_environment


def run_mocked_command(
    completed_process: subprocess.CompletedProcess[str],
) -> tuple[dict[str, bool | int | str | None], list[str]]:
    """Uruchom atrapę dostępnego polecenia i zwróć wynik z ostrzeżeniami."""
    warnings: list[str] = []
    with (
        patch.object(record_environment.shutil, "which", return_value="/bin/tool"),
        patch.object(
            record_environment.subprocess,
            "run",
            return_value=completed_process,
        ),
    ):
        result = record_environment.command_output(["tool"], warnings)
    return result, warnings


def test_command_output_accepts_zero_exit_code() -> None:
    """Kod zero udostępnia standardowe wyjście bez ostrzeżeń."""
    result, warnings = run_mocked_command(
        subprocess.CompletedProcess(["tool"], 0, "wartość\n", "")
    )

    assert result == {
        "available": True,
        "exit_code": 0,
        "stdout": "wartość",
        "error": None,
    }
    assert warnings == []


def test_command_output_rejects_nonzero_exit_code_with_stdout() -> None:
    """Kod niezerowy nie oznacza dostępności mimo standardowego wyjścia."""
    result, warnings = run_mocked_command(
        subprocess.CompletedProcess(["tool"], 3, "częściowy wynik\n", "")
    )

    assert result["available"] is False
    assert result["exit_code"] == 3
    assert result["stdout"] == "częściowy wynik"
    assert result["error"] == "polecenie 'tool' zakończyło się kodem 3"
    assert warnings == [result["error"]]


def test_command_output_keeps_stderr_out_of_stdout() -> None:
    """Komunikat błędu nie trafia do standardowego wyjścia."""
    result, warnings = run_mocked_command(
        subprocess.CompletedProcess(["tool"], 4, "", "opis błędu\n")
    )

    assert result == {
        "available": False,
        "exit_code": 4,
        "stdout": None,
        "error": "opis błędu",
    }
    assert warnings == ["opis błędu"]


def test_command_output_handles_timeout() -> None:
    """Przekroczenie czasu tworzy niedostępny wynik i ostrzeżenie."""
    warnings: list[str] = []
    with (
        patch.object(record_environment.shutil, "which", return_value="/bin/tool"),
        patch.object(
            record_environment.subprocess,
            "run",
            side_effect=subprocess.TimeoutExpired(["tool"], 10),
        ),
    ):
        result = record_environment.command_output(["tool"], warnings)

    assert result["available"] is False
    assert result["exit_code"] is None
    assert result["stdout"] is None
    assert result["error"] == warnings[0]
    assert "przekroczyło limit" in warnings[0]


def test_command_output_handles_missing_program() -> None:
    """Brak programu tworzy niedostępny wynik i ostrzeżenie."""
    warnings: list[str] = []
    with patch.object(record_environment.shutil, "which", return_value=None):
        result = record_environment.command_output(["missing"], warnings)

    assert result == {
        "available": False,
        "exit_code": None,
        "stdout": None,
        "error": "program 'missing' nie jest dostępny",
    }
    assert warnings == ["program 'missing' nie jest dostępny"]


def test_git_commit_requires_full_sha() -> None:
    """Skrócony identyfikator zatwierdzenia Git jest odrzucany."""
    warnings: list[str] = []
    command_result = {
        "available": True,
        "exit_code": 0,
        "stdout": "abc1234",
        "error": None,
    }
    with patch.object(
        record_environment,
        "command_output",
        return_value=command_result,
    ):
        result = record_environment.git_commit_record(warnings)

    assert result["available"] is False
    assert result["error"] == warnings[0]


def test_sha256_file_reports_missing_file(tmp_path: Path) -> None:
    """Brak wymaganego pliku jest zgłaszany jednoznacznie."""
    missing_path = tmp_path / "brak.json"

    with pytest.raises(record_environment.InputFileError, match="nie istnieje"):
        record_environment.sha256_file(missing_path)


def test_sha256_file_rejects_directory(tmp_path: Path) -> None:
    """Katalog nie jest akceptowany jako plik wejściowy."""
    with pytest.raises(record_environment.InputFileError, match="nie jest plikiem"):
        record_environment.sha256_file(tmp_path)


def test_main_reports_input_permission_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Błąd uprawnień kończy program kodem 2 bez tworzenia rekordu."""
    config = tmp_path / "config.json"
    metadata = tmp_path / "metadata.csv"
    splits = tmp_path / "splits.json"
    output = tmp_path / "record.json"
    for path in (config, metadata, splits):
        path.write_text("dane", encoding="utf-8")

    original_open = Path.open

    def deny_metadata(path: Path, *args: object, **kwargs: object) -> object:
        if path == metadata:
            raise PermissionError("brak uprawnień")
        return original_open(path, *args, **kwargs)

    arguments = [
        "record_environment.py",
        "--output",
        str(output),
        "--config",
        str(config),
        "--metadata",
        str(metadata),
        "--splits",
        str(splits),
    ]
    with (
        patch.object(sys, "argv", arguments),
        patch.object(Path, "open", deny_metadata),
    ):
        exit_code = record_environment.main()

    assert exit_code == 2
    assert "nie można odczytać" in capsys.readouterr().err
    assert not output.exists()


def test_main_writes_record_for_complete_inputs(tmp_path: Path) -> None:
    """Kompletny zestaw wejść tworzy rekord z poprawnymi sumami."""
    input_paths = {
        "config": tmp_path / "config.json",
        "metadata": tmp_path / "metadata.csv",
        "splits": tmp_path / "splits.json",
    }
    contents = {
        "config": b'{"sample_rate": 22050}',
        "metadata": b"audio.wav|Tekst\n",
        "splits": b'{"train": ["audio.wav"]}',
    }
    for name, path in input_paths.items():
        path.write_bytes(contents[name])
    output = tmp_path / "record.json"
    arguments = ["record_environment.py", "--output", str(output)]
    for name, path in input_paths.items():
        arguments.extend((f"--{name}", str(path)))

    with patch.object(sys, "argv", arguments):
        exit_code = record_environment.main()

    record = json.loads(output.read_text(encoding="utf-8"))
    assert exit_code == 0
    for name, path in input_paths.items():
        assert record["inputs"][name] == {
            "path": str(path),
            "sha256": hashlib.sha256(contents[name]).hexdigest(),
        }
