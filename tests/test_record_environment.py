"""Testy zapisywania informacji o środowisku wykonawczym."""

import subprocess
from unittest.mock import patch

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

