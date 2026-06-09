#!/usr/bin/env python3
"""
First working D* Lite implementation for the project.

Goals of this version:
1. Keep the external interface stable for future main-program integration.
2. Support the current JSON map format, including dynamic_updates.
3. Return results that match the project's output schema as closely as possible.
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


def _cell_list(cell: tuple[int, int]) -> list[int]:
    return [cell[0], cell[1]]


def _unique_cells(cells: list[list[int]]) -> list[list[int]]:
    normalized = {(int(cell[0]), int(cell[1])) for cell in cells}
    return [[x, y] for x, y in sorted(normalized, key=lambda item: (item[1], item[0]))]


def compute_turn_count(path: list[list[int]]) -> int:
    if len(path) < 3:
        return 0

    directions: list[tuple[int, int]] = []
    for i in range(1, len(path)):
        dx = path[i][0] - path[i - 1][0]
        dy = path[i][1] - path[i - 1][1]
        directions.append((dx, dy))

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
        "algorithm": "D* Lite",
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
    replan_count: int = 0,
    updated_nodes: int = 0,
    affected_cells: list[list[int]] | None = None,
    explored_cells: list[list[int]] | None = None,
    frontier_cells: list[list[int]] | None = None,
    queue_size: int = 0,
) -> dict[str, Any]:
    return {
        "step": step,
        "event": event,
        "current_cell": list(current_cell) if current_cell is not None else None,
        "path": [list(cell) for cell in (path or [])],
        "explored_cells": [list(cell) for cell in (explored_cells or [])],
        "frontier_cells": [list(cell) for cell in (frontier_cells or [])],
        "blocked_cells": [[x, y] for x, y in sorted(blocked_cells)],
        "replan_count": replan_count,
        "updated_nodes": updated_nodes,
        "affected_cells": [list(cell) for cell in (affected_cells or [])],
        "queue_size": queue_size,
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
            raw_cells = update.get(key, [])
            cells: list[list[int]] = []
            for cell in raw_cells:
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


class DStarLite:
    def __init__(self, map_data: dict[str, Any], *, debug: bool = False) -> None:
        self.map_data = map_data
        self.start = _normalize_state(map_data["start"])
        self.current_start = self.start
        self.last_start = self.start
        self.goals = {_normalize_state(cell) for cell in map_data.get("goal_cells", [map_data["goal"]])}

        self.g: defaultdict[tuple[int, int], float] = defaultdict(lambda: INF)
        self.rhs: defaultdict[tuple[int, int], float] = defaultdict(lambda: INF)
        self.open_heap: list[tuple[float, float, tuple[int, int]]] = []
        self.open_keys: dict[tuple[int, int], tuple[float, float]] = {}

        self.km = 0.0
        self.blocked_cells: set[tuple[int, int]] = set()
        self.expanded_nodes = 0
        self.expanded_cells: list[list[int]] = []
        self.debug = debug
        self.debug_log: list[dict[str, Any]] = []

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

    def is_goal(self, state: tuple[int, int]) -> bool:
        return state in self.goals

    def is_blocked(self, state: tuple[int, int]) -> bool:
        return state in self.blocked_cells

    def successors(self, state: tuple[int, int]) -> list[tuple[int, int]]:
        if self.is_blocked(state):
            return []
        x, y = state
        return [
            _normalize_state(cell)
            for cell in get_neighbors(self.map_data, x, y)
            if _normalize_state(cell) not in self.blocked_cells
        ]

    def predecessors(self, state: tuple[int, int]) -> list[tuple[int, int]]:
        x, y = state
        candidates = [
            (x, y - 1),
            (x + 1, y),
            (x, y + 1),
            (x - 1, y),
        ]
        predecessors: list[tuple[int, int]] = []
        for pred in candidates:
            px, py = pred
            if not (0 <= px < self.map_data["width"] and 0 <= py < self.map_data["height"]):
                continue
            if self.is_blocked(pred):
                continue
            if state in {
                _normalize_state(cell)
                for cell in get_neighbors(self.map_data, px, py)
            }:
                predecessors.append(pred)
        return predecessors

    def cost(self, a: tuple[int, int], b: tuple[int, int]) -> float:
        if self.is_blocked(a) or self.is_blocked(b):
            return INF
        return 1.0 if b in self.successors(a) else INF

    def calculate_key(self, state: tuple[int, int]) -> tuple[float, float]:
        best = min(self.g[state], self.rhs[state])
        return (best + manhattan(self.current_start, state) + self.km, best)

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

    def frontier_cells(self) -> list[list[int]]:
        return _unique_cells([_cell_list(state) for state in self.open_keys])

    def update_vertex(self, state: tuple[int, int]) -> None:
        if state not in self.goals:
            succ = self.successors(state)
            if succ:
                self.rhs[state] = min(self.cost(state, nxt) + self.g[nxt] for nxt in succ)
            else:
                self.rhs[state] = INF

        if state in self.open_keys:
            del self.open_keys[state]

        if self.g[state] != self.rhs[state]:
            self._push_open(state, self.calculate_key(state))
            self._log(
                "update_vertex_inconsistent",
                state=[state[0], state[1]],
                g=self.g[state],
                rhs=self.rhs[state],
            )

    def compute_shortest_path(self) -> list[list[int]]:
        expanded_this_call: list[list[int]] = []
        while self._top_key() < self.calculate_key(self.current_start) or self.rhs[self.current_start] != self.g[self.current_start]:
            state, old_key = self._pop_valid_open()
            if state is None:
                break

            self.expanded_nodes += 1
            expanded_cell = _cell_list(state)
            self.expanded_cells.append(expanded_cell)
            expanded_this_call.append(expanded_cell)
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
        return _unique_cells(expanded_this_call)

    def extract_planned_path(self) -> list[list[int]]:
        if self.g[self.current_start] == INF:
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

    def apply_dynamic_update(self, update: dict[str, Any]) -> tuple[int, list[list[int]]]:
        affected: set[tuple[int, int]] = set()
        blocked_added: list[list[int]] = []
        released_removed: list[list[int]] = []

        for cell in update.get("blocked_cells", []):
            state = _normalize_state(cell)
            neighbor_states = self.predecessors(state)
            self.blocked_cells.add(state)
            affected.add(state)
            affected.update(neighbor_states)
            blocked_added.append([state[0], state[1]])

        for cell in update.get("released_cells", []):
            state = _normalize_state(cell)
            if state in self.blocked_cells:
                self.blocked_cells.remove(state)
            affected.add(state)
            affected.update(self.predecessors(state))
            released_removed.append([state[0], state[1]])

        self.km += manhattan(self.last_start, self.current_start)
        self.last_start = self.current_start

        for state in affected:
            self.update_vertex(state)

        self._log(
            "dynamic_update",
            step=update.get("step"),
            blocked_cells=blocked_added,
            released_cells=released_removed,
            affected_count=len(affected),
        )
        affected_cells = [[x, y] for x, y in sorted(affected)]
        return len(update.get("blocked_cells", [])) + len(update.get("released_cells", [])), affected_cells


def run_dstar_lite(
    map_input: str | Path | dict[str, Any],
    *,
    dynamic_updates: list[dict[str, Any]] | None = None,
    debug: bool = False,
    include_debug_log: bool = False,
    p1: float = 1.0,
    p2: float = 1.0,
    p3: float = 3.0,
    p4: float = 2.0,
    p5: float = 2.0,
) -> dict[str, Any]:
    if isinstance(map_input, (str, Path)):
        map_data = load_map(map_input)
    else:
        map_data = deepcopy(map_input)

    map_data["dynamic_updates"] = validate_dynamic_updates(map_data, dynamic_updates)

    planner = DStarLite(map_data, debug=debug)
    runtime_start = time.perf_counter()
    initial_expanded = planner.compute_shortest_path()
    initial_plan = planner.extract_planned_path()
    visualization_trace = [
        _trace_frame(
            step=0,
            event="initial_plan",
            current_cell=planner.current_start,
            path=initial_plan,
            blocked_cells=planner.blocked_cells,
            replan_count=0,
            updated_nodes=0,
            explored_cells=initial_expanded,
            frontier_cells=planner.frontier_cells(),
            queue_size=len(planner.open_keys),
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

    max_runtime_steps = map_data["width"] * map_data["height"] * 8
    success = True

    for _ in range(max_runtime_steps):
        if planner.is_goal(planner.current_start):
            break

        planned_path = planner.extract_planned_path()
        if len(planned_path) < 2:
            success = False
            planner._log("path_missing", step=step_count, snapshot=planner.snapshot())
            break

        next_state = _normalize_state(planned_path[1])
        planner.current_start = next_state
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
                    replan_count=replan_count,
                    updated_nodes=updated_nodes,
                    explored_cells=[],
                    frontier_cells=planner.frontier_cells(),
                    queue_size=len(planner.open_keys),
                )
            )
            for update in updates_by_step[step_count]:
                replan_start = time.perf_counter()
                changed_nodes, affected_cells = planner.apply_dynamic_update(update)
                updated_nodes += changed_nodes
                visualization_trace.append(
                    _trace_frame(
                        step=step_count,
                        event="dynamic_update",
                        current_cell=planner.current_start,
                        path=pre_update_path,
                        blocked_cells=planner.blocked_cells,
                        replan_count=replan_count,
                        updated_nodes=updated_nodes,
                        affected_cells=affected_cells,
                        explored_cells=[],
                        frontier_cells=planner.frontier_cells(),
                        queue_size=len(planner.open_keys),
                    )
                )
                replan_expanded = planner.compute_shortest_path()
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
                        replan_count=replan_count,
                        updated_nodes=updated_nodes,
                        affected_cells=affected_cells,
                        explored_cells=replan_expanded,
                        frontier_cells=planner.frontier_cells(),
                        queue_size=len(planner.open_keys),
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
            replan_count=replan_count,
            updated_nodes=updated_nodes,
            explored_cells=_unique_cells(planner.expanded_cells),
            frontier_cells=planner.frontier_cells(),
            queue_size=len(planner.open_keys),
        )
    )

    result = {
        "maze_id": map_data["maze_id"],
        "algorithm": "D* Lite",
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


def summarize_dstar_result(result: dict[str, Any]) -> dict[str, Any]:
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
