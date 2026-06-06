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

GIF_EXPLORED_FILL = (254, 240, 138)
GIF_FRONTIER_FILL = (253, 186, 116)
GIF_BLOCKED_FILL = (148, 163, 184)
GIF_LPA_AFFECTED_FILL = (165, 243, 252)
GIF_DSTAR_AFFECTED_FILL = (221, 214, 254)

IMAGE_DPI = 300
PNG_WIDTH = 1800
PNG_HEIGHT = 1800
GIF_WIDTH = 960
GIF_HEIGHT = 960

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

GIF_SIDE_MARGIN = 56
GIF_TOP_MARGIN = 84
GIF_BOTTOM_MARGIN = 110
GIF_TITLE_SCALE = 3
GIF_LABEL_SCALE = 2

STATIC_GIF_FRAME_MS = 1000
DYNAMIC_GIF_FRAME_MS = 1000
DYNAMIC_EVENT_FRAME_MS = 1000
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


def _process_panel_bounds(index: int) -> dict[str, int]:
    grid_width = PNG_WIDTH - 2 * SIDE_MARGIN
    grid_height = PNG_HEIGHT - TOP_MARGIN - BOTTOM_MARGIN
    panel_width = (grid_width - GRID_GAP_X * (PANEL_COLUMNS - 1)) // PANEL_COLUMNS
    panel_height = (grid_height - GRID_GAP_Y * (PANEL_ROWS - 1)) // PANEL_ROWS
    col = index % PANEL_COLUMNS
    row = index // PANEL_COLUMNS
    left = SIDE_MARGIN + col * (panel_width + GRID_GAP_X)
    top = TOP_MARGIN + row * (panel_height + GRID_GAP_Y)
    return {"left": left, "top": top, "width": panel_width, "height": panel_height}


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


def draw_explored_nodes(canvas: RasterCanvas, layout: dict[str, int], explored_cells: list[list[int]]) -> None:
    _fill_cells(canvas, layout, explored_cells, EXPLORED_YELLOW, alpha=0.42)


def draw_frontier_cells(canvas: RasterCanvas, layout: dict[str, int], frontier_cells: list[list[int]]) -> None:
    _fill_cells(canvas, layout, frontier_cells, FRONTIER_ORANGE, alpha=0.32, inset_ratio=8)


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


def draw_gif_explored_nodes(canvas: RasterCanvas, layout: dict[str, int], explored_cells: list[list[int]]) -> None:
    _fill_cells(canvas, layout, explored_cells, GIF_EXPLORED_FILL, alpha=1.0)


def draw_gif_frontier_cells(canvas: RasterCanvas, layout: dict[str, int], frontier_cells: list[list[int]]) -> None:
    _fill_cells(canvas, layout, frontier_cells, GIF_FRONTIER_FILL, alpha=1.0, inset_ratio=8)


def draw_gif_blocked_cells(canvas: RasterCanvas, layout: dict[str, int], blocked_cells: list[list[int]]) -> None:
    _fill_cells(canvas, layout, blocked_cells, GIF_BLOCKED_FILL, alpha=1.0, inset_ratio=7)


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


def draw_panel_title(canvas: RasterCanvas, bounds: dict[str, int], title: str) -> None:
    title = _truncate_text(title.upper(), bounds["width"] - 2 * PANEL_INSET, SMALL_SCALE)
    draw_text(canvas, bounds["left"] + PANEL_INSET, bounds["top"] + 10, title, BLACK, scale=SMALL_SCALE)


def draw_process_legend(
    canvas: RasterCanvas,
    visualization_type: str,
    *,
    width: int,
    height: int,
    side_margin: int,
    algorithm: str = "",
) -> None:
    legend_y = height - 120 if height > 1000 else height - 76
    box_size = 24 if height > 1000 else 18
    label_scale = LABEL_SCALE if height > 1000 else GIF_LABEL_SCALE
    x = side_margin

    if visualization_type == "static_process_grid":
        items: list[tuple[str, tuple[int, int, int], str]] = [
            ("START", START_GREEN, "circle"),
            ("GOAL", GOAL_RED, "outline"),
            ("EXPLORED", EXPLORED_YELLOW if height > 1000 else GIF_EXPLORED_FILL, "fill"),
            ("FRONTIER", FRONTIER_ORANGE if height > 1000 else GIF_FRONTIER_FILL, "fill"),
            ("CURRENT", CURRENT_ORANGE, "circle"),
            ("PATH", PATH_BLUE, "line"),
        ]
    else:
        affected_color = (
            DSTAR_AFFECTED_VIOLET
            if algorithm == "D* Lite" and height > 1000
            else GIF_DSTAR_AFFECTED_FILL
            if algorithm == "D* Lite"
            else LPA_AFFECTED_CYAN
            if height > 1000
            else GIF_LPA_AFFECTED_FILL
        )
        items = [
            ("START", START_GREEN, "circle"),
            ("GOAL", GOAL_RED, "outline"),
            ("BLOCKED", BLOCKED_GRAY if height > 1000 else GIF_BLOCKED_FILL, "fill"),
            ("AFFECTED", affected_color, "fill"),
            ("CURRENT", CURRENT_ORANGE, "circle"),
            ("PATH", PATH_BLUE, "line"),
        ]

    spacing = 185 if height > 1000 else 145
    for label, color, kind in items:
        if kind == "circle":
            canvas.draw_circle(x + box_size // 2, legend_y + box_size // 2, box_size // 2, color, outline=BLACK, outline_width=2)
        elif kind == "outline":
            canvas.draw_rect_outline(x, legend_y, x + box_size, legend_y + box_size, color, thickness=3)
        elif kind == "line":
            canvas.draw_line(x, legend_y + box_size // 2, x + box_size, legend_y + box_size // 2, color, thickness=5 if height < 1000 else 6)
        else:
            canvas.fill_rect(x, legend_y, x + box_size, legend_y + box_size, color, alpha=1.0 if height < 1000 else 0.6)
            canvas.draw_rect_outline(x, legend_y, x + box_size, legend_y + box_size, LEGEND_BORDER, thickness=1)
        draw_text(canvas, x + box_size + 8, legend_y + 4, label, BLACK, scale=label_scale)
        x += spacing


def draw_metric_box(canvas: RasterCanvas, lines: list[str], *, width: int) -> None:
    if not lines:
        return
    scale = GIF_LABEL_SCALE
    line_height = 10 * scale
    box_width = max(_text_width(line, scale) for line in lines) + 24
    box_height = len(lines) * line_height + 18
    x1 = width - GIF_SIDE_MARGIN
    x0 = x1 - box_width
    y0 = 28
    y1 = y0 + box_height
    canvas.fill_rect(x0, y0, x1, y1, METRIC_BOX)
    canvas.draw_rect_outline(x0, y0, x1, y1, LEGEND_BORDER, thickness=2)
    for index, line in enumerate(lines):
        draw_text(canvas, x0 + 10, y0 + 8 + index * line_height, line, BLACK, scale=scale)


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


def select_dynamic_process_frames(trace: list[dict[str, Any]], panel_count: int = PANEL_COUNT) -> list[dict[str, Any]]:
    del panel_count
    titles = ["INITIAL PLAN", "BEFORE UPDATE", "REPLAN 1", "REPLAN 2", "REPLAN 3", "FINAL RESULT"]
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


def select_lpa_process_frames(trace: list[dict[str, Any]], panel_count: int = PANEL_COUNT) -> list[dict[str, Any]]:
    del panel_count
    titles = ["INITIAL PLAN", "UPDATE 1", "REPAIR 1", "UPDATE 2", "REPAIR 2", "FINAL RESULT"]
    if not trace:
        trace = [{"step": 0, "event": "empty", "current_cell": None, "path": [], "explored_cells": [], "frontier_cells": [], "blocked_cells": [], "affected_cells": [], "queue_size": 0}]

    initial = next((frame for frame in trace if frame.get("event") == "initial_plan"), trace[0])
    updates = [frame for frame in trace if frame.get("event") == "dynamic_update"]
    replans = [frame for frame in trace if frame.get("event") == "replan"]
    final = next((frame for frame in reversed(trace) if frame.get("event") == "final_result"), trace[-1])

    selected = [_clone_frame(initial)]
    last_frame = _clone_frame(initial)
    sequence: list[dict[str, Any]] = []
    for index in range(2):
        if index < len(updates):
            sequence.append(_clone_frame(updates[index]))
        elif sequence:
            sequence.append(_clone_frame(sequence[-1]))
        else:
            sequence.append(_clone_frame(last_frame))
        if index < len(replans):
            sequence.append(_clone_frame(replans[index]))
            last_frame = _clone_frame(replans[index])
        else:
            sequence.append(_clone_frame(last_frame))
    selected.extend(sequence[:4])
    selected.append(_clone_frame(final))

    while len(selected) < len(titles):
        selected.insert(-1, _clone_frame(selected[-2]))
    for index, frame in enumerate(selected[: len(titles)]):
        frame["panel_title"] = titles[index]
    return selected[: len(titles)]


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

    frames: list[dict[str, Any]] = []
    initial_frame = _clone_frame(initial)
    initial_frame["duration_ms"] = DYNAMIC_EVENT_FRAME_MS
    frames.append(initial_frame)

    for index, _update in enumerate(updates):
        if index < len(before_updates):
            before_frame = _clone_frame(before_updates[index])
            before_frame["duration_ms"] = DYNAMIC_GIF_FRAME_MS
            frames.append(before_frame)
        if index < len(dynamic_updates):
            update_frame = _clone_frame(dynamic_updates[index])
            update_frame["duration_ms"] = DYNAMIC_EVENT_FRAME_MS
            frames.append(update_frame)
        if index < len(replans):
            replan_frame = _clone_frame(replans[index])
            replan_frame["duration_ms"] = DYNAMIC_EVENT_FRAME_MS
            frames.append(replan_frame)

    final_frame = _clone_frame(final)
    final_frame["duration_ms"] = DYNAMIC_EVENT_FRAME_MS
    frames.append(final_frame)
    final_hold = _clone_frame(final)
    final_hold["duration_ms"] = FINAL_HOLD_MS
    frames.append(final_hold)
    return frames


def render_process_grid(
    canvas: RasterCanvas,
    map_data: dict[str, Any],
    frames: list[dict[str, Any]],
    *,
    static_mode: bool,
    algorithm: str,
) -> None:
    for index, frame in enumerate(frames):
        bounds = _process_panel_bounds(index)
        canvas.draw_rect_outline(bounds["left"], bounds["top"], bounds["left"] + bounds["width"], bounds["top"] + bounds["height"], PANEL_BORDER, thickness=2)
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
            if algorithm == "LPA*":
                draw_affected_cells(canvas, layout, frame.get("affected_cells", []), LPA_AFFECTED_CYAN, alpha=0.48)
            elif algorithm == "D* Lite":
                draw_affected_cells(canvas, layout, frame.get("affected_cells", []), DSTAR_AFFECTED_VIOLET, alpha=0.48)
            draw_path(canvas, layout, frame.get("path", []))
        draw_start_goal(canvas, map_data, layout)
        draw_current_cell(canvas, layout, frame.get("current_cell"))


def _draw_gif_frame(map_data: dict[str, Any], algorithm_result: dict[str, Any], frame: dict[str, Any], *, static_mode: bool) -> RasterCanvas:
    canvas = RasterCanvas(GIF_WIDTH, GIF_HEIGHT, background=WHITE)
    algorithm = str(algorithm_result.get("algorithm", ""))
    draw_header(canvas, algorithm_result, map_data, width=GIF_WIDTH, side_margin=GIF_SIDE_MARGIN, scale=GIF_TITLE_SCALE, suffix="GIF")

    event_label = f"{frame.get('event', '').replace('_', ' ')} STEP {frame.get('step', 0)}".strip().upper()
    event_label = _truncate_text(event_label, GIF_WIDTH - 2 * GIF_SIDE_MARGIN - 240, GIF_LABEL_SCALE)
    draw_text(canvas, GIF_SIDE_MARGIN, 62, event_label, BLACK, scale=GIF_LABEL_SCALE)

    layout = _layout_in_bounds(
        map_data,
        GIF_SIDE_MARGIN,
        GIF_TOP_MARGIN,
        GIF_WIDTH - 2 * GIF_SIDE_MARGIN,
        GIF_HEIGHT - GIF_TOP_MARGIN - GIF_BOTTOM_MARGIN,
    )
    draw_static_maze(canvas, map_data, layout)
    if static_mode:
        draw_gif_explored_nodes(canvas, layout, frame.get("explored_cells", []))
        draw_gif_frontier_cells(canvas, layout, frame.get("frontier_cells", []))
        if frame.get("path"):
            draw_path(canvas, layout, frame.get("path", []))
        metric_lines = [
            f"STEP {int(frame.get('step', 0))}",
            f"EXP {len(frame.get('explored_cells', []))}",
            f"FRONT {len(frame.get('frontier_cells', []))}",
        ]
    else:
        draw_gif_blocked_cells(canvas, layout, frame.get("blocked_cells", []))
        if algorithm == "LPA*":
            draw_affected_cells(canvas, layout, frame.get("affected_cells", []), GIF_LPA_AFFECTED_FILL, alpha=1.0)
        elif algorithm == "D* Lite":
            draw_affected_cells(canvas, layout, frame.get("affected_cells", []), GIF_DSTAR_AFFECTED_FILL, alpha=1.0)
        draw_path(canvas, layout, frame.get("path", []))
        if algorithm == "LPA*":
            metric_lines = [
                f"STEP {int(frame.get('step', 0))}",
                f"UPDATED {int(frame.get('updated_nodes', 0))}",
                f"QUEUE {int(frame.get('queue_size', 0))}",
                f"REPLAN {int(frame.get('replan_count', 0))}",
            ]
        else:
            current_cell = frame.get("current_cell")
            pos_text = "--,--" if current_cell is None else f"{int(current_cell[0])},{int(current_cell[1])}"
            metric_lines = [
                f"STEP {int(frame.get('step', 0))}",
                f"UPDATED {int(frame.get('updated_nodes', 0))}",
                f"POS {pos_text}",
                f"REPLAN {int(frame.get('replan_count', 0))}",
            ]
    draw_start_goal(canvas, map_data, layout)
    draw_current_cell(canvas, layout, frame.get("current_cell"))
    draw_metric_box(canvas, metric_lines, width=GIF_WIDTH)
    draw_process_legend(
        canvas,
        "static_process_grid" if static_mode else "dynamic_process_grid",
        width=GIF_WIDTH,
        height=GIF_HEIGHT,
        side_margin=GIF_SIDE_MARGIN,
        algorithm=algorithm,
    )
    return canvas


def render_process_png(map_data: dict[str, Any], algorithm_result: dict[str, Any], output_path: str | Path) -> dict[str, Any]:
    status = algorithm_result.get("status", "ok")
    if status != "ok":
        return {"status": status, "artifact_type": "image/png", "png_output_path": None, "visualization_type": "none", "panel_count": 0}

    algorithm = str(algorithm_result.get("algorithm", ""))
    trace = algorithm_result.get("visualization_trace", [])
    if algorithm in {"BFS", "DFS", "A*", "Cost-aware A*", "Weighted A*"}:
        frames = select_static_process_frames(trace, panel_count=PANEL_COUNT)
        visualization_type = "static_process_grid"
        static_mode = True
    elif algorithm == "LPA*":
        frames = select_lpa_process_frames(trace, panel_count=PANEL_COUNT)
        visualization_type = "dynamic_process_grid"
        static_mode = False
    elif algorithm == "D* Lite":
        frames = select_dynamic_process_frames(trace, panel_count=PANEL_COUNT)
        visualization_type = "dynamic_process_grid"
        static_mode = False
    else:
        return {"status": "not_implemented", "artifact_type": "image/png", "png_output_path": None, "visualization_type": "none", "panel_count": 0}

    canvas = RasterCanvas(PNG_WIDTH, PNG_HEIGHT, background=WHITE)
    draw_header(canvas, algorithm_result, map_data, width=PNG_WIDTH, side_margin=SIDE_MARGIN, scale=TITLE_SCALE, suffix="PROCESS")
    render_process_grid(canvas, map_data, frames, static_mode=static_mode, algorithm=algorithm)
    draw_process_legend(
        canvas,
        visualization_type,
        width=PNG_WIDTH,
        height=PNG_HEIGHT,
        side_margin=SIDE_MARGIN,
        algorithm=algorithm,
    )
    export_png(canvas, output_path, dpi=IMAGE_DPI)

    return {
        "status": "ok",
        "artifact_type": "image/png",
        "png_output_path": str(output_path),
        "width_px": PNG_WIDTH,
        "height_px": PNG_HEIGHT,
        "dpi": IMAGE_DPI,
        "visualization_type": visualization_type,
        "panel_count": PANEL_COUNT,
    }


def render_process_gif(map_data: dict[str, Any], algorithm_result: dict[str, Any], output_path: str | Path) -> dict[str, Any]:
    status = algorithm_result.get("status", "ok")
    if status != "ok":
        return {"status": status, "artifact_type": "image/gif", "gif_output_path": None, "visualization_type": "none", "gif_frame_count": 0}

    algorithm = str(algorithm_result.get("algorithm", ""))
    if algorithm in {"BFS", "DFS", "A*", "Cost-aware A*", "Weighted A*"}:
        frames = _sample_static_gif_frames(algorithm_result.get("visualization_trace", []))
        visualization_type = "static_process_gif"
        static_mode = True
        frame_duration_ms = STATIC_GIF_FRAME_MS
    elif algorithm == "LPA*":
        frames = _sample_lpa_gif_frames(map_data, algorithm_result)
        visualization_type = "dynamic_process_gif"
        static_mode = False
        frame_duration_ms = DYNAMIC_GIF_FRAME_MS
    elif algorithm == "D* Lite":
        frames = _sample_dynamic_gif_frames(map_data, algorithm_result)
        visualization_type = "dynamic_process_gif"
        static_mode = False
        frame_duration_ms = DYNAMIC_GIF_FRAME_MS
    else:
        return {"status": "not_implemented", "artifact_type": "image/gif", "gif_output_path": None, "visualization_type": "none", "gif_frame_count": 0}

    gif_frames = [{"canvas": _draw_gif_frame(map_data, algorithm_result, frame, static_mode=static_mode), "duration_ms": int(frame.get("duration_ms", frame_duration_ms))} for frame in frames]
    export_gif(gif_frames, output_path)
    return {
        "status": "ok",
        "artifact_type": "image/gif",
        "gif_output_path": str(output_path),
        "gif_frame_count": len(gif_frames),
        "frame_duration_ms": frame_duration_ms,
        "width_px": GIF_WIDTH,
        "height_px": GIF_HEIGHT,
        "visualization_type": visualization_type,
    }


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
