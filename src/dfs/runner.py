"""DFS implementation for maze pathfinding."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from scripts.load_map import get_neighbors, is_goal, load_map


def run_dfs(map_input: str | Path | dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    del kwargs
    map_data = load_map(map_input) if isinstance(map_input, (str, Path)) else map_input

    start = map_data["start"]
    start_time = time.perf_counter()

    stack: list[tuple[int, int, list[list[int]]]] = [(start[0], start[1], [start])]
    visited = {(start[0], start[1])}
    explored_nodes = 0
    explored_cells: list[list[int]] = []
    path: list[list[int]] = []
    visualization_trace: list[dict[str, Any]] = []
    step = 0

    while stack:
        x, y, current_path = stack.pop()
        explored_nodes += 1
        explored_cells.append([x, y])

        if is_goal(map_data, x, y):
            path = current_path
            break

        neighbors = get_neighbors(map_data, x, y)
        for nx, ny in reversed(neighbors):
            if (nx, ny) in visited:
                continue
            visited.add((nx, ny))
            stack.append((nx, ny, current_path + [[nx, ny]]))

        visualization_trace.append(
            {
                "step": step,
                "event": "expand",
                "current_cell": [x, y],
                "path": current_path,
                "explored_cells": [cell[:] for cell in explored_cells],
                "frontier_cells": [[state_x, state_y] for state_x, state_y, _ in stack],
                "blocked_cells": [],
            }
        )
        step += 1

    runtime_ms = (time.perf_counter() - start_time) * 1000.0
    success = bool(path)
    path_length = len(path) - 1 if success else -1

    turn_count = 0
    if success and len(path) > 2:
        for i in range(1, len(path) - 1):
            prev = path[i - 1]
            curr = path[i]
            next_ = path[i + 1]
            d_in = (curr[0] - prev[0], curr[1] - prev[1])
            d_out = (next_[0] - curr[0], next_[1] - curr[1])
            if d_in == d_out:
                continue
            if d_in[0] * d_out[0] + d_in[1] * d_out[1] == -1:
                turn_count += 2
            else:
                turn_count += 1

    visualization_trace.append(
        {
            "step": step,
            "event": "result",
            "current_cell": path[-1] if success else None,
            "path": path if success else [],
            "explored_cells": [cell[:] for cell in explored_cells],
            "frontier_cells": [],
            "blocked_cells": [],
        }
    )

    return {
        "maze_id": map_data["maze_id"],
        "algorithm": "DFS",
        "status": "ok",
        "success": success,
        "path": path,
        "path_length": path_length,
        "turn_count": turn_count,
        "risk_cost": 0,
        "narrow_cost": 0,
        "explored_nodes": explored_nodes,
        "explored_cells": explored_cells,
        "runtime_ms": runtime_ms,
        "total_cost": path_length + turn_count if success else -1,
        "replan_count": 0,
        "replan_time_ms": 0.0,
        "updated_nodes": 0,
        "replanned_path_length": -1,
        "visualization_trace": visualization_trace,
    }
