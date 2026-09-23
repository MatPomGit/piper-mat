#!/usr/bin/env python3
"""Build a deterministic release directory and SHA-256 manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

VOICE_NAME = "pl_PL-mateusz-medium"
DEFAULT_MODEL_CARD = Path("models/pl_PL-mateusz-medium/MODEL_CARD.md")
DEFAULT_SAMPLES = Path("samples/pl_PL-mateusz-medium")
DEFAULT_OUTPUT = Path("dist/pl_PL-mateusz-medium")
MANIFEST_NAME = "release-manifest.json"
CHECKSUMS_NAME = "checksums.txt"
CHUNK_SIZE = 1024 * 1024


def sha256_file(path: Path) -> str:
    """Return the SHA-256 checksum of a file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Przygotuj deterministyczny katalog wydania modelu głosu."
    )
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument(
        "--model-card",
        type=Path,
        default=DEFAULT_MODEL_CARD,
    )
    parser.add_argument("--samples", type=Path, default=DEFAULT_SAMPLES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Zastąp istniejący katalog wyjściowy gotową paczką.",
    )
    return parser.parse_args()


def validate_inputs(args: argparse.Namespace) -> list[Path] | None:
    """Validate required release inputs and return them in copy order."""
    required = [args.model, args.config, args.model_card]
    missing = [path for path in required if not path.is_file()]
    if missing:
        for path in missing:
            print(
                f"BŁĄD: brak wymaganego pliku wydania: {path}",
                file=sys.stderr,
            )
        return None
    return required


def validate_output(output: Path, overwrite: bool) -> bool:
    """Check whether the release can be published at the output path."""
    if output.exists():
        if not overwrite:
            print(
                f"BŁĄD: katalog wyjściowy już istnieje: {output}. "
                "Usuń go albo użyj --overwrite.",
                file=sys.stderr,
            )
            return False
        if not output.is_dir():
            print(
                f"BŁĄD: ścieżka wyjściowa nie jest katalogiem: {output}",
                file=sys.stderr,
            )
            return False

    return True


def create_working_directory(output: Path) -> Path:
    """Create a temporary working directory next to the output directory."""
    output.parent.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix=f".{output.name}.working-", dir=output.parent))


def copy_release_files(
    required: list[Path],
    samples_dir: Path,
    output: Path,
) -> list[Path]:
    """Copy release inputs into a clean output directory."""
    copied: list[Path] = []

    for source in required:
        target = output / source.name
        shutil.copy2(source, target)
        copied.append(target)

    if samples_dir.is_dir():
        target_samples = output / "samples"
        target_samples.mkdir()
        for source in sorted(samples_dir.glob("*.wav")):
            target = target_samples / source.name
            shutil.copy2(source, target)
            copied.append(target)

    return copied


def build_records(files: list[Path], output: Path) -> list[dict[str, object]]:
    """Build deterministic manifest records for copied release files."""
    records: list[dict[str, object]] = []
    for path in sorted(files, key=lambda item: item.relative_to(output).as_posix()):
        records.append(
            {
                "file": path.relative_to(output).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return records


def write_metadata(output: Path, records: list[dict[str, object]]) -> None:
    """Write the release manifest and checksum list."""
    manifest = {
        "schema_version": 1,
        "voice": VOICE_NAME,
        "files": records,
    }
    (output / MANIFEST_NAME).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output / CHECKSUMS_NAME).write_text(
        "".join(f"{record['sha256']}  {record['file']}\n" for record in records),
        encoding="utf-8",
    )


def verify_release(output: Path, records: list[dict[str, object]]) -> None:
    """Verify that the working directory contains a complete release."""
    expected = {
        *(str(record["file"]) for record in records),
        MANIFEST_NAME,
        CHECKSUMS_NAME,
    }
    actual = {
        path.relative_to(output).as_posix()
        for path in output.rglob("*")
        if path.is_file()
    }
    if actual != expected:
        raise OSError("katalog roboczy nie zawiera kompletnego wydania")

    for record in records:
        path = output / str(record["file"])
        if path.stat().st_size != record["size_bytes"]:
            raise OSError(f"niezgodny rozmiar pliku: {path}")
        if sha256_file(path) != record["sha256"]:
            raise OSError(f"niezgodna suma SHA-256 pliku: {path}")


def publish_release(working: Path, output: Path, overwrite: bool) -> None:
    """Publish a complete release and restore the previous one on failure."""
    backup: Path | None = None
    if output.exists():
        if not overwrite:
            raise OSError(f"katalog wyjściowy już istnieje: {output}")
        backup = Path(
            tempfile.mkdtemp(prefix=f".{output.name}.backup-", dir=output.parent)
        )
        backup.rmdir()
        output.rename(backup)

    try:
        working.rename(output)
    except OSError:
        if backup is not None:
            backup.rename(output)
        raise

    if backup is not None:
        shutil.rmtree(backup)


def main() -> int:
    """Build a clean release directory and its integrity metadata."""
    args = parse_args()
    required = validate_inputs(args)
    if required is None:
        return 2

    if not validate_output(args.output, args.overwrite):
        return 2

    working: Path | None = None
    try:
        working = create_working_directory(args.output)
        copied = copy_release_files(required, args.samples, working)
        records = build_records(copied, working)
        write_metadata(working, records)
        verify_release(working, records)
        publish_release(working, args.output, args.overwrite)
        working = None
    except OSError as exc:
        print(f"BŁĄD: nie udało się przygotować wydania: {exc}", file=sys.stderr)
        return 1
    finally:
        if working is not None:
            shutil.rmtree(working, ignore_errors=True)

    print(f"release_dir: {args.output}")
    print(f"files: {len(records)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
