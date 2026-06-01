#!/usr/bin/env python3
"""
Build one dynamic map variant from one static map.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from scripts.generate_dynamic_maps import annotate_dynamic_map, build_dynamic_updates  # noqa: E402
from scripts.load_map import load_map  # noqa: E402


DEFAULT_DYNAMIC_CONFIG = {
    "update_count": 3,
    "max_cells_per_update": 2,
    "step_min": 10,
    "step_max": 80,
    "path_bias": 0.65,
    "near_path_bias": 0.25,
    "path_margin": 2,
    "safety_radius": 1,
    "preserve_solvable": True,
}


def create_dynamic_map_variant(
    map_input: str | Path | dict[str, Any],
    *,
    output_dir: str | Path,
    variant_index: int = 1,
    seed: int = 42,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    config = {**DEFAULT_DYNAMIC_CONFIG, **(config or {})}
    map_data = load_map(map_input) if isinstance(map_input, (str, Path)) else map_input

    base_name = map_data["maze_id"]
    rng = random.Random(seed)
    dynamic_updates = build_dynamic_updates(
        map_data,
        rng=rng,
        update_count=config["update_count"],
        max_cells_per_update=config["max_cells_per_update"],
        step_min=config["step_min"],
        step_max=config["step_max"],
        path_bias=config["path_bias"],
        near_path_bias=config["near_path_bias"],
        path_margin=config["path_margin"],
        safety_radius=config["safety_radius"],
        preserve_solvable=config["preserve_solvable"],
    )

    dynamic_map_data = annotate_dynamic_map(
        map_data,
        dynamic_updates=dynamic_updates,
        variant_index=variant_index,
        base_name=base_name,
        generation_settings=config,
    )

    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    output_name = f"{base_name}_dynamic_{variant_index}.json"
    output_path = output_root / output_name
    output_path.write_text(
        json.dumps(dynamic_map_data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    return {
        "dynamic_map_data": dynamic_map_data,
        "dynamic_updates": dynamic_updates,
        "dynamic_map_file": str(output_path),
        "dynamic_generation_config": config,
    }
