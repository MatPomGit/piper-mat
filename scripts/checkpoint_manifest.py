"""Wczytywanie i walidacja wpisów manifestu punktów kontrolnych."""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlsplit

SHA256_RE = re.compile(r"[0-9a-fA-F]{64}")


def load_entry(manifest_path: Path, checkpoint_name: str) -> dict[str, object]:
    """Wczytaj i zwaliduj wpis punktu kontrolnego z manifestu."""
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"nie można odczytać manifestu: {exc}") from exc

    checkpoints = manifest.get("checkpoints")
    if not isinstance(checkpoints, dict):
        raise ValueError("manifest nie zawiera obiektu checkpoints")

    entry = checkpoints.get(checkpoint_name)
    if not isinstance(entry, dict):
        raise ValueError(f"nieznany punkt kontrolny: {checkpoint_name}")

    expected_hash = entry.get("sha256")
    if not isinstance(expected_hash, str) or SHA256_RE.fullmatch(expected_hash) is None:
        raise ValueError(f"niepoprawne sha256 dla: {checkpoint_name}")

    expected_size = entry.get("size_bytes")
    if (
        not isinstance(expected_size, int)
        or isinstance(expected_size, bool)
        or expected_size <= 0
    ):
        raise ValueError(f"niepoprawne size_bytes dla: {checkpoint_name}")

    source = entry.get("source")
    url = source.get("url") if isinstance(source, dict) else None
    if not isinstance(url, str) or not _is_https_url(url):
        raise ValueError(f"brak poprawnego źródła HTTPS dla: {checkpoint_name}")

    entry["sha256"] = expected_hash.lower()
    return entry


def _is_https_url(url: str) -> bool:
    """Sprawdź, czy wartość jest niepustym adresem HTTPS."""
    if not url or url != url.strip():
        return False

    try:
        parsed_url = urlsplit(url)
        return parsed_url.scheme == "https" and bool(parsed_url.hostname)
    except ValueError:
        return False
