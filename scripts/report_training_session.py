#!/usr/bin/env python3
"""Generuj raport Markdown i wykresy SVG z logów TensorBoard."""

from __future__ import annotations

import argparse
import html
import json
import math
import re
import sys
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
    """Zamień nazwę metryki na bezpieczną nazwę pliku."""
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_") or "metric"


def find_event_dirs(root: Path) -> list[Path]:
    """Znajdź katalogi zawierające pliki zdarzeń TensorBoard."""
    return sorted({path.parent for path in root.rglob("events.out.tfevents.*")})


def load_scalars(root: Path) -> dict[str, list[tuple[int, float]]]:
    """Wczytaj i scal metryki skalarne ze wszystkich logów TensorBoard."""
    merged: dict[str, list[tuple[int, float]]] = {}
    for event_dir in find_event_dirs(root):
        try:
            accumulator = EventAccumulator(
                str(event_dir),
                size_guidance={"scalars": 0},
            )
            accumulator.Reload()
        except (OSError, ValueError, RuntimeError) as exc:
            print(
                f"OSTRZEŻENIE: nie można odczytać logu TensorBoard "
                f"{event_dir}: {exc}",
                file=sys.stderr,
            )
            continue

        for tag in accumulator.Tags().get("scalars", []):
            points = merged.setdefault(tag, [])
            points.extend(
                (int(item.step), float(item.value))
                for item in accumulator.Scalars(tag)
            )

    for tag, points in merged.items():
        merged[tag] = sorted(dict(points).items())
    return merged


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
    for tag in selected:
        points = scalars[tag]
        chart = charts_dir / f"{safe_name(tag)}.svg"
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
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "REPORT.md").write_text(
        "\n".join(report_lines) + "\n",
        encoding="utf-8",
    )


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

    args.output_dir.mkdir(parents=True, exist_ok=True)
    scalars = load_scalars(args.session_dir)
    selected = select_metrics(scalars)
    lines = build_report_lines(
        args.session_dir,
        args.output_dir,
        metadata,
        scalars,
        selected,
    )
    write_outputs(
        args.session_dir,
        args.output_dir,
        scalars,
        selected,
        lines,
    )
    print(f"Raport: {args.output_dir / 'REPORT.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
