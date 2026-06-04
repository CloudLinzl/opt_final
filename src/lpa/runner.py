#!/usr/bin/env python3
"""Lifelong Planning A* implementation.

The public entry point intentionally matches the placeholder signature so that
``src.algorithm_registry`` can keep loading ``src.lpa.run_lpa`` unchanged.
"""

from __future__ import annotations

import heapq
import sys
import time
from collections import defaultdict
from copy import deepcopy
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from scripts.load_map import get_neighbors, load_map  # noqa: E402


INF = float("inf")


def manhattan(a: tuple[int, int], b: tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _normalize_state(cell: list[int] | tuple[int, int]) -> tuple[int, int]:
    return (int(cell[0]), int(cell[1]))


def compute_turn_count(path: list[list[int]]) -> int:
    if len(path) < 3:
        return 0

    directions: list[tuple[int, int]] = []
    for i in range(1, len(path)):
        directions.append((path[i][0] - path[i - 1][0], path[i][1] - path[i - 1][1]))

    turns = 0
    for i in range(1, len(directions)):
        prev_dir = directions[i - 1]
        curr_dir = directions[i]
        if curr_dir == prev_dir:
            continue
        if curr_dir == (-prev_dir[0], -prev_dir[1]):
            turns += 2
        else:
            turns += 1
    return turns


def compute_region_cost(path: list[list[int]], region_cells: list[list[int]]) -> int:
    region = {tuple(cell) for cell in region_cells}
    return sum(1 for cell in path if tuple(cell) in region)


def compute_total_cost(
    path_length: int,
    turn_count: int,
    risk_cost: int,
    narrow_cost: int,
    replan_count: int,
    p1: float = 1.0,
    p2: float = 1.0,
    p3: float = 3.0,
    p4: float = 2.0,
    p5: float = 2.0,
) -> float:
    return (
        p1 * path_length
        + p2 * turn_count
        + p3 * risk_cost
        + p4 * narrow_cost
        + p5 * replan_count
    )


def _default_result(maze_id: str, expanded_nodes: int = 0, runtime_ms: float = 0.0) -> dict[str, Any]:
    return {
        "maze_id": maze_id,
        "algorithm": "LPA*",
        "status": "ok",
        "success": False,
        "path": [],
        "path_length": -1,
        "turn_count": -1,
        "risk_cost": 0,
        "narrow_cost": 0,
        "explored_nodes": expanded_nodes,
        "runtime_ms": runtime_ms,
        "total_cost": -1,
        "replan_count": 0,
        "replan_time_ms": 0.0,
        "updated_nodes": 0,
        "replanned_path_length": -1,
        "visualization_trace": [],
    }


def _trace_frame(
    *,
    step: int,
    event: str,
    current_cell: tuple[int, int] | list[int] | None,
    path: list[list[int]] | None,
    blocked_cells: set[tuple[int, int]],
) -> dict[str, Any]:
    return {
        "step": step,
        "event": event,
        "current_cell": list(current_cell) if current_cell is not None else None,
        "path": [list(cell) for cell in (path or [])],
        "explored_cells": [],
        "frontier_cells": [],
        "blocked_cells": [[x, y] for x, y in sorted(blocked_cells)],
    }


def validate_dynamic_updates(
    map_data: dict[str, Any],
    dynamic_updates: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    updates = dynamic_updates if dynamic_updates is not None else map_data.get("dynamic_updates", [])
    width = map_data["width"]
    height = map_data["height"]
    protected = {
        _normalize_state(map_data["start"]),
        _normalize_state(map_data["goal"]),
        *[_normalize_state(cell) for cell in map_data.get("goal_cells", [])],
    }

    normalized: list[dict[str, Any]] = []
    last_step = -1
    for index, update in enumerate(updates):
        if "step" not in update:
            raise ValueError(f"dynamic update #{index} is missing 'step'")
        step = int(update["step"])
        if step < 0:
            raise ValueError(f"dynamic update #{index} has negative step")
        if step < last_step:
            raise ValueError("dynamic_updates must be sorted in nondecreasing step order")
        last_step = step

        def normalize_cells(key: str) -> list[list[int]]:
            cells: list[list[int]] = []
            for cell in update.get(key, []):
                state = _normalize_state(cell)
                x, y = state
                if not (0 <= x < width and 0 <= y < height):
                    raise ValueError(f"dynamic update #{index} has out-of-range cell {state}")
                if key == "blocked_cells" and state in protected:
                    raise ValueError(
                        f"dynamic update #{index} attempts to block protected cell {state}"
                    )
                cells.append([x, y])
            return cells

        normalized.append(
            {
                "step": step,
                "blocked_cells": normalize_cells("blocked_cells"),
                "released_cells": normalize_cells("released_cells"),
            }
        )
    return normalized


def render_map_snapshot(
    map_data: dict[str, Any],
    *,
    blocked_cells: set[tuple[int, int]] | None = None,
    path: list[list[int]] | None = None,
    current: tuple[int, int] | None = None,
) -> str:
    blocked = blocked_cells or set()
    path_cells = {_normalize_state(cell) for cell in (path or [])}
    goal_cells = {_normalize_state(cell) for cell in map_data.get("goal_cells", [map_data["goal"]])}
    start = _normalize_state(map_data["start"])

    rows: list[str] = []
    for y in range(map_data["height"]):
        chars: list[str] = []
        for x in range(map_data["width"]):
            state = (x, y)
            if current is not None and state == current:
                chars.append("C")
            elif state == start:
                chars.append("S")
            elif state in goal_cells:
                chars.append("G")
            elif state in blocked:
                chars.append("#")
            elif state in path_cells:
                chars.append("*")
            else:
                chars.append(".")
        rows.append("".join(chars))
    return "\n".join(rows)


class LPAStar:
    """Incremental shortest-path planner using LPA*'s g/rhs invariant.

    This implementation roots the search at the goal cells. The resulting
    ``g`` values are cost-to-go estimates, so the current robot position can be
    advanced between steps while dynamic map edits are still repaired
    incrementally through ``update_vertex`` and ``compute_shortest_path``.
    """

    def __init__(self, map_data: dict[str, Any], *, debug: bool = False) -> None:
        self.map_data = map_data
        self.current_start = _normalize_state(map_data["start"])
        self.goals = {_normalize_state(cell) for cell in map_data.get("goal_cells", [map_data["goal"]])}

        self.g: defaultdict[tuple[int, int], float] = defaultdict(lambda: INF)
        self.rhs: defaultdict[tuple[int, int], float] = defaultdict(lambda: INF)
        self.open_heap: list[tuple[float, float, tuple[int, int]]] = []
        self.open_keys: dict[tuple[int, int], tuple[float, float]] = {}

        self.blocked_cells: set[tuple[int, int]] = set()
        self.expanded_nodes = 0
        self.debug = debug
        self.debug_log: list[dict[str, Any]] = []

        # LPA* initialization: goal vertices are locally overconsistent and
        # seed the queue; every other vertex starts at g = rhs = infinity.
        for goal in self.goals:
            self.rhs[goal] = 0.0
            self._push_open(goal, self.calculate_key(goal))
        self._log("initialize", goals=[list(goal) for goal in sorted(self.goals)])

    def _log(self, event: str, **payload: Any) -> None:
        if not self.debug:
            return
        entry = {
            "event": event,
            "current_start": [self.current_start[0], self.current_start[1]],
            "open_size": len(self.open_keys),
            "expanded_nodes": self.expanded_nodes,
        }
        entry.update(payload)
        self.debug_log.append(entry)

    def snapshot(self, path: list[list[int]] | None = None) -> dict[str, Any]:
        return {
            "current_start": [self.current_start[0], self.current_start[1]],
            "blocked_cells": [[x, y] for x, y in sorted(self.blocked_cells)],
            "open_size": len(self.open_keys),
            "expanded_nodes": self.expanded_nodes,
            "render": render_map_snapshot(
                self.map_data,
                blocked_cells=self.blocked_cells,
                path=path,
                current=self.current_start,
            ),
        }

    def set_start(self, state: tuple[int, int]) -> None:
        if state == self.current_start:
            return
        self.current_start = state
        # The cost labels do not depend on the query start, but queue keys do.
        # Re-keying only inconsistent vertices preserves the LPA* invariant.
        queued_states = list(self.open_keys)
        self.open_heap.clear()
        self.open_keys.clear()
        for queued in queued_states:
            self._push_open(queued, self.calculate_key(queued))
        self._log("set_start", state=[state[0], state[1]])

    def is_goal(self, state: tuple[int, int]) -> bool:
        return state in self.goals

    def is_blocked(self, state: tuple[int, int]) -> bool:
        return state in self.blocked_cells

    def wall_neighbors(self, state: tuple[int, int]) -> list[tuple[int, int]]:
        x, y = state
        return [_normalize_state(cell) for cell in get_neighbors(self.map_data, x, y)]

    def successors(self, state: tuple[int, int]) -> list[tuple[int, int]]:
        if self.is_blocked(state):
            return []
        return [neighbor for neighbor in self.wall_neighbors(state) if neighbor not in self.blocked_cells]

    def predecessors(self, state: tuple[int, int]) -> list[tuple[int, int]]:
        return self.successors(state)

    def cost(self, a: tuple[int, int], b: tuple[int, int]) -> float:
        if self.is_blocked(a) or self.is_blocked(b):
            return INF
        return 1.0 if b in self.successors(a) else INF

    def heuristic_to_start(self, state: tuple[int, int]) -> int:
        return manhattan(self.current_start, state)

    def calculate_key(self, state: tuple[int, int]) -> tuple[float, float]:
        best = min(self.g[state], self.rhs[state])
        return (best + self.heuristic_to_start(state), best)

    def _push_open(self, state: tuple[int, int], key: tuple[float, float]) -> None:
        self.open_keys[state] = key
        heapq.heappush(self.open_heap, (key[0], key[1], state))

    def _pop_valid_open(self) -> tuple[tuple[int, int] | None, tuple[float, float]]:
        while self.open_heap:
            k1, k2, state = heapq.heappop(self.open_heap)
            key = (k1, k2)
            if self.open_keys.get(state) == key:
                del self.open_keys[state]
                return state, key
        return None, (INF, INF)

    def _top_key(self) -> tuple[float, float]:
        while self.open_heap:
            k1, k2, state = self.open_heap[0]
            key = (k1, k2)
            if self.open_keys.get(state) == key:
                return key
            heapq.heappop(self.open_heap)
        return (INF, INF)

    def update_vertex(self, state: tuple[int, int]) -> None:
        if state not in self.goals:
            succ = self.successors(state)
            self.rhs[state] = min((self.cost(state, nxt) + self.g[nxt] for nxt in succ), default=INF)

        if state in self.open_keys:
            del self.open_keys[state]

        # A vertex is queued exactly when it is locally inconsistent.
        if self.g[state] != self.rhs[state]:
            self._push_open(state, self.calculate_key(state))
            self._log(
                "update_vertex_inconsistent",
                state=[state[0], state[1]],
                g=self.g[state],
                rhs=self.rhs[state],
            )

    def compute_shortest_path(self) -> None:
        while self._top_key() < self.calculate_key(self.current_start) or self.rhs[self.current_start] != self.g[self.current_start]:
            state, old_key = self._pop_valid_open()
            if state is None:
                break

            self.expanded_nodes += 1
            new_key = self.calculate_key(state)
            self._log(
                "expand",
                state=[state[0], state[1]],
                old_key=list(old_key),
                new_key=list(new_key),
                g=self.g[state],
                rhs=self.rhs[state],
            )
            if old_key < new_key:
                self._push_open(state, new_key)
            elif self.g[state] > self.rhs[state]:
                self.g[state] = self.rhs[state]
                for pred in self.predecessors(state):
                    self.update_vertex(pred)
            else:
                self.g[state] = INF
                self.update_vertex(state)
                for pred in self.predecessors(state):
                    self.update_vertex(pred)

    def extract_planned_path(self) -> list[list[int]]:
        if self.is_blocked(self.current_start) or self.g[self.current_start] == INF:
            return []

        path: list[list[int]] = [[self.current_start[0], self.current_start[1]]]
        current = self.current_start
        visited = {current}
        max_steps = self.map_data["width"] * self.map_data["height"] * 4

        for _ in range(max_steps):
            if self.is_goal(current):
                return path

            succ = self.successors(current)
            if not succ:
                return []

            best_next = min(succ, key=lambda nxt: (self.cost(current, nxt) + self.g[nxt], nxt[1], nxt[0]))
            if self.cost(current, best_next) == INF or self.g[best_next] == INF:
                return []
            if best_next in visited:
                return []

            current = best_next
            visited.add(current)
            path.append([current[0], current[1]])

        return []

    def apply_dynamic_update(self, update: dict[str, Any]) -> int:
        affected: set[tuple[int, int]] = set()
        blocked_added: list[list[int]] = []
        released_removed: list[list[int]] = []

        for cell in update.get("blocked_cells", []):
            state = _normalize_state(cell)
            affected.add(state)
            affected.update(self.wall_neighbors(state))
            self.blocked_cells.add(state)
            blocked_added.append([state[0], state[1]])

        for cell in update.get("released_cells", []):
            state = _normalize_state(cell)
            affected.add(state)
            affected.update(self.wall_neighbors(state))
            self.blocked_cells.discard(state)
            released_removed.append([state[0], state[1]])

        for state in affected:
            self.update_vertex(state)

        self._log(
            "dynamic_update",
            step=update.get("step"),
            blocked_cells=blocked_added,
            released_cells=released_removed,
            affected_count=len(affected),
        )
        return len(update.get("blocked_cells", [])) + len(update.get("released_cells", []))


def run_lpa(
    map_input: str | Path | dict[str, Any],
    dynamic_updates: list[dict[str, Any]] | None = None,
    *,
    debug: bool = False,
    include_debug_log: bool = False,
    p1: float = 1.0,
    p2: float = 1.0,
    p3: float = 3.0,
    p4: float = 2.0,
    p5: float = 2.0,
    **kwargs: Any,
) -> dict[str, Any]:
    del kwargs
    if isinstance(map_input, (str, Path)):
        map_data = load_map(map_input)
    else:
        map_data = deepcopy(map_input)

    map_data["dynamic_updates"] = validate_dynamic_updates(map_data, dynamic_updates)

    planner = LPAStar(map_data, debug=debug)
    runtime_start = time.perf_counter()
    planner.compute_shortest_path()
    initial_plan = planner.extract_planned_path()
    visualization_trace = [
        _trace_frame(
            step=0,
            event="initial_plan",
            current_cell=planner.current_start,
            path=initial_plan,
            blocked_cells=planner.blocked_cells,
        )
    ]

    if not initial_plan:
        runtime_ms = (time.perf_counter() - runtime_start) * 1000.0
        result = _default_result(map_data["maze_id"], expanded_nodes=planner.expanded_nodes, runtime_ms=runtime_ms)
        result["visualization_trace"] = visualization_trace
        if include_debug_log:
            result["debug_log"] = planner.debug_log
            result["debug_snapshot"] = planner.snapshot()
        return result

    updates_by_step: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for update in map_data.get("dynamic_updates", []):
        updates_by_step[int(update["step"])].append(update)

    actual_path: list[list[int]] = [[planner.current_start[0], planner.current_start[1]]]
    replan_times: list[float] = []
    replan_count = 0
    updated_nodes = 0
    replanned_path_length = 0
    step_count = 0
    success = True

    max_runtime_steps = map_data["width"] * map_data["height"] * 8
    for _ in range(max_runtime_steps):
        if planner.is_goal(planner.current_start):
            break

        planner.compute_shortest_path()
        planned_path = planner.extract_planned_path()
        if len(planned_path) < 2:
            success = False
            planner._log("path_missing", step=step_count, snapshot=planner.snapshot())
            break

        next_state = _normalize_state(planned_path[1])
        planner.set_start(next_state)
        actual_path.append([next_state[0], next_state[1]])
        step_count += 1
        planner._log("move", step=step_count, moved_to=[next_state[0], next_state[1]])

        if step_count in updates_by_step:
            pre_update_path = planner.extract_planned_path()
            visualization_trace.append(
                _trace_frame(
                    step=step_count,
                    event="before_update",
                    current_cell=planner.current_start,
                    path=pre_update_path,
                    blocked_cells=planner.blocked_cells,
                )
            )
            for update in updates_by_step[step_count]:
                replan_start = time.perf_counter()
                updated_nodes += planner.apply_dynamic_update(update)
                planner.compute_shortest_path()
                replan_times.append((time.perf_counter() - replan_start) * 1000.0)
                replan_count += 1

                replanned_path = planner.extract_planned_path()
                replanned_path_length = len(replanned_path) - 1 if replanned_path else -1
                planner._log(
                    "replan",
                    step=step_count,
                    replanned_path_length=replanned_path_length,
                    snapshot=planner.snapshot(replanned_path),
                )
                visualization_trace.append(
                    _trace_frame(
                        step=step_count,
                        event="replan",
                        current_cell=planner.current_start,
                        path=replanned_path,
                        blocked_cells=planner.blocked_cells,
                    )
                )
                if not replanned_path:
                    success = False
                    break
            if not success:
                break

    if not planner.is_goal(planner.current_start):
        success = False

    runtime_ms = (time.perf_counter() - runtime_start) * 1000.0
    path_length = len(actual_path) - 1 if success else -1
    turn_count = compute_turn_count(actual_path) if success else -1
    risk_cost = compute_region_cost(actual_path, map_data.get("risk_cells", [])) if success else 0
    narrow_cost = compute_region_cost(actual_path, map_data.get("narrow_cells", [])) if success else 0
    total_cost = (
        compute_total_cost(path_length, turn_count, risk_cost, narrow_cost, replan_count, p1, p2, p3, p4, p5)
        if success
        else -1
    )
    replan_time_ms = sum(replan_times) / len(replan_times) if replan_times else 0.0
    visualization_trace.append(
        _trace_frame(
            step=step_count,
            event="final_result",
            current_cell=planner.current_start,
            path=actual_path if success else [],
            blocked_cells=planner.blocked_cells,
        )
    )

    result = {
        "maze_id": map_data["maze_id"],
        "algorithm": "LPA*",
        "status": "ok",
        "success": success,
        "path": actual_path if success else [],
        "path_length": path_length,
        "turn_count": turn_count,
        "risk_cost": risk_cost,
        "narrow_cost": narrow_cost,
        "explored_nodes": planner.expanded_nodes,
        "runtime_ms": runtime_ms,
        "total_cost": total_cost,
        "replan_count": replan_count,
        "replan_time_ms": replan_time_ms,
        "updated_nodes": updated_nodes,
        "replanned_path_length": replanned_path_length if replan_count > 0 else 0,
        "visualization_trace": visualization_trace,
    }
    if include_debug_log:
        result["debug_log"] = planner.debug_log
        result["debug_snapshot"] = planner.snapshot(actual_path if success else [])
    return result


def summarize_lpa_result(result: dict[str, Any]) -> dict[str, Any]:
    summary_keys = [
        "maze_id",
        "algorithm",
        "success",
        "path_length",
        "turn_count",
        "explored_nodes",
        "runtime_ms",
        "replan_count",
        "replan_time_ms",
        "updated_nodes",
        "replanned_path_length",
    ]
    return {key: result.get(key) for key in summary_keys}
