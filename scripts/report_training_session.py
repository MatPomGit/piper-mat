#!/usr/bin/env python3
"""Generuj raport Markdown i wykresy SVG z logów TensorBoard."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

from tensorboard.backend.event_processing.event_accumulator import EventAccumulator

PREFERRED_METRICS = (
    "loss",
    "mel",
    "mos",
    "disc",
    "gen",
    "kl",
    "duration",
    "learning_rate",
    "lr",
)
REPORT_SCHEMA_VERSION = 1


def safe_name(value: str) -> str:
    """Zamień nazwę metryki na bezpieczną i stabilną nazwę pliku."""
    prefix = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_") or "metric"
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:10]
    return f"{prefix}-{digest}"


def find_event_dirs(root: Path) -> list[Path]:
    """Znajdź katalogi zawierające pliki zdarzeń TensorBoard."""
    return sorted({path.parent for path in root.rglob("events.out.tfevents.*")})


def load_scalars(root: Path) -> dict[str, list[tuple[int, float]]]:
    """Wczytaj i scal metryki skalarne ze wszystkich logów TensorBoard.

    Dla duplikatów wygrywa największy ``wall_time``. Remisy rozstrzyga
    leksykograficznie pełna ścieżka pliku, a potem pozycja zdarzenia w pliku.
    Wynik nie zawiera tych danych pomocniczych, aby zachować publiczny format.
    """
    merged: dict[str, dict[int, tuple[float, str, int, float]]] = {}
    event_files = sorted(root.rglob("events.out.tfevents.*"))
    for event_file in event_files:
        try:
            accumulator = EventAccumulator(
                str(event_file),
                size_guidance={"scalars": 0},
            )
            accumulator.Reload()
        except (OSError, ValueError, RuntimeError) as exc:
            print(
                f"OSTRZEŻENIE: nie można odczytać logu TensorBoard "
                f"{event_file}: {exc}",
                file=sys.stderr,
            )
            continue

        for tag in accumulator.Tags().get("scalars", []):
            points = merged.setdefault(tag, {})
            for position, item in enumerate(accumulator.Scalars(tag)):
                step = int(item.step)
                candidate = (
                    float(item.wall_time),
                    str(event_file.resolve()),
                    position,
                    float(item.value),
                )
                current = points.get(step)
                # Przy równym wall_time wygrywa pełna ścieżka, a następnie
                # późniejsza pozycja zdarzenia w pliku.
                if current is None or candidate[:3] > current[:3]:
                    points[step] = candidate

    return {
        tag: [(step, point[3]) for step, point in sorted(points.items())]
        for tag, points in merged.items()
    }


def select_metrics(
    scalars: dict[str, list[tuple[int, float]]],
    limit: int = 12,
) -> list[str]:
    """Wybierz najbardziej przydatne metryki do raportu."""
    ranked: list[tuple[int, str]] = []
    for tag, points in scalars.items():
        if len(points) < 2:
            continue
        lower = tag.lower()
        score = sum(token in lower for token in PREFERRED_METRICS)
        ranked.append((-score, tag))
    return [tag for _, tag in sorted(ranked)[:limit]]


def render_svg(tag: str, points: list[tuple[int, float]], output: Path) -> bool:
    """Wyrenderuj prosty wykres SVG i zwróć informację o utworzeniu pliku."""
    width = 900
    height = 360
    left = 70
    right = 25
    top = 30
    bottom = 55

    finite_points = [(x, y) for x, y in points if math.isfinite(y)]
    if not finite_points:
        return False

    x_values = [point[0] for point in finite_points]
    y_values = [point[1] for point in finite_points]
    x_min, x_max = min(x_values), max(x_values)
    y_min, y_max = min(y_values), max(y_values)

    if x_min == x_max:
        x_max += 1
    if y_min == y_max:
        padding = abs(y_min) * 0.05 or 1.0
        y_min -= padding
        y_max += padding

    def scale_x(value: float) -> float:
        return left + (value - x_min) / (x_max - x_min) * (width - left - right)

    def scale_y(value: float) -> float:
        return top + (y_max - value) / (y_max - y_min) * (height - top - bottom)

    polyline = " ".join(
        f"{scale_x(x):.2f},{scale_y(y):.2f}"
        for x, y in finite_points
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="100%" height="100%" fill="white"/>
<text x="{left}" y="20" font-family="sans-serif" font-size="16">{html.escape(tag)}</text>
<line x1="{left}" y1="{height-bottom}" x2="{width-right}" y2="{height-bottom}" stroke="black"/>
<line x1="{left}" y1="{top}" x2="{left}" y2="{height-bottom}" stroke="black"/>
<text x="{left}" y="{height-15}" font-family="sans-serif" font-size="12">krok {x_min}</text>
<text x="{width-right-90}" y="{height-15}" font-family="sans-serif" font-size="12">krok {x_max}</text>
<text x="5" y="{top+10}" font-family="sans-serif" font-size="12">{y_max:.5g}</text>
<text x="5" y="{height-bottom}" font-family="sans-serif" font-size="12">{y_min:.5g}</text>
<polyline points="{polyline}" fill="none" stroke="black" stroke-width="2"/>
</svg>\n''',
        encoding="utf-8",
    )
    return True


def load_metadata(path: Path | None) -> dict[str, Any] | None:
    """Wczytaj opcjonalne metadane sesji."""
    if path is None or not path.is_file():
        return None

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise RuntimeError(f"nie można odczytać metadanych {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"niepoprawny JSON w metadanych {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise RuntimeError("metadane sesji muszą zawierać obiekt JSON")
    return data


def metric_lines(
    tag: str,
    points: list[tuple[int, float]],
    chart_path: Path,
) -> list[str]:
    """Zbuduj fragment Markdown opisujący jedną metrykę."""
    finite_values = [value for _, value in points if math.isfinite(value)]
    if not finite_values:
        return []

    return [
        f"### `{tag}`",
        "",
        f"- pierwszy krok: {points[0][0]}",
        f"- ostatni krok: {points[-1][0]}",
        f"- wartość początkowa: {points[0][1]:.6g}",
        f"- wartość końcowa: {points[-1][1]:.6g}",
        f"- minimum: {min(finite_values):.6g}",
        f"- maksimum: {max(finite_values):.6g}",
        "",
        f"![{tag}]({chart_path.as_posix()})",
        "",
    ]


def build_report_lines(
    session_dir: Path,
    output_dir: Path,
    metadata: dict[str, Any] | None,
    scalars: dict[str, list[tuple[int, float]]],
    selected: list[str],
) -> list[str]:
    """Zbuduj kompletną treść raportu Markdown."""
    lines = [
        "# Raport z sesji treningowej",
        "",
        f"Katalog sesji: `{session_dir}`",
        "",
    ]

    if metadata is not None:
        lines.extend(
            [
                "## Parametry sesji",
                "",
                "```json",
                json.dumps(metadata, ensure_ascii=False, indent=2),
                "```",
                "",
            ]
        )

    lines.extend(["## Metryki", ""])
    if not selected:
        lines.append(
            "Nie znaleziono co najmniej dwupunktowych metryk skalarnych TensorBoard. "
            "Sprawdź, czy logger zapisał pliki `events.out.tfevents.*`."
        )
        return lines

    charts_dir = output_dir / "charts"
    planned_charts = [(tag, charts_dir / f"{safe_name(tag)}.svg") for tag in selected]
    chart_paths = [chart for _, chart in planned_charts]
    if len(chart_paths) != len(set(chart_paths)):
        raise RuntimeError("planowane ścieżki wykresów nie są unikalne")

    for tag, chart in planned_charts:
        points = scalars[tag]
        if not render_svg(tag, points, chart):
            continue
        relative_chart = chart.relative_to(output_dir)
        lines.extend(metric_lines(tag, points, relative_chart))

    return lines


def write_outputs(
    session_dir: Path,
    output_dir: Path,
    scalars: dict[str, list[tuple[int, float]]],
    selected: list[str],
    report_lines: list[str],
) -> None:
    """Zapisz raport Markdown i maszynowe podsumowanie JSON."""
    summary = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "session_dir": str(session_dir),
        "scalar_tags": sorted(scalars),
        "reported_tags": selected,
    }
    write_text_atomically(
        output_dir / "summary.json",
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
    )
    write_text_atomically(
        output_dir / "REPORT.md",
        "\n".join(report_lines) + "\n",
    )


def write_text_atomically(path: Path, content: str) -> None:
    """Zapisz tekst do pliku tymczasowego, a następnie opublikuj go atomowo."""
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        text=True,
    )
    temporary_path = Path(temporary_name)
    try:
        with open(descriptor, "w", encoding="utf-8") as temporary_file:
            temporary_file.write(content)
        temporary_path.replace(path)
    finally:
        temporary_path.unlink(missing_ok=True)


def publish_outputs(staging_dir: Path, output_dir: Path) -> None:
    """Opublikuj kompletny zestaw plików przygotowany w katalogu roboczym."""
    charts = staging_dir / "charts"
    if charts.is_dir():
        target_charts = output_dir / "charts"
        shutil.rmtree(target_charts, ignore_errors=True)
        charts.replace(target_charts)

    for name in ("summary.json", "REPORT.md"):
        (staging_dir / name).replace(output_dir / name)


def parse_args() -> argparse.Namespace:
    """Wczytaj argumenty interfejsu wiersza poleceń."""
    parser = argparse.ArgumentParser(
        description="Wygeneruj raport po sesji treningowej"
    )
    parser.add_argument("--session-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--metadata",
        type=Path,
        help="Opcjonalny JSON z metadanymi sesji",
    )
    return parser.parse_args()


def main() -> int:
    """Wygeneruj raport dla wskazanego katalogu sesji."""
    args = parse_args()
    if not args.session_dir.is_dir():
        print(
            f"BŁĄD: nie znaleziono katalogu sesji: {args.session_dir}",
            file=sys.stderr,
        )
        return 2

    try:
        metadata = load_metadata(args.metadata)
    except RuntimeError as exc:
        print(f"BŁĄD: {exc}", file=sys.stderr)
        return 2

    scalars = load_scalars(args.session_dir)
    selected = select_metrics(scalars)
    try:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(
            dir=args.output_dir,
            prefix=".report-",
        ) as staging_name:
            staging_dir = Path(staging_name)
            lines = build_report_lines(
                args.session_dir,
                staging_dir,
                metadata,
                scalars,
                selected,
            )
            write_outputs(
                args.session_dir,
                staging_dir,
                scalars,
                selected,
                lines,
            )
            publish_outputs(staging_dir, args.output_dir)
    except OSError as exc:
        print(
            f"BŁĄD: nie można zapisać raportu w {args.output_dir}: {exc}",
            file=sys.stderr,
        )
        return 2
    print(f"Raport: {args.output_dir / 'REPORT.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
