#!/usr/bin/env python3
"""
Unified visualization interface placeholder.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.dlite import render_map_snapshot  # noqa: E402


def visualize_result(
    map_data: dict[str, Any],
    algorithm_result: dict[str, Any],
    output_path: str | Path | None = None,
    mode: str = "text",
) -> dict[str, Any]:
    if mode == "image":
        return {
            "status": "not_implemented",
            "mode": "image",
            "output_path": str(output_path) if output_path else None,
            "artifact_type": "image",
        }

    path = algorithm_result.get("path", []) if algorithm_result.get("success") else []
    snapshot = render_map_snapshot(map_data, path=path)
    artifact: dict[str, Any] = {
        "status": "ok",
        "mode": "text",
        "artifact_type": "text",
        "output_path": str(output_path) if output_path else None,
        "render": snapshot,
    }

    if output_path:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(snapshot + "\n", encoding="utf-8")

    return artifact


def write_visualization_manifest(
    artifacts: dict[str, dict[str, Any]],
    output_path: str | Path,
) -> None:
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(artifacts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
