"""A* implementation for maze pathfinding."""

from __future__ import annotations

import heapq
import time
from pathlib import Path
from typing import Any

from scripts.load_map import get_neighbors, is_goal, load_map


def _reconstruct_path(
    parent: dict[tuple[int, int], tuple[int, int] | None],
    state: tuple[int, int],
) -> list[list[int]]:
    path: list[list[int]] = []
    current: tuple[int, int] | None = state
    while current is not None:
        path.insert(0, [current[0], current[1]])
        current = parent.get(current)
    return path


def run_a_star(map_input: str | Path | dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    del kwargs
    map_data = load_map(map_input) if isinstance(map_input, (str, Path)) else map_input

    start = map_data["start"]
    goals = map_data.get("goal_cells", [map_data["goal"]])

    def heuristic(x: int, y: int) -> float:
        return min(abs(x - goal[0]) + abs(y - goal[1]) for goal in goals)

    start_time = time.perf_counter()

    start_state = (start[0], start[1])
    g_score = {start_state: 0}
    parent = {start_state: None}
    open_set = [(heuristic(start[0], start[1]), start[0], start[1])]
    closed_set: set[tuple[int, int]] = set()
    explored_nodes = 0
    explored_cells: list[list[int]] = []
    goal_pos: tuple[int, int] | None = None
    visualization_trace: list[dict[str, Any]] = []
    step = 0

    while open_set:
        _, x, y = heapq.heappop(open_set)
        state = (x, y)
        if state in closed_set:
            continue

        closed_set.add(state)
        explored_nodes += 1
        explored_cells.append([x, y])

        if is_goal(map_data, x, y):
            goal_pos = state
            break

        for nx, ny in get_neighbors(map_data, x, y):
            neighbor = (nx, ny)
            if neighbor in closed_set:
                continue

            tentative_g = g_score[state] + 1
            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                parent[neighbor] = state
                g_score[neighbor] = tentative_g
                heapq.heappush(open_set, (tentative_g + heuristic(nx, ny), nx, ny))

        frontier_cells = sorted(
            {
                (open_x, open_y)
                for _, open_x, open_y in open_set
                if (open_x, open_y) not in closed_set
            },
            key=lambda cell: (cell[1], cell[0]),
        )
        visualization_trace.append(
            {
                "step": step,
                "event": "expand",
                "current_cell": [x, y],
                "path": _reconstruct_path(parent, state),
                "explored_cells": [cell[:] for cell in explored_cells],
                "frontier_cells": [[cell_x, cell_y] for cell_x, cell_y in frontier_cells],
                "blocked_cells": [],
            }
        )
        step += 1

    runtime_ms = (time.perf_counter() - start_time) * 1000.0

    path: list[list[int]] = []
    if goal_pos is not None:
        path = _reconstruct_path(parent, goal_pos)

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
        "algorithm": "A*",
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
