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

STFT_CONFIG = {
    "sampling_rate": 16_000,
    "n_fft": 16,
    "hop_size": 4,
    "win_size": 16,
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


@pytest.mark.parametrize(
    ("parameter", "value"),
    [
        ("n_fft", 0),
        ("n_fft", 16.5),
        ("n_fft", True),
        ("sampling_rate", 0),
        ("sampling_rate", 16_000.5),
        ("sampling_rate", False),
        ("hop_size", 0),
        ("hop_size", 4.5),
        ("hop_size", True),
        ("win_size", 0),
        ("win_size", 16.5),
        ("win_size", False),
        ("num_mels", 0),
        ("num_mels", 6.5),
        ("num_mels", None),
        ("num_mels", True),
    ],
)
def test_mel_spectrogram_rejects_non_positive_and_boolean_integers(parameter, value):
    """Reject invalid integer settings and identify their values."""
    config = {**BASE_CONFIG, "hop_size": 4, "win_size": 16}
    config[parameter] = value

    with pytest.raises(ValueError, match=rf"{parameter}.*{value!r}"):
        mel_processing.mel_spectrogram_torch(torch.zeros(1, 128), **config)


@pytest.mark.parametrize(
    ("parameter", "value"),
    [
        ("hop_size", 17),
        ("win_size", 17),
    ],
)
def test_spectrogram_rejects_window_or_hop_larger_than_fft(parameter, value):
    """Reject hop and window sizes above the transform size."""
    config = STFT_CONFIG.copy()
    config[parameter] = value

    with pytest.raises(ValueError, match=rf"{parameter}.*{value}"):
        mel_processing.spectrogram_torch(torch.zeros(1, 128), **config)


@pytest.mark.parametrize(
    ("fmin", "fmax", "parameter", "value"),
    [
        (-1, 7_000, "fmin", -1),
        (7_000, 7_000, "fmin", 7_000),
        (7_001, 7_000, "fmin", 7_001),
        (0, 8_001, "fmax", 8_001),
    ],
)
def test_mel_spectrogram_rejects_invalid_frequency_bounds(fmin, fmax, parameter, value):
    """Reject frequency limits outside their valid interval."""
    config = {**BASE_CONFIG, "fmin": fmin, "fmax": fmax}

    with pytest.raises(ValueError, match=rf"{parameter}.*{value}"):
        mel_processing.mel_spectrogram_torch(
            torch.zeros(1, 128), **config, hop_size=4, win_size=16
        )


def test_mel_spectrogram_accepts_inclusive_boundaries():
    """Accept equal FFT, hop, and window sizes and the Nyquist frequency."""
    result = mel_processing.mel_spectrogram_torch(
        torch.zeros(1, 32),
        **{**BASE_CONFIG, "fmin": 0, "fmax": 8_000},
        hop_size=16,
        win_size=16,
    )

    assert result.shape[:2] == (1, BASE_CONFIG["num_mels"])


@pytest.mark.parametrize(
    "function,extra_parameters",
    [
        (mel_processing.spectrogram_torch, {}),
        (
            mel_processing.mel_spectrogram_torch,
            {"num_mels": 6, "fmin": 0, "fmax": 7_000},
        ),
    ],
)
def test_spectral_analysis_rejects_input_too_short_for_reflect_padding(
    function, extra_parameters
):
    """Report short input before applying reflection padding."""
    waveform = torch.zeros(1, 6)

    with pytest.raises(ValueError, match=r"input_length.*6"):
        function(waveform, **STFT_CONFIG, **extra_parameters)


def test_spectrogram_accepts_minimum_length_for_reflect_padding():
    """Accept one sample more than the reflection-padding width."""
    result = mel_processing.spectrogram_torch(torch.zeros(1, 7), **STFT_CONFIG)

    assert result.shape[0] == 1
