#!/usr/bin/env python3
"""Build a deterministic release directory and SHA-256 manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
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
        help="Usuń istniejący katalog wyjściowy przed utworzeniem paczki.",
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


def prepare_output(output: Path, overwrite: bool) -> bool:
    """Create an empty output directory without leaving stale artifacts."""
    if output.exists():
        if not overwrite:
            print(
                f"BŁĄD: katalog wyjściowy już istnieje: {output}. "
                "Usuń go albo użyj --overwrite.",
                file=sys.stderr,
            )
            return False
        if output.is_dir():
            shutil.rmtree(output)
        else:
            print(
                f"BŁĄD: ścieżka wyjściowa nie jest katalogiem: {output}",
                file=sys.stderr,
            )
            return False

    output.mkdir(parents=True)
    return True


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
        "".join(
            f"{record['sha256']}  {record['file']}\n"
            for record in records
        ),
        encoding="utf-8",
    )


def main() -> int:
    """Build a clean release directory and its integrity metadata."""
    args = parse_args()
    required = validate_inputs(args)
    if required is None:
        return 2

    if not prepare_output(args.output, args.overwrite):
        return 2

    try:
        copied = copy_release_files(required, args.samples, args.output)
        records = build_records(copied, args.output)
        write_metadata(args.output, records)
    except OSError as exc:
        print(f"BŁĄD: nie udało się przygotować wydania: {exc}", file=sys.stderr)
        return 1

    print(f"release_dir: {args.output}")
    print(f"files: {len(records)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
