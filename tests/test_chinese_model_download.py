"""Tests for secure downloading of the Chinese phonemization model."""

import hashlib
import io
import json
import sys
import tarfile
import types
from pathlib import Path

import pytest

unicode_rbnf = types.ModuleType("unicode_rbnf")
unicode_rbnf.RbnfEngine = object
sys.modules.setdefault("unicode_rbnf", unicode_rbnf)

from piper import phonemize_chinese


@pytest.fixture(autouse=True)
def mock_onnx_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Treat the small test fixture named ``valid-onnx`` as a valid model."""

    def validate(model_path: Path) -> None:
        if model_path.read_bytes() != b"valid-onnx":
            raise ValueError("invalid ONNX model")

    monkeypatch.setattr(phonemize_chinese, "_validate_onnx_model", validate)


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
        [
            _file(name, b"valid-onnx" if name == "g2pw.onnx" else name.encode())
            for name in phonemize_chinese.G2PW_REQUIRED_FILES
        ]
    )
    model_dir = tmp_path / "model"

    _download(monkeypatch, model_dir, data)

    assert {path.name for path in model_dir.iterdir()} == set(
        phonemize_chinese.G2PW_REQUIRED_FILES
    )
    assert {path.name for path in tmp_path.iterdir()} == {"model"}


def _complete_members() -> list[tuple[tarfile.TarInfo, bytes]]:
    """Build the complete minimal model used by validation tests."""
    return [
        _file(name, b"valid-onnx" if name == "g2pw.onnx" else name.encode())
        for name in phonemize_chinese.G2PW_REQUIRED_FILES
    ]


@pytest.mark.parametrize("missing_name", phonemize_chinese.G2PW_REQUIRED_FILES[1:])
def test_download_replaces_directory_missing_each_helper_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, missing_name: str
) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    for member, contents in _complete_members():
        if member.name != missing_name:
            (model_dir / member.name).write_bytes(contents)

    _download(monkeypatch, model_dir, _archive(_complete_members()))

    assert {path.name for path in model_dir.iterdir()} == set(
        phonemize_chinese.G2PW_REQUIRED_FILES
    )


@pytest.mark.parametrize("model_contents", [b"", b"broken-onnx"])
def test_download_replaces_empty_or_corrupt_onnx_model(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, model_contents: bytes
) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    for member, contents in _complete_members():
        (model_dir / member.name).write_bytes(
            model_contents if member.name == "g2pw.onnx" else contents
        )

    _download(monkeypatch, model_dir, _archive(_complete_members()))

    assert (model_dir / "g2pw.onnx").read_bytes() == b"valid-onnx"


def test_complete_directory_skips_download(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    for member, contents in _complete_members():
        (model_dir / member.name).write_bytes(contents)

    def unexpected_download(_url: str) -> io.BytesIO:
        raise AssertionError("complete model must not be downloaded again")

    monkeypatch.setattr(phonemize_chinese, "urlopen", unexpected_download)

    phonemize_chinese.download_model(model_dir)


def test_manifest_checksum_mismatch_triggers_replacement(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    checksums = {}
    for member, contents in _complete_members():
        (model_dir / member.name).write_bytes(contents)
        checksums[member.name] = {"sha256": hashlib.sha256(contents).hexdigest()}
    (model_dir / "config.py").write_bytes(b"tampered")
    (model_dir / phonemize_chinese.G2PW_MANIFEST_FILE).write_text(
        json.dumps({"files": checksums}), encoding="utf-8"
    )

    _download(monkeypatch, model_dir, _archive(_complete_members()))

    assert (model_dir / "config.py").read_bytes() == b"config.py"
    assert not (model_dir / phonemize_chinese.G2PW_MANIFEST_FILE).exists()
