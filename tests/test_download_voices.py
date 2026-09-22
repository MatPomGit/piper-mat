"""Tests for atomic voice downloads."""

import hashlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from piper.download_voices import download_voice


class DownloadVoiceTestCase(unittest.TestCase):
    """Verify that voice artifacts are downloaded atomically."""

    voice = "en_US-test-low"
    model_data = b"complete model"
    config_data = json.dumps({"audio": {"sample_rate": 22_050}}).encode()

    def _catalog_data(self) -> bytes:
        """Build catalog data for the test voice."""
        catalog = {
            self.voice: {
                "files": {
                    f"en/en_US/test/low/{self.voice}.onnx": {
                        "size_bytes": len(self.model_data),
                        "md5_digest": hashlib.md5(self.model_data).hexdigest(),
                    },
                    f"en/en_US/test/low/{self.voice}.onnx.json": {
                        "size_bytes": len(self.config_data),
                        "md5_digest": hashlib.md5(self.config_data).hexdigest(),
                    },
                }
            }
        }
        return json.dumps(catalog).encode()

    def _write_old_pair(self, download_dir: Path) -> tuple[Path, Path]:
        """Write and return a complete pre-existing voice pair."""
        model_path = download_dir / f"{self.voice}.onnx"
        config_path = download_dir / f"{self.voice}.onnx.json"
        model_path.write_bytes(b"old model")
        config_path.write_text('{"version": "old"}', encoding="utf-8")
        return model_path, config_path

    def _assert_old_pair(self, model_path: Path, config_path: Path) -> None:
        """Assert that both pre-existing voice artifacts remain unchanged."""
        self.assertEqual(b"old model", model_path.read_bytes())
        self.assertEqual('{"version": "old"}', config_path.read_text(encoding="utf-8"))
        self.assertFalse(model_path.with_name(f"{model_path.name}.part").exists())
        self.assertFalse(config_path.with_name(f"{config_path.name}.part").exists())
        self.assertFalse(model_path.with_name(f"{model_path.name}.bak").exists())
        self.assertFalse(config_path.with_name(f"{config_path.name}.bak").exists())

    def test_interrupted_download_is_removed_and_retried(self) -> None:
        """An interrupted copy must not leave a partial destination file."""
        catalog_data = self._catalog_data()

        with tempfile.TemporaryDirectory() as temporary_directory:
            download_dir = Path(temporary_directory)
            model_path = download_dir / f"{self.voice}.onnx"
            part_path = download_dir / f"{self.voice}.onnx.part"

            def interrupt_copy(source: io.BytesIO, destination: object) -> None:
                destination.write(source.read(4))
                raise OSError("connection interrupted")

            with patch(
                "piper.download_voices.urlopen",
                side_effect=[io.BytesIO(catalog_data), io.BytesIO(self.model_data)],
            ), patch.object(shutil, "copyfileobj", side_effect=interrupt_copy):
                with self.assertRaises(OSError):
                    download_voice(self.voice, download_dir)

            self.assertFalse(model_path.exists())
            self.assertFalse(part_path.exists())

            with patch(
                "piper.download_voices.urlopen",
                side_effect=[
                    io.BytesIO(catalog_data),
                    io.BytesIO(self.model_data),
                    io.BytesIO(self.config_data),
                ],
            ) as urlopen_mock:
                download_voice(self.voice, download_dir)

            self.assertEqual(self.model_data, model_path.read_bytes())
            self.assertEqual(
                self.config_data,
                download_dir.joinpath(f"{self.voice}.onnx.json").read_bytes(),
            )
            self.assertEqual(3, urlopen_mock.call_count)

    def test_first_download_failure_preserves_old_pair(self) -> None:
        """A model transfer failure must preserve both old artifacts."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            download_dir = Path(temporary_directory)
            model_path, config_path = self._write_old_pair(download_dir)

            with patch(
                "piper.download_voices.urlopen",
                side_effect=[io.BytesIO(self._catalog_data()), OSError("model")],
            ):
                with self.assertRaises(OSError):
                    download_voice(self.voice, download_dir, force_redownload=True)

            self._assert_old_pair(model_path, config_path)

    def test_second_download_failure_preserves_old_pair(self) -> None:
        """A config transfer failure must preserve both old artifacts."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            download_dir = Path(temporary_directory)
            model_path, config_path = self._write_old_pair(download_dir)

            with patch(
                "piper.download_voices.urlopen",
                side_effect=[
                    io.BytesIO(self._catalog_data()),
                    io.BytesIO(self.model_data),
                    OSError("config"),
                ],
            ):
                with self.assertRaises(OSError):
                    download_voice(self.voice, download_dir, force_redownload=True)

            self._assert_old_pair(model_path, config_path)

    def test_second_publish_failure_restores_old_pair(self) -> None:
        """A config publication failure must roll back the model publication."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            download_dir = Path(temporary_directory)
            model_path, config_path = self._write_old_pair(download_dir)
            config_part_path = config_path.with_name(f"{config_path.name}.part")
            original_replace = Path.replace

            def fail_config_publish(source: Path, target: Path) -> Path:
                if source == config_part_path:
                    raise OSError("config publication")
                return original_replace(source, target)

            with patch(
                "piper.download_voices.urlopen",
                side_effect=[
                    io.BytesIO(self._catalog_data()),
                    io.BytesIO(self.model_data),
                    io.BytesIO(self.config_data),
                ],
            ), patch.object(Path, "replace", autospec=True) as replace_mock:
                replace_mock.side_effect = fail_config_publish
                with self.assertRaises(OSError):
                    download_voice(self.voice, download_dir, force_redownload=True)

            self._assert_old_pair(model_path, config_path)


if __name__ == "__main__":
    unittest.main()
