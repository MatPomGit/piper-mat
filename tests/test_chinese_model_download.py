"""Tests for secure downloading of the Chinese phonemization model."""

import hashlib
import io
import sys
import tarfile
import types
from pathlib import Path

import pytest

unicode_rbnf = types.ModuleType("unicode_rbnf")
unicode_rbnf.RbnfEngine = object
sys.modules.setdefault("unicode_rbnf", unicode_rbnf)

from piper import phonemize_chinese


def _archive(members: list[tuple[tarfile.TarInfo, bytes]]) -> bytes:
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w:gz") as archive:
        for member, contents in members:
            if member.isfile():
                member.size = len(contents)
                archive.addfile(member, io.BytesIO(contents))
            else:
                archive.addfile(member)
    return stream.getvalue()


def _file(name: str, contents: bytes = b"model") -> tuple[tarfile.TarInfo, bytes]:
    return tarfile.TarInfo(name), contents


def _download(monkeypatch: pytest.MonkeyPatch, model_dir: Path, data: bytes) -> None:
    monkeypatch.setattr(
        phonemize_chinese, "G2PW_SHA256", hashlib.sha256(data).hexdigest()
    )
    monkeypatch.setattr(phonemize_chinese, "urlopen", lambda _url: io.BytesIO(data))
    phonemize_chinese.download_model(model_dir)


def test_download_rejects_invalid_checksum(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    data = _archive([_file("g2pw.onnx")])
    monkeypatch.setattr(phonemize_chinese, "G2PW_SHA256", "0" * 64)
    monkeypatch.setattr(phonemize_chinese, "urlopen", lambda _url: io.BytesIO(data))

    with pytest.raises(ValueError, match="SHA-256"):
        phonemize_chinese.download_model(tmp_path / "model")

    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("name", ["../outside", "/absolute"])
def test_download_rejects_unsafe_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, name: str
) -> None:
    data = _archive([_file(name)])

    with pytest.raises(ValueError, match="Unsafe path"):
        _download(monkeypatch, tmp_path / "model", data)

    assert not (tmp_path / "model").exists()
    assert {path.name for path in tmp_path.iterdir()} == set()


@pytest.mark.parametrize("link_type", [tarfile.SYMTYPE, tarfile.LNKTYPE])
def test_download_rejects_link_outside(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, link_type: bytes
) -> None:
    link = tarfile.TarInfo("link")
    link.type = link_type
    link.linkname = "../outside"
    data = _archive([(link, b"")])

    with pytest.raises(ValueError, match="Unsafe link"):
        _download(monkeypatch, tmp_path / "model", data)

    assert not (tmp_path / "model").exists()
    assert {path.name for path in tmp_path.iterdir()} == set()


def test_download_publishes_complete_archive(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    data = _archive(
        [_file(name, name.encode()) for name in phonemize_chinese.G2PW_REQUIRED_FILES]
    )
    model_dir = tmp_path / "model"

    _download(monkeypatch, model_dir, data)

    assert {path.name for path in model_dir.iterdir()} == set(
        phonemize_chinese.G2PW_REQUIRED_FILES
    )
    assert {path.name for path in tmp_path.iterdir()} == {"model"}
