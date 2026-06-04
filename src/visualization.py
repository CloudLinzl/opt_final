#!/usr/bin/env python3
"""
Unified visualization interface for text and PNG outputs.
"""

from __future__ import annotations

import json
import struct
import sys
import zlib
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.dlite import render_map_snapshot  # noqa: E402


WHITE = (255, 255, 255)
BLACK = (18, 18, 18)
WALL = (20, 20, 20)
PANEL_BORDER = (190, 190, 190)
PATH_BLUE = (37, 99, 235)
START_GREEN = (22, 163, 74)
GOAL_RED = (220, 38, 38)
EXPLORED_YELLOW = (250, 204, 21)
FRONTIER_ORANGE = (249, 115, 22)
CURRENT_ORANGE = (194, 65, 12)
BLOCKED_GRAY = (75, 85, 99)
GOAL_FILL = (254, 226, 226)
START_FILL = (220, 252, 231)
LEGEND_BORDER = (120, 120, 120)

IMAGE_DPI = 300
IMAGE_WIDTH = 1800
IMAGE_HEIGHT = 1800
SIDE_MARGIN = 100
TOP_MARGIN = 130
BOTTOM_MARGIN = 180
GRID_GAP_X = 36
GRID_GAP_Y = 44
PANEL_TITLE_HEIGHT = 42
PANEL_INSET = 14
TITLE_SCALE = 4
LABEL_SCALE = 2
SMALL_SCALE = 2
PANEL_COUNT = 6
PANEL_COLUMNS = 3
PANEL_ROWS = 2


FONT_5X7 = {
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
    "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    "_": ["00000", "00000", "00000", "00000", "00000", "00000", "11111"],
    "*": ["00000", "01010", "00100", "11111", "00100", "01010", "00000"],
    ":": ["00000", "00100", "00100", "00000", "00100", "00100", "00000"],
    ".": ["00000", "00000", "00000", "00000", "00000", "00110", "00110"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "10000", "11110", "00001", "00001", "11110"],
    "6": ["01110", "10000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00001", "01110"],
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
    "J": ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "10101", "01010"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "?": ["01110", "10001", "00010", "00100", "00100", "00000", "00100"],
}


class RasterCanvas:
    def __init__(self, width: int, height: int, background: tuple[int, int, int] = WHITE) -> None:
        self.width = width
        self.height = height
        self.pixels = bytearray(background * (width * height))

    def _offset(self, x: int, y: int) -> int:
        return (y * self.width + x) * 3

    def set_pixel(self, x: int, y: int, color: tuple[int, int, int], alpha: float = 1.0) -> None:
        if not (0 <= x < self.width and 0 <= y < self.height):
            return
        alpha = max(0.0, min(1.0, alpha))
        idx = self._offset(x, y)
        if alpha >= 1.0:
            self.pixels[idx: idx + 3] = bytes(color)
            return
        base_r, base_g, base_b = self.pixels[idx], self.pixels[idx + 1], self.pixels[idx + 2]
        r = int(round(base_r * (1.0 - alpha) + color[0] * alpha))
        g = int(round(base_g * (1.0 - alpha) + color[1] * alpha))
        b = int(round(base_b * (1.0 - alpha) + color[2] * alpha))
        self.pixels[idx: idx + 3] = bytes((r, g, b))

    def fill_rect(
        self,
        x0: int,
        y0: int,
        x1: int,
        y1: int,
        color: tuple[int, int, int],
        alpha: float = 1.0,
    ) -> None:
        left = max(0, min(x0, x1))
        right = min(self.width, max(x0, x1))
        top = max(0, min(y0, y1))
        bottom = min(self.height, max(y0, y1))
        for y in range(top, bottom):
            for x in range(left, right):
                self.set_pixel(x, y, color, alpha)

    def draw_line(
        self,
        x0: int,
        y0: int,
        x1: int,
        y1: int,
        color: tuple[int, int, int],
        thickness: int = 1,
    ) -> None:
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self._paint_brush(x0, y0, thickness, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def _paint_brush(self, x: int, y: int, thickness: int, color: tuple[int, int, int]) -> None:
        radius = max(0, thickness // 2)
        for yy in range(y - radius, y + radius + 1):
            for xx in range(x - radius, x + radius + 1):
                self.set_pixel(xx, yy, color)

    def draw_circle(
        self,
        cx: int,
        cy: int,
        radius: int,
        fill: tuple[int, int, int],
        outline: tuple[int, int, int] | None = None,
        outline_width: int = 1,
    ) -> None:
        r_sq = radius * radius
        inner_sq = max(0, (radius - outline_width) * (radius - outline_width))
        for y in range(cy - radius, cy + radius + 1):
            for x in range(cx - radius, cx + radius + 1):
                dist_sq = (x - cx) * (x - cx) + (y - cy) * (y - cy)
                if dist_sq <= r_sq:
                    if outline is not None and dist_sq >= inner_sq:
                        self.set_pixel(x, y, outline)
                    else:
                        self.set_pixel(x, y, fill)

    def draw_rect_outline(
        self,
        x0: int,
        y0: int,
        x1: int,
        y1: int,
        color: tuple[int, int, int],
        thickness: int = 1,
    ) -> None:
        self.fill_rect(x0, y0, x1, y0 + thickness, color)
        self.fill_rect(x0, y1 - thickness, x1, y1, color)
        self.fill_rect(x0, y0, x0 + thickness, y1, color)
        self.fill_rect(x1 - thickness, y0, x1, y1, color)


def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    return (
        struct.pack("!I", len(data))
        + chunk_type
        + data
        + struct.pack("!I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
    )


def export_png(canvas: RasterCanvas, output_path: str | Path, dpi: int = IMAGE_DPI) -> None:
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for y in range(canvas.height):
        start = y * canvas.width * 3
        end = start + canvas.width * 3
        rows.append(b"\x00" + bytes(canvas.pixels[start:end]))
    image_data = zlib.compress(b"".join(rows), level=9)

    ppm = int(round(dpi / 0.0254))
    ihdr = struct.pack("!IIBBBBB", canvas.width, canvas.height, 8, 2, 0, 0, 0)
    phys = struct.pack("!IIB", ppm, ppm, 1)
    png_bytes = b"".join(
        [
            b"\x89PNG\r\n\x1a\n",
            _png_chunk(b"IHDR", ihdr),
            _png_chunk(b"pHYs", phys),
            _png_chunk(b"IDAT", image_data),
            _png_chunk(b"IEND", b""),
        ]
    )
    target.write_bytes(png_bytes)


def build_wall_segments(map_data: dict[str, Any]) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    segments: set[tuple[tuple[int, int], tuple[int, int]]] = set()
    for y, row in enumerate(map_data["wall_matrix"]):
        for x, cell in enumerate(row):
            north, east, south, west = cell
            raw_segments = []
            if north:
                raw_segments.append(((x, y), (x + 1, y)))
            if east:
                raw_segments.append(((x + 1, y), (x + 1, y + 1)))
            if south:
                raw_segments.append(((x, y + 1), (x + 1, y + 1)))
            if west:
                raw_segments.append(((x, y), (x, y + 1)))
            for a, b in raw_segments:
                segment = (a, b) if a <= b else (b, a)
                segments.add(segment)
    return sorted(segments)


def _panel_bounds(index: int) -> dict[str, int]:
    grid_width = IMAGE_WIDTH - 2 * SIDE_MARGIN
    grid_height = IMAGE_HEIGHT - TOP_MARGIN - BOTTOM_MARGIN
    panel_width = (grid_width - GRID_GAP_X * (PANEL_COLUMNS - 1)) // PANEL_COLUMNS
    panel_height = (grid_height - GRID_GAP_Y * (PANEL_ROWS - 1)) // PANEL_ROWS
    col = index % PANEL_COLUMNS
    row = index // PANEL_COLUMNS
    left = SIDE_MARGIN + col * (panel_width + GRID_GAP_X)
    top = TOP_MARGIN + row * (panel_height + GRID_GAP_Y)
    return {
        "left": left,
        "top": top,
        "width": panel_width,
        "height": panel_height,
    }


def _layout_in_bounds(
    map_data: dict[str, Any],
    left: int,
    top: int,
    width: int,
    height: int,
) -> dict[str, int]:
    cell_size = max(1, min(width // map_data["width"], height // map_data["height"]))
    draw_width = cell_size * map_data["width"]
    draw_height = cell_size * map_data["height"]
    return {
        "cell_size": cell_size,
        "left": left + (width - draw_width) // 2,
        "top": top + (height - draw_height) // 2,
        "draw_width": draw_width,
        "draw_height": draw_height,
    }


def _cell_box(layout: dict[str, int], x: int, y: int) -> tuple[int, int, int, int]:
    cell_size = layout["cell_size"]
    left = layout["left"] + x * cell_size
    top = layout["top"] + y * cell_size
    return (left, top, left + cell_size, top + cell_size)


def _cell_center(layout: dict[str, int], x: int, y: int) -> tuple[int, int]:
    x0, y0, x1, y1 = _cell_box(layout, x, y)
    return ((x0 + x1) // 2, (y0 + y1) // 2)


def draw_static_maze(canvas: RasterCanvas, map_data: dict[str, Any], layout: dict[str, int]) -> None:
    goal_cells = map_data.get("goal_cells", [map_data["goal"]])
    for goal_x, goal_y in goal_cells:
        x0, y0, x1, y1 = _cell_box(layout, goal_x, goal_y)
        canvas.fill_rect(x0, y0, x1, y1, GOAL_FILL, alpha=1.0)

    start_x, start_y = map_data["start"]
    x0, y0, x1, y1 = _cell_box(layout, start_x, start_y)
    canvas.fill_rect(x0, y0, x1, y1, START_FILL, alpha=1.0)

    wall_thickness = max(2, layout["cell_size"] // 14)
    for (ax, ay), (bx, by) in build_wall_segments(map_data):
        px0 = layout["left"] + ax * layout["cell_size"]
        py0 = layout["top"] + ay * layout["cell_size"]
        px1 = layout["left"] + bx * layout["cell_size"]
        py1 = layout["top"] + by * layout["cell_size"]
        canvas.draw_line(px0, py0, px1, py1, WALL, thickness=wall_thickness)


def draw_filled_cells(
    canvas: RasterCanvas,
    layout: dict[str, int],
    cells: list[list[int]],
    color: tuple[int, int, int],
    *,
    alpha: float,
    inset_ratio: int = 10,
) -> None:
    inset = max(1, layout["cell_size"] // inset_ratio)
    for cell in cells:
        x0, y0, x1, y1 = _cell_box(layout, int(cell[0]), int(cell[1]))
        canvas.fill_rect(x0 + inset, y0 + inset, x1 - inset, y1 - inset, color, alpha=alpha)


def draw_explored_nodes(canvas: RasterCanvas, layout: dict[str, int], explored_cells: list[list[int]]) -> None:
    draw_filled_cells(canvas, layout, explored_cells, EXPLORED_YELLOW, alpha=0.42)


def draw_frontier_cells(canvas: RasterCanvas, layout: dict[str, int], frontier_cells: list[list[int]]) -> None:
    draw_filled_cells(canvas, layout, frontier_cells, FRONTIER_ORANGE, alpha=0.32, inset_ratio=8)


def draw_blocked_cells(canvas: RasterCanvas, layout: dict[str, int], blocked_cells: list[list[int]]) -> None:
    draw_filled_cells(canvas, layout, blocked_cells, BLOCKED_GRAY, alpha=0.85, inset_ratio=7)


def draw_path(canvas: RasterCanvas, layout: dict[str, int], path: list[list[int]]) -> None:
    if len(path) < 2:
        return
    thickness = max(3, layout["cell_size"] // 8)
    centers = [_cell_center(layout, int(cell[0]), int(cell[1])) for cell in path]
    for (x0, y0), (x1, y1) in zip(centers, centers[1:]):
        canvas.draw_line(x0, y0, x1, y1, PATH_BLUE, thickness=thickness)


def draw_start_goal(canvas: RasterCanvas, map_data: dict[str, Any], layout: dict[str, int]) -> None:
    start_x, start_y = map_data["start"]
    start_cx, start_cy = _cell_center(layout, start_x, start_y)
    radius = max(6, layout["cell_size"] // 5)
    canvas.draw_circle(start_cx, start_cy, radius, START_GREEN, outline=BLACK, outline_width=max(1, radius // 5))

    outline_width = max(2, layout["cell_size"] // 12)
    inset = max(2, layout["cell_size"] // 8)
    for goal_x, goal_y in map_data.get("goal_cells", [map_data["goal"]]):
        x0, y0, x1, y1 = _cell_box(layout, goal_x, goal_y)
        canvas.draw_rect_outline(x0 + inset, y0 + inset, x1 - inset, y1 - inset, GOAL_RED, thickness=outline_width)


def draw_current_cell(
    canvas: RasterCanvas,
    layout: dict[str, int],
    current_cell: list[int] | None,
    *,
    color: tuple[int, int, int] = CURRENT_ORANGE,
) -> None:
    if current_cell is None:
        return
    cx, cy = _cell_center(layout, int(current_cell[0]), int(current_cell[1]))
    radius = max(6, layout["cell_size"] // 6)
    canvas.draw_circle(cx, cy, radius, color, outline=BLACK, outline_width=max(1, radius // 5))


def _text_width(text: str, scale: int) -> int:
    glyph_width = 5 * scale
    spacing = scale
    return sum(glyph_width + spacing for _ in text) - spacing if text else 0


def draw_text(
    canvas: RasterCanvas,
    x: int,
    y: int,
    text: str,
    color: tuple[int, int, int],
    scale: int = 2,
) -> None:
    cursor_x = x
    for char in text.upper():
        glyph = FONT_5X7.get(char, FONT_5X7["?"])
        for row_index, row in enumerate(glyph):
            for col_index, bit in enumerate(row):
                if bit == "1":
                    canvas.fill_rect(
                        cursor_x + col_index * scale,
                        y + row_index * scale,
                        cursor_x + (col_index + 1) * scale,
                        y + (row_index + 1) * scale,
                        color,
                    )
        cursor_x += 6 * scale


def _truncate_text(text: str, max_width: int, scale: int) -> str:
    if _text_width(text, scale) <= max_width:
        return text
    trimmed = text
    while trimmed and _text_width(trimmed + "...", scale) > max_width:
        trimmed = trimmed[:-1]
    return (trimmed + "...") if trimmed else "..."


def draw_header(canvas: RasterCanvas, algorithm_result: dict[str, Any], map_data: dict[str, Any]) -> None:
    title = f"{algorithm_result.get('algorithm', 'ALGORITHM')} PROCESS {map_data.get('maze_id', '')}".strip().upper()
    title = _truncate_text(title, IMAGE_WIDTH - 2 * SIDE_MARGIN, TITLE_SCALE)
    draw_text(canvas, SIDE_MARGIN, 36, title, BLACK, scale=TITLE_SCALE)


def draw_panel_title(canvas: RasterCanvas, bounds: dict[str, int], title: str) -> None:
    max_width = bounds["width"] - 2 * PANEL_INSET
    title = _truncate_text(title.upper(), max_width, SMALL_SCALE)
    draw_text(canvas, bounds["left"] + PANEL_INSET, bounds["top"] + 10, title, BLACK, scale=SMALL_SCALE)


def draw_process_legend(canvas: RasterCanvas, visualization_type: str) -> None:
    legend_y = IMAGE_HEIGHT - 120
    box_size = 24
    x = SIDE_MARGIN

    if visualization_type == "static_process_grid":
        items: list[tuple[str, tuple[int, int, int], str]] = [
            ("START", START_GREEN, "circle"),
            ("GOAL", GOAL_RED, "outline"),
            ("EXPLORED", EXPLORED_YELLOW, "fill"),
            ("FRONTIER", FRONTIER_ORANGE, "fill"),
            ("CURRENT", CURRENT_ORANGE, "circle"),
            ("PATH", PATH_BLUE, "line"),
        ]
    else:
        items = [
            ("START", START_GREEN, "circle"),
            ("GOAL", GOAL_RED, "outline"),
            ("BLOCKED", BLOCKED_GRAY, "fill"),
            ("CURRENT", CURRENT_ORANGE, "circle"),
            ("PATH", PATH_BLUE, "line"),
        ]

    for label, color, kind in items:
        if kind == "circle":
            canvas.draw_circle(x + box_size // 2, legend_y + box_size // 2, box_size // 2, color, outline=BLACK, outline_width=2)
        elif kind == "outline":
            canvas.draw_rect_outline(x, legend_y, x + box_size, legend_y + box_size, color, thickness=3)
        elif kind == "line":
            canvas.draw_line(x, legend_y + box_size // 2, x + box_size, legend_y + box_size // 2, color, thickness=6)
        else:
            canvas.fill_rect(x, legend_y, x + box_size, legend_y + box_size, color, alpha=0.6)
            canvas.draw_rect_outline(x, legend_y, x + box_size, legend_y + box_size, LEGEND_BORDER, thickness=1)

        draw_text(canvas, x + box_size + 10, legend_y + 4, label, BLACK, scale=LABEL_SCALE)
        x += 185


def _clone_frame(frame: dict[str, Any]) -> dict[str, Any]:
    return {
        "step": int(frame.get("step", 0)),
        "event": frame.get("event", ""),
        "current_cell": frame.get("current_cell"),
        "path": [list(cell) for cell in frame.get("path", [])],
        "explored_cells": [list(cell) for cell in frame.get("explored_cells", [])],
        "frontier_cells": [list(cell) for cell in frame.get("frontier_cells", [])],
        "blocked_cells": [list(cell) for cell in frame.get("blocked_cells", [])],
    }


def select_static_process_frames(trace: list[dict[str, Any]], panel_count: int = PANEL_COUNT) -> list[dict[str, Any]]:
    titles = [
        "SEARCH START",
        "EARLY SEARCH",
        "MID SEARCH",
        "LATE SEARCH",
        "NEAR GOAL",
        "FINAL PATH",
    ]
    if not trace:
        trace = [{"step": 0, "event": "empty", "current_cell": None, "path": [], "explored_cells": [], "frontier_cells": [], "blocked_cells": []}]

    if len(trace) == 1:
        frames = [_clone_frame(trace[0]) for _ in range(panel_count)]
    else:
        indices = [round(i * (len(trace) - 1) / (panel_count - 1)) for i in range(panel_count)]
        frames = [_clone_frame(trace[index]) for index in indices]
        frames[0] = _clone_frame(trace[0])
        frames[-1] = _clone_frame(trace[-1])

    for index, frame in enumerate(frames):
        frame["panel_title"] = titles[index]
        if index != panel_count - 1:
            frame["path"] = []
    return frames


def select_dynamic_process_frames(trace: list[dict[str, Any]], panel_count: int = PANEL_COUNT) -> list[dict[str, Any]]:
    del panel_count
    titles = [
        "INITIAL PLAN",
        "BEFORE UPDATE",
        "REPLAN 1",
        "REPLAN 2",
        "REPLAN 3",
        "FINAL RESULT",
    ]
    if not trace:
        trace = [{"step": 0, "event": "empty", "current_cell": None, "path": [], "explored_cells": [], "frontier_cells": [], "blocked_cells": []}]

    initial = next((frame for frame in trace if frame.get("event") == "initial_plan"), trace[0])
    before_update = next((frame for frame in trace if frame.get("event") == "before_update"), initial)
    replans = [frame for frame in trace if frame.get("event") == "replan"]
    final = next((frame for frame in reversed(trace) if frame.get("event") == "final_result"), trace[-1])

    selected = [_clone_frame(initial), _clone_frame(before_update)]
    last_available = selected[-1]
    for index in range(3):
        if index < len(replans):
            last_available = _clone_frame(replans[index])
        selected.append(_clone_frame(last_available))
    selected.append(_clone_frame(final))

    for index, frame in enumerate(selected):
        frame["panel_title"] = titles[index]
    return selected


def render_process_grid(
    canvas: RasterCanvas,
    map_data: dict[str, Any],
    frames: list[dict[str, Any]],
    *,
    static_mode: bool,
) -> None:
    for index, frame in enumerate(frames):
        bounds = _panel_bounds(index)
        canvas.draw_rect_outline(
            bounds["left"],
            bounds["top"],
            bounds["left"] + bounds["width"],
            bounds["top"] + bounds["height"],
            PANEL_BORDER,
            thickness=2,
        )
        draw_panel_title(canvas, bounds, frame.get("panel_title", f"STEP {index + 1}"))

        inner_left = bounds["left"] + PANEL_INSET
        inner_top = bounds["top"] + PANEL_TITLE_HEIGHT
        inner_width = bounds["width"] - 2 * PANEL_INSET
        inner_height = bounds["height"] - PANEL_TITLE_HEIGHT - PANEL_INSET
        layout = _layout_in_bounds(map_data, inner_left, inner_top, inner_width, inner_height)

        draw_static_maze(canvas, map_data, layout)
        if static_mode:
            draw_explored_nodes(canvas, layout, frame.get("explored_cells", []))
            draw_frontier_cells(canvas, layout, frame.get("frontier_cells", []))
            if index == len(frames) - 1:
                draw_path(canvas, layout, frame.get("path", []))
        else:
            draw_blocked_cells(canvas, layout, frame.get("blocked_cells", []))
            draw_path(canvas, layout, frame.get("path", []))

        draw_start_goal(canvas, map_data, layout)
        draw_current_cell(canvas, layout, frame.get("current_cell"))


def _render_process_png(
    map_data: dict[str, Any],
    algorithm_result: dict[str, Any],
    output_path: str | Path,
) -> dict[str, Any]:
    status = algorithm_result.get("status", "ok")
    if status != "ok":
        return {
            "status": status,
            "mode": "image",
            "artifact_type": "image/png",
            "output_path": None,
            "visualization_type": "none",
            "panel_count": 0,
        }

    algorithm = str(algorithm_result.get("algorithm", ""))
    trace = algorithm_result.get("visualization_trace", [])
    if algorithm in {"BFS", "A*"}:
        frames = select_static_process_frames(trace, panel_count=PANEL_COUNT)
        visualization_type = "static_process_grid"
        static_mode = True
    elif algorithm in {"LPA*", "D* Lite"}:
        frames = select_dynamic_process_frames(trace, panel_count=PANEL_COUNT)
        visualization_type = "dynamic_process_grid"
        static_mode = False
    else:
        return {
            "status": "not_implemented",
            "mode": "image",
            "artifact_type": "image/png",
            "output_path": None,
            "visualization_type": "none",
            "panel_count": 0,
        }

    canvas = RasterCanvas(IMAGE_WIDTH, IMAGE_HEIGHT, background=WHITE)
    draw_header(canvas, algorithm_result, map_data)
    render_process_grid(canvas, map_data, frames, static_mode=static_mode)
    draw_process_legend(canvas, visualization_type)
    export_png(canvas, output_path, dpi=IMAGE_DPI)

    return {
        "status": "ok",
        "mode": "image",
        "artifact_type": "image/png",
        "output_path": str(output_path),
        "width_px": IMAGE_WIDTH,
        "height_px": IMAGE_HEIGHT,
        "dpi": IMAGE_DPI,
        "visualization_type": visualization_type,
        "panel_count": PANEL_COUNT,
    }


def visualize_result(
    map_data: dict[str, Any],
    algorithm_result: dict[str, Any],
    output_path: str | Path | None = None,
    mode: str = "text",
) -> dict[str, Any]:
    if mode == "image":
        if output_path is None:
            raise ValueError("output_path is required for image mode")
        return _render_process_png(map_data, algorithm_result, output_path)

    path = algorithm_result.get("path", []) if algorithm_result.get("success") else []
    snapshot = render_map_snapshot(map_data, path=path)
    artifact: dict[str, Any] = {
        "status": "ok",
        "mode": "text",
        "artifact_type": "text",
        "output_path": str(output_path) if output_path else None,
        "render": snapshot,
    }

    if output_path:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(snapshot + "\n", encoding="utf-8")

    return artifact


def write_visualization_manifest(
    artifacts: dict[str, dict[str, Any]],
    output_path: str | Path,
) -> None:
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(artifacts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
