#!/usr/bin/env python3
"""
Algorithm registry for the project main entry.

This module keeps main.py decoupled from concrete algorithm implementations.
"""

from __future__ import annotations

from dataclasses import dataclass
import importlib
from pathlib import Path
from typing import Any, Callable


UNIFIED_RESULT_KEYS = [
    "maze_id",
    "algorithm",
    "success",
    "path",
    "path_length",
    "turn_count",
    "risk_cost",
    "narrow_cost",
    "explored_nodes",
    "runtime_ms",
    "total_cost",
    "replan_count",
    "replan_time_ms",
    "updated_nodes",
    "replanned_path_length",
]


@dataclass(frozen=True)
class AlgorithmRegistration:
    key: str
    label: str
    module_name: str
    function_name: str
    dynamic: bool = False


def _placeholder_result(maze_id: str, algorithm: str, status: str) -> dict[str, Any]:
    result = {
        "maze_id": maze_id,
        "algorithm": algorithm,
        "status": status,
        "success": False,
        "path": [],
        "path_length": -1,
        "turn_count": -1,
        "risk_cost": 0,
        "narrow_cost": 0,
        "explored_nodes": 0,
        "runtime_ms": 0.0,
        "total_cost": -1,
        "replan_count": 0,
        "replan_time_ms": 0.0,
        "updated_nodes": 0,
        "replanned_path_length": -1,
    }
    return result


def default_registry() -> list[AlgorithmRegistration]:
    return [
        AlgorithmRegistration("bfs", "BFS", "src.bfs", "run_bfs", dynamic=False),
        AlgorithmRegistration("a_star", "A*", "src.a_star", "run_a_star", dynamic=False),
        AlgorithmRegistration(
            "weighted_a_star",
            "Weighted A*",
            "src.weighted_a_star",
            "run_weighted_a_star",
            dynamic=False,
        ),
        AlgorithmRegistration(
            "lpa",
            "LPA*",
            "src.lpa",
            "run_lpa",
            dynamic=True,
        ),
        AlgorithmRegistration(
            "dstar_lite",
            "D* Lite",
            "src.dlite",
            "run_dstar_lite",
            dynamic=True,
        ),
    ]


def load_algorithm_callable(
    registration: AlgorithmRegistration,
) -> tuple[Callable[..., dict[str, Any]] | None, str]:
    try:
        module = importlib.import_module(registration.module_name)
    except ModuleNotFoundError:
        return None, "not_available"

    fn = getattr(module, registration.function_name, None)
    if fn is None or not callable(fn):
        return None, "not_registered"
    return fn, "available"


def run_registered_algorithm(
    registration: AlgorithmRegistration,
    *,
    map_input: str | Path | dict[str, Any],
    map_data: dict[str, Any],
    dynamic_updates: list[dict[str, Any]] | None = None,
    extra_kwargs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    extra_kwargs = extra_kwargs or {}
    fn, status = load_algorithm_callable(registration)
    if fn is None:
        return _placeholder_result(map_data["maze_id"], registration.label, status)

    kwargs = dict(extra_kwargs)
    if registration.dynamic:
        kwargs["dynamic_updates"] = dynamic_updates or []

    result = fn(map_input, **kwargs)
    result.setdefault("status", "ok")
    result.setdefault("algorithm", registration.label)
    result.setdefault("maze_id", map_data["maze_id"])
    for key in UNIFIED_RESULT_KEYS:
        result.setdefault(key, _placeholder_result(map_data["maze_id"], registration.label, "ok")[key])
    return result


def summarize_algorithm_result(result: dict[str, Any]) -> dict[str, Any]:
    summary = {
        "maze_id": result.get("maze_id"),
        "algorithm": result.get("algorithm"),
        "status": result.get("status", "ok"),
        "success": result.get("success"),
        "path_length": result.get("path_length"),
        "turn_count": result.get("turn_count"),
        "explored_nodes": result.get("explored_nodes"),
        "runtime_ms": result.get("runtime_ms"),
        "total_cost": result.get("total_cost"),
        "replan_count": result.get("replan_count"),
        "replan_time_ms": result.get("replan_time_ms"),
        "updated_nodes": result.get("updated_nodes"),
        "replanned_path_length": result.get("replanned_path_length"),
    }
    return summary
