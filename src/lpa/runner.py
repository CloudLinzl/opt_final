"""LPA* placeholder entry."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.placeholders import build_not_implemented_result


def run_lpa(
    map_input: str | Path | dict[str, Any],
    dynamic_updates: list[dict[str, Any]] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    del dynamic_updates, kwargs
    return build_not_implemented_result(map_input, algorithm="LPA*")
