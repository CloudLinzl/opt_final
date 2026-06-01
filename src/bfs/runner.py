"""BFS placeholder entry."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.placeholders import build_not_implemented_result


def run_bfs(map_input: str | Path | dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    del kwargs
    return build_not_implemented_result(map_input, algorithm="BFS")
