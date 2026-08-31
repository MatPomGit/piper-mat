#!/usr/bin/env python3
"""Generuj raport Markdown i wykresy SVG z logów TensorBoard po sesji treningowej."""

from __future__ import annotations

import argparse
import html
import json
import math
import re
from pathlib import Path

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


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_") or "metric"


def find_event_dirs(root: Path) -> list[Path]:
    return sorted({path.parent for path in root.rglob("events.out.tfevents.*")})


def load_scalars(root: Path) -> dict[str, list[tuple[int, float]]]:
    merged: dict[str, list[tuple[int, float]]] = {}
    for event_dir in find_event_dirs(root):
        accumulator = EventAccumulator(str(event_dir), size_guidance={"scalars": 0})
        accumulator.Reload()
        for tag in accumulator.Tags().get("scalars", []):
            points = merged.setdefault(tag, [])
            points.extend((int(item.step), float(item.value)) for item in accumulator.Scalars(tag))
    for tag, points in merged.items():
        merged[tag] = sorted(dict(points).items())
    return merged


def select_metrics(scalars: dict[str, list[tuple[int, float]]], limit: int = 12) -> list[str]:
    ranked = []
    for tag, points in scalars.items():
        if len(points) < 2:
            continue
        lower = tag.lower()
        score = sum(1 for token in PREFERRED_METRICS if token in lower)
        ranked.append((-score, tag))
    return [tag for _, tag in sorted(ranked)[:limit]]


def render_svg(tag: str, points: list[tuple[int, float]], output: Path) -> None:
    width, height = 900, 360
    left, right, top, bottom = 70, 25, 30, 55
    xs = [p[0] for p in points]
    ys = [p[1] for p in points if math.isfinite(p[1])]
    if not ys:
        return
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    if x_min == x_max:
        x_max += 1
    if y_min == y_max:
        pad = abs(y_min) * 0.05 or 1.0
        y_min -= pad
        y_max += pad

    def sx(x: float) -> float:
        return left + (x - x_min) / (x_max - x_min) * (width - left - right)

    def sy(y: float) -> float:
        return top + (y_max - y) / (y_max - y_min) * (height - top - bottom)

    poly = " ".join(f"{sx(x):.2f},{sy(y):.2f}" for x, y in points if math.isfinite(y))
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
<polyline points="{poly}" fill="none" stroke="black" stroke-width="2"/>
</svg>\n''',
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Wygeneruj raport po sesji treningowej")
    parser.add_argument("--session-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, help="Opcjonalny JSON z metadanymi sesji")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    scalars = load_scalars(args.session_dir)
    selected = select_metrics(scalars)
    charts_dir = args.output_dir / "charts"

    lines = ["# Raport z sesji treningowej", "", f"Katalog sesji: `{args.session_dir}`", ""]
    if args.metadata and args.metadata.is_file():
        metadata = json.loads(args.metadata.read_text(encoding="utf-8"))
        lines.extend(["## Parametry sesji", "", "```json", json.dumps(metadata, ensure_ascii=False, indent=2), "```", ""])

    lines.extend(["## Metryki", ""])
    if not selected:
        lines.append("Nie znaleziono co najmniej dwupunktowych metryk skalarnych TensorBoard. Sprawdź, czy logger zapisał pliki `events.out.tfevents.*`.")
    else:
        for tag in selected:
            points = scalars[tag]
            values = [value for _, value in points if math.isfinite(value)]
            if not values:
                continue
            chart = charts_dir / f"{safe_name(tag)}.svg"
            render_svg(tag, points, chart)
            rel = chart.relative_to(args.output_dir)
            lines.extend([
                f"### `{tag}`",
                "",
                f"- pierwszy krok: {points[0][0]}",
                f"- ostatni krok: {points[-1][0]}",
                f"- wartość początkowa: {points[0][1]:.6g}",
                f"- wartość końcowa: {points[-1][1]:.6g}",
                f"- minimum: {min(values):.6g}",
                f"- maksimum: {max(values):.6g}",
                "",
                f"![{tag}]({rel.as_posix()})",
                "",
            ])

    summary = {
        "schema_version": 1,
        "session_dir": str(args.session_dir),
        "scalar_tags": sorted(scalars),
        "reported_tags": selected,
    }
    (args.output_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.output_dir / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Raport: {args.output_dir / 'REPORT.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
