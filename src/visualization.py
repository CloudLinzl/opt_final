#!/usr/bin/env python3
"""
Unified visualization interface for text, PNG, and GIF outputs.
"""

from __future__ import annotations

import json
import math
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
LPA_AFFECTED_CYAN = (34, 197, 214)
DSTAR_AFFECTED_VIOLET = (168, 85, 247)
GOAL_FILL = (254, 226, 226)
START_FILL = (220, 252, 231)
LEGEND_BORDER = (120, 120, 120)
METRIC_BOX = (248, 250, 252)
DYNAMIC_PANEL_FILL = (252, 253, 255)
DYNAMIC_STRIP_FILL = (248, 250, 252)
DYNAMIC_TEXT_MUTED = (71, 85, 105)
DYNAMIC_RISK_FILL = (255, 237, 213)
DYNAMIC_NARROW_FILL = (220, 252, 231)
DYNAMIC_REPAIR_FILL = (254, 249, 195)
DYNAMIC_FRONTIER_FILL = (254, 215, 170)

GIF_EXPLORED_FILL = (254, 240, 138)
GIF_FRONTIER_FILL = (253, 186, 116)
GIF_BLOCKED_FILL = (148, 163, 184)
GIF_LPA_AFFECTED_FILL = (165, 243, 252)
GIF_DSTAR_AFFECTED_FILL = (221, 214, 254)
GIF_RISK_FILL = (255, 237, 213)
GIF_NARROW_FILL = (220, 252, 231)
GIF_EXECUTED_LINE = (180, 83, 9)
GIF_SEARCH_DOT = (234, 179, 8)
GIF_FRONTIER_DOT = (245, 158, 11)

IMAGE_DPI = 300
PNG_WIDTH = 1800
PNG_HEIGHT = 1800
GIF_WIDTH = 960
GIF_HEIGHT = 960

SIDE_MARGIN = 100
TOP_MARGIN = 130
BOTTOM_MARGIN = 180
TITLE_SCALE = 4
LABEL_SCALE = 2
SMALL_SCALE = 2
PANEL_COUNT = 6

GIF_SIDE_MARGIN = 56
GIF_TOP_MARGIN = 84
GIF_BOTTOM_MARGIN = 110
GIF_TITLE_SCALE = 3
GIF_LABEL_SCALE = 2

STATIC_GIF_FRAME_MS = 1000
DYNAMIC_GIF_FRAME_MS = 1000
DYNAMIC_EVENT_FRAME_MS = 1000
DYNAMIC_MOVE_FRAME_MS = 420
FINAL_HOLD_MS = 1000


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


def _gif_subblocks(data: bytes) -> bytes:
    return b"".join(bytes([len(data[i : i + 255])]) + data[i : i + 255] for i in range(0, len(data), 255)) + b"\x00"


def _lzw_compress(indices: list[int], min_code_size: int) -> bytes:
    clear_code = 1 << min_code_size
    end_code = clear_code + 1
    code_size = min_code_size + 1
    max_segment_len = max(1, clear_code - 2)

    bit_buffer = 0
    bit_count = 0
    output = bytearray()

    def emit(code: int) -> None:
        nonlocal bit_buffer, bit_count
        bit_buffer |= code << bit_count
        bit_count += code_size
        while bit_count >= 8:
            output.append(bit_buffer & 0xFF)
            bit_buffer >>= 8
            bit_count -= 8

    # Use frequent clear codes so the decoder never needs to grow the code size.
    # This is less compact than a full LZW implementation, but much more robust.
    for start in range(0, len(indices), max_segment_len):
        emit(clear_code)
        for value in indices[start : start + max_segment_len]:
            emit(value)

    emit(end_code)
    if bit_count:
        output.append(bit_buffer & 0xFF)
    return bytes(output)


def export_gif(frames: list[dict[str, Any]], output_path: str | Path) -> None:
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if not frames:
        raise ValueError("GIF export requires at least one frame")

    width = frames[0]["canvas"].width
    height = frames[0]["canvas"].height
    colors = sorted(
        {
            tuple(canvas.pixels[i : i + 3])
            for frame in frames
            for canvas in [frame["canvas"]]
            for i in range(0, len(canvas.pixels), 3)
        }
    )
    if len(colors) > 256:
        raise ValueError("GIF palette exceeded 256 colors")

    table_size = 1
    while table_size < len(colors):
        table_size <<= 1
    table_size = max(2, table_size)
    palette = colors + [WHITE] * (table_size - len(colors))
    palette_map = {color: index for index, color in enumerate(palette)}
    min_code_size = max(2, (table_size - 1).bit_length())

    header = bytearray()
    header.extend(b"GIF89a")
    header.extend(struct.pack("<HH", width, height))
    packed = 0x80 | 0x70 | ((table_size.bit_length() - 1) - 1)
    header.extend(bytes([packed, 0x00, 0x00]))
    for color in palette:
        header.extend(bytes(color))
    header.extend(b"\x21\xFF\x0BNETSCAPE2.0\x03\x01\x00\x00\x00")

    body = bytearray()
    for frame in frames:
        canvas = frame["canvas"]
        duration_ms = int(frame.get("duration_ms", STATIC_GIF_FRAME_MS))
        delay_cs = max(1, round(duration_ms / 10))
        body.extend(b"\x21\xF9\x04\x04")
        body.extend(struct.pack("<H", delay_cs))
        body.extend(b"\x00\x00")

        body.extend(b"\x2C")
        body.extend(struct.pack("<HHHHB", 0, 0, width, height, 0))

        indices = [
            palette_map[tuple(canvas.pixels[i : i + 3])]
            for i in range(0, len(canvas.pixels), 3)
        ]
        compressed = _lzw_compress(indices, min_code_size)
        body.extend(bytes([min_code_size]))
        body.extend(_gif_subblocks(compressed))

    body.extend(b"\x3B")
    target.write_bytes(bytes(header + body))


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
    for goal_x, goal_y in map_data.get("goal_cells", [map_data["goal"]]):
        x0, y0, x1, y1 = _cell_box(layout, goal_x, goal_y)
        canvas.fill_rect(x0, y0, x1, y1, GOAL_FILL)

    start_x, start_y = map_data["start"]
    x0, y0, x1, y1 = _cell_box(layout, start_x, start_y)
    canvas.fill_rect(x0, y0, x1, y1, START_FILL)

    wall_thickness = max(2, layout["cell_size"] // 14)
    for (ax, ay), (bx, by) in build_wall_segments(map_data):
        px0 = layout["left"] + ax * layout["cell_size"]
        py0 = layout["top"] + ay * layout["cell_size"]
        px1 = layout["left"] + bx * layout["cell_size"]
        py1 = layout["top"] + by * layout["cell_size"]
        canvas.draw_line(px0, py0, px1, py1, WALL, thickness=wall_thickness)


def _fill_cells(
    canvas: RasterCanvas,
    layout: dict[str, int],
    cells: list[list[int]],
    color: tuple[int, int, int],
    *,
    alpha: float = 1.0,
    inset_ratio: int = 10,
) -> None:
    inset = max(1, layout["cell_size"] // inset_ratio)
    for cell in cells:
        x0, y0, x1, y1 = _cell_box(layout, int(cell[0]), int(cell[1]))
        canvas.fill_rect(x0 + inset, y0 + inset, x1 - inset, y1 - inset, color, alpha=alpha)


def draw_blocked_cells(canvas: RasterCanvas, layout: dict[str, int], blocked_cells: list[list[int]]) -> None:
    _fill_cells(canvas, layout, blocked_cells, BLOCKED_GRAY, alpha=0.85, inset_ratio=7)


def draw_affected_cells(
    canvas: RasterCanvas,
    layout: dict[str, int],
    affected_cells: list[list[int]],
    color: tuple[int, int, int],
    *,
    alpha: float = 0.45,
) -> None:
    _fill_cells(canvas, layout, affected_cells, color, alpha=alpha, inset_ratio=6)


def draw_gif_blocked_cells(canvas: RasterCanvas, layout: dict[str, int], blocked_cells: list[list[int]]) -> None:
    _fill_cells(canvas, layout, blocked_cells, GIF_BLOCKED_FILL, alpha=1.0, inset_ratio=7)


def draw_cell_dot(
    canvas: RasterCanvas,
    layout: dict[str, int],
    cell: list[int],
    color: tuple[int, int, int],
    *,
    radius: int | None = None,
    outline: tuple[int, int, int] | None = None,
) -> None:
    cx, cy = _cell_center(layout, int(cell[0]), int(cell[1]))
    dot_radius = radius if radius is not None else max(3, layout["cell_size"] // 10)
    canvas.draw_circle(cx, cy, dot_radius, color, outline=outline, outline_width=max(1, dot_radius // 4))


def draw_cell_ring(
    canvas: RasterCanvas,
    layout: dict[str, int],
    cell: list[int],
    color: tuple[int, int, int],
    *,
    radius: int | None = None,
    thickness: int | None = None,
) -> None:
    cx, cy = _cell_center(layout, int(cell[0]), int(cell[1]))
    ring_radius = radius if radius is not None else max(5, layout["cell_size"] // 6)
    ring_thickness = thickness if thickness is not None else max(2, layout["cell_size"] // 18)
    canvas.draw_circle(cx, cy, ring_radius, WHITE, outline=color, outline_width=ring_thickness)


def draw_lpa_gif_search_activity(canvas: RasterCanvas, layout: dict[str, int], frame: dict[str, Any]) -> None:
    event = frame.get("event")
    if event not in {"dynamic_update", "replan"}:
        return

    affected = frame.get("affected_cells", [])
    explored = frame.get("explored_cells", [])
    frontier = frame.get("frontier_cells", [])
    if affected:
        draw_affected_cells(canvas, layout, affected, GIF_LPA_AFFECTED_FILL, alpha=1.0)

    if event == "dynamic_update":
        for cell in affected:
            draw_cell_ring(canvas, layout, cell, LPA_AFFECTED_CYAN, radius=max(5, layout["cell_size"] // 5))
        return

    # Search is drawn as local activity dots, not full-cell residue. The last
    # cells are emphasized to read as an expanding repair front.
    recent_explored = explored[-42:] if len(explored) > 42 else explored
    for index, cell in enumerate(recent_explored):
        radius = max(2, layout["cell_size"] // (9 if index >= max(0, len(recent_explored) - 12) else 12))
        draw_cell_dot(canvas, layout, cell, GIF_SEARCH_DOT, radius=radius)
    recent_frontier = frontier[-28:] if len(frontier) > 28 else frontier
    for cell in recent_frontier:
        draw_cell_ring(canvas, layout, cell, GIF_FRONTIER_DOT, radius=max(4, layout["cell_size"] // 7), thickness=max(1, layout["cell_size"] // 22))


def draw_cost_regions(canvas: RasterCanvas, map_data: dict[str, Any], layout: dict[str, int], *, gif_mode: bool = False) -> None:
    risk_color = GIF_RISK_FILL if gif_mode else DYNAMIC_RISK_FILL
    narrow_color = GIF_NARROW_FILL if gif_mode else DYNAMIC_NARROW_FILL
    _fill_cells(canvas, layout, map_data.get("risk_cells", []), risk_color, alpha=0.62 if gif_mode else 0.34, inset_ratio=16)
    _fill_cells(canvas, layout, map_data.get("narrow_cells", []), narrow_color, alpha=0.70 if gif_mode else 0.38, inset_ratio=13)


def draw_dynamic_maze(canvas: RasterCanvas, map_data: dict[str, Any], layout: dict[str, int], *, gif_mode: bool = False) -> None:
    draw_cost_regions(canvas, map_data, layout, gif_mode=gif_mode)
    draw_static_maze(canvas, map_data, layout)


def draw_path_with_style(
    canvas: RasterCanvas,
    layout: dict[str, int],
    path: list[list[int]],
    *,
    color: tuple[int, int, int],
    thickness: int | None = None,
    dashed: bool = False,
    offset: tuple[int, int] = (0, 0),
) -> None:
    if len(path) < 2:
        return
    line_thickness = thickness or max(3, layout["cell_size"] // 8)
    centers = [
        (_cell_center(layout, int(cell[0]), int(cell[1]))[0] + offset[0], _cell_center(layout, int(cell[0]), int(cell[1]))[1] + offset[1])
        for cell in path
    ]
    for (x0, y0), (x1, y1) in zip(centers, centers[1:]):
        if not dashed:
            canvas.draw_line(x0, y0, x1, y1, color, thickness=line_thickness)
            continue
        dx = x1 - x0
        dy = y1 - y0
        steps = max(abs(dx), abs(dy), 1)
        dash = max(8, layout["cell_size"] // 3)
        gap = max(5, layout["cell_size"] // 5)
        drawn = 0
        while drawn < steps:
            end = min(steps, drawn + dash)
            sx = x0 + round(dx * drawn / steps)
            sy = y0 + round(dy * drawn / steps)
            ex = x0 + round(dx * end / steps)
            ey = y0 + round(dy * end / steps)
            canvas.draw_line(sx, sy, ex, ey, color, thickness=line_thickness)
            drawn = end + gap


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


def draw_text(canvas: RasterCanvas, x: int, y: int, text: str, color: tuple[int, int, int], scale: int = 2) -> None:
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


def draw_header(canvas: RasterCanvas, algorithm_result: dict[str, Any], map_data: dict[str, Any], *, width: int, side_margin: int, scale: int, suffix: str) -> None:
    title = f"{algorithm_result.get('algorithm', 'ALGORITHM')} {suffix} {map_data.get('maze_id', '')}".strip().upper()
    title = _truncate_text(title, width - 2 * side_margin, scale)
    draw_text(canvas, side_margin, 28 if scale == GIF_TITLE_SCALE else 36, title, BLACK, scale=scale)


def _frame_phase_label(frame: dict[str, Any]) -> str:
    event = str(frame.get("event", "")).replace("_", " ").upper()
    if event == "INITIAL PLAN":
        return "INITIAL PLAN"
    if event == "BEFORE UPDATE":
        return "MOVE BEFORE UPDATE"
    if event == "DYNAMIC UPDATE":
        return "MAP CHANGE"
    if event == "REPLAN":
        return "LOCAL REPAIR"
    if event == "FINAL RESULT":
        return "FINAL RESULT"
    return event or "PROCESS"


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _first_trace_frame(trace: list[dict[str, Any]], event: str, fallback: dict[str, Any]) -> dict[str, Any]:
    return next((frame for frame in trace if frame.get("event") == event), fallback)


def _last_trace_frame(trace: list[dict[str, Any]], event: str, fallback: dict[str, Any]) -> dict[str, Any]:
    return next((frame for frame in reversed(trace) if frame.get("event") == event), fallback)


def _collect_cells_from_frames(frames: list[dict[str, Any]], key: str) -> list[list[int]]:
    cells: list[list[int]] = []
    for frame in frames:
        cells.extend(frame.get(key, []))
    normalized = {(int(cell[0]), int(cell[1])) for cell in cells}
    return [[x, y] for x, y in sorted(normalized, key=lambda item: (item[1], item[0]))]


def _cell_set(cells: list[list[int]]) -> set[tuple[int, int]]:
    return {(int(cell[0]), int(cell[1])) for cell in cells}


def _cells_from_set(cells: set[tuple[int, int]]) -> list[list[int]]:
    return [[x, y] for x, y in sorted(cells, key=lambda item: (item[1], item[0]))]


def _path_prefix(path: list[list[int]], step: int) -> list[list[int]]:
    if not path:
        return []
    clipped = max(0, min(int(step), len(path) - 1))
    return [list(cell) for cell in path[: clipped + 1]]


def _combine_prefix_and_tail(prefix: list[list[int]], tail: list[list[int]]) -> list[list[int]]:
    if not prefix:
        return [list(cell) for cell in tail]
    if not tail:
        return [list(cell) for cell in prefix]
    if tuple(prefix[-1]) == tuple(tail[0]):
        return [list(cell) for cell in prefix[:-1]] + [list(cell) for cell in tail]
    return [list(cell) for cell in prefix] + [list(cell) for cell in tail]


def _new_blocked_cells(before_frame: dict[str, Any], update_frame: dict[str, Any]) -> list[list[int]]:
    before = _cell_set(before_frame.get("blocked_cells", []))
    after = _cell_set(update_frame.get("blocked_cells", []))
    return _cells_from_set(after - before)


def _choose_lpa_story_event(
    before_frames: list[dict[str, Any]],
    update_frames: list[dict[str, Any]],
    replan_frames: list[dict[str, Any]],
) -> int:
    if not update_frames:
        return 0

    best_index = 0
    best_score = (-1, -1, -1, -1)
    pair_count = max(len(update_frames), len(before_frames), len(replan_frames), 1)
    for index in range(pair_count):
        before = before_frames[min(index, len(before_frames) - 1)] if before_frames else update_frames[min(index, len(update_frames) - 1)]
        update = update_frames[min(index, len(update_frames) - 1)]
        replan = replan_frames[min(index, len(replan_frames) - 1)] if replan_frames else update
        old_path = before.get("path", [])
        new_path = replan.get("path", [])
        old_cells = _cell_set(old_path)
        changed_cells = _cell_set(_new_blocked_cells(before, update))
        affected_cells = _cell_set(update.get("affected_cells", []))

        # Prefer an event that changes the remaining route, then one that
        # touches the current route, then one that visibly expands repair work.
        route_changed = 1 if old_path != new_path else 0
        blocks_old_route = 1 if changed_cells & old_cells else 0
        affects_old_route = 1 if affected_cells & old_cells else 0
        explored_count = len(replan.get("explored_cells", []))
        score = (route_changed, blocks_old_route, affects_old_route, explored_count)
        if score > best_score:
            best_score = score
            best_index = index
    return best_index


def _lpa_story_bundle(algorithm_result: dict[str, Any]) -> dict[str, Any]:
    trace = [_clone_frame(frame) for frame in algorithm_result.get("visualization_trace", [])]
    if not trace:
        empty = {"step": 0, "event": "empty", "current_cell": None, "path": [], "explored_cells": [], "frontier_cells": [], "blocked_cells": [], "affected_cells": [], "queue_size": 0}
        trace = [empty]

    initial = _first_trace_frame(trace, "initial_plan", trace[0])
    before_frames = [frame for frame in trace if frame.get("event") == "before_update"]
    update_frames = [frame for frame in trace if frame.get("event") == "dynamic_update"]
    final = _last_trace_frame(trace, "final_result", trace[-1])
    repair_frames = [frame for frame in trace if frame.get("event") == "replan"]

    event_index = _choose_lpa_story_event(before_frames, update_frames, repair_frames)
    before_update = before_frames[min(event_index, len(before_frames) - 1)] if before_frames else initial
    map_change = update_frames[min(event_index, len(update_frames) - 1)] if update_frames else before_update
    repair = repair_frames[min(event_index, len(repair_frames) - 1)] if repair_frames else map_change
    repaired = _last_trace_frame(trace, "replan", repair)
    repair_frames = [frame for frame in trace if frame.get("event") == "replan"]
    update_frames = [frame for frame in trace if frame.get("event") == "dynamic_update"]
    final_path = algorithm_result.get("path") or final.get("path", [])
    event_step = _safe_int(map_change.get("step", before_update.get("step", 0)))
    actual_prefix = _path_prefix(final_path, event_step)
    old_candidate_path = _combine_prefix_and_tail(actual_prefix, before_update.get("path", []))
    repaired_candidate_path = _combine_prefix_and_tail(actual_prefix, repair.get("path", []))
    final_blocked = _cell_set(final.get("blocked_cells", map_change.get("blocked_cells", [])))
    final_path_cells = _cell_set(final_path)
    late_blocked_overlap = final_blocked & final_path_cells
    new_blocked_cells = _new_blocked_cells(before_update, map_change)
    old_plan_hit = bool(_cell_set(new_blocked_cells) & _cell_set(before_update.get("path", [])))

    return {
        "trace": trace,
        "initial": initial,
        "before_update": before_update,
        "map_change": map_change,
        "repair": repair,
        "repaired": repaired,
        "final": final,
        "initial_path": initial.get("path", []),
        "final_path": final_path,
        "event_index": event_index,
        "event_step": event_step,
        "actual_prefix": actual_prefix,
        "old_candidate_path": old_candidate_path,
        "repaired_candidate_path": repaired_candidate_path,
        "new_blocked_cells": new_blocked_cells,
        "old_plan_hit": old_plan_hit,
        "route_changed": old_candidate_path != repaired_candidate_path,
        "initial_final_same": initial.get("path", []) == final_path,
        "late_blocked_overlap": _cells_from_set(late_blocked_overlap),
        "final_blocked_without_history_overlap": _cells_from_set(final_blocked - late_blocked_overlap),
        "affected_cells": _collect_cells_from_frames(update_frames + repair_frames, "affected_cells"),
        "repair_cells": _collect_cells_from_frames(repair_frames + [final], "explored_cells"),
        "frontier_cells": _collect_cells_from_frames(repair_frames, "frontier_cells"),
        "blocked_cells": final.get("blocked_cells", map_change.get("blocked_cells", [])),
    }


def _draw_story_metric_bars(canvas: RasterCanvas, algorithm_result: dict[str, Any], x: int, y: int, width: int, height: int) -> None:
    canvas.fill_rect(x, y, x + width, y + height, DYNAMIC_PANEL_FILL)
    canvas.draw_rect_outline(x, y, x + width, y + height, PANEL_BORDER, thickness=2)
    draw_text(canvas, x + 22, y + 20, "OBJECTIVE SUMMARY", BLACK, scale=SMALL_SCALE)

    metrics = [
        ("LENGTH", _safe_float(algorithm_result.get("path_length", 0))),
        ("TURNS", _safe_float(algorithm_result.get("turn_count", 0))),
        ("RISK", _safe_float(algorithm_result.get("risk_cost", 0))),
        ("NARROW", _safe_float(algorithm_result.get("narrow_cost", 0))),
        ("REPLAN", _safe_float(algorithm_result.get("replan_count", 0))),
        ("UPDATED", _safe_float(algorithm_result.get("updated_nodes", 0))),
        ("COST", _safe_float(algorithm_result.get("total_cost", 0))),
    ]
    max_value = max([value for _, value in metrics] + [1.0])
    bar_x = x + 170
    bar_width = width - 260
    row_y = y + 70
    row_gap = 26
    for label, value in metrics:
        draw_text(canvas, x + 22, row_y, label, DYNAMIC_TEXT_MUTED, scale=SMALL_SCALE)
        fill_w = max(4, round(bar_width * value / max_value))
        canvas.fill_rect(bar_x, row_y + 2, bar_x + bar_width, row_y + 14, DYNAMIC_STRIP_FILL)
        canvas.fill_rect(bar_x, row_y + 2, bar_x + fill_w, row_y + 14, PATH_BLUE if label == "COST" else LPA_AFFECTED_CYAN)
        canvas.draw_rect_outline(bar_x, row_y + 2, bar_x + bar_width, row_y + 14, PANEL_BORDER, thickness=1)
        draw_text(canvas, bar_x + bar_width + 12, row_y, f"{value:.0f}", BLACK, scale=SMALL_SCALE)
        row_y += row_gap


def _draw_lpa_story_legend(canvas: RasterCanvas, x: int, y: int, *, compact: bool = False) -> None:
    items = [
        ("OLD PLAN", (100, 116, 139), "line"),
        ("REPAIRED", PATH_BLUE, "line"),
        ("EXECUTED", CURRENT_ORANGE, "line"),
        ("BLOCK", BLOCKED_GRAY, "fill"),
        ("AFFECT", LPA_AFFECTED_CYAN, "fill"),
        ("SEARCH", GIF_SEARCH_DOT, "dot"),
        ("FRONT", GIF_FRONTIER_DOT, "ring"),
    ]
    cursor = x
    spacing = 102 if compact else 180
    for label, color, kind in items:
        if kind == "line":
            canvas.draw_line(cursor, y + 12, cursor + 28, y + 12, color, thickness=6)
        elif kind == "dot":
            canvas.draw_circle(cursor + 14, y + 12, 6, color)
        elif kind == "ring":
            canvas.draw_circle(cursor + 14, y + 12, 8, WHITE, outline=color, outline_width=3)
        else:
            canvas.fill_rect(cursor, y, cursor + 24, y + 24, color, alpha=0.8)
            canvas.draw_rect_outline(cursor, y, cursor + 24, y + 24, LEGEND_BORDER, thickness=1)
        draw_text(canvas, cursor + 34, y + 4, label, BLACK, scale=SMALL_SCALE)
        cursor += spacing


def _draw_story_legend(
    canvas: RasterCanvas,
    x: int,
    y: int,
    items: list[tuple[str, tuple[int, int, int], str]],
    *,
    compact: bool = False,
) -> None:
    cursor = x
    spacing = 102 if compact else 180
    for label, color, kind in items:
        if kind == "line":
            canvas.draw_line(cursor, y + 12, cursor + 28, y + 12, color, thickness=6)
        elif kind == "dash":
            draw_path_with_style(
                canvas,
                {"left": cursor, "top": y, "cell_size": 28},
                [[0, 0], [1, 0]],
                color=color,
                thickness=5,
                dashed=True,
            )
        elif kind == "dot":
            canvas.draw_circle(cursor + 14, y + 12, 6, color)
        elif kind == "ring":
            canvas.draw_circle(cursor + 14, y + 12, 8, WHITE, outline=color, outline_width=3)
        else:
            canvas.fill_rect(cursor, y, cursor + 24, y + 24, color, alpha=0.8)
            canvas.draw_rect_outline(cursor, y, cursor + 24, y + 24, LEGEND_BORDER, thickness=1)
        draw_text(canvas, cursor + 34, y + 4, label, BLACK, scale=SMALL_SCALE)
        cursor += spacing


def _draw_story_summary_card(
    canvas: RasterCanvas,
    algorithm_result: dict[str, Any],
    x: int,
    y: int,
    width: int,
    height: int,
    *,
    title: str,
    extra_lines: list[str] | None = None,
) -> None:
    canvas.fill_rect(x, y, x + width, y + height, DYNAMIC_PANEL_FILL)
    canvas.draw_rect_outline(x, y, x + width, y + height, PANEL_BORDER, thickness=2)
    draw_text(canvas, x + 18, y + 18, _truncate_text(title, width - 36, SMALL_SCALE), BLACK, scale=SMALL_SCALE)
    lines = [
        f"STATUS {algorithm_result.get('status', 'ok')}",
        f"SUCCESS {algorithm_result.get('success')}",
        f"LENGTH {_safe_int(algorithm_result.get('path_length', 0))}",
        f"TURNS {_safe_int(algorithm_result.get('turn_count', 0))}",
        f"NODES {_safe_int(algorithm_result.get('explored_nodes', 0))}",
        f"COST {_safe_float(algorithm_result.get('total_cost', 0.0)):.0f}",
    ]
    if extra_lines:
        lines.extend(extra_lines)
    cursor_y = y + 62
    for line in lines[:7]:
        draw_text(canvas, x + 18, cursor_y, _truncate_text(line, width - 36, SMALL_SCALE), DYNAMIC_TEXT_MUTED, scale=SMALL_SCALE)
        cursor_y += 30


def _draw_lpa_story_map_panel(
    canvas: RasterCanvas,
    map_data: dict[str, Any],
    bounds: dict[str, int],
    *,
    title: str,
    subtitle: str,
    frame: dict[str, Any],
    paths: list[dict[str, Any]],
    blocked_cells: list[list[int]] | None = None,
    affected_cells: list[list[int]] | None = None,
    repair_cells: list[list[int]] | None = None,
    frontier_cells: list[list[int]] | None = None,
    current_cell: list[int] | None = None,
    note: str | None = None,
    affected_color: tuple[int, int, int] = LPA_AFFECTED_CYAN,
) -> None:
    canvas.fill_rect(bounds["left"], bounds["top"], bounds["left"] + bounds["width"], bounds["top"] + bounds["height"], DYNAMIC_PANEL_FILL)
    canvas.draw_rect_outline(bounds["left"], bounds["top"], bounds["left"] + bounds["width"], bounds["top"] + bounds["height"], PANEL_BORDER, thickness=2)
    draw_text(canvas, bounds["left"] + 18, bounds["top"] + 16, _truncate_text(title, bounds["width"] - 36, SMALL_SCALE), BLACK, scale=SMALL_SCALE)
    draw_text(canvas, bounds["left"] + 18, bounds["top"] + 40, _truncate_text(subtitle, bounds["width"] - 36, SMALL_SCALE), DYNAMIC_TEXT_MUTED, scale=SMALL_SCALE)

    footer_h = 34 if note else 10
    layout = _layout_in_bounds(
        map_data,
        bounds["left"] + 22,
        bounds["top"] + 72,
        bounds["width"] - 44,
        bounds["height"] - 82 - footer_h,
    )
    draw_static_maze(canvas, map_data, layout)
    if blocked_cells:
        draw_blocked_cells(canvas, layout, blocked_cells)
    if affected_cells:
        draw_affected_cells(canvas, layout, affected_cells, affected_color, alpha=0.42)
    if repair_cells:
        recent_repair = repair_cells[-60:] if len(repair_cells) > 60 else repair_cells
        for index, cell in enumerate(recent_repair):
            radius = max(2, layout["cell_size"] // (9 if index >= max(0, len(recent_repair) - 16) else 12))
            draw_cell_dot(canvas, layout, cell, GIF_SEARCH_DOT, radius=radius)
    if frontier_cells:
        recent_frontier = frontier_cells[-36:] if len(frontier_cells) > 36 else frontier_cells
        for cell in recent_frontier:
            draw_cell_ring(canvas, layout, cell, GIF_FRONTIER_DOT, radius=max(4, layout["cell_size"] // 7), thickness=max(1, layout["cell_size"] // 24))

    for spec in paths:
        draw_path_with_style(
            canvas,
            layout,
            spec.get("path", []),
            color=spec.get("color", PATH_BLUE),
            thickness=spec.get("thickness", max(3, layout["cell_size"] // 8)),
            dashed=bool(spec.get("dashed", False)),
            offset=spec.get("offset", (0, 0)),
        )
    draw_start_goal(canvas, map_data, layout)
    draw_current_cell(canvas, layout, current_cell if current_cell is not None else frame.get("current_cell"))

    if note:
        draw_text(canvas, bounds["left"] + 18, bounds["top"] + bounds["height"] - 28, _truncate_text(note, bounds["width"] - 36, SMALL_SCALE), DYNAMIC_TEXT_MUTED, scale=SMALL_SCALE)


def _draw_lpa_story_status_card(canvas: RasterCanvas, bundle: dict[str, Any], x: int, y: int, width: int, height: int) -> None:
    canvas.fill_rect(x, y, x + width, y + height, DYNAMIC_PANEL_FILL)
    canvas.draw_rect_outline(x, y, x + width, y + height, PANEL_BORDER, thickness=2)
    draw_text(canvas, x + 18, y + 18, "UPDATE LOGIC", BLACK, scale=SMALL_SCALE)
    status = "ROUTE CHANGED" if bundle.get("route_changed") else "ROUTE STABLE"
    old_hit = "YES" if bundle.get("old_plan_hit") else "NO"
    late = len(bundle.get("late_blocked_overlap", []))
    lines = [
        f"EVENT STEP {bundle.get('event_step', 0)}",
        status,
        f"OLD PLAN HIT {old_hit}",
        f"LATE BLOCKED PASS {late}",
        "ORANGE PREFIX IS HISTORY",
        "BLUE TAIL IS CURRENT PLAN",
    ]
    cursor_y = y + 62
    for line in lines:
        draw_text(canvas, x + 18, cursor_y, _truncate_text(line, width - 36, SMALL_SCALE), DYNAMIC_TEXT_MUTED if line != status else BLACK, scale=SMALL_SCALE)
        cursor_y += 30


def render_lpa_story_png(map_data: dict[str, Any], algorithm_result: dict[str, Any], output_path: str | Path) -> dict[str, Any]:
    bundle = _lpa_story_bundle(algorithm_result)
    canvas = RasterCanvas(PNG_WIDTH, PNG_HEIGHT, background=WHITE)
    draw_header(canvas, algorithm_result, map_data, width=PNG_WIDTH, side_margin=SIDE_MARGIN, scale=TITLE_SCALE, suffix="STORY")

    event_note = "ROUTE CHANGED BY REPAIR" if bundle["route_changed"] else "ROUTE STABLE AFTER LOCAL CHECK"
    main_bounds = {"left": 82, "top": 145, "width": 1060, "height": 940}
    _draw_lpa_story_map_panel(
        canvas,
        map_data,
        main_bounds,
        title=f"LOCAL REPAIR AT STEP {bundle['event_step']}",
        subtitle=event_note,
        frame=bundle["repair"],
        blocked_cells=bundle["map_change"].get("blocked_cells", []),
        affected_cells=bundle["map_change"].get("affected_cells", []),
        repair_cells=bundle["repair"].get("explored_cells", []),
        frontier_cells=bundle["repair"].get("frontier_cells", []),
        current_cell=bundle["map_change"].get("current_cell"),
        paths=[
            {"path": bundle["actual_prefix"], "color": CURRENT_ORANGE, "thickness": 9},
            {"path": bundle["before_update"].get("path", []), "color": (100, 116, 139), "thickness": 6, "dashed": True, "offset": (-4, -4)},
            {"path": bundle["repair"].get("path", []), "color": PATH_BLUE, "thickness": 8, "offset": (4, 4)},
        ],
        note="OLD DASHED TAIL VS BLUE REPAIRED TAIL SHARE THE SAME CURRENT CELL",
    )

    right_x = 1182
    mini_w = 250
    mini_h = 305
    gap_x = 22
    gap_y = 24
    mini_panels = [
        (
            {"left": right_x, "top": 145, "width": mini_w, "height": mini_h},
            "1 INITIAL",
            "START STATE",
            bundle["initial"],
            [],
            bundle["initial"].get("blocked_cells", []),
            [],
            [],
        ),
        (
            {"left": right_x + mini_w + gap_x, "top": 145, "width": mini_w, "height": mini_h},
            "2 BEFORE",
            f"STEP {bundle['event_step']}",
            bundle["before_update"],
            [
                {"path": bundle["actual_prefix"], "color": CURRENT_ORANGE, "thickness": 5},
                {"path": bundle["before_update"].get("path", []), "color": (100, 116, 139), "thickness": 5, "dashed": True},
            ],
            bundle["before_update"].get("blocked_cells", []),
            [],
            [],
        ),
        (
            {"left": right_x, "top": 145 + mini_h + gap_y, "width": mini_w, "height": mini_h},
            "3 CHANGE",
            f"NEW BLOCKS {len(bundle['new_blocked_cells'])}",
            bundle["map_change"],
            [{"path": bundle["before_update"].get("path", []), "color": (100, 116, 139), "thickness": 5, "dashed": True}],
            bundle["map_change"].get("blocked_cells", []),
            bundle["map_change"].get("affected_cells", []),
            [],
        ),
        (
            {"left": right_x + mini_w + gap_x, "top": 145 + mini_h + gap_y, "width": mini_w, "height": mini_h},
            "4 REPAIR",
            "G RHS REUSED",
            bundle["repair"],
            [
                {"path": bundle["actual_prefix"], "color": CURRENT_ORANGE, "thickness": 5},
                {"path": bundle["repair"].get("path", []), "color": PATH_BLUE, "thickness": 6},
            ],
            bundle["repair"].get("blocked_cells", []),
            bundle["repair"].get("affected_cells", []),
            bundle["repair"].get("explored_cells", []),
        ),
    ]
    for bounds, title, subtitle, frame, paths, blocked, affected, repair_cells in mini_panels:
        _draw_lpa_story_map_panel(
            canvas,
            map_data,
            bounds,
            title=title,
            subtitle=subtitle,
            frame=frame,
            paths=paths,
            blocked_cells=blocked,
            affected_cells=affected,
            repair_cells=repair_cells,
            current_cell=frame.get("current_cell"),
        )

    _draw_lpa_story_map_panel(
        canvas,
        map_data,
        {"left": 1182, "top": 145 + 2 * mini_h + 2 * gap_y, "width": 522, "height": 302},
        title="5 EXECUTED ROUTE",
        subtitle="TIME VALID HISTORY",
        frame=bundle["final"],
        paths=[
            {"path": bundle["final_path"], "color": CURRENT_ORANGE, "thickness": 5},
        ],
        blocked_cells=bundle["final_blocked_without_history_overlap"],
        affected_cells=bundle["late_blocked_overlap"],
        current_cell=bundle["final"].get("current_cell"),
        note="CYAN ON ROUTE MEANS BLOCKED AFTER THE ROBOT HAD PASSED",
    )

    _draw_lpa_story_status_card(canvas, bundle, 82, 1125, 370, 260)
    _draw_story_metric_bars(canvas, algorithm_result, 482, 1125, 1222, 260)
    _draw_lpa_story_legend(canvas, 95, 1450)
    export_png(canvas, output_path, dpi=IMAGE_DPI)
    return {
        "status": "ok",
        "artifact_type": "image/png",
        "png_output_path": str(output_path),
        "width_px": PNG_WIDTH,
        "height_px": PNG_HEIGHT,
        "dpi": IMAGE_DPI,
        "visualization_type": "lpa_story_png",
        "panel_count": 1,
    }


def render_static_story_png(map_data: dict[str, Any], algorithm_result: dict[str, Any], output_path: str | Path) -> dict[str, Any]:
    trace = [_clone_frame(frame) for frame in algorithm_result.get("visualization_trace", [])]
    if not trace:
        trace = [{"step": 0, "event": "empty", "current_cell": None, "path": [], "explored_cells": [], "frontier_cells": []}]
    final_frame = _clone_frame(trace[-1])
    final_path = algorithm_result.get("path") or final_frame.get("path", [])
    final_frame["path"] = final_path
    frames = select_static_process_frames(trace, panel_count=4)

    canvas = RasterCanvas(PNG_WIDTH, PNG_HEIGHT, background=WHITE)
    draw_header(canvas, algorithm_result, map_data, width=PNG_WIDTH, side_margin=SIDE_MARGIN, scale=TITLE_SCALE, suffix="STORY")

    main_bounds = {"left": 82, "top": 145, "width": 1060, "height": 940}
    _draw_lpa_story_map_panel(
        canvas,
        map_data,
        main_bounds,
        title="SEARCH RESULT",
        subtitle="DOTS SHOW EXPANSION, BLUE SHOWS FINAL ROUTE",
        frame=final_frame,
        paths=[{"path": final_path, "color": PATH_BLUE, "thickness": 8}],
        repair_cells=final_frame.get("explored_cells", []),
        frontier_cells=final_frame.get("frontier_cells", []),
        current_cell=final_path[-1] if final_path else None,
    )

    right_x = 1182
    mini_w = 250
    mini_h = 305
    gap_x = 22
    gap_y = 24
    mini_titles = [("1 START", "INITIAL WAVE"), ("2 EARLY", "LOCAL EXPANSION"), ("3 LATE", "NEAR GOAL"), ("4 RESULT", "FINAL PATH")]
    for index, frame in enumerate(frames):
        col = index % 2
        row = index // 2
        bounds = {
            "left": right_x + col * (mini_w + gap_x),
            "top": 145 + row * (mini_h + gap_y),
            "width": mini_w,
            "height": mini_h,
        }
        title, subtitle = mini_titles[index]
        paths = [{"path": final_path, "color": PATH_BLUE, "thickness": 5}] if index == len(frames) - 1 else []
        _draw_lpa_story_map_panel(
            canvas,
            map_data,
            bounds,
            title=title,
            subtitle=subtitle,
            frame=frame,
            paths=paths,
            repair_cells=frame.get("explored_cells", []),
            frontier_cells=frame.get("frontier_cells", []),
            current_cell=frame.get("current_cell"),
        )

    _draw_story_summary_card(canvas, algorithm_result, 82, 1125, 370, 260, title="SEARCH SUMMARY")
    _draw_story_metric_bars(canvas, algorithm_result, 482, 1125, 1222, 260)
    _draw_story_legend(
        canvas,
        95,
        1450,
        [
            ("PATH", PATH_BLUE, "line"),
            ("SEARCH", GIF_SEARCH_DOT, "dot"),
            ("FRONT", GIF_FRONTIER_DOT, "ring"),
        ],
    )
    export_png(canvas, output_path, dpi=IMAGE_DPI)
    return {
        "status": "ok",
        "artifact_type": "image/png",
        "png_output_path": str(output_path),
        "width_px": PNG_WIDTH,
        "height_px": PNG_HEIGHT,
        "dpi": IMAGE_DPI,
        "visualization_type": "static_story_png",
        "panel_count": 1,
    }


def render_dynamic_story_png(map_data: dict[str, Any], algorithm_result: dict[str, Any], output_path: str | Path) -> dict[str, Any]:
    bundle = _lpa_story_bundle(algorithm_result)
    canvas = RasterCanvas(PNG_WIDTH, PNG_HEIGHT, background=WHITE)
    draw_header(canvas, algorithm_result, map_data, width=PNG_WIDTH, side_margin=SIDE_MARGIN, scale=TITLE_SCALE, suffix="STORY")

    changed = "ROUTE CHANGED BY REPAIR" if bundle["route_changed"] else "ROUTE STABLE AFTER UPDATE"
    main_bounds = {"left": 82, "top": 145, "width": 1060, "height": 940}
    _draw_lpa_story_map_panel(
        canvas,
        map_data,
        main_bounds,
        title=f"DYNAMIC REPAIR AT STEP {bundle['event_step']}",
        subtitle=changed,
        frame=bundle["repair"],
        blocked_cells=bundle["map_change"].get("blocked_cells", []),
        affected_cells=bundle["map_change"].get("affected_cells", []),
        repair_cells=bundle["repair"].get("explored_cells", []),
        frontier_cells=bundle["repair"].get("frontier_cells", []),
        current_cell=bundle["map_change"].get("current_cell"),
        paths=[
            {"path": bundle["actual_prefix"], "color": CURRENT_ORANGE, "thickness": 9},
            {"path": bundle["before_update"].get("path", []), "color": (100, 116, 139), "thickness": 6, "dashed": True, "offset": (-4, -4)},
            {"path": bundle["repair"].get("path", []), "color": PATH_BLUE, "thickness": 8, "offset": (4, 4)},
        ],
        affected_color=DSTAR_AFFECTED_VIOLET,
        note="OLD DASHED PLAN VS BLUE REPAIRED PLAN AT THE SAME UPDATE STEP",
    )

    right_x = 1182
    mini_w = 250
    mini_h = 305
    gap_x = 22
    gap_y = 24
    mini_panels = [
        ("1 INITIAL", "BASE PLAN", bundle["initial"], [], bundle["initial"].get("blocked_cells", []), []),
        (
            "2 BEFORE",
            f"STEP {bundle['event_step']}",
            bundle["before_update"],
            [
                {"path": bundle["actual_prefix"], "color": CURRENT_ORANGE, "thickness": 5},
                {"path": bundle["before_update"].get("path", []), "color": (100, 116, 139), "thickness": 5, "dashed": True},
            ],
            bundle["before_update"].get("blocked_cells", []),
            [],
        ),
        (
            "3 CHANGE",
            f"NEW BLOCKS {len(bundle['new_blocked_cells'])}",
            bundle["map_change"],
            [{"path": bundle["before_update"].get("path", []), "color": (100, 116, 139), "thickness": 5, "dashed": True}],
            bundle["map_change"].get("blocked_cells", []),
            bundle["map_change"].get("affected_cells", []),
        ),
        (
            "4 REPAIR",
            "INCREMENTAL UPDATE",
            bundle["repair"],
            [
                {"path": bundle["actual_prefix"], "color": CURRENT_ORANGE, "thickness": 5},
                {"path": bundle["repair"].get("path", []), "color": PATH_BLUE, "thickness": 6},
            ],
            bundle["repair"].get("blocked_cells", []),
            bundle["repair"].get("affected_cells", []),
        ),
    ]
    for index, (title, subtitle, frame, paths, blocked, affected) in enumerate(mini_panels):
        col = index % 2
        row = index // 2
        _draw_lpa_story_map_panel(
            canvas,
            map_data,
            {"left": right_x + col * (mini_w + gap_x), "top": 145 + row * (mini_h + gap_y), "width": mini_w, "height": mini_h},
            title=title,
            subtitle=subtitle,
            frame=frame,
            paths=paths,
            blocked_cells=blocked,
            affected_cells=affected,
            repair_cells=frame.get("explored_cells", []) if title == "4 REPAIR" else [],
            frontier_cells=frame.get("frontier_cells", []) if title == "4 REPAIR" else [],
            current_cell=frame.get("current_cell"),
            affected_color=DSTAR_AFFECTED_VIOLET,
        )

    _draw_lpa_story_map_panel(
        canvas,
        map_data,
        {"left": 1182, "top": 145 + 2 * mini_h + 2 * gap_y, "width": 522, "height": 302},
        title="5 EXECUTED ROUTE",
        subtitle="TIME VALID HISTORY",
        frame=bundle["final"],
        paths=[{"path": bundle["final_path"], "color": CURRENT_ORANGE, "thickness": 5}],
        blocked_cells=bundle["final_blocked_without_history_overlap"],
        affected_cells=bundle["late_blocked_overlap"],
        current_cell=bundle["final"].get("current_cell"),
        affected_color=DSTAR_AFFECTED_VIOLET,
    )

    _draw_story_summary_card(
        canvas,
        algorithm_result,
        82,
        1125,
        370,
        260,
        title="UPDATE SUMMARY",
        extra_lines=[
            f"ROUTE {'CHANGED' if bundle['route_changed'] else 'STABLE'}",
            f"OLD HIT {'YES' if bundle['old_plan_hit'] else 'NO'}",
        ],
    )
    _draw_story_metric_bars(canvas, algorithm_result, 482, 1125, 1222, 260)
    _draw_story_legend(
        canvas,
        95,
        1450,
        [
            ("OLD PLAN", (100, 116, 139), "line"),
            ("REPAIRED", PATH_BLUE, "line"),
            ("EXECUTED", CURRENT_ORANGE, "line"),
            ("BLOCK", BLOCKED_GRAY, "fill"),
            ("AFFECT", DSTAR_AFFECTED_VIOLET, "fill"),
            ("SEARCH", GIF_SEARCH_DOT, "dot"),
            ("FRONT", GIF_FRONTIER_DOT, "ring"),
        ],
    )
    export_png(canvas, output_path, dpi=IMAGE_DPI)
    return {
        "status": "ok",
        "artifact_type": "image/png",
        "png_output_path": str(output_path),
        "width_px": PNG_WIDTH,
        "height_px": PNG_HEIGHT,
        "dpi": IMAGE_DPI,
        "visualization_type": "dynamic_story_png",
        "panel_count": 1,
    }


def _clone_frame(frame: dict[str, Any]) -> dict[str, Any]:
    clone = dict(frame)
    clone["step"] = int(frame.get("step", 0))
    clone["event"] = frame.get("event", "")
    clone["current_cell"] = frame.get("current_cell")
    clone["path"] = [list(cell) for cell in frame.get("path", [])]
    clone["explored_cells"] = [list(cell) for cell in frame.get("explored_cells", [])]
    clone["frontier_cells"] = [list(cell) for cell in frame.get("frontier_cells", [])]
    clone["blocked_cells"] = [list(cell) for cell in frame.get("blocked_cells", [])]
    clone["replan_count"] = int(frame.get("replan_count", 0))
    clone["updated_nodes"] = int(frame.get("updated_nodes", 0))
    clone["affected_cells"] = [list(cell) for cell in frame.get("affected_cells", [])]
    clone["queue_size"] = int(frame.get("queue_size", 0))
    return clone


def _cosine_sample_indices(length: int, target_count: int) -> list[int]:
    if length <= 1:
        return [0]
    indices = []
    for i in range(target_count):
        t = i / max(1, target_count - 1)
        u = 0.5 - 0.5 * math.cos(math.pi * t)
        indices.append(round(u * (length - 1)))
    ordered: list[int] = []
    seen: set[int] = set()
    for index in indices:
        if index not in seen:
            seen.add(index)
            ordered.append(index)
    if ordered[-1] != length - 1:
        ordered.append(length - 1)
    return ordered


def select_static_process_frames(trace: list[dict[str, Any]], panel_count: int = PANEL_COUNT) -> list[dict[str, Any]]:
    titles = ["SEARCH START", "EARLY SEARCH", "MID SEARCH", "LATE SEARCH", "NEAR GOAL", "FINAL PATH"]
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


def _sample_static_gif_frames(trace: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not trace:
        trace = [{"step": 0, "event": "empty", "current_cell": None, "path": [], "explored_cells": [], "frontier_cells": [], "blocked_cells": []}]
    indices = _cosine_sample_indices(len(trace), 28)
    frames = [_clone_frame(trace[index]) for index in indices]
    for frame in frames:
        frame["path"] = []
        frame["duration_ms"] = STATIC_GIF_FRAME_MS
    final = _clone_frame(trace[-1])
    final["duration_ms"] = STATIC_GIF_FRAME_MS
    hold = _clone_frame(trace[-1])
    hold["duration_ms"] = FINAL_HOLD_MS
    frames.extend([final, hold])
    return frames


def _movement_offsets(path: list[list[int]], segment_steps: int, max_samples: int = 5) -> list[int]:
    usable = min(segment_steps, max(0, len(path) - 1))
    if usable <= 0:
        return []
    if usable <= max_samples:
        return list(range(1, usable + 1))
    return sorted({max(1, round(i * usable / max_samples)) for i in range(1, max_samples + 1)})


def _sample_dynamic_gif_frames(map_data: dict[str, Any], algorithm_result: dict[str, Any]) -> list[dict[str, Any]]:
    trace = [_clone_frame(frame) for frame in algorithm_result.get("visualization_trace", [])]
    if not trace:
        return [{"step": 0, "event": "empty", "current_cell": None, "path": [], "explored_cells": [], "frontier_cells": [], "blocked_cells": [], "duration_ms": FINAL_HOLD_MS}]

    updates = sorted(map_data.get("dynamic_updates", []), key=lambda item: int(item.get("step", 0)))
    initial = next((frame for frame in trace if frame.get("event") == "initial_plan"), trace[0])
    before_updates = [frame for frame in trace if frame.get("event") == "before_update"]
    dynamic_updates = [frame for frame in trace if frame.get("event") == "dynamic_update"]
    replans = [frame for frame in trace if frame.get("event") == "replan"]
    final = next((frame for frame in reversed(trace) if frame.get("event") == "final_result"), trace[-1])

    frames: list[dict[str, Any]] = []

    initial_frame = _clone_frame(initial)
    initial_frame["duration_ms"] = DYNAMIC_EVENT_FRAME_MS
    frames.append(initial_frame)

    plan_frame = initial
    previous_step = 0
    for index, update in enumerate(updates):
        update_step = int(update["step"])
        segment_steps = max(0, update_step - previous_step)
        for offset in _movement_offsets(plan_frame.get("path", []), segment_steps):
            move_frame = _clone_frame(plan_frame)
            move_frame["current_cell"] = move_frame["path"][offset]
            move_frame["path"] = move_frame["path"][offset:]
            move_frame["duration_ms"] = DYNAMIC_GIF_FRAME_MS
            frames.append(move_frame)

        if index < len(before_updates):
            before_frame = _clone_frame(before_updates[index])
            before_frame["duration_ms"] = DYNAMIC_EVENT_FRAME_MS
            frames.append(before_frame)
        if index < len(dynamic_updates):
            update_frame = _clone_frame(dynamic_updates[index])
            update_frame["duration_ms"] = DYNAMIC_EVENT_FRAME_MS
            frames.append(update_frame)
        if index < len(replans):
            replan_frame = _clone_frame(replans[index])
            replan_frame["duration_ms"] = DYNAMIC_EVENT_FRAME_MS
            frames.append(replan_frame)
            plan_frame = replans[index]
        previous_step = update_step

    tail_path = plan_frame.get("path", [])
    if tail_path:
        for offset in _movement_offsets(tail_path, len(tail_path) - 1, max_samples=6):
            move_frame = _clone_frame(plan_frame)
            move_frame["current_cell"] = tail_path[offset]
            move_frame["path"] = tail_path[offset:]
            move_frame["duration_ms"] = DYNAMIC_GIF_FRAME_MS
            frames.append(move_frame)

    final_frame = _clone_frame(final)
    final_frame["duration_ms"] = DYNAMIC_EVENT_FRAME_MS
    frames.append(final_frame)
    final_hold = _clone_frame(final)
    final_hold["duration_ms"] = FINAL_HOLD_MS
    frames.append(final_hold)
    return frames


def _sample_lpa_gif_frames(map_data: dict[str, Any], algorithm_result: dict[str, Any]) -> list[dict[str, Any]]:
    trace = [_clone_frame(frame) for frame in algorithm_result.get("visualization_trace", [])]
    if not trace:
        return [{"step": 0, "event": "empty", "current_cell": None, "path": [], "explored_cells": [], "frontier_cells": [], "blocked_cells": [], "affected_cells": [], "queue_size": 0, "duration_ms": FINAL_HOLD_MS}]

    updates = sorted(map_data.get("dynamic_updates", []), key=lambda item: int(item.get("step", 0)))
    initial = next((frame for frame in trace if frame.get("event") == "initial_plan"), trace[0])
    before_updates = [frame for frame in trace if frame.get("event") == "before_update"]
    dynamic_updates = [frame for frame in trace if frame.get("event") == "dynamic_update"]
    replans = [frame for frame in trace if frame.get("event") == "replan"]
    final = next((frame for frame in reversed(trace) if frame.get("event") == "final_result"), trace[-1])
    applied_update_steps = {_safe_int(frame.get("step", 0)) for frame in dynamic_updates}
    final_step = _safe_int(final.get("step", 0))
    if applied_update_steps:
        updates = [update for update in updates if int(update.get("step", 0)) in applied_update_steps]
    else:
        updates = [update for update in updates if int(update.get("step", 0)) <= final_step]

    frames: list[dict[str, Any]] = []
    initial_frame = _clone_frame(initial)
    initial_frame["duration_ms"] = DYNAMIC_EVENT_FRAME_MS
    frames.append(initial_frame)

    plan_frame = initial
    previous_step = 0
    for index, update in enumerate(updates):
        update_step = int(update.get("step", 0))
        segment_steps = max(0, update_step - previous_step)
        for offset in _movement_offsets(plan_frame.get("path", []), segment_steps, max_samples=5):
            move_frame = _clone_frame(plan_frame)
            move_frame["event"] = "move"
            move_frame["step"] = _safe_int(plan_frame.get("step", previous_step)) + offset
            move_frame["current_cell"] = move_frame["path"][offset]
            move_frame["path"] = move_frame["path"][offset:]
            move_frame["duration_ms"] = DYNAMIC_MOVE_FRAME_MS
            frames.append(move_frame)

        if index < len(before_updates):
            before_frame = _clone_frame(before_updates[index])
            before_frame["duration_ms"] = DYNAMIC_EVENT_FRAME_MS
            frames.append(before_frame)
        if index < len(dynamic_updates):
            update_frame = _clone_frame(dynamic_updates[index])
            update_frame["duration_ms"] = DYNAMIC_EVENT_FRAME_MS
            frames.append(update_frame)
        if index < len(replans):
            replan_frame = _clone_frame(replans[index])
            replan_frame["duration_ms"] = DYNAMIC_EVENT_FRAME_MS
            frames.append(replan_frame)
            plan_frame = replans[index]
        previous_step = update_step

    tail_path = plan_frame.get("path", [])
    if tail_path:
        for offset in _movement_offsets(tail_path, len(tail_path) - 1, max_samples=6):
            move_frame = _clone_frame(plan_frame)
            move_frame["event"] = "move"
            move_frame["step"] = _safe_int(plan_frame.get("step", previous_step)) + offset
            move_frame["current_cell"] = tail_path[offset]
            move_frame["path"] = tail_path[offset:]
            move_frame["duration_ms"] = DYNAMIC_MOVE_FRAME_MS
            frames.append(move_frame)

    final_frame = _clone_frame(final)
    final_frame["duration_ms"] = DYNAMIC_EVENT_FRAME_MS
    frames.append(final_frame)
    final_hold = _clone_frame(final)
    final_hold["duration_ms"] = FINAL_HOLD_MS
    frames.append(final_hold)
    return frames


def _sample_lpa_story_gif_frames(map_data: dict[str, Any], algorithm_result: dict[str, Any]) -> list[dict[str, Any]]:
    frames = _sample_lpa_gif_frames(map_data, algorithm_result)
    for frame in frames:
        event = frame.get("event")
        if event == "move":
            frame["duration_ms"] = DYNAMIC_MOVE_FRAME_MS
        elif event in {"dynamic_update", "replan", "final_result", "initial_plan"}:
            frame["duration_ms"] = DYNAMIC_EVENT_FRAME_MS
        else:
            frame["duration_ms"] = DYNAMIC_GIF_FRAME_MS
    return frames


def _draw_story_side_panel(canvas: RasterCanvas, algorithm_result: dict[str, Any], frame: dict[str, Any], x: int, y: int, width: int, height: int) -> None:
    canvas.fill_rect(x, y, x + width, y + height, DYNAMIC_PANEL_FILL)
    canvas.draw_rect_outline(x, y, x + width, y + height, PANEL_BORDER, thickness=2)
    draw_text(canvas, x + 14, y + 18, "PHASE", DYNAMIC_TEXT_MUTED, scale=GIF_LABEL_SCALE)
    draw_text(canvas, x + 14, y + 46, _truncate_text(_frame_phase_label(frame), width - 28, GIF_LABEL_SCALE), BLACK, scale=GIF_LABEL_SCALE)

    lines = [
        f"STEP {_safe_int(frame.get('step', 0))}",
        f"REP {_safe_int(frame.get('replan_count', 0))}",
        f"UPD {_safe_int(frame.get('updated_nodes', 0))}",
        f"AFF {len(frame.get('affected_cells', []))}",
        f"Q {_safe_int(frame.get('queue_size', 0))}",
        f"LEN {_safe_int(algorithm_result.get('path_length', 0))}",
        f"TURN {_safe_int(algorithm_result.get('turn_count', 0))}",
        f"COST {_safe_float(algorithm_result.get('total_cost', 0.0)):.0f}",
    ]
    cursor_y = y + 104
    for line in lines:
        draw_text(canvas, x + 14, cursor_y, line, BLACK, scale=GIF_LABEL_SCALE)
        cursor_y += 32

    note_y = y + height - 118
    canvas.draw_line(x + 14, note_y, x + width - 14, note_y, PANEL_BORDER, thickness=2)
    legend_items = [
        ("EXEC", GIF_EXECUTED_LINE, "line"),
        ("PLAN", PATH_BLUE, "line"),
        ("SEARCH", GIF_SEARCH_DOT, "dot"),
        ("FRONT", GIF_FRONTIER_DOT, "ring"),
        ("AFFECT", GIF_LPA_AFFECTED_FILL, "fill"),
    ]
    row_y = note_y + 18
    for label, color, kind in legend_items:
        icon_x = x + 16
        icon_y = row_y + 6
        if kind == "line":
            canvas.draw_line(icon_x, icon_y, icon_x + 26, icon_y, color, thickness=5)
        elif kind == "dot":
            canvas.draw_circle(icon_x + 13, icon_y, 5, color)
        elif kind == "ring":
            canvas.draw_circle(icon_x + 13, icon_y, 7, WHITE, outline=color, outline_width=2)
        else:
            canvas.fill_rect(icon_x + 4, icon_y - 8, icon_x + 22, icon_y + 8, color)
            canvas.draw_rect_outline(icon_x + 4, icon_y - 8, icon_x + 22, icon_y + 8, LEGEND_BORDER, thickness=1)
        draw_text(canvas, x + 52, row_y, label, BLACK, scale=GIF_LABEL_SCALE)
        row_y += 18


def _draw_lpa_story_gif_frame(map_data: dict[str, Any], algorithm_result: dict[str, Any], frame: dict[str, Any], bundle: dict[str, Any]) -> RasterCanvas:
    canvas = RasterCanvas(GIF_WIDTH, GIF_HEIGHT, background=WHITE)
    draw_header(canvas, algorithm_result, map_data, width=GIF_WIDTH, side_margin=GIF_SIDE_MARGIN, scale=GIF_TITLE_SCALE, suffix="STORY")

    map_left = GIF_SIDE_MARGIN
    map_top = 116
    map_width = 650
    map_height = 690
    panel_left = map_left + map_width + 28
    panel_width = GIF_WIDTH - panel_left - GIF_SIDE_MARGIN

    canvas.fill_rect(map_left, map_top, map_left + map_width, map_top + map_height, DYNAMIC_PANEL_FILL)
    canvas.draw_rect_outline(map_left, map_top, map_left + map_width, map_top + map_height, PANEL_BORDER, thickness=2)
    layout = _layout_in_bounds(map_data, map_left + 28, map_top + 34, map_width - 56, map_height - 68)

    draw_dynamic_maze(canvas, map_data, layout, gif_mode=True)
    frame_blocked = frame.get("blocked_cells", bundle.get("blocked_cells", []))
    final_path_cells = _cell_set(bundle.get("final_path", []))
    if frame.get("event") == "final_result":
        blocked_now = _cell_set(frame_blocked)
        draw_gif_blocked_cells(canvas, layout, _cells_from_set(blocked_now - final_path_cells))
        draw_affected_cells(canvas, layout, _cells_from_set(blocked_now & final_path_cells), GIF_LPA_AFFECTED_FILL, alpha=1.0)
    else:
        draw_gif_blocked_cells(canvas, layout, frame_blocked)
    draw_lpa_gif_search_activity(canvas, layout, frame)

    initial_offset = (-3, -3) if bundle.get("initial_final_same") else (0, 0)
    draw_path_with_style(canvas, layout, bundle.get("initial_path", []), color=(147, 197, 253), thickness=max(3, layout["cell_size"] // 11), dashed=True, offset=initial_offset)
    executed_prefix = _path_prefix(bundle.get("final_path", []), _safe_int(frame.get("step", 0)))
    if frame.get("event") == "final_result":
        draw_path_with_style(canvas, layout, bundle.get("final_path", []), color=GIF_EXECUTED_LINE, thickness=max(4, layout["cell_size"] // 8))
    else:
        draw_path_with_style(canvas, layout, executed_prefix, color=GIF_EXECUTED_LINE, thickness=max(3, layout["cell_size"] // 9))
        for cell in executed_prefix[-8:]:
            draw_cell_dot(canvas, layout, cell, GIF_EXECUTED_LINE, radius=max(2, layout["cell_size"] // 13))
        draw_path_with_style(canvas, layout, frame.get("path", []), color=PATH_BLUE, thickness=max(4, layout["cell_size"] // 7), offset=(3, 3))
    draw_start_goal(canvas, map_data, layout)
    draw_current_cell(canvas, layout, frame.get("current_cell"), color=GIF_EXECUTED_LINE)

    _draw_story_side_panel(canvas, algorithm_result, frame, panel_left, map_top, panel_width, map_height)
    return canvas


def render_lpa_story_gif(map_data: dict[str, Any], algorithm_result: dict[str, Any], output_path: str | Path) -> dict[str, Any]:
    frames = _sample_lpa_story_gif_frames(map_data, algorithm_result)
    bundle = _lpa_story_bundle(algorithm_result)
    gif_frames = [
        {
            "canvas": _draw_lpa_story_gif_frame(map_data, algorithm_result, frame, bundle),
            "duration_ms": int(frame.get("duration_ms", DYNAMIC_GIF_FRAME_MS)),
        }
        for frame in frames
    ]
    export_gif(gif_frames, output_path)
    return {
        "status": "ok",
        "artifact_type": "image/gif",
        "gif_output_path": str(output_path),
        "gif_frame_count": len(gif_frames),
        "frame_duration_ms": DYNAMIC_GIF_FRAME_MS,
        "width_px": GIF_WIDTH,
        "height_px": GIF_HEIGHT,
        "visualization_type": "lpa_story_gif",
    }


def _draw_compact_story_side_panel(
    canvas: RasterCanvas,
    algorithm_result: dict[str, Any],
    frame: dict[str, Any],
    x: int,
    y: int,
    width: int,
    height: int,
    *,
    legend_items: list[tuple[str, tuple[int, int, int], str]],
) -> None:
    canvas.fill_rect(x, y, x + width, y + height, DYNAMIC_PANEL_FILL)
    canvas.draw_rect_outline(x, y, x + width, y + height, PANEL_BORDER, thickness=2)
    draw_text(canvas, x + 14, y + 18, "PHASE", DYNAMIC_TEXT_MUTED, scale=GIF_LABEL_SCALE)
    draw_text(canvas, x + 14, y + 46, _truncate_text(_frame_phase_label(frame), width - 28, GIF_LABEL_SCALE), BLACK, scale=GIF_LABEL_SCALE)
    lines = [
        f"STEP {_safe_int(frame.get('step', 0))}",
        f"LEN {_safe_int(algorithm_result.get('path_length', 0))}",
        f"TURN {_safe_int(algorithm_result.get('turn_count', 0))}",
        f"NODES {_safe_int(algorithm_result.get('explored_nodes', 0))}",
        f"REP {_safe_int(algorithm_result.get('replan_count', 0))}",
        f"COST {_safe_float(algorithm_result.get('total_cost', 0.0)):.0f}",
    ]
    cursor_y = y + 104
    for line in lines:
        draw_text(canvas, x + 14, cursor_y, line, BLACK, scale=GIF_LABEL_SCALE)
        cursor_y += 32

    note_y = y + height - 118
    canvas.draw_line(x + 14, note_y, x + width - 14, note_y, PANEL_BORDER, thickness=2)
    row_y = note_y + 18
    for label, color, kind in legend_items[:5]:
        icon_x = x + 16
        icon_y = row_y + 6
        if kind == "line":
            canvas.draw_line(icon_x, icon_y, icon_x + 26, icon_y, color, thickness=5)
        elif kind == "dot":
            canvas.draw_circle(icon_x + 13, icon_y, 5, color)
        elif kind == "ring":
            canvas.draw_circle(icon_x + 13, icon_y, 7, WHITE, outline=color, outline_width=2)
        else:
            canvas.fill_rect(icon_x + 4, icon_y - 8, icon_x + 22, icon_y + 8, color)
            canvas.draw_rect_outline(icon_x + 4, icon_y - 8, icon_x + 22, icon_y + 8, LEGEND_BORDER, thickness=1)
        draw_text(canvas, x + 52, row_y, label, BLACK, scale=GIF_LABEL_SCALE)
        row_y += 18


def _story_gif_layout() -> tuple[dict[str, int], dict[str, int]]:
    map_bounds = {"left": GIF_SIDE_MARGIN, "top": 116, "width": 650, "height": 690}
    panel_bounds = {
        "left": map_bounds["left"] + map_bounds["width"] + 28,
        "top": map_bounds["top"],
        "width": GIF_WIDTH - (map_bounds["left"] + map_bounds["width"] + 28) - GIF_SIDE_MARGIN,
        "height": map_bounds["height"],
    }
    return map_bounds, panel_bounds


def _draw_static_story_gif_frame(map_data: dict[str, Any], algorithm_result: dict[str, Any], frame: dict[str, Any]) -> RasterCanvas:
    canvas = RasterCanvas(GIF_WIDTH, GIF_HEIGHT, background=WHITE)
    draw_header(canvas, algorithm_result, map_data, width=GIF_WIDTH, side_margin=GIF_SIDE_MARGIN, scale=GIF_TITLE_SCALE, suffix="STORY")
    map_bounds, panel_bounds = _story_gif_layout()
    canvas.fill_rect(map_bounds["left"], map_bounds["top"], map_bounds["left"] + map_bounds["width"], map_bounds["top"] + map_bounds["height"], DYNAMIC_PANEL_FILL)
    canvas.draw_rect_outline(map_bounds["left"], map_bounds["top"], map_bounds["left"] + map_bounds["width"], map_bounds["top"] + map_bounds["height"], PANEL_BORDER, thickness=2)
    layout = _layout_in_bounds(map_data, map_bounds["left"] + 28, map_bounds["top"] + 34, map_bounds["width"] - 56, map_bounds["height"] - 68)

    draw_static_maze(canvas, map_data, layout)
    explored = frame.get("explored_cells", [])
    frontier = frame.get("frontier_cells", [])
    for cell in (explored[-48:] if len(explored) > 48 else explored):
        draw_cell_dot(canvas, layout, cell, GIF_SEARCH_DOT, radius=max(2, layout["cell_size"] // 11))
    for cell in (frontier[-32:] if len(frontier) > 32 else frontier):
        draw_cell_ring(canvas, layout, cell, GIF_FRONTIER_DOT, radius=max(4, layout["cell_size"] // 7), thickness=max(1, layout["cell_size"] // 22))
    if frame.get("path"):
        draw_path_with_style(canvas, layout, frame.get("path", []), color=PATH_BLUE, thickness=max(4, layout["cell_size"] // 7))
    draw_start_goal(canvas, map_data, layout)
    draw_current_cell(canvas, layout, frame.get("current_cell"), color=GIF_FRONTIER_DOT)
    _draw_compact_story_side_panel(
        canvas,
        algorithm_result,
        frame,
        panel_bounds["left"],
        panel_bounds["top"],
        panel_bounds["width"],
        panel_bounds["height"],
        legend_items=[("PATH", PATH_BLUE, "line"), ("SEARCH", GIF_SEARCH_DOT, "dot"), ("FRONT", GIF_FRONTIER_DOT, "ring")],
    )
    return canvas


def render_static_story_gif(map_data: dict[str, Any], algorithm_result: dict[str, Any], output_path: str | Path) -> dict[str, Any]:
    frames = _sample_static_gif_frames(algorithm_result.get("visualization_trace", []))
    gif_frames = [
        {"canvas": _draw_static_story_gif_frame(map_data, algorithm_result, frame), "duration_ms": int(frame.get("duration_ms", STATIC_GIF_FRAME_MS))}
        for frame in frames
    ]
    export_gif(gif_frames, output_path)
    return {
        "status": "ok",
        "artifact_type": "image/gif",
        "gif_output_path": str(output_path),
        "gif_frame_count": len(gif_frames),
        "frame_duration_ms": STATIC_GIF_FRAME_MS,
        "width_px": GIF_WIDTH,
        "height_px": GIF_HEIGHT,
        "visualization_type": "static_story_gif",
    }


def _draw_dynamic_story_gif_frame(
    map_data: dict[str, Any],
    algorithm_result: dict[str, Any],
    frame: dict[str, Any],
    bundle: dict[str, Any],
) -> RasterCanvas:
    canvas = RasterCanvas(GIF_WIDTH, GIF_HEIGHT, background=WHITE)
    draw_header(canvas, algorithm_result, map_data, width=GIF_WIDTH, side_margin=GIF_SIDE_MARGIN, scale=GIF_TITLE_SCALE, suffix="STORY")
    map_bounds, panel_bounds = _story_gif_layout()
    canvas.fill_rect(map_bounds["left"], map_bounds["top"], map_bounds["left"] + map_bounds["width"], map_bounds["top"] + map_bounds["height"], DYNAMIC_PANEL_FILL)
    canvas.draw_rect_outline(map_bounds["left"], map_bounds["top"], map_bounds["left"] + map_bounds["width"], map_bounds["top"] + map_bounds["height"], PANEL_BORDER, thickness=2)
    layout = _layout_in_bounds(map_data, map_bounds["left"] + 28, map_bounds["top"] + 34, map_bounds["width"] - 56, map_bounds["height"] - 68)

    draw_static_maze(canvas, map_data, layout)
    draw_gif_blocked_cells(canvas, layout, frame.get("blocked_cells", []))
    draw_affected_cells(canvas, layout, frame.get("affected_cells", []), GIF_DSTAR_AFFECTED_FILL, alpha=1.0)
    if frame.get("event") == "replan":
        explored = frame.get("explored_cells", [])
        frontier = frame.get("frontier_cells", [])
        for cell in (explored[-42:] if len(explored) > 42 else explored):
            draw_cell_dot(canvas, layout, cell, GIF_SEARCH_DOT, radius=max(2, layout["cell_size"] // 11))
        for cell in (frontier[-28:] if len(frontier) > 28 else frontier):
            draw_cell_ring(canvas, layout, cell, GIF_FRONTIER_DOT, radius=max(4, layout["cell_size"] // 7), thickness=max(1, layout["cell_size"] // 22))
    executed_prefix = _path_prefix(bundle.get("final_path", []), _safe_int(frame.get("step", 0)))
    draw_path_with_style(canvas, layout, executed_prefix, color=GIF_EXECUTED_LINE, thickness=max(3, layout["cell_size"] // 9))
    if frame.get("event") == "final_result":
        draw_path_with_style(canvas, layout, bundle.get("final_path", []), color=GIF_EXECUTED_LINE, thickness=max(4, layout["cell_size"] // 8))
    else:
        draw_path_with_style(canvas, layout, frame.get("path", []), color=PATH_BLUE, thickness=max(4, layout["cell_size"] // 7), offset=(3, 3))
    draw_start_goal(canvas, map_data, layout)
    draw_current_cell(canvas, layout, frame.get("current_cell"), color=GIF_EXECUTED_LINE)
    _draw_compact_story_side_panel(
        canvas,
        algorithm_result,
        frame,
        panel_bounds["left"],
        panel_bounds["top"],
        panel_bounds["width"],
        panel_bounds["height"],
        legend_items=[
            ("EXEC", GIF_EXECUTED_LINE, "line"),
            ("PLAN", PATH_BLUE, "line"),
            ("SEARCH", GIF_SEARCH_DOT, "dot"),
            ("FRONT", GIF_FRONTIER_DOT, "ring"),
            ("AFFECT", GIF_DSTAR_AFFECTED_FILL, "fill"),
        ],
    )
    return canvas


def render_dynamic_story_gif(map_data: dict[str, Any], algorithm_result: dict[str, Any], output_path: str | Path) -> dict[str, Any]:
    frames = _sample_dynamic_gif_frames(map_data, algorithm_result)
    bundle = _lpa_story_bundle(algorithm_result)
    gif_frames = [
        {"canvas": _draw_dynamic_story_gif_frame(map_data, algorithm_result, frame, bundle), "duration_ms": int(frame.get("duration_ms", DYNAMIC_GIF_FRAME_MS))}
        for frame in frames
    ]
    export_gif(gif_frames, output_path)
    return {
        "status": "ok",
        "artifact_type": "image/gif",
        "gif_output_path": str(output_path),
        "gif_frame_count": len(gif_frames),
        "frame_duration_ms": DYNAMIC_GIF_FRAME_MS,
        "width_px": GIF_WIDTH,
        "height_px": GIF_HEIGHT,
        "visualization_type": "dynamic_story_gif",
    }


def render_process_png(map_data: dict[str, Any], algorithm_result: dict[str, Any], output_path: str | Path) -> dict[str, Any]:
    status = algorithm_result.get("status", "ok")
    if status != "ok":
        return {"status": status, "artifact_type": "image/png", "png_output_path": None, "visualization_type": "none", "panel_count": 0}

    algorithm = str(algorithm_result.get("algorithm", ""))
    if algorithm in {"BFS", "DFS", "A*", "Cost-aware A*", "Weighted A*"}:
        return render_static_story_png(map_data, algorithm_result, output_path)
    elif algorithm == "LPA*":
        return render_lpa_story_png(map_data, algorithm_result, output_path)
    elif algorithm == "D* Lite":
        return render_dynamic_story_png(map_data, algorithm_result, output_path)
    else:
        return {"status": "not_implemented", "artifact_type": "image/png", "png_output_path": None, "visualization_type": "none", "panel_count": 0}


def render_process_gif(map_data: dict[str, Any], algorithm_result: dict[str, Any], output_path: str | Path) -> dict[str, Any]:
    status = algorithm_result.get("status", "ok")
    if status != "ok":
        return {"status": status, "artifact_type": "image/gif", "gif_output_path": None, "visualization_type": "none", "gif_frame_count": 0}

    algorithm = str(algorithm_result.get("algorithm", ""))
    if algorithm in {"BFS", "DFS", "A*", "Cost-aware A*", "Weighted A*"}:
        return render_static_story_gif(map_data, algorithm_result, output_path)
    elif algorithm == "LPA*":
        return render_lpa_story_gif(map_data, algorithm_result, output_path)
    elif algorithm == "D* Lite":
        return render_dynamic_story_gif(map_data, algorithm_result, output_path)
    else:
        return {"status": "not_implemented", "artifact_type": "image/gif", "gif_output_path": None, "visualization_type": "none", "gif_frame_count": 0}


def visualize_result(map_data: dict[str, Any], algorithm_result: dict[str, Any], output_path: str | Path | None = None, mode: str = "text") -> dict[str, Any]:
    if mode == "image":
        if output_path is None:
            raise ValueError("output_path is required for image mode")
        png_path = Path(output_path)
        gif_path = png_path.with_suffix(".gif")
        png_artifact = render_process_png(map_data, algorithm_result, png_path)
        gif_artifact = render_process_gif(map_data, algorithm_result, gif_path)
        return {
            "status": gif_artifact.get("status", png_artifact.get("status", "ok")),
            "mode": "image",
            "artifact_type": "image_bundle",
            "png_output_path": png_artifact.get("png_output_path"),
            "gif_output_path": gif_artifact.get("gif_output_path"),
            "gif_frame_count": gif_artifact.get("gif_frame_count", 0),
            "frame_duration_ms": gif_artifact.get("frame_duration_ms"),
            "png_width_px": png_artifact.get("width_px"),
            "png_height_px": png_artifact.get("height_px"),
            "gif_width_px": gif_artifact.get("width_px"),
            "gif_height_px": gif_artifact.get("height_px"),
            "dpi": png_artifact.get("dpi", IMAGE_DPI),
            "visualization_type": gif_artifact.get("visualization_type") or png_artifact.get("visualization_type", "none"),
            "panel_count": png_artifact.get("panel_count", 0),
        }

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


def write_visualization_manifest(artifacts: dict[str, dict[str, Any]], output_path: str | Path) -> None:
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(artifacts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
