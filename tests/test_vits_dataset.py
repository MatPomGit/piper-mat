"""Unit tests for the VITS training dataset."""

import logging
from pathlib import Path
from types import SimpleNamespace
from typing import Optional

import numpy as np
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
    data_module.piper_config = SimpleNamespace(
        speaker_id_map={}, phoneme_id_map=dataset.DEFAULT_PHONEME_ID_MAP
    )
    return data_module


def _create_cached_artifacts(
    data_module, row_number: int, text: str, missing_suffix: Optional[str] = None
) -> None:
    """Create cached artifacts for an utterance except the selected one."""
    utterance_id = (
        data_module.csv_path.read_text(encoding="utf-8")
        .splitlines()[row_number - 1]
        .split("|", maxsplit=1)[0]
    )
    audio_path = data_module.audio_dir / f"{utterance_id}.wav"
    cache_paths = data_module._get_cache_paths(
        row_number,
        text,
        None,
        audio_path,
        dataset.DEFAULT_PHONEME_ID_MAP,
    )
    artifacts = {
        "phonemes.pt": cache_paths.phoneme_ids,
        "audio.pt": cache_paths.audio,
        "spec.pt": cache_paths.spectrogram,
    }
    for suffix, path in artifacts.items():
        if suffix != missing_suffix:
            path.touch()


@pytest.mark.parametrize(
    ("row", "dataset_type", "num_speakers", "field"),
    [
        ([], dataset.DatasetType.TEXT, 1, "columns"),
        (["recording"], dataset.DatasetType.TEXT, 1, "columns"),
        (["", "Text"], dataset.DatasetType.TEXT, 1, "utterance_id"),
        (["recording", ""], dataset.DatasetType.TEXT, 1, "text"),
        (["recording", "", "Text"], dataset.DatasetType.TEXT, 2, "speaker_name"),
        (
            ["recording", "Text", ""],
            dataset.DatasetType.PHONEME_IDS,
            1,
            "phoneme_ids",
        ),
        (
            ["recording", "Text", "-1"],
            dataset.DatasetType.PHONEME_IDS,
            1,
            "phoneme_ids",
        ),
        (
            ["recording", "Text", "4"],
            dataset.DatasetType.PHONEME_IDS,
            1,
            "phoneme_ids",
        ),
        (
            ["recording", "Text", "1.5"],
            dataset.DatasetType.PHONEME_IDS,
            1,
            "phoneme_ids",
        ),
    ],
)
def test_parse_metadata_row_rejects_invalid_fields(
    tmp_path: Path,
    row: list[str],
    dataset_type: dataset.DatasetType,
    num_speakers: int,
    field: str,
) -> None:
    """Metadata validation identifies the invalid row and field."""
    data_module = dataset.VitsDataModule(
        csv_path=tmp_path / "metadata.csv",
        cache_dir=tmp_path / "cache",
        espeak_voice="en-us",
        config_path=tmp_path / "config.json",
        voice_name="test",
        dataset_type=dataset_type,
        num_speakers=num_speakers,
        num_symbols=4,
    )

    with pytest.raises(
        dataset.DatasetValidationError,
        match=rf"row 7, field '{field}'",
    ):
        data_module._parse_metadata_row(row, 7)


@pytest.mark.parametrize(
    ("row", "dataset_type", "num_speakers"),
    [
        (["recording", "Text"], dataset.DatasetType.TEXT, 1),
        (["recording", "speaker", "Text"], dataset.DatasetType.TEXT, 2),
        (
            ["recording", "Text", "0 3"],
            dataset.DatasetType.PHONEME_IDS,
            1,
        ),
        (
            ["recording", "speaker", "Text", "0 3"],
            dataset.DatasetType.PHONEME_IDS,
            2,
        ),
    ],
)
def test_parse_metadata_row_accepts_required_columns(
    tmp_path: Path,
    row: list[str],
    dataset_type: dataset.DatasetType,
    num_speakers: int,
) -> None:
    """Metadata parser accepts each supported column layout."""
    data_module = dataset.VitsDataModule(
        csv_path=tmp_path / "metadata.csv",
        cache_dir=tmp_path / "cache",
        espeak_voice="en-us",
        config_path=tmp_path / "config.json",
        voice_name="test",
        dataset_type=dataset_type,
        num_speakers=num_speakers,
        num_symbols=4,
    )

    metadata = data_module._parse_metadata_row(row, 1)

    assert metadata.utterance_id == "recording"
    assert metadata.text == "Text"


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

    with (
        caplog.at_level(logging.WARNING),
        pytest.raises(ValueError, match="No complete utterances found"),
    ):
        data_module.setup("fit")

    assert "Missing phoneme ids" in caplog.text
    assert "Missing normalized audio" in caplog.text
    assert "Missing mel spec" in caplog.text


def test_prepare_data_versions_cache_artifacts_by_dependencies(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Preparation rebuilds only artifacts affected by changed inputs."""
    csv_path = tmp_path / "metadata.csv"
    csv_path.write_text("recording|Original text|1 2 3\n", encoding="utf-8")
    audio_path = tmp_path / "recording.wav"
    audio_path.write_bytes(b"first recording")
    cache_dir = tmp_path / "cache"
    calls = {"load": 0, "spectrogram": 0}

    def load_audio(path, sr, mono):
        del path, mono
        calls["load"] += 1
        return np.ones(32, dtype=np.float32), sr

    def make_spectrogram(**kwargs):
        del kwargs
        calls["spectrogram"] += 1
        return dataset.torch.ones((1, 3, 4))

    monkeypatch.setattr(dataset.librosa, "load", load_audio)
    monkeypatch.setattr(dataset, "spectrogram_torch", make_spectrogram)
    monkeypatch.setattr(dataset, "SileroVoiceActivityDetector", lambda: object())

    def prepare(sample_rate=22050, filter_length=1024):
        data_module = dataset.VitsDataModule(
            csv_path=csv_path,
            cache_dir=cache_dir,
            espeak_voice="en-us",
            config_path=tmp_path / "config.json",
            voice_name="test",
            dataset_type=dataset.DatasetType.PHONEME_IDS,
            sample_rate=sample_rate,
            filter_length=filter_length,
            trim_silence=False,
        )
        data_module.prepare_data()

    prepare()
    assert calls == {"load": 1, "spectrogram": 1}
    assert len(list(cache_dir.glob("*.phonemes.pt"))) == 1
    assert len(list(cache_dir.glob("*.audio.pt"))) == 1
    assert len(list(cache_dir.glob("*.spec.pt"))) == 1

    prepare()
    assert calls == {"load": 1, "spectrogram": 1}

    audio_path.write_bytes(b"changed recording")
    prepare()
    assert calls == {"load": 2, "spectrogram": 2}
    assert len(list(cache_dir.glob("*.phonemes.pt"))) == 1
    assert len(list(cache_dir.glob("*.audio.pt"))) == 2
    assert len(list(cache_dir.glob("*.spec.pt"))) == 2

    csv_path.write_text("recording|Changed text|1 2 3\n", encoding="utf-8")
    prepare()
    assert calls == {"load": 2, "spectrogram": 2}
    assert len(list(cache_dir.glob("*.phonemes.pt"))) == 2

    prepare(sample_rate=16000)
    assert calls == {"load": 3, "spectrogram": 3}
    assert len(list(cache_dir.glob("*.audio.pt"))) == 3

    prepare(sample_rate=16000, filter_length=512)
    assert calls == {"load": 3, "spectrogram": 4}
    assert len(list(cache_dir.glob("*.audio.pt"))) == 3
    assert len(list(cache_dir.glob("*.spec.pt"))) == 4
