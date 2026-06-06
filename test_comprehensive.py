#!/usr/bin/env python3
"""Comprehensive smoke test for the full project pipeline."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.load_map import load_map
from src.main import run_pipeline


def main() -> None:
    project_root = Path(__file__).resolve().parent
    maps_dir = project_root / "maps" / "json"
    maps = [m for m in sorted(maps_dir.glob("*.json")) if m.name != "manifest.json"][:2]

    results: list[dict[str, object]] = []

    print("=" * 90)
    print("FULL PROJECT SMOKE TEST")
    print("Testing BFS / DFS / A* / Cost-aware A* / Weighted A* / LPA* / D* Lite")
    print("=" * 90)
    print()

    for index, map_path in enumerate(maps, start=1):
        map_data = load_map(map_path)
        run_name = f"comprehensive_smoke_{index:02d}_{map_data['maze_id']}"
        output_dir = project_root / "outputs" / "tests" / run_name

        print(f"Processing: {map_path.name}")
        try:
            pipeline_result = run_pipeline(
                static_map_file=map_path,
                output_dir=output_dir,
                variant_index=1,
                seed=42,
                visualize_mode="text",
                skip_visualization=True,
            )
            summary = {
                "maze_id": map_data["maze_id"],
                "run_output_dir": str(output_dir),
                "algorithms": {
                    key: {
                        "status": value.get("status"),
                        "success": value.get("success"),
                        "path_length": value.get("path_length"),
                        "turn_count": value.get("turn_count"),
                        "explored_nodes": value.get("explored_nodes"),
                        "runtime_ms": value.get("runtime_ms"),
                        "total_cost": value.get("total_cost"),
                        "replan_count": value.get("replan_count"),
                        "updated_nodes": value.get("updated_nodes"),
                    }
                    for key, value in pipeline_result["algorithm_results"].items()
                },
            }
            results.append(summary)
            print("  [OK]")
        except Exception as exc:
            results.append(
                {
                    "maze_id": map_data["maze_id"],
                    "run_output_dir": str(output_dir),
                    "error": str(exc),
                }
            )
            print(f"  [ERROR] {exc}")

    print()
    print("=" * 90)
    print("SUMMARY TABLE")
    print("=" * 90)
    print()

    headers = [
        ("Algorithm", 16),
        ("Status", 12),
        ("Success", 8),
        ("Path Len", 10),
        ("Turns", 8),
        ("Nodes", 8),
        ("Time(ms)", 12),
        ("Cost", 10),
        ("Replan", 8),
    ]

    for result in results:
        print(f"Maze: {result['maze_id']}")
        if "error" in result:
            print(f"  [ERROR] {result['error']}")
            print()
            continue

        header_line = " ".join(f"{name:<{width}}" for name, width in headers)
        print(header_line)
        print("-" * len(header_line))

        algorithms = result["algorithms"]
        assert isinstance(algorithms, dict)
        for key, data in algorithms.items():
            assert isinstance(data, dict)
            print(
                f"{key:<16} "
                f"{str(data.get('status')):<12} "
                f"{str(data.get('success')):<8} "
                f"{str(data.get('path_length')):<10} "
                f"{str(data.get('turn_count')):<8} "
                f"{str(data.get('explored_nodes')):<8} "
                f"{float(data.get('runtime_ms', 0.0)):<12.4f} "
                f"{str(data.get('total_cost')):<10} "
                f"{str(data.get('replan_count')):<8}"
            )
        print()

    output_path = project_root / "outputs" / "tests" / "comprehensive_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Results saved to: {output_path}")


if __name__ == "__main__":
    main()
