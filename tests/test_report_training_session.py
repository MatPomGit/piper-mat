"""Testy generowania raportu z sesji treningowej."""

from pathlib import Path

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
