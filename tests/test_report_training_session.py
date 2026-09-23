"""Testy generowania raportu z sesji treningowej."""

from pathlib import Path
from types import SimpleNamespace

import pytest

pytest.importorskip("tensorboard")

from tensorboard.compat.proto.event_pb2 import Event  # noqa: E402
from tensorboard.compat.proto.summary_pb2 import Summary  # noqa: E402
from tensorboard.summary.writer.event_file_writer import EventFileWriter  # noqa: E402

from scripts import report_training_session  # noqa: E402


def write_scalar(
    directory: Path,
    *,
    step: int,
    value: float,
    wall_time: float,
) -> None:
    """Zapisz pojedyncze zdarzenie skalarne TensorBoard."""
    writer = EventFileWriter(str(directory))
    writer.add_event(
        Event(
            wall_time=wall_time,
            step=step,
            summary=Summary(value=[Summary.Value(tag="loss", simple_value=value)]),
        )
    )
    writer.close()


def test_load_scalars_prefers_later_wall_time_across_event_dirs(
    tmp_path: Path,
) -> None:
    """Wybierz nowszy pomiar niezależnie od kolejności katalogów."""
    write_scalar(tmp_path / "a-later", step=7, value=2.5, wall_time=200.0)
    write_scalar(tmp_path / "z-earlier", step=7, value=1.5, wall_time=100.0)

    scalars = report_training_session.load_scalars(tmp_path)

    assert scalars == {"loss": [(7, 2.5)]}


def test_metric_lines_uses_only_finite_points_for_summary() -> None:
    """Oblicz podsumowanie z tych samych skończonych punktów co wykres."""
    lines = report_training_session.metric_lines(
        "loss",
        [
            (0, float("nan")),
            (1, 4.0),
            (2, float("nan")),
            (3, float("-inf")),
            (4, 2.0),
            (5, float("inf")),
        ],
        Path("charts/loss.svg"),
    )

    assert "- pierwszy krok: 1" in lines
    assert "- ostatni krok: 4" in lines
    assert "- wartość początkowa: 4" in lines
    assert "- wartość końcowa: 2" in lines
    assert "- minimum: 2" in lines
    assert "- maksimum: 4" in lines


def test_metric_lines_ignores_point_with_non_finite_step() -> None:
    """Pomiń wartość, jeśli odpowiadający jej krok nie jest skończony."""
    lines = report_training_session.metric_lines(
        "loss",
        [(1, 3.0), (float("nan"), -10.0), (2, 2.0)],
        Path("charts/loss.svg"),
    )

    assert "- pierwszy krok: 1" in lines
    assert "- ostatni krok: 2" in lines
    assert "- minimum: 2" in lines


def test_metric_lines_describes_single_finite_point_without_trend() -> None:
    """Opisz pojedynczy punkt bez pól sugerujących zmianę wartości."""
    lines = report_training_session.metric_lines(
        "loss",
        [(0, float("nan")), (7, 1.25), (8, float("inf"))],
        Path("charts/loss.svg"),
    )

    assert "- krok: 7" in lines
    assert "- wartość: 1.25" in lines
    assert not any("początkowa" in line or "końcowa" in line for line in lines)
    assert not any("minimum" in line or "maksimum" in line for line in lines)


def test_metric_lines_skips_metric_without_finite_points() -> None:
    """Pomiń sekcję metryki, jeśli żaden punkt nie jest skończony."""
    lines = report_training_session.metric_lines(
        "loss",
        [(0, float("nan")), (1, float("inf")), (2, float("-inf"))],
        Path("charts/loss.svg"),
    )

    assert lines == []


def test_build_report_uses_filtered_points_for_chart_and_summary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Przekaż do wykresu punkty używane później w podsumowaniu."""
    rendered_points: list[tuple[int, float]] = []

    def capture_points(
        _tag: str,
        points: list[tuple[int, float]],
        _output: Path,
    ) -> bool:
        rendered_points.extend(points)
        return True

    monkeypatch.setattr(report_training_session, "render_svg", capture_points)
    lines = report_training_session.build_report_lines(
        Path("session"),
        tmp_path,
        None,
        {
            "loss": [
                (0, float("nan")),
                (1, 4.0),
                (2, float("inf")),
                (3, 2.0),
            ]
        },
        ["loss"],
    )

    assert rendered_points == [(1, 4.0), (3, 2.0)]
    assert "- pierwszy krok: 1" in lines
    assert "- ostatni krok: 3" in lines


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


def run_main(
    monkeypatch: pytest.MonkeyPatch,
    session_dir: Path,
    output_dir: Path,
) -> int:
    """Uruchom funkcję główną ze stałymi danymi skalarnymi."""
    args = SimpleNamespace(
        session_dir=session_dir,
        output_dir=output_dir,
        metadata=None,
    )
    monkeypatch.setattr(report_training_session, "parse_args", lambda: args)
    monkeypatch.setattr(
        report_training_session,
        "load_scalars",
        lambda _path: {"loss": [(1, 2.0), (2, 1.0)]},
    )
    return report_training_session.main()


def test_main_handles_output_directory_creation_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Zwróć kod 2, gdy nie można utworzyć katalogu raportu."""
    session_dir = tmp_path / "session"
    session_dir.mkdir()
    output_dir = tmp_path / "output"
    output_dir.write_text("blokada", encoding="utf-8")

    result = run_main(monkeypatch, session_dir, output_dir)

    captured = capsys.readouterr()
    assert result == 2
    assert str(output_dir) in captured.err
    assert "BŁĄD: nie można zapisać raportu" in captured.err


def test_main_handles_svg_write_error_without_replacing_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Zachowaj poprzedni raport po błędzie zapisu wykresu SVG."""
    session_dir = tmp_path / "session"
    session_dir.mkdir()
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    report_path = output_dir / "REPORT.md"
    report_path.write_text("poprzedni raport\n", encoding="utf-8")

    def fail_render(*_args: object, **_kwargs: object) -> bool:
        raise OSError("brak miejsca na SVG")

    monkeypatch.setattr(report_training_session, "render_svg", fail_render)

    result = run_main(monkeypatch, session_dir, output_dir)

    captured = capsys.readouterr()
    assert result == 2
    assert "brak miejsca na SVG" in captured.err
    assert str(output_dir) in captured.err
    assert report_path.read_text(encoding="utf-8") == "poprzedni raport\n"


def test_main_handles_report_write_error_without_replacing_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Zachowaj poprzedni raport po błędzie zapisu pliku REPORT.md."""
    session_dir = tmp_path / "session"
    session_dir.mkdir()
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    report_path = output_dir / "REPORT.md"
    report_path.write_text("poprzedni raport\n", encoding="utf-8")
    original_write = report_training_session.write_text_atomically

    def fail_report_write(path: Path, content: str) -> None:
        if path.name == "REPORT.md":
            raise OSError("odmowa zapisu REPORT.md")
        original_write(path, content)

    monkeypatch.setattr(
        report_training_session,
        "write_text_atomically",
        fail_report_write,
    )

    result = run_main(monkeypatch, session_dir, output_dir)

    captured = capsys.readouterr()
    assert result == 2
    assert "odmowa zapisu REPORT.md" in captured.err
    assert str(output_dir) in captured.err
    assert report_path.read_text(encoding="utf-8") == "poprzedni raport\n"
