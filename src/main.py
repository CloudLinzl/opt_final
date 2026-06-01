#!/usr/bin/env python3
"""
Project main entry for orchestrating map loading, dynamic generation,
algorithm execution, result saving, and visualization placeholders.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from scripts.load_map import load_map, summarize_map  # noqa: E402
from src.algorithm_registry import (  # noqa: E402
    default_registry,
    run_registered_algorithm,
    summarize_algorithm_result,
)
from src.dynamic_map_builder import DEFAULT_DYNAMIC_CONFIG, create_dynamic_map_variant  # noqa: E402
from src.visualization import visualize_result, write_visualization_manifest  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the project pipeline on one static map.")
    parser.add_argument(
        "--static-map",
        type=Path,
        default=PROJECT_ROOT / "maps" / "json" / "alljapan-045-2024-exp-fin.json",
        help="Path to one static JSON map",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "outputs",
        help="Directory for pipeline outputs",
    )
    parser.add_argument("--variant-index", type=int, default=1, help="Dynamic variant index")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for dynamic map generation")
    parser.add_argument(
        "--visualize-mode",
        choices=["text", "image"],
        default="text",
        help="Visualization output mode",
    )
    parser.add_argument(
        "--skip-visualization",
        action="store_true",
        help="Skip visualization artifact generation",
    )
    return parser


def save_json(data: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_pipeline(
    *,
    static_map_file: str | Path,
    output_dir: str | Path,
    variant_index: int = 1,
    seed: int = 42,
    visualize_mode: str = "text",
    skip_visualization: bool = False,
    dynamic_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    static_map_path = Path(static_map_file)
    out_root = Path(output_dir)
    out_root.mkdir(parents=True, exist_ok=True)

    static_map_data = load_map(static_map_path)
    dynamic_dir = out_root / "dynamic_maps"
    results_dir = out_root / "results"
    visuals_dir = out_root / "visualizations"

    dynamic_bundle = create_dynamic_map_variant(
        static_map_data,
        output_dir=dynamic_dir,
        variant_index=variant_index,
        seed=seed,
        config=dynamic_config,
    )

    algorithm_results: dict[str, dict[str, Any]] = {}
    visualization_artifacts: dict[str, dict[str, Any]] = {}

    registry = default_registry()
    for registration in registry:
        if registration.dynamic:
            map_input = static_map_data
            result = run_registered_algorithm(
                registration,
                map_input=map_input,
                map_data=dynamic_bundle["dynamic_map_data"],
                dynamic_updates=dynamic_bundle["dynamic_updates"],
            )
            visualization_map = dynamic_bundle["dynamic_map_data"]
        else:
            map_input = static_map_data
            result = run_registered_algorithm(
                registration,
                map_input=map_input,
                map_data=static_map_data,
            )
            visualization_map = static_map_data

        algorithm_results[registration.key] = result

        if skip_visualization:
            visualization_artifacts[registration.key] = {
                "status": "skipped",
                "mode": visualize_mode,
                "artifact_type": "none",
            }
        else:
            suffix = "txt" if visualize_mode == "text" else "png"
            artifact_path = visuals_dir / f"{registration.key}.{suffix}"
            visualization_artifacts[registration.key] = visualize_result(
                visualization_map,
                result,
                output_path=artifact_path,
                mode=visualize_mode,
            )

    timestamp = datetime.now().isoformat(timespec="seconds")
    total_result = {
        "static_map_file": str(static_map_path),
        "static_map": summarize_map(static_map_data),
        "dynamic_map_file": dynamic_bundle["dynamic_map_file"],
        "dynamic_updates": dynamic_bundle["dynamic_updates"],
        "dynamic_generation_config": dynamic_bundle["dynamic_generation_config"],
        "algorithm_results": algorithm_results,
        "visualization_artifacts": visualization_artifacts,
        "run_metadata": {
            "timestamp": timestamp,
            "seed": seed,
            "variant_index": variant_index,
            "visualize_mode": visualize_mode,
            "skip_visualization": skip_visualization,
        },
    }

    summary_result = {
        "static_map_file": str(static_map_path),
        "dynamic_map_file": dynamic_bundle["dynamic_map_file"],
        "algorithm_results": {
            key: summarize_algorithm_result(result)
            for key, result in algorithm_results.items()
        },
        "run_metadata": total_result["run_metadata"],
    }

    save_json(total_result, results_dir / "run_result.json")
    save_json(summary_result, results_dir / "run_summary.json")
    write_visualization_manifest(visualization_artifacts, visuals_dir / "manifest.json")

    return total_result


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    dynamic_config = dict(DEFAULT_DYNAMIC_CONFIG)
    run_pipeline(
        static_map_file=args.static_map,
        output_dir=args.output_dir,
        variant_index=args.variant_index,
        seed=args.seed,
        visualize_mode=args.visualize_mode,
        skip_visualization=args.skip_visualization,
        dynamic_config=dynamic_config,
    )


if __name__ == "__main__":
    main()
