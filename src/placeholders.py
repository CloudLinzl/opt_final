"""Shared placeholder helpers for not-yet-implemented algorithms."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.load_map import load_map


def build_not_implemented_result(
    map_input: str | Path | dict[str, Any],
    *,
    algorithm: str,
    status: str = "not_implemented",
) -> dict[str, Any]:
    map_data = load_map(map_input) if isinstance(map_input, (str, Path)) else map_input
    return {
        "maze_id": map_data["maze_id"],
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
