"""Flask web server with HTTP API for Piper."""

import argparse
import importlib.util
import io
import json
import logging
import math
import re
import time
import wave
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence
from urllib.request import urlopen

from flask import Flask, abort, render_template, request

from . import PiperVoice, SynthesisConfig
from .argparse_utils import nonnegative_finite_float, positive_finite_float
from .download_voices import VOICES_JSON, download_voice

_LOGGER = logging.getLogger()
_MODEL_ID_PATTERN = re.compile(r"[A-Za-z0-9_.-]+")
_URL_OPEN_TIMEOUT_SECONDS = 10
_ALL_VOICES_CACHE_SECONDS = 300


def _model_id_from_path(path: Path, suffix: str) -> str:
    """Return a model identifier after removing an exact filename suffix."""
    if not path.name.endswith(suffix):
        raise ValueError(f"Model path must end with {suffix!r}: {path}")

    return path.name[: -len(suffix)]


def _validate_model_id(model_id: Any) -> str:
    """Return a safe model identifier or abort with HTTP 400."""
    if (
        not isinstance(model_id, str)
        or not model_id
        or model_id in {".", ".."}
        or model_id.endswith(".onnx")
        or _MODEL_ID_PATTERN.fullmatch(model_id) is None
    ):
        abort(
            400,
            description=(
                "voice must be a nonempty model identifier containing only "
                "ASCII letters, digits, '_', '-' and '.', without an .onnx suffix"
            ),
        )

    return model_id


def _find_model_path(model_id: str, data_dirs: Sequence[str]) -> Optional[Path]:
    """Find a model file contained within one of the data directories."""
    for data_dir in data_dirs:
        root = Path(data_dir).resolve()
        candidate = (root / f"{model_id}.onnx").resolve()
        if candidate.is_relative_to(root) and candidate.is_file():
            return candidate

    return None


def _positive_int(value: str) -> int:
    """Parse a positive integer command-line value."""
    parsed_value = int(value)
    if parsed_value < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")

    return parsed_value


def _request_float(value: Any, name: str, *, positive: bool) -> float:
    """Validate a numeric synthesis option supplied in a JSON request."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        abort(400, description=f"{name} must be a number")

    parsed_value = float(value)
    if not math.isfinite(parsed_value):
        abort(400, description=f"{name} must be finite")
    if positive:
        if parsed_value <= 0:
            abort(400, description=f"{name} must be greater than zero")
    elif parsed_value < 0:
        abort(400, description=f"{name} must be nonnegative")

    return parsed_value


def _request_bool(value: Any, name: str) -> bool:
    """Validate a Boolean option supplied in a JSON request."""
    if not isinstance(value, bool):
        abort(400, description=f"{name} must be a boolean")

    return value


def _validate_speaker_id(speaker_id: Any, num_speakers: int) -> int:
    """Return a valid speaker identifier or abort with HTTP 400."""
    if (
        isinstance(speaker_id, bool)
        or not isinstance(speaker_id, int)
        or not 0 <= speaker_id < num_speakers
    ):
        abort(
            400,
            description=(
                "speaker_id must be an integer in the range "
                f"0 <= speaker_id < {num_speakers}"
            ),
        )

    return speaker_id


def _select_speaker_id(
    data: Dict[str, Any], voice: PiperVoice, args: argparse.Namespace
) -> Optional[int]:
    """Select and validate a speaker identifier for a synthesis request."""
    if voice.config.num_speakers <= 1:
        # Match PiperVoice: single-speaker models have no speaker input, so all
        # speaker selections are ignored for backward compatibility.
        return None

    speaker_id = data.get("speaker_id")
    if speaker_id is None:
        speaker = data.get("speaker")
        if speaker is not None:
            speaker_id = voice.config.speaker_id_map.get(speaker)
            if speaker_id is None:
                _LOGGER.warning(
                    "Speaker not found: '%s' in %s",
                    speaker,
                    voice.config.speaker_id_map.keys(),
                )

    if speaker_id is None:
        speaker_id = (
            args.speaker
            if args.speaker is not None
            else voice.config.default_speaker_id
        )

    return _validate_speaker_id(speaker_id, voice.config.num_speakers)


def _load_voice(model_path: Path, args: argparse.Namespace) -> PiperVoice:
    """Load a voice using the HTTP server's shared environment settings."""
    return PiperVoice.load(
        model_path,
        use_cuda=args.cuda,
        download_dir=Path(args.download_dir),
        include_alignments=True,
    )


def _alignment_info() -> Dict[str, Any]:
    """Describe whether in-memory alignment output patching is available."""
    if importlib.util.find_spec("onnx") is None:
        return {
            "available": False,
            "error": (
                "The onnx package is required to add alignment output. "
                "Install piper-tts[alignment]."
            ),
        }

    return {"available": True, "error": None}


def main() -> None:
    """Run HTTP server."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1", help="HTTP server host")
    parser.add_argument("--port", type=int, default=5000, help="HTTP server port")
    parser.add_argument(
        "--max-request-bytes",
        type=_positive_int,
        default=64 * 1024,
        help="Maximum HTTP request size in bytes (default: 65536)",
    )
    parser.add_argument(
        "--max-text-chars",
        type=_positive_int,
        default=10_000,
        help="Maximum synthesis text length in characters (default: 10000)",
    )
    parser.add_argument(
        "--enable-download",
        action="store_true",
        help="Enable the voice download endpoint",
    )
    #
    parser.add_argument("-m", "--model", required=True, help="Path to Onnx model file")
    #
    parser.add_argument("-s", "--speaker", type=int, help="Id of speaker (default: 0)")
    parser.add_argument(
        "--length-scale",
        "--length_scale",
        type=positive_finite_float,
        help="Phoneme length",
    )
    parser.add_argument(
        "--noise-scale",
        "--noise_scale",
        type=nonnegative_finite_float,
        help="Generator noise",
    )
    parser.add_argument(
        "--noise-w-scale",
        "--noise_w_scale",
        "--noise-w",
        "--noise_w",
        type=nonnegative_finite_float,
        help="Phoneme width noise",
    )
    #
    parser.add_argument("--cuda", action="store_true", help="Use GPU")
    #
    parser.add_argument(
        "--sentence-silence",
        "--sentence_silence",
        type=nonnegative_finite_float,
        default=0.0,
        help="Seconds of silence after each sentence",
    )
    #
    parser.add_argument(
        "--data-dir",
        "--data_dir",
        action="append",
        default=[str(Path.cwd())],
        help="Data directory to check for downloaded models (default: current directory)",
    )
    parser.add_argument(
        "--download-dir",
        "--download_dir",
        help="Path to download voices (default: first data dir)",
    )
    parser.add_argument(
        "--max-loaded-voices",
        type=_positive_int,
        default=8,
        help="Maximum number of voices kept in memory (default: 8)",
    )
    #
    parser.add_argument(
        "--debug", action="store_true", help="Print DEBUG messages to console"
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)
    _LOGGER.debug(args)

    if not args.download_dir:
        # Download voices to first data directory if not specified
        args.download_dir = args.data_dir[0]

    download_dir = Path(args.download_dir)

    # Download voice if file doesn't exist
    model_path = Path(args.model)
    if not model_path.is_file():
        # Look in data directories
        voice_name = args.model
        for data_dir in args.data_dir:
            maybe_model_path = Path(data_dir) / f"{voice_name}.onnx"
            _LOGGER.debug("Checking '%s'", maybe_model_path)
            if maybe_model_path.is_file():
                model_path = maybe_model_path
                break

    if not model_path.is_file():
        raise ValueError(
            f"Unable to find voice: {model_path} (use piper.download_voices)"
        )

    default_model_id = _model_id_from_path(model_path, ".onnx")

    # Load voice
    default_voice = _load_voice(model_path, args)
    loaded_voices: OrderedDict[str, PiperVoice] = OrderedDict(
        [(default_model_id, default_voice)]
    )

    # Create web server.
    # Images live in the "img" directory and are served under "/img".
    app = Flask(__name__, static_folder="img", static_url_path="/img")
    app.config["MAX_CONTENT_LENGTH"] = args.max_request_bytes

    # Info about the most recently synthesized utterance (for the web page).
    last_synthesis: Dict[str, Any] = {}
    all_voices_cache: Dict[str, Any] = {}

    @app.route("/", methods=["GET"])
    def app_index() -> str:
        """Web page for testing a voice in the browser."""
        return render_template("index.html")

    @app.route("/info", methods=["GET"])
    def app_info() -> Dict[str, Any]:
        """Info about the current voice and most recently synthesized utterance.

        Outputs a JSON object with the format:
        {
          "voice": {
            "name": "<voice name>",
            "language": "<espeak voice/alphabet>",
            "num_speakers": <number of speakers>
          },
          "last": {                            (null until something is synthesized)
            "text": "<synthesized text>",
            "synthesize_seconds": <wall-clock synthesis time>,
            "phonemes": ["<phoneme>", ...],
            "alignments": [
              { "phoneme": "<phoneme>", "seconds": <duration> },
              ...
            ]
          }
        }
        """
        return {
            "voice": {
                "name": default_model_id,
                "language": default_voice.config.espeak_voice,
                "num_speakers": default_voice.config.num_speakers,
            },
            "alignments": _alignment_info(),
            "last": last_synthesis or None,
        }

    @app.route("/voices", methods=["GET"])
    def app_voices() -> Dict[str, Any]:
        """List downloaded voices.

        Outputs a JSON object with the format:
        {
          "<voice name>": { <voice config> },
          ...
        }

        for each voice in your data directories.
        """
        voices_dict: Dict[str, Any] = {}
        config_paths: List[Path] = [Path(f"{model_path}.json")]

        for data_dir in args.data_dir:
            for onnx_path in Path(data_dir).glob("*.onnx"):
                config_path = Path(f"{onnx_path}.json")
                if config_path.exists():
                    config_paths.append(config_path)

        for config_path in config_paths:
            model_id = _model_id_from_path(config_path, ".onnx.json")
            if model_id in voices_dict:
                continue

            with open(config_path, "r", encoding="utf-8") as config_file:
                voices_dict[model_id] = json.load(config_file)

        return voices_dict

    @app.route("/all-voices", methods=["GET"])
    def app_all_voices() -> Dict[str, Any]:
        """List all Piper voices.

        Outputs voices.json from the piper-voices repo on HuggingFace.
        See: https://huggingface.co/rhasspy/piper-voices
        """
        now = time.monotonic()
        if now >= all_voices_cache.get("expires_at", 0):
            with urlopen(VOICES_JSON, timeout=_URL_OPEN_TIMEOUT_SECONDS) as response:
                all_voices_cache["voices"] = json.load(response)
            all_voices_cache["expires_at"] = now + _ALL_VOICES_CACHE_SECONDS

        return all_voices_cache["voices"]

    @app.route("/download", methods=["POST"])
    def app_download() -> str:
        """Download a voice.

        Downloads the .onnx and .onnx.json file from piper-voices repo on HuggingFace.
        See: https://huggingface.co/rhasspy/piper-voices

        Expects a JSON object with the format:
        {
          "voice": "<voice name>",   (required)
          "force_redownload": false  (optional)
        }

        Returns the name of the voice.
        Voice format must be <language>-<name>-<quality> like "en_US-lessac-medium".
        """
        if not args.enable_download:
            abort(403, description="Voice downloads are disabled")

        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            abort(400, description="Request body must be a JSON object")

        model_id = data.get("voice")
        if not isinstance(model_id, str) or not model_id.strip():
            abort(400, description="voice must be a nonempty string")

        force_redownload = _request_bool(
            data.get("force_redownload", False), "force_redownload"
        )
        try:
            download_voice(
                model_id,
                download_dir,
                force_redownload=force_redownload,
                timeout=_URL_OPEN_TIMEOUT_SECONDS,
            )
        except ValueError as exc:
            abort(400, description=str(exc))

        return model_id

    @app.route("/synthesize", methods=["POST"])
    def app_synthesize() -> bytes:
        """Synthesize audio from text.

        Expects a JSON object with the format:
        {
          "text": "Text to speak.",      (required)
          "voice": "<voice name>",       (optional)
          "speaker": "<speaker name>",   (optional)
          "speaker_id": "<speaker id>",  (optional, overrides speaker)
          "length_scale": 1.0,           (optional)
          "noise_scale": 0.667,          (optional)
          "noise_w_scale": 0.8          (optional)
        }
        """
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            abort(400, description="Request body must be a JSON object")

        raw_text = data.get("text", "")
        if not isinstance(raw_text, str):
            abort(400, description="text must be a string")
        if len(raw_text) > args.max_text_chars:
            abort(413, description="Text exceeds the configured character limit")

        text = raw_text.strip()
        if not text:
            abort(400, description="No text provided")

        _LOGGER.debug(data)

        model_id = _validate_model_id(
            data["voice"] if "voice" in data else default_model_id
        )
        voice = loaded_voices.get(model_id)
        if voice is None:
            model_path = _find_model_path(model_id, args.data_dir)
            if model_path is not None:
                _LOGGER.debug("Loading voice %s", model_id)
                voice = _load_voice(model_path, args)
                if args.max_loaded_voices > 1:
                    while len(loaded_voices) >= args.max_loaded_voices:
                        oldest_model_id = next(iter(loaded_voices))
                        if oldest_model_id == default_model_id:
                            loaded_voices.move_to_end(oldest_model_id)
                            continue

                        loaded_voices.popitem(last=False)

                    loaded_voices[model_id] = voice

        elif model_id != default_model_id:
            loaded_voices.move_to_end(model_id)

        if voice is None:
            _LOGGER.warning("Voice not found: %s", model_id)
            abort(404, description=f"Voice not found: {model_id}")

        speaker_id = _select_speaker_id(data, voice, args)
        silence_samples = int(voice.config.sample_rate * args.sentence_silence)
        silence_bytes = bytes(silence_samples * 2)

        length_scale = data.get(
            "length_scale",
            (
                args.length_scale
                if args.length_scale is not None
                else voice.config.length_scale
            ),
        )
        noise_scale = data.get(
            "noise_scale",
            (
                args.noise_scale
                if args.noise_scale is not None
                else voice.config.noise_scale
            ),
        )
        noise_w_scale = data.get(
            "noise_w_scale",
            (
                args.noise_w_scale
                if args.noise_w_scale is not None
                else voice.config.noise_w_scale
            ),
        )
        syn_config = SynthesisConfig(
            speaker_id=speaker_id,
            length_scale=_request_float(length_scale, "length_scale", positive=True),
            noise_scale=_request_float(noise_scale, "noise_scale", positive=False),
            noise_w_scale=_request_float(
                noise_w_scale, "noise_w_scale", positive=False
            ),
        )

        _LOGGER.debug("Synthesizing text: '%s' with config=%s", text, syn_config)
        phonemes: List[str] = []
        alignments: List[Dict[str, Any]] = []
        start_time = time.monotonic()
        with io.BytesIO() as wav_io:
            wav_file: wave.Wave_write = wave.open(wav_io, "wb")
            with wav_file:
                wav_params_set = False
                for i, audio_chunk in enumerate(
                    voice.synthesize(text, syn_config, include_alignments=True)
                ):
                    if not wav_params_set:
                        wav_file.setframerate(audio_chunk.sample_rate)
                        wav_file.setsampwidth(audio_chunk.sample_width)
                        wav_file.setnchannels(audio_chunk.sample_channels)
                        wav_params_set = True

                    if i > 0:
                        wav_file.writeframes(silence_bytes)

                    wav_file.writeframes(audio_chunk.audio_int16_bytes)

                    # Collect phonemes/alignments for the web page
                    phonemes.extend(audio_chunk.phonemes)
                    for alignment in audio_chunk.phoneme_alignments or []:
                        alignments.append(
                            {
                                "phoneme": alignment.phoneme,
                                "seconds": alignment.num_samples
                                / audio_chunk.sample_rate,
                            }
                        )

            synthesize_seconds = time.monotonic() - start_time
            last_synthesis.clear()
            last_synthesis.update(
                text=text,
                synthesize_seconds=synthesize_seconds,
                phonemes=phonemes,
                alignments=alignments,
            )

            return wav_io.getvalue()

    app.run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
