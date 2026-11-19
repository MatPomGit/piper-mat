"""Walidacja punktów wznowienia i odzyskiwanie zakończonych sesji."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

if __package__:
    from .checkpoint_compat import torch_load_checkpoint
else:
    from checkpoint_compat import torch_load_checkpoint

HASH_CHUNK_SIZE = 1024 * 1024


def sha256_file(path: Path) -> str:
    """Oblicz SHA-256 pliku checkpointu bez wczytywania go w całości."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(HASH_CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_resume_checkpoint(path: Path, min_epoch: int) -> int:
    """Odczytaj checkpoint i zweryfikuj stan konieczny do wznowienia."""
    try:
        checkpoint = torch_load_checkpoint(
            path, map_location="cpu", weights_only=False
        )
    except (OSError, RuntimeError, ValueError, EOFError, KeyError) as exc:
        raise RuntimeError(
            f"Nie można odczytać checkpointu {path}: {exc}"
        ) from exc

    if not isinstance(checkpoint, dict):
        raise RuntimeError(f"Checkpoint musi zawierać słownik: {path}")

    epoch = checkpoint.get("epoch")
    step = checkpoint.get("global_step")
    if (
        type(epoch) is not int
        or epoch < min_epoch
        or type(step) is not int
        or step < 0
    ):
        raise RuntimeError(
            f"Checkpoint ma niepoprawną epokę lub krok: {path}"
        )

    if not isinstance(checkpoint.get("state_dict"), dict) or not checkpoint[
        "state_dict"
    ]:
        raise RuntimeError(
            f"Checkpoint nie zawiera parametrów modelu: {path}"
        )
    if not isinstance(checkpoint.get("optimizer_states"), list) or not checkpoint[
        "optimizer_states"
    ]:
        raise RuntimeError(
            f"Checkpoint nie zawiera stanu optymalizatora: {path}"
        )
    if not isinstance(checkpoint.get("loops"), dict):
        raise RuntimeError(
            f"Checkpoint nie zawiera stanu pętli Lightning: {path}"
        )
    return epoch


def recoverable_session_archive(
    metadata_path: Path,
    archived_last: Path,
    *,
    session: int,
    previous_checkpoint: Path,
    target_max_epochs: int,
) -> tuple[int, dict[str, Any]] | None:
    """Potwierdź kompletny archiwalny checkpoint przed odtworzeniem stanu."""
    if not metadata_path.is_file():
        return None
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"Nie można odczytać metadanych sesji: {exc}"
        ) from exc

    if not isinstance(metadata, dict):
        raise RuntimeError(
            f"Metadane sesji muszą być obiektem JSON: {metadata_path}"
        )
    if (
        metadata.get("session") != session
        or metadata.get("resume_checkpoint") != str(previous_checkpoint)
        or metadata.get("target_max_epochs") != target_max_epochs
        or metadata.get("return_code") != 0
    ):
        return None

    archives = metadata.get("archived_checkpoints")
    expected_hash = metadata.get("archive_last_sha256")
    if not isinstance(archives, dict) or not isinstance(expected_hash, str):
        return None
    if archives.get("last") != str(archived_last):
        raise RuntimeError(
            "Metadane wskazują inny ostatni checkpoint."
        )
    if not archived_last.is_file():
        raise RuntimeError(
            "Brak zarchiwizowanego punktu wznowienia."
        )

    actual_hash = sha256_file(archived_last)
    if actual_hash != expected_hash:
        raise RuntimeError(
            "Suma SHA-256 archiwalnego checkpointu nie jest zgodna."
        )
    epoch = validate_resume_checkpoint(
        archived_last, target_max_epochs - 1
    )
    if metadata.get("completed_epoch") != epoch:
        raise RuntimeError(
            "Metadane epoki nie odpowiadają checkpointowi."
        )
    if not isinstance(metadata.get("finished_at"), str) or not metadata[
        "finished_at"
    ]:
        raise RuntimeError(
            "Metadane nie zawierają czasu zakończenia sesji."
        )
    return epoch, metadata
