"""Directional A* variants for multi-cost maze pathfinding."""

from __future__ import annotations

import heapq
import time
from pathlib import Path
from typing import Any

from scripts.load_map import get_neighbors, is_goal, load_map


def _reconstruct_path(
    parent: dict[
        tuple[int, int, int | None, int | None],
        tuple[int, int, int | None, int | None] | None,
    ],
    state: tuple[int, int, int | None, int | None],
) -> list[list[int]]:
    path: list[list[int]] = []
    current: tuple[int, int, int | None, int | None] | None = state
    while current is not None:
        path.insert(0, [current[0], current[1]])
        current = parent.get(current)
    return path


def _load_cost_weights(kwargs: dict[str, Any]) -> tuple[float, float, float, float]:
    cost_weights = kwargs.get("cost_weights", {})
    p1 = float(kwargs.get("p1", cost_weights.get("p1", 1.0)))
    p2 = float(kwargs.get("p2", cost_weights.get("p2", 1.0)))
    p3 = float(kwargs.get("p3", cost_weights.get("p3", 3.0)))
    p4 = float(kwargs.get("p4", cost_weights.get("p4", 2.0)))
    return p1, p2, p3, p4


def _run_directional_a_star(
    map_input: str | Path | dict[str, Any],
    *,
    algorithm_name: str,
    heuristic_weight: float,
    p1: float,
    p2: float,
    p3: float,
    p4: float,
) -> dict[str, Any]:
    map_data = load_map(map_input) if isinstance(map_input, (str, Path)) else map_input

    start = map_data["start"]
    goals = map_data.get("goal_cells", [map_data["goal"]])
    risk_cells = {tuple(cell) for cell in map_data.get("risk_cells", [])}
    narrow_cells = {tuple(cell) for cell in map_data.get("narrow_cells", [])}

    def heuristic(x: int, y: int) -> float:
        return min(abs(x - goal[0]) + abs(y - goal[1]) for goal in goals) * p1

    start_time = time.perf_counter()

    start_state = (start[0], start[1], None, None)
    g_score = {start_state: 0.0}
    parent: dict[
        tuple[int, int, int | None, int | None],
        tuple[int, int, int | None, int | None] | None,
    ] = {start_state: None}

    open_set: list[tuple[float, int, tuple[int, int, int | None, int | None]]] = []
    order = 0
    heapq.heappush(open_set, (heuristic_weight * heuristic(start[0], start[1]), order, start_state))
    order += 1

    closed_set: set[tuple[int, int, int | None, int | None]] = set()
    explored_nodes = 0
    explored_cells: list[list[int]] = []
    goal_state: tuple[int, int, int | None, int | None] | None = None
    visualization_trace: list[dict[str, Any]] = []
    step = 0

    while open_set:
        _, _, state = heapq.heappop(open_set)
        x, y, dx, dy = state

        if state in closed_set:
            continue

        closed_set.add(state)
        explored_nodes += 1
        explored_cells.append([x, y])

        if is_goal(map_data, x, y):
            goal_state = state
            break

        for nx, ny in get_neighbors(map_data, x, y):
            ndx = nx - x
            ndy = ny - y
            neighbor = (nx, ny, ndx, ndy)

            if neighbor in closed_set:
                continue

            step_cost = p1
            turn_cost = 0.0

            if dx is not None and dy is not None and (dx, dy) != (ndx, ndy):
                if dx * ndx + dy * ndy == -1:
                    turn_cost = 2.0 * p2
                else:
                    turn_cost = 1.0 * p2

            risk_cost = p3 if (nx, ny) in risk_cells else 0.0
            narrow_cost = p4 if (nx, ny) in narrow_cells else 0.0

            edge_cost = step_cost + turn_cost + risk_cost + narrow_cost
            tentative_g = g_score[state] + edge_cost

            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                parent[neighbor] = state
                g_score[neighbor] = tentative_g
                f_score = tentative_g + heuristic_weight * heuristic(nx, ny)
                heapq.heappush(open_set, (f_score, order, neighbor))
                order += 1

        frontier_cells = sorted(
            {
                (open_state[0], open_state[1])
                for _, _, open_state in open_set
                if open_state not in closed_set
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
    if goal_state is not None:
        path = _reconstruct_path(parent, goal_state)

    success = bool(path)
    path_length = len(path) - 1 if success else -1

    turn_count = 0
    total_risk_cost = 0
    total_narrow_cost = 0

    if success and len(path) > 1:
        for node in path[1:]:
            tuple_node = tuple(node)
            if tuple_node in risk_cells:
                total_risk_cost += 1
            if tuple_node in narrow_cells:
                total_narrow_cost += 1

        if len(path) > 2:
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

    total_cost = -1.0
    if success:
        total_cost = (
            p1 * path_length
            + p2 * turn_count
            + p3 * total_risk_cost
            + p4 * total_narrow_cost
        )

    return {
        "maze_id": map_data["maze_id"],
        "algorithm": algorithm_name,
        "status": "ok",
        "success": success,
        "path": path,
        "path_length": path_length,
        "turn_count": turn_count,
        "risk_cost": total_risk_cost,
        "narrow_cost": total_narrow_cost,
        "explored_nodes": explored_nodes,
        "explored_cells": explored_cells,
        "runtime_ms": runtime_ms,
        "total_cost": total_cost,
        "replan_count": 0,
        "replan_time_ms": 0.0,
        "updated_nodes": 0,
        "replanned_path_length": -1,
        "visualization_trace": visualization_trace,
        "heuristic_weight": heuristic_weight,
        "cost_weights": {"p1": p1, "p2": p2, "p3": p3, "p4": p4},
    }


def run_cost_aware_a_star(
    map_input: str | Path | dict[str, Any],
    **kwargs: Any,
) -> dict[str, Any]:
    p1, p2, p3, p4 = _load_cost_weights(kwargs)
    return _run_directional_a_star(
        map_input,
        algorithm_name="Cost-aware A*",
        heuristic_weight=1.0,
        p1=p1,
        p2=p2,
        p3=p3,
        p4=p4,
    )


def run_weighted_a_star(
    map_input: str | Path | dict[str, Any],
    **kwargs: Any,
) -> dict[str, Any]:
    p1, p2, p3, p4 = _load_cost_weights(kwargs)
    cost_weights = kwargs.get("cost_weights", {})
    heuristic_weight = float(
        kwargs.get("heuristic_weight", kwargs.get("w", cost_weights.get("heuristic_weight", 1.5)))
    )
    return _run_directional_a_star(
        map_input,
        algorithm_name="Weighted A*",
        heuristic_weight=heuristic_weight,
        p1=p1,
        p2=p2,
        p3=p3,
        p4=p4,
    )
