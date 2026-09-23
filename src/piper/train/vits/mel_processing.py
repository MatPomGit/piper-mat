from numbers import Integral, Real

import torch
import torch.utils.data
from librosa.filters import mel as librosa_mel_fn

MAX_WAV_VALUE = 32768.0


def dynamic_range_compression_torch(x, C=1, clip_val=1e-5):
    """
    PARAMS
    ------
    C: compression factor
    """
    return torch.log(torch.clamp(x, min=clip_val) * C)


def dynamic_range_decompression_torch(x, C=1):
    """
    PARAMS
    ------
    C: compression factor used to compress
    """
    return torch.exp(x) / C


def spectral_normalize_torch(magnitudes):
    output = dynamic_range_compression_torch(magnitudes)
    return output


def spectral_de_normalize_torch(magnitudes):
    output = dynamic_range_decompression_torch(magnitudes)
    return output


mel_basis = {}
hann_window = {}
_UNSET = object()


def _validate_spectral_parameters(
    y,
    n_fft,
    sampling_rate,
    hop_size,
    win_size,
    num_mels=_UNSET,
    fmin=None,
    fmax=None,
):
    """Validate spectral-analysis parameters and reflect-padding length."""
    integer_parameters = {
        "n_fft": n_fft,
        "sampling_rate": sampling_rate,
        "hop_size": hop_size,
        "win_size": win_size,
    }
    if num_mels is not _UNSET:
        integer_parameters["num_mels"] = num_mels

    for name, value in integer_parameters.items():
        if isinstance(value, bool) or not isinstance(value, Integral) or value <= 0:
            raise ValueError(f"{name} must be a positive integer; got {name}={value!r}")

    if hop_size > n_fft:
        raise ValueError(
            "hop_size must be less than or equal to n_fft; "
            f"got hop_size={hop_size!r}, n_fft={n_fft!r}"
        )
    if win_size > n_fft:
        raise ValueError(
            "win_size must be less than or equal to n_fft; "
            f"got win_size={win_size!r}, n_fft={n_fft!r}"
        )

    if num_mels is not _UNSET:
        for name, value in (("fmin", fmin), ("fmax", fmax)):
            if isinstance(value, bool) or not isinstance(value, Real):
                raise ValueError(f"{name} must be a real number; got {name}={value!r}")

        if not 0 <= fmin < fmax:
            raise ValueError(
                "fmin must satisfy 0 <= fmin < fmax; "
                f"got fmin={fmin!r}, fmax={fmax!r}"
            )
        if fmax > sampling_rate / 2:
            raise ValueError(
                "fmax must be less than or equal to sampling_rate / 2; "
                f"got fmax={fmax!r}, sampling_rate={sampling_rate!r}"
            )

    padding = (n_fft - hop_size) // 2
    input_length = y.shape[-1] if y.ndim else 0
    if padding and input_length <= padding:
        raise ValueError(
            "input_length must be greater than reflect padding; "
            f"got input_length={input_length!r}, padding={padding!r}"
        )


def _mel_basis_key(spec, n_fft, num_mels, sampling_rate, fmin, fmax):
    return (
        sampling_rate,
        n_fft,
        num_mels,
        fmin,
        fmax,
        spec.dtype,
        spec.device,
    )


def _get_mel_basis(spec, n_fft, num_mels, sampling_rate, fmin, fmax):
    key = _mel_basis_key(spec, n_fft, num_mels, sampling_rate, fmin, fmax)
    if key not in mel_basis:
        mel = librosa_mel_fn(
            sr=sampling_rate,
            n_fft=n_fft,
            n_mels=num_mels,
            fmin=fmin,
            fmax=fmax,
        )
        mel_basis[key] = torch.from_numpy(mel).type_as(spec)

    return mel_basis[key]


def clear_mel_processing_caches():
    """Clear cached mel filters and Hann windows."""
    mel_basis.clear()
    hann_window.clear()


def spectrogram_torch(y, n_fft, sampling_rate, hop_size, win_size, center=False):
    _validate_spectral_parameters(y, n_fft, sampling_rate, hop_size, win_size)

    if torch.min(y) < -1.0:
        print("min value is ", torch.min(y))
    if torch.max(y) > 1.0:
        print("max value is ", torch.max(y))

    global hann_window
    dtype_device = str(y.dtype) + "_" + str(y.device)
    wnsize_dtype_device = str(win_size) + "_" + dtype_device
    if wnsize_dtype_device not in hann_window:
        hann_window[wnsize_dtype_device] = torch.hann_window(win_size).type_as(y)

    y = torch.nn.functional.pad(
        y.unsqueeze(1),
        (int((n_fft - hop_size) / 2), int((n_fft - hop_size) / 2)),
        mode="reflect",
    )
    y = y.squeeze(1)

    spec = torch.view_as_real(
        torch.stft(
            y,
            n_fft,
            hop_length=hop_size,
            win_length=win_size,
            window=hann_window[wnsize_dtype_device],
            center=center,
            pad_mode="reflect",
            normalized=False,
            onesided=True,
            return_complex=True,
        )
    )

    spec = torch.sqrt(spec.pow(2).sum(-1) + 1e-6)

    return spec


def spec_to_mel_torch(spec, n_fft, num_mels, sampling_rate, fmin, fmax):
    mel = _get_mel_basis(spec, n_fft, num_mels, sampling_rate, fmin, fmax)
    spec = torch.matmul(mel, spec)
    spec = spectral_normalize_torch(spec)
    return spec


def mel_spectrogram_torch(
    y, n_fft, num_mels, sampling_rate, hop_size, win_size, fmin, fmax, center=False
):
    _validate_spectral_parameters(
        y,
        n_fft,
        sampling_rate,
        hop_size,
        win_size,
        num_mels,
        fmin,
        fmax,
    )

    if torch.min(y) < -1.0:
        print("min value is ", torch.min(y))
    if torch.max(y) > 1.0:
        print("max value is ", torch.max(y))

    dtype_device = str(y.dtype) + "_" + str(y.device)
    wnsize_dtype_device = str(win_size) + "_" + dtype_device
    if wnsize_dtype_device not in hann_window:
        hann_window[wnsize_dtype_device] = torch.hann_window(win_size).type_as(y)

    y = torch.nn.functional.pad(
        y.unsqueeze(1),
        (int((n_fft - hop_size) / 2), int((n_fft - hop_size) / 2)),
        mode="reflect",
    )
    y = y.squeeze(1)
    spec = torch.view_as_real(
        torch.stft(
            y,
            n_fft,
            hop_length=hop_size,
            win_length=win_size,
            window=hann_window[wnsize_dtype_device],
            center=center,
            pad_mode="reflect",
            normalized=False,
            onesided=True,
            return_complex=True,
        )
    )

    spec = torch.sqrt(spec.pow(2).sum(-1) + 1e-6)

    mel = _get_mel_basis(spec, n_fft, num_mels, sampling_rate, fmin, fmax)
    spec = torch.matmul(mel, spec)
    spec = spectral_normalize_torch(spec)

    return spec
