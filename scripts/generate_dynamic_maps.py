#!/usr/bin/env python3
"""
Generate dynamic map variants from static JSON maps.

Each output file preserves the original map structure and appends randomized
dynamic_updates for use with LPA* / D* Lite experiments.
"""

from __future__ import annotations

import argparse
from collections import deque
import json
import random
from copy import deepcopy
from pathlib import Path
from typing import Any

try:
    from .load_map import load_map, get_neighbors
except ImportError:
    from load_map import load_map, get_neighbors


def list_walkable_cells(map_data: dict[str, Any]) -> list[list[int]]:
    width = map_data["width"]
    height = map_data["height"]
    return [[x, y] for y in range(height) for x in range(width)]


def within_manhattan_radius(a: list[int], b: list[int], radius: int) -> bool:
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) <= radius


def valid_block_candidates(map_data: dict[str, Any], safety_radius: int) -> list[list[int]]:
    protected_points = [map_data["start"], map_data["goal"], *map_data.get("goal_cells", [])]
    candidates: list[list[int]] = []
    for cell in list_walkable_cells(map_data):
        if any(within_manhattan_radius(cell, point, safety_radius) for point in protected_points):
            continue
        candidates.append(cell)
    return candidates


def get_neighbors_with_blocked(
    map_data: dict[str, Any],
    x: int,
    y: int,
    blocked_cells: set[tuple[int, int]],
) -> list[list[int]]:
    neighbors = get_neighbors(map_data, x, y)
    return [cell for cell in neighbors if tuple(cell) not in blocked_cells]


def shortest_path(
    map_data: dict[str, Any],
    blocked_cells: set[tuple[int, int]] | None = None,
) -> list[list[int]]:
    blocked = blocked_cells or set()
    start = map_data["start"]
    goals = {tuple(cell) for cell in map_data.get("goal_cells", [map_data["goal"]])}

    if tuple(start) in blocked:
        return []

    queue: deque[list[int]] = deque([start])
    parents: dict[tuple[int, int], tuple[int, int] | None] = {tuple(start): None}

    found_goal: tuple[int, int] | None = None
    while queue:
        current = queue.popleft()
        current_key = tuple(current)
        if current_key in goals:
            found_goal = current_key
            break
        for nx, ny in get_neighbors_with_blocked(map_data, current[0], current[1], blocked):
            key = (nx, ny)
            if key not in parents:
                parents[key] = current_key
                queue.append([nx, ny])

    if found_goal is None:
        return []

    path_rev: list[list[int]] = []
    cursor: tuple[int, int] | None = found_goal
    while cursor is not None:
        path_rev.append([cursor[0], cursor[1]])
        cursor = parents[cursor]
    path_rev.reverse()
    return path_rev


def build_candidate_groups(
    map_data: dict[str, Any],
    path_margin: int,
    safety_radius: int,
) -> tuple[list[list[int]], list[list[int]], list[list[int]], list[list[int]]]:
    all_candidates = valid_block_candidates(map_data, safety_radius=safety_radius)
    base_path = shortest_path(map_data)
    if not base_path:
        return [], [], all_candidates, []

    trimmed_path = base_path[path_margin: len(base_path) - path_margin]
    if not trimmed_path:
        trimmed_path = base_path[1:-1]

    path_cells = [cell for cell in trimmed_path if cell not in map_data.get("goal_cells", [])]
    path_keys = {tuple(cell) for cell in path_cells}

    near_path_keys: set[tuple[int, int]] = set()
    for x, y in path_cells:
        for neighbor in get_neighbors(map_data, x, y):
            key = tuple(neighbor)
            if key not in path_keys:
                near_path_keys.add(key)

    general = [
        cell
        for cell in all_candidates
        if tuple(cell) not in path_keys and tuple(cell) not in near_path_keys
    ]
    near_path = [list(cell) for cell in sorted(near_path_keys)]
    return path_cells, near_path, general, base_path


def random_update_steps(
    rng: random.Random,
    update_count: int,
    step_min: int,
    step_max: int,
) -> list[int]:
    if update_count <= 0:
        return []
    step_pool = list(range(step_min, step_max + 1))
    if update_count > len(step_pool):
        raise ValueError("update_count is larger than available unique step values")
    return sorted(rng.sample(step_pool, update_count))


def weighted_group_order(
    rng: random.Random,
    path_bias: float,
    near_path_bias: float,
) -> list[str]:
    roll = rng.random()
    if roll < path_bias:
        return ["path", "near", "general"]
    if roll < path_bias + near_path_bias:
        return ["near", "path", "general"]
    return ["general", "near", "path"]


def path_exists_after_block(
    map_data: dict[str, Any],
    blocked_cells: set[tuple[int, int]],
) -> bool:
    return bool(shortest_path(map_data, blocked_cells))


def choose_blocked_cells(
    map_data: dict[str, Any],
    rng: random.Random,
    path_candidates: list[list[int]],
    near_path_candidates: list[list[int]],
    general_candidates: list[list[int]],
    used: set[tuple[int, int]],
    already_blocked: set[tuple[int, int]],
    max_cells_per_update: int,
    path_bias: float,
    near_path_bias: float,
    preserve_solvable: bool,
) -> list[list[int]]:
    candidate_groups = {
        "path": path_candidates,
        "near": near_path_candidates,
        "general": general_candidates,
    }

    available_total = [
        cell
        for group in candidate_groups.values()
        for cell in group
        if tuple(cell) not in used and tuple(cell) not in already_blocked
    ]
    if not available_total:
        return []

    count = rng.randint(1, min(max_cells_per_update, len(available_total)))
    blocked: list[list[int]] = []

    for _ in range(count):
        selected = None
        for _attempt in range(50):
            group_order = weighted_group_order(rng, path_bias, near_path_bias)
            pool: list[list[int]] = []
            for group_name in group_order:
                pool = [
                    cell
                    for cell in candidate_groups[group_name]
                    if tuple(cell) not in used and tuple(cell) not in already_blocked
                ]
                if pool:
                    break
            if not pool:
                break

            candidate = rng.choice(pool)
            candidate_key = tuple(candidate)
            test_blocked = set(already_blocked)
            test_blocked.update(tuple(cell) for cell in blocked)
            test_blocked.add(candidate_key)

            if preserve_solvable and not path_exists_after_block(map_data, test_blocked):
                continue

            selected = candidate
            break

        if selected is None:
            break

        blocked.append(selected)
        used.add(tuple(selected))

    return blocked


def build_dynamic_updates(
    map_data: dict[str, Any],
    rng: random.Random,
    update_count: int,
    max_cells_per_update: int,
    step_min: int,
    step_max: int,
    path_bias: float,
    near_path_bias: float,
    path_margin: int,
    safety_radius: int,
    preserve_solvable: bool,
) -> list[dict[str, Any]]:
    path_candidates, near_path_candidates, general_candidates, _base_path = build_candidate_groups(
        map_data,
        path_margin=path_margin,
        safety_radius=safety_radius,
    )
    steps = random_update_steps(rng, update_count, step_min, step_max)
    used_cells: set[tuple[int, int]] = set()
    cumulative_blocked: set[tuple[int, int]] = set()

    updates: list[dict[str, Any]] = []
    for step in steps:
        blocked_cells = choose_blocked_cells(
            map_data,
            rng=rng,
            path_candidates=path_candidates,
            near_path_candidates=near_path_candidates,
            general_candidates=general_candidates,
            used=used_cells,
            already_blocked=cumulative_blocked,
            max_cells_per_update=max_cells_per_update,
            path_bias=path_bias,
            near_path_bias=near_path_bias,
            preserve_solvable=preserve_solvable,
        )
        if not blocked_cells:
            break
        if preserve_solvable:
            test_blocked = set(cumulative_blocked)
            test_blocked.update(tuple(cell) for cell in blocked_cells)
            if not path_exists_after_block(map_data, test_blocked):
                continue
        cumulative_blocked.update(tuple(cell) for cell in blocked_cells)
        updates.append(
            {
                "step": step,
                "blocked_cells": blocked_cells,
                "released_cells": [],
            }
        )
    return updates


def annotate_dynamic_map(
    map_data: dict[str, Any],
    dynamic_updates: list[dict[str, Any]],
    variant_index: int,
    base_name: str,
    generation_settings: dict[str, Any],
) -> dict[str, Any]:
    result = deepcopy(map_data)
    result["maze_id"] = f"{base_name}_dynamic_{variant_index}"
    result["dynamic_updates"] = dynamic_updates
    result["dynamic_metadata"] = {
        "base_maze_id": map_data["maze_id"],
        "variant_index": variant_index,
        "update_count": len(dynamic_updates),
        "generation_mode": "path_aware_random",
        "generation_settings": generation_settings,
    }
    return result


def write_dynamic_map(output_path: Path, map_data: dict[str, Any]) -> None:
    output_path.write_text(
        json.dumps(map_data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def generate_dynamic_variants(
    input_dir: Path,
    output_dir: Path,
    variants_per_map: int,
    update_count: int,
    max_cells_per_update: int,
    step_min: int,
    step_max: int,
    seed: int,
    path_bias: float,
    near_path_bias: float,
    path_margin: int,
    safety_radius: int,
    preserve_solvable: bool,
) -> list[dict[str, Any]]:
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest: list[dict[str, Any]] = []
    json_files = sorted(path for path in input_dir.glob("*.json") if path.name != "manifest.json")
    if not json_files:
        raise ValueError(f"no static json maps found in {input_dir}")

    rng = random.Random(seed)
    generation_settings = {
        "path_bias": path_bias,
        "near_path_bias": near_path_bias,
        "path_margin": path_margin,
        "safety_radius": safety_radius,
        "preserve_solvable": preserve_solvable,
    }

    for map_path in json_files:
        base_map = load_map(map_path)
        base_name = map_path.stem

        for index in range(1, variants_per_map + 1):
            dynamic_updates = build_dynamic_updates(
                base_map,
                rng=rng,
                update_count=update_count,
                max_cells_per_update=max_cells_per_update,
                step_min=step_min,
                step_max=step_max,
                path_bias=path_bias,
                near_path_bias=near_path_bias,
                path_margin=path_margin,
                safety_radius=safety_radius,
                preserve_solvable=preserve_solvable,
            )
            dynamic_map = annotate_dynamic_map(
                base_map,
                dynamic_updates=dynamic_updates,
                variant_index=index,
                base_name=base_name,
                generation_settings=generation_settings,
            )
            output_name = f"{base_name}_dynamic_{index}.json"
            output_path = output_dir / output_name
            write_dynamic_map(output_path, dynamic_map)
            manifest.append(
                {
                    "base_map": map_path.name,
                    "output_file": output_name,
                    "maze_id": dynamic_map["maze_id"],
                    "update_count": len(dynamic_updates),
                    "generation_mode": "path_aware_random",
                    "generation_settings": generation_settings,
                    "dynamic_updates": dynamic_updates,
                }
            )

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate randomized dynamic map variants from static JSON maps."
    )
    root = Path(__file__).resolve().parent.parent
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=root / "maps" / "json",
        help="Directory containing static JSON maps",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=root / "maps" / "dynamic_json",
        help="Directory to write generated dynamic JSON maps",
    )
    parser.add_argument(
        "--variants-per-map",
        type=int,
        default=1,
        help="How many dynamic variants to generate for each base map",
    )
    parser.add_argument(
        "--update-count",
        type=int,
        default=3,
        help="How many dynamic update events to generate per map",
    )
    parser.add_argument(
        "--max-cells-per-update",
        type=int,
        default=2,
        help="Maximum blocked cells introduced in a single update event",
    )
    parser.add_argument(
        "--step-min",
        type=int,
        default=10,
        help="Minimum step value for dynamic updates",
    )
    parser.add_argument(
        "--step-max",
        type=int,
        default=80,
        help="Maximum step value for dynamic updates",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible map generation",
    )
    parser.add_argument(
        "--path-bias",
        type=float,
        default=0.65,
        help="Probability of prioritizing shortest-path cells when generating obstacles",
    )
    parser.add_argument(
        "--near-path-bias",
        type=float,
        default=0.25,
        help="Probability of prioritizing cells adjacent to the shortest path",
    )
    parser.add_argument(
        "--path-margin",
        type=int,
        default=2,
        help="Number of cells near path ends that should be avoided when selecting path obstacles",
    )
    parser.add_argument(
        "--safety-radius",
        type=int,
        default=1,
        help="Manhattan radius around start/goal cells where dynamic obstacles are not generated",
    )
    parser.add_argument(
        "--allow-disconnect",
        action="store_true",
        help="Allow generated updates to disconnect the maze; default keeps a valid path",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    manifest = generate_dynamic_variants(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        variants_per_map=args.variants_per_map,
        update_count=args.update_count,
        max_cells_per_update=args.max_cells_per_update,
        step_min=args.step_min,
        step_max=args.step_max,
        seed=args.seed,
        path_bias=args.path_bias,
        near_path_bias=args.near_path_bias,
        path_margin=args.path_margin,
        safety_radius=args.safety_radius,
        preserve_solvable=not args.allow_disconnect,
    )
    print(f"Generated {len(manifest)} dynamic map files in {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
