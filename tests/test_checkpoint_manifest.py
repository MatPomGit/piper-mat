"""Testy walidacji manifestu punktów kontrolnych."""

import json
from pathlib import Path

import pytest

from scripts.checkpoint_manifest import load_entry

VALID_HASH = "A1" * 32
VALID_URL = "https://example.com/checkpoint.ckpt"


def write_manifest(tmp_path: Path, entry: dict[str, object]) -> Path:
    """Zapisz manifest zawierający podany wpis testowy."""
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps({"checkpoints": {"model.ckpt": entry}}),
        encoding="utf-8",
    )
    return manifest_path


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("sha256", ""),
        ("sha256", "a" * 63),
        ("sha256", "g" + "a" * 63),
        ("size_bytes", -1),
        ("size_bytes", True),
        ("url", ""),
        ("url", "http://example.com/checkpoint.ckpt"),
    ],
    ids=[
        "pusty-skrot",
        "bledna-dlugosc",
        "znak-spoza-systemu-szesnastkowego",
        "ujemny-rozmiar",
        "wartosc-logiczna",
        "pusty-url",
        "url-bez-https",
    ],
)
def test_load_entry_rejects_invalid_values(
    tmp_path: Path,
    field: str,
    value: object,
) -> None:
    """Niepoprawne pola wpisu powodują błąd walidacji."""
    entry: dict[str, object] = {
        "sha256": VALID_HASH,
        "size_bytes": 1,
        "source": {"url": VALID_URL},
    }
    if field == "url":
        entry["source"] = {"url": value}
    else:
        entry[field] = value

    with pytest.raises(ValueError):
        load_entry(write_manifest(tmp_path, entry), "model.ckpt")


@pytest.mark.parametrize("sha256", [VALID_HASH, VALID_HASH.lower()])
def test_load_entry_accepts_valid_entry_and_normalizes_hash(
    tmp_path: Path,
    sha256: str,
) -> None:
    """Poprawny wpis jest zwracany ze skrótem zapisanym małymi literami."""
    entry: dict[str, object] = {
        "sha256": sha256,
        "size_bytes": 1,
        "source": {"url": VALID_URL},
    }

    loaded_entry = load_entry(write_manifest(tmp_path, entry), "model.ckpt")

    assert loaded_entry["sha256"] == VALID_HASH.lower()
    assert loaded_entry["size_bytes"] == 1
    assert loaded_entry["source"] == {"url": VALID_URL}
