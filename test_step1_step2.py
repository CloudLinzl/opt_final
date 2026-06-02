#!/usr/bin/env python3
"""Test script for BFS and A* (Step 1 and Step 2)."""

import json
from pathlib import Path
from scripts.load_map import load_map
from src.bfs.runner import run_bfs
from src.a_star.runner import run_a_star

def main():
    # Test map
    map_path = Path("maps/json/alljapan-045-2024-exp-fin.json")
    print(f"Loading map from {map_path}...")

    map_data = load_map(map_path)
    print(f"[OK] Map loaded: {map_data['maze_id']}")
    print(f"  Size: {map_data['width']}x{map_data['height']}")
    print(f"  Start: {map_data['start']}, Goal: {map_data['goal']}")
    print()

    # Step 1: BFS
    print("=" * 60)
    print("STEP 1: BFS Algorithm (Static, Unweighted Shortest Path)")
    print("=" * 60)
    bfs_result = run_bfs(map_data)
    print(json.dumps(bfs_result, indent=2, ensure_ascii=False))
    print()

    # Step 2: A*
    print("=" * 60)
    print("STEP 2: A* Algorithm (Search Efficiency Optimization)")
    print("=" * 60)
    astar_result = run_a_star(map_data)
    print(json.dumps(astar_result, indent=2, ensure_ascii=False))
    print()

    # Comparison
    print("=" * 60)
    print("COMPARISON: BFS vs A*")
    print("=" * 60)
    print(f"BFS Results:")
    print(f"  Success: {bfs_result['success']}")
    print(f"  Path Length: {bfs_result['path_length']}")
    print(f"  Turn Count: {bfs_result['turn_count']}")
    print(f"  Explored Nodes: {bfs_result['explored_nodes']}")
    print(f"  Runtime: {bfs_result['runtime_ms']:.3f} ms")
    print(f"  Total Cost: {bfs_result['total_cost']}")
    print()

    print(f"A* Results:")
    print(f"  Success: {astar_result['success']}")
    print(f"  Path Length: {astar_result['path_length']}")
    print(f"  Turn Count: {astar_result['turn_count']}")
    print(f"  Explored Nodes: {astar_result['explored_nodes']}")
    print(f"  Runtime: {astar_result['runtime_ms']:.3f} ms")
    print(f"  Total Cost: {astar_result['total_cost']}")
    print()

    print("Analysis:")
    if bfs_result['path_length'] == astar_result['path_length']:
        print(f"[OK] Both algorithms found path of same length: {bfs_result['path_length']}")
    else:
        print(f"[DIFF] Path lengths differ: BFS={bfs_result['path_length']}, A*={astar_result['path_length']}")

    efficiency_gain = ((bfs_result['explored_nodes'] - astar_result['explored_nodes'])
                       / bfs_result['explored_nodes'] * 100)
    print(f"[OK] A* explored {efficiency_gain:.1f}% fewer nodes than BFS")

    speedup = bfs_result['runtime_ms'] / astar_result['runtime_ms']
    print(f"[OK] A* is {speedup:.2f}x faster than BFS")

if __name__ == "__main__":
    main()
