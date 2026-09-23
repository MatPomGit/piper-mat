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
