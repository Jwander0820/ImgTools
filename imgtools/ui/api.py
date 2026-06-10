from __future__ import annotations

from typing import Any

from imgtools.service.registry import list_tools
from imgtools.service.runner import run_tool


def handle_get_tools() -> dict[str, Any]:
    return {"ok": True, "tools": list_tools()}


def handle_run(payload: dict[str, Any]) -> dict[str, Any]:
    action = payload.get("action")
    if not action:
        return {
            "ok": False,
            "error_code": "VALIDATION_ERROR",
            "message": "Missing required field: action",
            "outputs": {},
            "warnings": [],
        }
    return run_tool(str(action), payload.get("params", {}))

