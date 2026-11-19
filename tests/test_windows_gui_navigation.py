"""Testy podstawowej nawigacji i zamykania kreatora Windows."""

from __future__ import annotations

import pytest

from tools import windows_setup_gui


class StubWidget:
    """Zastąp kontrolkę Tk podczas testowania nawigacji bez wyświetlacza."""

    def __init__(self) -> None:
        """Utwórz zapis konfiguracji kontrolki."""
        self.options: dict[str, object] = {}

    def config(self, **options: object) -> None:
        """Zachowaj nową konfigurację kontrolki."""
        self.options.update(options)


def wizard_without_screen() -> windows_setup_gui.WindowsSetupWizard:
    """Utwórz kontroler bez rzeczywistego okna Tk."""
    wizard = object.__new__(windows_setup_gui.WindowsSetupWizard)
    wizard.running = False
    wizard.current_step = 0
    wizard.training_step_succeeded = False
    wizard.progress = {}
    for name in (
        "counter_label",
        "step_title_label",
        "summary_label",
        "explanation_label",
        "action_button",
        "previous_button",
        "next_button",
        "status_label",
    ):
        setattr(wizard, name, StubWidget())
    return wizard


def test_every_gui_step_has_a_matching_action() -> None:
    """Każdy krok kreatora wskazuje istniejącą metodę obsługi."""
    assert len(windows_setup_gui.STEPS) == 11
    assert [step.number for step in windows_setup_gui.STEPS] == list(range(1, 12))
    for step in windows_setup_gui.STEPS:
        assert hasattr(
            windows_setup_gui.WindowsSetupWizard,
            f"_action_{step.action_name}",
        )


def test_next_button_is_disabled_until_training_succeeds() -> None:
    """Po wejściu na krok treningowy nie można ominąć wyniku sesji."""
    wizard = wizard_without_screen()

    wizard._show_step(9)
    assert wizard.progress["value"] == 10
    assert wizard.next_button.options["state"] == "disabled"

    wizard.training_step_succeeded = True
    wizard._show_step(9)
    assert wizard.next_button.options["state"] == "normal"


def test_navigation_respects_first_and_last_steps() -> None:
    """Nawigacja zachowuje granice listy kroków."""
    wizard = wizard_without_screen()

    wizard._show_step(-100)
    assert wizard.current_step == 0
    assert wizard.previous_button.options["state"] == "disabled"

    wizard._show_step(100)
    assert wizard.current_step == 10
    assert wizard.next_button.options["state"] == "disabled"


@pytest.mark.parametrize("user_confirms", [False, True])
def test_close_during_operation_requires_confirmation(
    monkeypatch: pytest.MonkeyPatch,
    user_confirms: bool,
) -> None:
    """Odmowa zamknięcia pozostawia aktywną operację pod kontrolą."""
    wizard = wizard_without_screen()
    wizard.running = True
    destroyed: list[bool] = []
    wizard.destroy = lambda: destroyed.append(True)
    messages: list[tuple[str, str]] = []

    def confirm(title: str, message: str) -> bool:
        messages.append((title, message))
        return user_confirms

    monkeypatch.setattr(windows_setup_gui.messagebox, "askyesno", confirm)
    wizard._request_close()

    assert bool(destroyed) == user_confirms
    assert len(messages) == 1
    assert "Trwa operacja" in messages[0][0]


def test_close_when_idle_does_not_show_warning(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """W stanie bezczynności okno można zamknąć bez potwierdzenia."""
    wizard = wizard_without_screen()
    destroyed: list[bool] = []
    wizard.destroy = lambda: destroyed.append(True)
    monkeypatch.setattr(
        windows_setup_gui.messagebox,
        "askyesno",
        lambda *args: pytest.fail("Nie powinno być ostrzeżenia"),
    )

    wizard._request_close()

    assert destroyed == [True]
