"""BFS implementation for maze pathfinding."""

from __future__ import annotations

import time
from collections import deque
from pathlib import Path
from typing import Any

from scripts.load_map import load_map, is_goal, get_neighbors


def run_bfs(map_input: str | Path | dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    del kwargs
    map_data = load_map(map_input) if isinstance(map_input, (str, Path)) else map_input

    start = map_data["start"]
    width = map_data["width"]
    height = map_data["height"]

    start_time = time.perf_counter()

    queue = deque([(start[0], start[1], [start])])
    visited = {(start[0], start[1])}
    explored_nodes = 0
    path = []

    while queue:
        x, y, current_path = queue.popleft()
        explored_nodes += 1

        if is_goal(map_data, x, y):
            path = current_path
            break

        neighbors = get_neighbors(map_data, x, y)
        for nx, ny in neighbors:
            if (nx, ny) not in visited:
                visited.add((nx, ny))
                queue.append((nx, ny, current_path + [[nx, ny]]))

    runtime_ms = (time.perf_counter() - start_time) * 1000

    success = len(path) > 0
    path_length = len(path) - 1 if success else -1

    turn_count = 0
    if success and len(path) > 2:
        for i in range(1, len(path) - 1):
            prev = path[i - 1]
            curr = path[i]
            next_ = path[i + 1]

            d_in = (curr[0] - prev[0], curr[1] - prev[1])
            d_out = (next_[0] - curr[0], next_[1] - curr[1])

            if d_in != d_out:
                if d_in[0] * d_out[0] + d_in[1] * d_out[1] == -1:
                    turn_count += 2
                else:
                    turn_count += 1

    return {
        "maze_id": map_data["maze_id"],
        "algorithm": "BFS",
        "status": "ok",
        "success": success,
        "path": path,
        "path_length": path_length,
        "turn_count": turn_count,
        "risk_cost": 0,
        "narrow_cost": 0,
        "explored_nodes": explored_nodes,
        "runtime_ms": runtime_ms,
        "total_cost": path_length + turn_count if success else -1,
        "replan_count": 0,
        "replan_time_ms": 0.0,
        "updated_nodes": 0,
        "replanned_path_length": -1,
    }
