"""Tests for engine-independent phoneme timing conversion."""

from dataclasses import dataclass

import pytest

from piper.alignment_timing import phoneme_alignments_to_timings


@dataclass
class Alignment:
    """Minimal alignment object used by converter tests."""

    phoneme: str
    phoneme_ids: tuple[int, ...]
    num_samples: int


def test_phoneme_alignments_to_timings() -> None:
    """Convert relative sample counts to one continuous timeline."""
    alignments = [
        Alignment("a", (10, 0), 2205),
        Alignment("b", (11, 0), 1102),
    ]

    timings = phoneme_alignments_to_timings(alignments, 22050)

    assert len(timings) == 2
    assert timings[0].start_sample == 0
    assert timings[0].end_sample == 2205
    assert timings[0].start_seconds == pytest.approx(0.0)
    assert timings[0].end_seconds == pytest.approx(0.1)
    assert timings[0].duration_samples == 2205
    assert timings[0].duration_seconds == pytest.approx(0.1)

    assert timings[1].start_sample == 2205
    assert timings[1].end_sample == 3307
    assert timings[1].start_seconds == pytest.approx(0.1)
    assert timings[1].end_seconds == pytest.approx(3307 / 22050)
    assert timings[1].phoneme_ids == (11, 0)


def test_phoneme_alignments_to_timings_with_offset() -> None:
    """Place a later audio chunk on the same absolute sample timeline."""
    alignment = Alignment("a", (10,), 100)

    timing = phoneme_alignments_to_timings(
        [alignment],
        1000,
        start_sample=500,
    )[0]

    assert timing.start_sample == 500
    assert timing.end_sample == 600
    assert timing.start_seconds == pytest.approx(0.5)
    assert timing.end_seconds == pytest.approx(0.6)


def test_phoneme_alignments_to_timings_rejects_invalid_values() -> None:
    """Reject invalid rates, offsets, and alignment durations."""
    alignment = Alignment("a", (10,), 100)

    with pytest.raises(ValueError):
        phoneme_alignments_to_timings([alignment], 0)
    with pytest.raises(ValueError):
        phoneme_alignments_to_timings([alignment], 1000, start_sample=-1)
    with pytest.raises(ValueError):
        phoneme_alignments_to_timings([Alignment("a", (10,), -1)], 1000)
