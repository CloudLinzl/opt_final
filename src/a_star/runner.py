"""A* implementation for maze pathfinding."""

from __future__ import annotations

import heapq
import time
from pathlib import Path
from typing import Any

from scripts.load_map import load_map, is_goal, get_neighbors


def run_a_star(map_input: str | Path | dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    del kwargs
    map_data = load_map(map_input) if isinstance(map_input, (str, Path)) else map_input

    start = map_data["start"]
    goal = map_data["goal"]
    width = map_data["width"]
    height = map_data["height"]

    def heuristic(x: int, y: int) -> float:
        return abs(x - goal[0]) + abs(y - goal[1])

    start_time = time.perf_counter()

    g_score = {(start[0], start[1]): 0}
    f_score = {(start[0], start[1]): heuristic(start[0], start[1])}
    parent = {(start[0], start[1]): None}
    open_set = [(f_score[(start[0], start[1])], start[0], start[1])]
    open_dict = {(start[0], start[1]): True}
    closed_set = set()
    explored_nodes = 0

    goal_pos = None

    while open_set:
        _, x, y = heapq.heappop(open_set)
        open_dict.pop((x, y), None)

        if (x, y) in closed_set:
            continue

        closed_set.add((x, y))
        explored_nodes += 1

        if is_goal(map_data, x, y):
            goal_pos = (x, y)
            break

        neighbors = get_neighbors(map_data, x, y)
        for nx, ny in neighbors:
            if (nx, ny) in closed_set:
                continue

            tentative_g = g_score[(x, y)] + 1

            if (nx, ny) not in g_score or tentative_g < g_score[(nx, ny)]:
                parent[(nx, ny)] = (x, y)
                g_score[(nx, ny)] = tentative_g
                f_score[(nx, ny)] = tentative_g + heuristic(nx, ny)

                if (nx, ny) not in open_dict:
                    heapq.heappush(open_set, (f_score[(nx, ny)], nx, ny))
                    open_dict[(nx, ny)] = True

    runtime_ms = (time.perf_counter() - start_time) * 1000

    path = []
    if goal_pos is not None:
        current = goal_pos
        while current is not None:
            path.insert(0, list(current))
            current = parent.get(current)

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
        "algorithm": "A*",
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
