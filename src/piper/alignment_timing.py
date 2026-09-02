"""Convert Piper phoneme alignments into engine-independent timing records."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Protocol, Sequence


class PhonemeAlignmentLike(Protocol):
    """Describe the alignment fields required by the timing converter."""

    phoneme: str
    phoneme_ids: Sequence[int]
    num_samples: int


@dataclass(frozen=True)
class PhonemeTiming:
    """Describe the absolute position of one phoneme in an audio timeline.

    ``start_sample`` is inclusive and ``end_sample`` is exclusive. Times in
    seconds are derived directly from these sample indices, so no additional
    rounding is introduced by the conversion.
    """

    phoneme: str
    phoneme_ids: tuple[int, ...]
    start_sample: int
    end_sample: int
    start_seconds: float
    end_seconds: float

    @property
    def duration_samples(self) -> int:
        """Return the duration in audio samples."""
        return self.end_sample - self.start_sample

    @property
    def duration_seconds(self) -> float:
        """Return the duration in seconds."""
        return self.end_seconds - self.start_seconds

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation of the timing record."""
        return asdict(self)


def phoneme_alignments_to_timings(
    alignments: Sequence[PhonemeAlignmentLike],
    sample_rate: int,
    *,
    start_sample: int = 0,
) -> list[PhonemeTiming]:
    """Convert relative alignment durations to absolute timing records.

    A dopasowanie fonemu (phoneme alignment) describes how many audio samples
    belong to a phoneme. This function converts those relative durations into
    an absolute timeline. For example, at 22,050 Hz a duration of 2,205 samples
    corresponds to 0.1 s.

    ``start_sample`` allows consecutive audio chunks to be placed on one common
    timeline. The default value of 0 creates timings local to a single chunk.

    :param alignments: Ordered phoneme alignments from Piper.
    :param sample_rate: Audio sample rate in Hertz, for example 22050.
    :param start_sample: Absolute sample offset of the first alignment.
    :return: Ordered absolute timing records.
    :raises ValueError: If the sample rate, offset, or duration is invalid.
    """
    if isinstance(sample_rate, bool) or sample_rate <= 0:
        raise ValueError("sample_rate must be a positive integer")
    if isinstance(start_sample, bool) or start_sample < 0:
        raise ValueError("start_sample must be a non-negative integer")

    current_sample = int(start_sample)
    timings: list[PhonemeTiming] = []

    for alignment in alignments:
        num_samples = alignment.num_samples
        if isinstance(num_samples, bool) or not isinstance(num_samples, int):
            raise ValueError("alignment num_samples must be an integer")
        if num_samples < 0:
            raise ValueError("alignment num_samples cannot be negative")

        end_sample = current_sample + num_samples
        timings.append(
            PhonemeTiming(
                phoneme=alignment.phoneme,
                phoneme_ids=tuple(int(value) for value in alignment.phoneme_ids),
                start_sample=current_sample,
                end_sample=end_sample,
                start_seconds=current_sample / sample_rate,
                end_seconds=end_sample / sample_rate,
            )
        )
        current_sample = end_sample

    return timings
