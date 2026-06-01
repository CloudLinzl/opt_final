#!/usr/bin/env python3
"""
Convert Micromouse ASCII maze files into the project's JSON map interface.

Input:
  - Micromouse text mazes such as the files in ../maps/*.txt

Output:
  - One JSON file per maze in ../maps/json/
  - A manifest file listing all converted mazes
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable


def read_ascii_maze(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        raise ValueError(f"{path.name}: empty maze file")

    width = max(len(line) for line in lines)
    normalized = [line.ljust(width) for line in lines]

    if len(normalized) % 2 == 0:
        raise ValueError(f"{path.name}: invalid row count {len(normalized)}")

    return normalized


def infer_dimensions(lines: list[str]) -> tuple[int, int]:
    height = (len(lines) - 1) // 2
    width = (len(lines[0]) - 1) // 4

    if 2 * height + 1 != len(lines):
        raise ValueError("maze height does not match ascii structure")
    if 4 * width + 1 != len(lines[0]):
        raise ValueError("maze width does not match ascii structure")

    return width, height


def parse_cell_walls(lines: list[str], width: int, height: int) -> list[list[list[int]]]:
    wall_matrix: list[list[list[int]]] = []
    for y in range(height):
        row: list[list[int]] = []
        top_line = lines[2 * y]
        mid_line = lines[2 * y + 1]
        bottom_line = lines[2 * y + 2]

        for x in range(width):
            north = 1 if "-" in top_line[4 * x + 1 : 4 * x + 4] else 0
            south = 1 if "-" in bottom_line[4 * x + 1 : 4 * x + 4] else 0
            west = 1 if mid_line[4 * x] == "|" else 0
            east = 1 if mid_line[4 * (x + 1)] == "|" else 0
            row.append([north, east, south, west])

        wall_matrix.append(row)

    return wall_matrix


def parse_markers(lines: list[str], width: int, height: int) -> tuple[list[int], list[list[int]]]:
    start: list[int] | None = None
    goals: list[list[int]] = []

    for y in range(height):
        mid_line = lines[2 * y + 1]
        for x in range(width):
            marker = mid_line[4 * x + 2]
            if marker == "S":
                start = [x, y]
            elif marker == "G":
                goals.append([x, y])

    if start is None:
        raise ValueError("maze start cell 'S' not found")
    if not goals:
        raise ValueError("maze goal cell 'G' not found")

    goals.sort(key=lambda p: (p[1], p[0]))
    return start, goals


def convert_maze(path: Path) -> dict:
    lines = read_ascii_maze(path)
    width, height = infer_dimensions(lines)
    wall_matrix = parse_cell_walls(lines, width, height)
    start, goal_cells = parse_markers(lines, width, height)

    return {
        "maze_id": path.stem,
        "source_file": path.name,
        "source_format": "micromouse_ascii",
        "width": width,
        "height": height,
        "coordinate_origin": "top_left",
        "coordinate_axes": {"x": "column", "y": "row"},
        "wall_encoding": ["N", "E", "S", "W"],
        "wall_matrix": wall_matrix,
        "start": start,
        # Keep a single goal field for interface compatibility,
        # and retain all actual goal cells for algorithms that support multi-goal targets.
        "goal": goal_cells[0],
        "goal_cells": goal_cells,
        "risk_cells": [],
        "narrow_cells": [],
        "dynamic_updates": [],
    }


def convert_all(paths: Iterable[Path], output_dir: Path) -> list[dict]:
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest: list[dict] = []
    for path in sorted(paths):
        converted = convert_maze(path)
        out_path = output_dir / f"{path.stem}.json"
        out_path.write_text(
            json.dumps(converted, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        manifest.append(
            {
                "maze_id": converted["maze_id"],
                "input_file": str(path.name),
                "output_file": out_path.name,
                "width": converted["width"],
                "height": converted["height"],
                "start": converted["start"],
                "goal": converted["goal"],
                "goal_cells": converted["goal_cells"],
            }
        )

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert Micromouse ASCII maps to project JSON interface format."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "maps",
        help="Directory containing .txt maze files",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "maps" / "json",
        help="Directory where converted JSON files will be written",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    txt_files = sorted(args.input_dir.glob("*.txt"))
    if not txt_files:
        parser.error(f"no .txt files found in {args.input_dir}")

    manifest = convert_all(txt_files, args.output_dir)
    print(f"Converted {len(manifest)} mazes to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
