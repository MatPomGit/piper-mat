"""Testy działania kroków GUI bez inicjalizowania okna Windows."""

from __future__ import annotations

import queue
import sys
import time

from tools import windows_setup_gui


def wizard_without_display() -> windows_setup_gui.WindowsSetupWizard:
    """Utwórz obiekt do testowania poleceń bez ekranu Tk."""
    wizard = object.__new__(windows_setup_gui.WindowsSetupWizard)
    wizard.log_queue = queue.Queue()
    return wizard


def test_command_timeout_is_enforced_while_output_is_open() -> None:
    """Proces z otwartym strumieniem wyjścia nie blokuje limitu czasu."""
    wizard = wizard_without_display()
    start = time.monotonic()

    result = wizard._run_command(
        [
            sys.executable,
            "-u",
            "-c",
            "import time; print('START', flush=True); time.sleep(4)",
        ],
        timeout=0.2,
    )

    elapsed = time.monotonic() - start
    assert result == windows_setup_gui.COMMAND_FAILURE
    assert elapsed < 2.5
    logged = list(wizard.log_queue.queue)
    assert any("przekroczono limit czasu" in line for line in logged)


def test_command_streams_output_and_returns_exit_code() -> None:
    """Poprawne polecenie przekazuje log do GUI i zwraca kod zakończenia."""
    wizard = wizard_without_display()

    result = wizard._run_command(
        [sys.executable, "-u", "-c", "print('ETAP_1'); print('ETAP_2')"],
        timeout=5,
    )

    assert result == 0
    logged = list(wizard.log_queue.queue)
    assert "ETAP_1" in logged
    assert "ETAP_2" in logged


def test_command_reports_nonzero_exit_code() -> None:
    """Błędne polecenie powinno zakończyć się znanym kodem błędu."""
    wizard = wizard_without_display()

    result = wizard._run_command(
        [sys.executable, "-c", "raise SystemExit(23)"],
        timeout=5,
    )

    assert result == 23
