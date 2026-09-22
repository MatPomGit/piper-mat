"""Testy generowania raportu z sesji treningowej."""

from pathlib import Path

import pytest

from scripts import report_training_session


def test_safe_name_distinguishes_tags_with_the_same_clean_prefix() -> None:
    """Rozróżnij znaczniki sprowadzane wcześniej do tego samego prefiksu."""
    slash_name = report_training_session.safe_name("validation/mel")
    colon_name = report_training_session.safe_name("validation:mel")

    assert slash_name.startswith("validation_mel-")
    assert colon_name.startswith("validation_mel-")
    assert slash_name != colon_name


@pytest.mark.parametrize("tag", ["", "///"])
def test_safe_name_uses_fallback_for_empty_clean_prefix(tag: str) -> None:
    """Zachowaj czytelny prefiks zastępczy dla pustej oczyszczonej nazwy."""
    assert report_training_session.safe_name(tag).startswith("metric-")


def test_safe_name_is_stable() -> None:
    """Zwróć tę samą nazwę przy każdym wywołaniu dla tego samego znacznika."""
    tag = "validation/mel"

    assert report_training_session.safe_name(tag) == report_training_session.safe_name(
        tag
    )


def test_build_report_rejects_duplicate_chart_paths_before_rendering(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Nie renderuj wykresów, jeśli ich planowane ścieżki się zderzają."""
    existing_chart = tmp_path / "charts" / "collision.svg"
    existing_chart.parent.mkdir()
    existing_chart.write_text("istniejący wykres", encoding="utf-8")
    render_calls: list[str] = []

    monkeypatch.setattr(report_training_session, "safe_name", lambda tag: "collision")
    monkeypatch.setattr(
        report_training_session,
        "render_svg",
        lambda tag, points, output: render_calls.append(tag) or True,
    )
    scalars = {
        "validation/mel": [(0, 1.0), (1, 0.5)],
        "validation:mel": [(0, 2.0), (1, 1.0)],
    }

    with pytest.raises(RuntimeError, match="nie są unikalne"):
        report_training_session.build_report_lines(
            Path("session"),
            tmp_path,
            None,
            scalars,
            list(scalars),
        )

    assert render_calls == []
    assert existing_chart.read_text(encoding="utf-8") == "istniejący wykres"
