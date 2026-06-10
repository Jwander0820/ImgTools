from __future__ import annotations

from pathlib import Path
from typing import Any

from imgtools.service.registry import ToolSpec


def ensure_output_allowed(path: str | Path, *, overwrite: bool = False) -> None:
    resolved = Path(path).expanduser().resolve()
    if resolved.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {resolved}")


def default_params_for_safety(spec: ToolSpec, params: dict[str, Any]) -> dict[str, Any]:
    safe_params = dict(params)
    if spec.danger_level == "high" and "confirm" not in safe_params:
        safe_params["confirm"] = False
    return safe_params

