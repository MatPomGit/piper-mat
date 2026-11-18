"""Testy bezpiecznego pobierania punktów kontrolnych bez sieci."""

import hashlib
import sys
from pathlib import Path

import pytest

from scripts import download_checkpoint


def configure_cli(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    data: bytes,
) -> Path:
    """Skonfiguruj zweryfikowane pobieranie do lokalnego pliku."""
    output = tmp_path / "checkpoints" / "base.ckpt"
    monkeypatch.setattr(
        sys,
        "argv",
        ["download_checkpoint.py", "--output", str(output)],
    )
    monkeypatch.setattr(
        download_checkpoint,
        "load_entry",
        lambda *args: {
            "source": {"url": "https://example.org/base.ckpt"},
            "size_bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        },
    )
    return output


def test_downloads_use_distinct_temporary_files(tmp_path: Path) -> None:
    """Równoległe pobrania nie mogą współdzielić pliku .part."""
    output = tmp_path / "checkpoints" / "base.ckpt"
    first = download_checkpoint.create_temporary_download(output)
    second = download_checkpoint.create_temporary_download(output)
    try:
        assert first != second
        assert first.is_file() and second.is_file()
    finally:
        first.unlink()
        second.unlink()


def test_successful_download_replaces_output_and_cleans_up(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Publikuj wyłącznie kompletny plik o poprawnym skrócie."""
    content = b"new verified checkpoint"
    output = configure_cli(tmp_path, monkeypatch, content)
    output.parent.mkdir(parents=True)
    output.write_bytes(b"old checkpoint")
    monkeypatch.setattr(
        download_checkpoint,
        "download_file",
        lambda url, destination: destination.write_bytes(content),
    )

    assert download_checkpoint.main() == 0
    assert output.read_bytes() == content
    assert list(output.parent.iterdir()) == [output]


def test_network_error_preserves_output_and_removes_partial_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Awaria w trakcie pobierania nie może naruszyć poprzedniego pliku."""
    content = b"verified checkpoint"
    output = configure_cli(tmp_path, monkeypatch, content)
    output.parent.mkdir(parents=True)
    output.write_bytes(b"old checkpoint")

    def fail_download(url: str, destination: Path) -> None:
        destination.write_bytes(b"partial")
        raise OSError("symulowana awaria")

    monkeypatch.setattr(download_checkpoint, "download_file", fail_download)

    assert download_checkpoint.main() == 2
    assert output.read_bytes() == b"old checkpoint"
    assert list(output.parent.iterdir()) == [output]


def test_checksum_error_preserves_previous_checkpoint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Nie publikuj pobranego pliku, gdy SHA-256 nie odpowiada manifestowi."""
    output = configure_cli(tmp_path, monkeypatch, b"expected checkpoint")
    output.parent.mkdir(parents=True)
    output.write_bytes(b"old checkpoint")
    monkeypatch.setattr(
        download_checkpoint,
        "download_file",
        lambda url, destination: destination.write_bytes(b"incorrect"),
    )

    assert download_checkpoint.main() == 1
    assert output.read_bytes() == b"old checkpoint"
    assert list(output.parent.iterdir()) == [output]
