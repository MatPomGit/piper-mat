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

    def test_interrupted_download_is_removed_and_retried(self) -> None:
        """An interrupted copy must not leave a partial destination file."""
        voice = "en_US-test-low"
        model_data = b"complete model"
        config_data = json.dumps({"audio": {"sample_rate": 22_050}}).encode()
        catalog = {
            voice: {
                "files": {
                    f"en/en_US/test/low/{voice}.onnx": {
                        "size_bytes": len(model_data),
                        "md5_digest": hashlib.md5(model_data).hexdigest(),
                    },
                    f"en/en_US/test/low/{voice}.onnx.json": {
                        "size_bytes": len(config_data),
                        "md5_digest": hashlib.md5(config_data).hexdigest(),
                    },
                }
            }
        }
        catalog_data = json.dumps(catalog).encode()

        with tempfile.TemporaryDirectory() as temporary_directory:
            download_dir = Path(temporary_directory)
            model_path = download_dir / f"{voice}.onnx"
            part_path = download_dir / f"{voice}.onnx.part"

            def interrupt_copy(source: io.BytesIO, destination: object) -> None:
                destination.write(source.read(4))
                raise OSError("connection interrupted")

            with patch(
                "piper.download_voices.urlopen",
                side_effect=[io.BytesIO(catalog_data), io.BytesIO(model_data)],
            ), patch.object(shutil, "copyfileobj", side_effect=interrupt_copy):
                with self.assertRaises(OSError):
                    download_voice(voice, download_dir)

            self.assertFalse(model_path.exists())
            self.assertFalse(part_path.exists())

            with patch(
                "piper.download_voices.urlopen",
                side_effect=[
                    io.BytesIO(catalog_data),
                    io.BytesIO(model_data),
                    io.BytesIO(config_data),
                ],
            ) as urlopen_mock:
                download_voice(voice, download_dir)

            self.assertEqual(model_data, model_path.read_bytes())
            self.assertEqual(3, urlopen_mock.call_count)


if __name__ == "__main__":
    unittest.main()
