#!/usr/bin/env python3
"""Comprehensive test for BFS and A* on multiple maps."""

import json
from pathlib import Path

from scripts.load_map import load_map
from src.bfs.runner import run_bfs
from src.a_star.runner import run_a_star

def main():
    maps_dir = Path("maps/json")
    maps = [m for m in sorted(maps_dir.glob("*.json")) if m.name != "manifest.json"][:3]

    results = []

    print("=" * 80)
    print("STEP 1 & STEP 2: BFS vs A* Algorithm Comparison")
    print("Testing on multiple maze maps")
    print("=" * 80)
    print()

    for map_path in maps:
        print(f"Processing: {map_path.name}")
        try:
            map_data = load_map(map_path)

            bfs_result = run_bfs(map_data)
            astar_result = run_a_star(map_data)

            results.append({
                "map": map_data["maze_id"],
                "bfs": bfs_result,
                "astar": astar_result
            })
            print(f"  [OK]")
        except Exception as e:
            print(f"  [ERROR] {e}")

    print()
    print("=" * 80)
    print("SUMMARY TABLE")
    print("=" * 80)
    print()

    print("Algorithm Comparison Summary")
    print("-" * 80)
    print(f"{'Maze ID':<30} {'Algorithm':<12} {'Success':<8} {'Path Len':<10} {'Turns':<8} {'Nodes':<8} {'Time(ms)':<10}")
    print("-" * 80)

    for result in results:
        bfs = result["bfs"]
        astar = result["astar"]

        print(f"{bfs['maze_id'][:29]:<30} {'BFS':<12} {str(bfs['success']):<8} {bfs['path_length']:<10} {bfs['turn_count']:<8} {bfs['explored_nodes']:<8} {bfs['runtime_ms']:<10.4f}")
        print(f"{'':<30} {'A*':<12} {str(astar['success']):<8} {astar['path_length']:<10} {astar['turn_count']:<8} {astar['explored_nodes']:<8} {astar['runtime_ms']:<10.4f}")
        print()

    print("=" * 80)
    print("DETAILED ANALYSIS")
    print("=" * 80)
    print()

    for result in results:
        maze_id = result["map"]
        bfs = result["bfs"]
        astar = result["astar"]

        print(f"Map: {maze_id}")
        print("-" * 60)

        # Path quality
        if bfs["success"] and astar["success"]:
            if bfs["path_length"] == astar["path_length"]:
                print(f"Path Quality: Both found same shortest path length = {bfs['path_length']}")
            else:
                print(f"Path Quality: DIFFERENT - BFS={bfs['path_length']}, A*={astar['path_length']}")

        # Search efficiency
        if bfs["explored_nodes"] > 0:
            reduction = (bfs["explored_nodes"] - astar["explored_nodes"]) / bfs["explored_nodes"] * 100
            print(f"Search Efficiency: A* explored {reduction:+.1f}% nodes ({astar['explored_nodes']} vs {bfs['explored_nodes']})")

        # Runtime
        if bfs["runtime_ms"] > 0:
            speedup = bfs["runtime_ms"] / astar["runtime_ms"]
            print(f"Execution Speed: A* is {speedup:.2f}x ({astar['runtime_ms']:.3f}ms vs {bfs['runtime_ms']:.3f}ms)")

        print()

    # Save results
    output_path = Path("outputs") / "tests" / "step1_step2_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Results saved to: {output_path}")

if __name__ == "__main__":
    main()
