"""Tests for mel-spectrogram cache isolation."""

import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("librosa")
mel_processing = pytest.importorskip("piper.train.vits.mel_processing")


BASE_CONFIG = {
    "sampling_rate": 16_000,
    "n_fft": 16,
    "num_mels": 6,
    "fmin": 0,
    "fmax": 7_000,
}


@pytest.fixture(autouse=True)
def clear_mel_processing_caches():
    """Keep every test independent of process-global cache contents."""
    mel_processing.clear_mel_processing_caches()
    yield
    mel_processing.clear_mel_processing_caches()


@pytest.fixture(
    params=[
        ("sampling_rate", 22_050),
        ("n_fft", 32),
        ("num_mels", 8),
        ("fmin", 500),
        ("fmax", 6_000),
    ],
    ids=lambda value: value[0],
)
def changed_config(request):
    """Return mel settings that differ from the baseline in one field."""
    parameter, value = request.param
    config = BASE_CONFIG.copy()
    config[parameter] = value
    return config


def _spectrogram_for(config):
    frequency_bins = config["n_fft"] // 2 + 1
    return torch.linspace(
        0.1,
        1.0,
        steps=frequency_bins * 10,
        dtype=torch.float32,
    ).reshape(1, frequency_bins, 10)


def test_spec_to_mel_cache_separates_all_filter_parameters(changed_config):
    """Use a distinct cached filter whenever one filter setting changes."""
    mel_processing.spec_to_mel_torch(_spectrogram_for(BASE_CONFIG), **BASE_CONFIG)
    spec = _spectrogram_for(changed_config)
    cached_result = mel_processing.spec_to_mel_torch(spec, **changed_config)

    assert len(mel_processing.mel_basis) == 2

    mel_processing.clear_mel_processing_caches()
    uncached_result = mel_processing.spec_to_mel_torch(spec, **changed_config)

    torch.testing.assert_close(cached_result, uncached_result)


def test_mel_spectrogram_cache_separates_all_filter_parameters(changed_config):
    """Match an empty-cache result after one filter setting changes."""
    waveform = torch.linspace(-0.8, 0.8, steps=128).unsqueeze(0)
    stft_config = {"hop_size": 4, "win_size": 16}

    mel_processing.mel_spectrogram_torch(waveform, **BASE_CONFIG, **stft_config)
    cached_result = mel_processing.mel_spectrogram_torch(
        waveform, **changed_config, **stft_config
    )

    assert len(mel_processing.mel_basis) == 2

    mel_processing.clear_mel_processing_caches()
    uncached_result = mel_processing.mel_spectrogram_torch(
        waveform, **changed_config, **stft_config
    )

    torch.testing.assert_close(cached_result, uncached_result)
