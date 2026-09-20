"""Unit tests for the VITS training dataset."""

import logging
from pathlib import Path
from types import SimpleNamespace
from typing import Optional

import pytest

dataset = pytest.importorskip("piper.train.vits.dataset")


def _create_data_module(tmp_path: Path, utterances: list[tuple[str, str]]):
    """Create a data module and its source audio files."""
    csv_path = tmp_path / "metadata.csv"
    csv_path.write_text(
        "".join(f"{utterance_id}|{text}\n" for utterance_id, text in utterances),
        encoding="utf-8",
    )

    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    for utterance_id, _ in utterances:
        (tmp_path / f"{utterance_id}.wav").touch()

    data_module = dataset.VitsDataModule(
        csv_path=csv_path,
        cache_dir=cache_dir,
        espeak_voice="en-us",
        config_path=tmp_path / "config.json",
        voice_name="test",
    )
    data_module.piper_config = SimpleNamespace(speaker_id_map={})
    return data_module


def _create_cached_artifacts(
    data_module, row_number: int, text: str, missing_suffix: Optional[str] = None
) -> None:
    """Create cached artifacts for an utterance except the selected one."""
    cache_id = dataset.get_cache_id(row_number, text, speaker_id=None)
    for suffix in ("phonemes.pt", "audio.pt", "spec.pt"):
        if suffix != missing_suffix:
            (data_module.cache_dir / f"{cache_id}.{suffix}").touch()


@pytest.mark.parametrize(
    ("missing_suffix", "warning"),
    [
        ("phonemes.pt", "Missing phoneme ids"),
        ("audio.pt", "Missing normalized audio"),
        ("spec.pt", "Missing mel spec"),
    ],
)
def test_setup_skips_utterance_with_missing_cached_artifact(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
    missing_suffix: str,
    warning: str,
) -> None:
    """Setup skips an utterance when any required cache file is missing."""
    utterances = [("incomplete", "Missing cache"), ("complete", "Ready")]
    data_module = _create_data_module(tmp_path, utterances)
    _create_cached_artifacts(data_module, 1, utterances[0][1], missing_suffix)
    _create_cached_artifacts(data_module, 2, utterances[1][1])

    with caplog.at_level(logging.WARNING):
        data_module.setup("fit")

    assert warning in caplog.text
    assert (
        sum(
            len(split)
            for split in (
                data_module.train_dataset,
                data_module.test_dataset,
                data_module.val_dataset,
            )
        )
        == 1
    )


def test_setup_rejects_dataset_without_complete_utterances(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Setup reports an error when every utterance is incomplete."""
    utterances = [
        ("no_phonemes", "One"),
        ("no_audio", "Two"),
        ("no_spec", "Three"),
    ]
    data_module = _create_data_module(tmp_path, utterances)
    for row_number, (_, text) in enumerate(utterances, start=1):
        _create_cached_artifacts(
            data_module,
            row_number,
            text,
            missing_suffix=("phonemes.pt", "audio.pt", "spec.pt")[row_number - 1],
        )

    with caplog.at_level(logging.WARNING), pytest.raises(
        ValueError, match="No complete utterances found"
    ):
        data_module.setup("fit")

    assert "Missing phoneme ids" in caplog.text
    assert "Missing normalized audio" in caplog.text
    assert "Missing mel spec" in caplog.text
