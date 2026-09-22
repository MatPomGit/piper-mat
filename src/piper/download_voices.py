"""Command-line utility for downloading Piper voices."""

import argparse
import hashlib
import json
import logging
import re
import shutil
from pathlib import Path
from urllib.request import urlopen

URL_FORMAT = "https://huggingface.co/rhasspy/piper-voices/resolve/main/{lang_family}/{lang_code}/{voice_name}/{voice_quality}/{lang_code}-{voice_name}-{voice_quality}{extension}?download=true"
VOICES_JSON = (
    "https://huggingface.co/rhasspy/piper-voices/resolve/main/voices.json?download=true"
)
VOICE_PATTERN = re.compile(
    r"^(?P<lang_family>[^-]+)_(?P<lang_region>[^-]+)-(?P<voice_name>[^-]+)-(?P<voice_quality>.+)$"
)

_LOGGER = logging.getLogger(__name__)


def main() -> None:
    """Download Piper voices."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "voice", nargs="*", help="Name of voice like 'en_US-lessac-medium'"
    )
    parser.add_argument(
        "--download-dir",
        "--download_dir",
        "--data-dir",
        "--data_dir",
        help="Directory to download voices into (default: current directory)",
    )
    parser.add_argument(
        "--force-redownload",
        "--force_redownload",
        action="store_true",
        help="Force redownloading of voice files even if they exist already",
    )
    parser.add_argument(
        "--debug", action="store_true", help="Print DEBUG logs to console"
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)

    if not args.voice:
        list_voices()
        return

    if args.download_dir:
        download_dir = Path(args.download_dir)
    else:
        download_dir = Path.cwd()

    download_dir.mkdir(parents=True, exist_ok=True)

    for voice in args.voice:
        download_voice(voice, download_dir, force_redownload=args.force_redownload)


# -----------------------------------------------------------------------------


def list_voices() -> None:
    """List available voices and exit."""
    _LOGGER.debug("Downloading voices.json file: '%s'", VOICES_JSON)
    with urlopen(VOICES_JSON) as response:
        voices_dict = json.load(response)

    for voice in sorted(voices_dict.keys()):
        print(voice)


def download_voice(
    voice: str, download_dir: Path, force_redownload: bool = False
) -> None:
    """Download a voice model and config file to a directory."""
    voice = voice.strip()
    voice_match = VOICE_PATTERN.match(voice)
    if not voice_match:
        raise ValueError(
            f"Voice '{voice}' did not match pattern: <language>-<name>-<quality> like 'en_US-lessac-medium'",
        )

    lang_family = voice_match.group("lang_family")
    lang_code = lang_family + "_" + voice_match.group("lang_region")
    voice_name = voice_match.group("voice_name")
    voice_quality = voice_match.group("voice_quality")

    voice_code = f"{lang_code}-{voice_name}-{voice_quality}"
    format_args = {
        "lang_family": lang_family,
        "lang_code": lang_code,
        "voice_name": voice_name,
        "voice_quality": voice_quality,
    }

    _LOGGER.debug("Downloading voices.json file: '%s'", VOICES_JSON)
    with urlopen(VOICES_JSON) as response:
        voices_dict = json.load(response)

    voice_info = voices_dict.get(voice, {})
    voice_files = voice_info.get("files", {})

    model_path = download_dir / f"{voice_code}.onnx"
    model_info = _get_file_info(voice_files, model_path.name)
    if force_redownload or _needs_download(model_path, model_info):
        model_url = URL_FORMAT.format(extension=".onnx", **format_args)
        _LOGGER.debug("Downloading model from '%s' to '%s'", model_url, model_path)
        _download_file(model_url, model_path, model_info)

        _LOGGER.debug("Downloaded: '%s'", model_path)

    config_path = download_dir / f"{voice_code}.onnx.json"
    config_info = _get_file_info(voice_files, config_path.name)
    if force_redownload or _needs_download(config_path, config_info, is_json=True):
        config_url = URL_FORMAT.format(extension=".onnx.json", **format_args)
        _LOGGER.debug("Downloading config from '%s' to '%s'", config_url, config_path)
        _download_file(config_url, config_path, config_info, is_json=True)

        _LOGGER.debug("Downloaded: '%s'", config_path)

    _LOGGER.info("Downloaded: %s", voice)


def _get_file_info(voice_files: object, file_name: str) -> dict:
    """Return catalog metadata for a voice artifact, when available."""
    if not isinstance(voice_files, dict):
        return {}

    for catalog_path, file_info in voice_files.items():
        if Path(catalog_path).name == file_name and isinstance(file_info, dict):
            return file_info

    return {}


def _download_file(
    url: str, path: Path, file_info: dict, is_json: bool = False
) -> None:
    """Download and validate a file before atomically replacing its destination."""
    temporary_path = path.with_name(f"{path.name}.part")
    try:
        with urlopen(url) as response:
            with open(temporary_path, "wb") as output_file:
                shutil.copyfileobj(response, output_file)
                output_file.flush()

        _validate_file(temporary_path, file_info, is_json=is_json)
        temporary_path.replace(path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


def _validate_file(path: Path, file_info: dict, is_json: bool = False) -> None:
    """Validate an artifact against catalog metadata and its expected format."""
    expected_size = file_info.get("size_bytes")
    if expected_size is not None and path.stat().st_size != expected_size:
        raise ValueError(f"Unexpected size for downloaded file: {path}")

    for algorithm, metadata_key in (
        ("sha256", "sha256_digest"),
        ("md5", "md5_digest"),
    ):
        expected_digest = file_info.get(metadata_key)
        if expected_digest:
            digest = hashlib.new(algorithm)
            with open(path, "rb") as input_file:
                for chunk in iter(lambda: input_file.read(64 * 1024), b""):
                    digest.update(chunk)

            if digest.hexdigest().lower() != str(expected_digest).lower():
                raise ValueError(f"Unexpected checksum for downloaded file: {path}")

    if is_json:
        with open(path, "r", encoding="utf-8") as config_file:
            config = json.load(config_file)

        if not isinstance(config, dict):
            raise ValueError(f"Voice config must be a JSON object: {path}")


def _needs_download(path: Path, file_info: dict, is_json: bool = False) -> bool:
    """Return True if file needs to be downloaded."""
    if not path.exists():
        return True

    if not file_info and not is_json:
        return True

    try:
        _validate_file(path, file_info, is_json=is_json)
    except (OSError, ValueError, json.JSONDecodeError):
        return True

    return False


# -----------------------------------------------------------------------------

if __name__ == "__main__":
    main()
