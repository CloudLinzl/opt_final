#!/usr/bin/env python3
"""Lifelong Planning A* implementation.

The public entry point follows the shared registry signature so that
``src.algorithm_registry`` can load ``src.lpa.run_lpa`` directly.
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
DIRECTIONS = [(0, -1), (1, 0), (0, 1), (-1, 0)]
State = tuple[int, int, int | None, int | None]


def manhattan(a: tuple[int, int], b: tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _normalize_state(cell: list[int] | tuple[int, int]) -> tuple[int, int]:
    return (int(cell[0]), int(cell[1]))


def _make_state(cell: tuple[int, int], heading: tuple[int, int] | None) -> State:
    if heading is None:
        return (cell[0], cell[1], None, None)
    return (cell[0], cell[1], int(heading[0]), int(heading[1]))


def _state_cell(state: State) -> tuple[int, int]:
    return (state[0], state[1])


def _cell_list(cell: tuple[int, int]) -> list[int]:
    return [cell[0], cell[1]]


def _unique_cells(cells: list[tuple[int, int]] | list[list[int]]) -> list[list[int]]:
    normalized = {_normalize_state(cell) for cell in cells}
    return [[x, y] for x, y in sorted(normalized, key=lambda item: (item[1], item[0]))]


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
        "explored_cells": [],
        "visualization_trace": [],
        "cost_weights": None,
        "optimization_profile": None,
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
    """Cost-aware incremental planner using LPA*'s g/rhs invariant.

    The algorithm is lifted from cell vertices to directional vertices
    ``(x, y, dx, dy)``. This is the graph-theoretic step that turns a broad
    dynamic shortest-path method into a smaller but richer operations problem:
    turn cost, risk exposure, and narrow-corridor penalties are optimized in the
    edge weights, not merely reported after the path is found.
    """

    def __init__(
        self,
        map_data: dict[str, Any],
        *,
        p1: float = 1.0,
        p2: float = 1.0,
        p3: float = 3.0,
        p4: float = 2.0,
        debug: bool = False,
    ) -> None:
        self.map_data = map_data
        start_cell = _normalize_state(map_data["start"])
        self.current_start: State = _make_state(start_cell, None)
        self.goals = {_normalize_state(cell) for cell in map_data.get("goal_cells", [map_data["goal"]])}
        self.risk_cells = {_normalize_state(cell) for cell in map_data.get("risk_cells", [])}
        self.narrow_cells = {_normalize_state(cell) for cell in map_data.get("narrow_cells", [])}

        self.p1 = p1
        self.p2 = p2
        self.p3 = p3
        self.p4 = p4

        self.g: defaultdict[State, float] = defaultdict(lambda: INF)
        self.rhs: defaultdict[State, float] = defaultdict(lambda: INF)
        self.open_heap: list[tuple[float, float, int, State]] = []
        self.open_keys: dict[State, tuple[float, float]] = {}
        self.push_order = 0

        self.blocked_cells: set[tuple[int, int]] = set()
        self.expanded_nodes = 0
        self.expanded_cells: list[list[int]] = []
        self.debug = debug
        self.debug_log: list[dict[str, Any]] = []

        # Goal-rooted LPA*: every directional state located in the goal region
        # has rhs = 0. All other states begin locally consistent at infinity.
        for goal in self.goals:
            for goal_state in self.states_for_cell(goal):
                self.rhs[goal_state] = 0.0
                self._push_open(goal_state, self.calculate_key(goal_state))
        self._log("initialize", goals=[list(goal) for goal in sorted(self.goals)])

    def _log(self, event: str, **payload: Any) -> None:
        if not self.debug:
            return
        entry = {
            "event": event,
            "current_start": _cell_list(_state_cell(self.current_start)),
            "open_size": len(self.open_keys),
            "expanded_nodes": self.expanded_nodes,
        }
        entry.update(payload)
        self.debug_log.append(entry)

    def snapshot(self, path: list[list[int]] | None = None) -> dict[str, Any]:
        current_cell = _state_cell(self.current_start)
        return {
            "current_start": _cell_list(current_cell),
            "blocked_cells": [[x, y] for x, y in sorted(self.blocked_cells)],
            "open_size": len(self.open_keys),
            "expanded_nodes": self.expanded_nodes,
            "render": render_map_snapshot(
                self.map_data,
                blocked_cells=self.blocked_cells,
                path=path,
                current=current_cell,
            ),
        }

    def states_for_cell(self, cell: tuple[int, int], *, include_none: bool = True) -> list[State]:
        states = [_make_state(cell, direction) for direction in DIRECTIONS]
        if include_none:
            states.append(_make_state(cell, None))
        return states

    def set_start(self, state: State) -> None:
        if state == self.current_start:
            return
        self.current_start = state
        # Moving the robot changes the query heuristic in the priority key.
        # Re-keying inconsistent vertices keeps the previous g/rhs work.
        queued_states = list(self.open_keys)
        self.open_heap.clear()
        self.open_keys.clear()
        for queued in queued_states:
            self._push_open(queued, self.calculate_key(queued))
        self._log("set_start", state=_cell_list(_state_cell(state)))

    def is_goal(self, state: State) -> bool:
        return _state_cell(state) in self.goals

    def is_blocked_cell(self, cell: tuple[int, int]) -> bool:
        return cell in self.blocked_cells

    def wall_neighbors(self, cell: tuple[int, int]) -> list[tuple[int, int]]:
        x, y = cell
        return [_normalize_state(neighbor) for neighbor in get_neighbors(self.map_data, x, y)]

    def successors(self, state: State) -> list[State]:
        cell = _state_cell(state)
        if self.is_blocked_cell(cell):
            return []

        successors: list[State] = []
        x, y = cell
        for neighbor in self.wall_neighbors(cell):
            if self.is_blocked_cell(neighbor):
                continue
            nx, ny = neighbor
            successors.append(_make_state(neighbor, (nx - x, ny - y)))
        return successors

    def predecessors(self, state: State) -> list[State]:
        cell = _state_cell(state)
        dx, dy = state[2], state[3]
        if dx is None or dy is None:
            return []

        pred = (cell[0] - dx, cell[1] - dy)
        px, py = pred
        if not (0 <= px < self.map_data["width"] and 0 <= py < self.map_data["height"]):
            return []
        if self.is_blocked_cell(pred) or cell not in self.wall_neighbors(pred):
            return []
        return self.states_for_cell(pred)

    def _entry_cost(self, cell: tuple[int, int]) -> float:
        return (
            self.p1
            + (self.p3 if cell in self.risk_cells else 0.0)
            + (self.p4 if cell in self.narrow_cells else 0.0)
        )

    def _turn_cost(self, state: State, next_direction: tuple[int, int]) -> float:
        dx, dy = state[2], state[3]
        if dx is None or dy is None or (dx, dy) == next_direction:
            return 0.0
        if dx * next_direction[0] + dy * next_direction[1] == -1:
            return 2.0 * self.p2
        return self.p2

    def cost(self, a: State, b: State) -> float:
        a_cell = _state_cell(a)
        b_cell = _state_cell(b)
        if self.is_blocked_cell(a_cell) or self.is_blocked_cell(b_cell):
            return INF
        if b_cell not in self.wall_neighbors(a_cell):
            return INF

        direction = (b_cell[0] - a_cell[0], b_cell[1] - a_cell[1])
        if (b[2], b[3]) != direction:
            return INF
        return self._entry_cost(b_cell) + self._turn_cost(a, direction)

    def heuristic_to_start(self, state: State) -> float:
        return self.p1 * manhattan(_state_cell(self.current_start), _state_cell(state))

    def calculate_key(self, state: State) -> tuple[float, float]:
        best = min(self.g[state], self.rhs[state])
        return (best + self.heuristic_to_start(state), best)

    def _push_open(self, state: State, key: tuple[float, float]) -> None:
        self.open_keys[state] = key
        heapq.heappush(self.open_heap, (key[0], key[1], self.push_order, state))
        self.push_order += 1

    def _pop_valid_open(self) -> tuple[State | None, tuple[float, float]]:
        while self.open_heap:
            k1, k2, _, state = heapq.heappop(self.open_heap)
            key = (k1, k2)
            if self.open_keys.get(state) == key:
                del self.open_keys[state]
                return state, key
        return None, (INF, INF)

    def _top_key(self) -> tuple[float, float]:
        while self.open_heap:
            k1, k2, _, state = self.open_heap[0]
            key = (k1, k2)
            if self.open_keys.get(state) == key:
                return key
            heapq.heappop(self.open_heap)
        return (INF, INF)

    def frontier_cells(self) -> list[list[int]]:
        return _unique_cells([_cell_list(_state_cell(state)) for state in self.open_keys])

    def update_vertex(self, state: State) -> None:
        if not self.is_goal(state):
            succ = self.successors(state)
            self.rhs[state] = min((self.cost(state, nxt) + self.g[nxt] for nxt in succ), default=INF)

        if state in self.open_keys:
            del self.open_keys[state]

        # A vertex is queued exactly when it is locally inconsistent.
        if self.g[state] != self.rhs[state]:
            self._push_open(state, self.calculate_key(state))
            self._log(
                "update_vertex_inconsistent",
                state=_cell_list(_state_cell(state)),
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
            cell_as_list = _cell_list(_state_cell(state))
            self.expanded_cells.append(cell_as_list)
            expanded_this_call.append(cell_as_list)
            new_key = self.calculate_key(state)
            self._log(
                "expand",
                state=cell_as_list,
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

    def extract_planned_route(self) -> tuple[list[list[int]], list[State]]:
        if self.is_blocked_cell(_state_cell(self.current_start)) or self.g[self.current_start] == INF:
            return [], []

        path: list[list[int]] = [_cell_list(_state_cell(self.current_start))]
        states: list[State] = [self.current_start]
        current = self.current_start
        visited = {current}
        max_steps = self.map_data["width"] * self.map_data["height"] * 4

        for _ in range(max_steps):
            if self.is_goal(current):
                return path, states

            succ = self.successors(current)
            if not succ:
                return [], []

            best_next = min(
                succ,
                key=lambda nxt: (
                    self.cost(current, nxt) + self.g[nxt],
                    self._turn_cost(current, (nxt[2] or 0, nxt[3] or 0)),
                    nxt[1],
                    nxt[0],
                ),
            )
            if self.cost(current, best_next) == INF or self.g[best_next] == INF:
                return [], []
            if best_next in visited:
                return [], []

            current = best_next
            visited.add(current)
            states.append(current)
            path.append(_cell_list(_state_cell(current)))

        return [], []

    def extract_planned_path(self) -> list[list[int]]:
        path, _ = self.extract_planned_route()
        return path

    def apply_dynamic_update(self, update: dict[str, Any]) -> tuple[int, list[list[int]], int]:
        changed_cells: set[tuple[int, int]] = set()
        blocked_added: list[list[int]] = []
        released_removed: list[list[int]] = []

        for cell in update.get("blocked_cells", []):
            state = _normalize_state(cell)
            changed_cells.add(state)
            self.blocked_cells.add(state)
            blocked_added.append([state[0], state[1]])

        for cell in update.get("released_cells", []):
            state = _normalize_state(cell)
            changed_cells.add(state)
            self.blocked_cells.discard(state)
            released_removed.append([state[0], state[1]])

        affected_cells: set[tuple[int, int]] = set(changed_cells)
        for cell in changed_cells:
            affected_cells.update(self.wall_neighbors(cell))

        affected_states: list[State] = []
        for cell in affected_cells:
            affected_states.extend(self.states_for_cell(cell))
        for state in affected_states:
            self.update_vertex(state)

        self._log(
            "dynamic_update",
            step=update.get("step"),
            blocked_cells=blocked_added,
            released_cells=released_removed,
            affected_count=len(affected_cells),
            affected_state_count=len(affected_states),
        )
        affected_cell_list = [[x, y] for x, y in sorted(affected_cells, key=lambda item: (item[1], item[0]))]
        return len(changed_cells), affected_cell_list, len(affected_states)


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

    cost_weights = {"p1": p1, "p2": p2, "p3": p3, "p4": p4, "p5": p5}
    optimization_profile = {
        "state_space": "directional_cell_state",
        "objective": "incremental_dynamic_multi_cost_shortest_path",
        "edge_cost": "p1*step + p2*turn + p3*risk_entry + p4*narrow_entry",
        "replan_penalty": "p5 is applied to the reported total_cost per dynamic repair",
        "tradeoff": "richer costs narrow the applicable problem class, but improve operational realism",
    }

    planner = LPAStar(map_data, p1=p1, p2=p2, p3=p3, p4=p4, debug=debug)
    runtime_start = time.perf_counter()
    initial_expanded = planner.compute_shortest_path()
    initial_plan, initial_states = planner.extract_planned_route()
    visualization_trace = [
        _trace_frame(
            step=0,
            event="initial_plan",
            current_cell=_cell_list(_state_cell(planner.current_start)),
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
        result["explored_cells"] = _unique_cells(planner.expanded_cells)
        result["visualization_trace"] = visualization_trace
        result["cost_weights"] = cost_weights
        result["optimization_profile"] = optimization_profile
        if include_debug_log:
            result["debug_log"] = planner.debug_log
            result["debug_snapshot"] = planner.snapshot()
        return result

    updates_by_step: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for update in map_data.get("dynamic_updates", []):
        updates_by_step[int(update["step"])].append(update)

    actual_path: list[list[int]] = [_cell_list(_state_cell(planner.current_start))]
    replan_times: list[float] = []
    replan_count = 0
    updated_nodes = 0
    changed_cells_count = 0
    replanned_path_length = 0
    step_count = 0
    success = True

    max_runtime_steps = map_data["width"] * map_data["height"] * 8
    for _ in range(max_runtime_steps):
        if planner.is_goal(planner.current_start):
            break

        step_expanded = planner.compute_shortest_path()
        planned_path, planned_states = planner.extract_planned_route()
        if len(planned_path) < 2 or len(planned_states) < 2:
            success = False
            planner._log("path_missing", step=step_count, snapshot=planner.snapshot())
            break

        next_state = planned_states[1]
        planner.set_start(next_state)
        actual_path.append(_cell_list(_state_cell(next_state)))
        step_count += 1
        planner._log("move", step=step_count, moved_to=_cell_list(_state_cell(next_state)))

        if step_count in updates_by_step:
            pre_update_path, _ = planner.extract_planned_route()
            visualization_trace.append(
                _trace_frame(
                    step=step_count,
                    event="before_update",
                    current_cell=_cell_list(_state_cell(planner.current_start)),
                    path=pre_update_path,
                    blocked_cells=planner.blocked_cells,
                    replan_count=replan_count,
                    updated_nodes=updated_nodes,
                    explored_cells=step_expanded,
                    frontier_cells=planner.frontier_cells(),
                    queue_size=len(planner.open_keys),
                )
            )
            for update in updates_by_step[step_count]:
                replan_start = time.perf_counter()
                changed_cells, affected_cells, affected_state_count = planner.apply_dynamic_update(update)
                changed_cells_count += changed_cells
                updated_nodes += affected_state_count
                visualization_trace.append(
                    _trace_frame(
                        step=step_count,
                        event="dynamic_update",
                        current_cell=_cell_list(_state_cell(planner.current_start)),
                        path=pre_update_path,
                        blocked_cells=planner.blocked_cells,
                        replan_count=replan_count,
                        updated_nodes=updated_nodes,
                        affected_cells=affected_cells,
                        explored_cells=step_expanded,
                        frontier_cells=planner.frontier_cells(),
                        queue_size=len(planner.open_keys),
                    )
                )
                replan_expanded = planner.compute_shortest_path()
                replan_times.append((time.perf_counter() - replan_start) * 1000.0)
                replan_count += 1

                replanned_path, _ = planner.extract_planned_route()
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
                        current_cell=_cell_list(_state_cell(planner.current_start)),
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
            current_cell=_cell_list(_state_cell(planner.current_start)),
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
        "algorithm": "LPA*",
        "status": "ok",
        "success": success,
        "path": actual_path if success else [],
        "path_length": path_length,
        "turn_count": turn_count,
        "risk_cost": risk_cost,
        "narrow_cost": narrow_cost,
        "explored_nodes": planner.expanded_nodes,
        "explored_cells": _unique_cells(planner.expanded_cells),
        "runtime_ms": runtime_ms,
        "total_cost": total_cost,
        "replan_count": replan_count,
        "replan_time_ms": replan_time_ms,
        "updated_nodes": updated_nodes,
        "changed_cells": changed_cells_count,
        "replanned_path_length": replanned_path_length if replan_count > 0 else 0,
        "visualization_trace": visualization_trace,
        "cost_weights": cost_weights,
        "optimization_profile": optimization_profile,
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
