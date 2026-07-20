from __future__ import annotations

from typing import Any

from imgtools.service.registry import list_tools
from imgtools.service.runner import run_tool
from imgtools.ui.picker import pick_paths


PICKER_MODES = {"file", "files", "folder", "save"}


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


def handle_pick(payload: dict[str, Any]) -> dict[str, Any]:
    mode = str(payload.get("mode", ""))
    if mode not in PICKER_MODES:
        return {
            "ok": False,
            "error_code": "VALIDATION_ERROR",
            "message": "mode must be one of: file, files, folder, save",
            "paths": [],
        }
    try:
        paths = pick_paths(
            mode,
            title=str(payload.get("title") or "選擇檔案"),
            default_name=str(payload.get("default_name") or ""),
        )
        return {"ok": True, "paths": paths}
    except Exception as exc:
        return {
            "ok": False,
            "error_code": exc.__class__.__name__,
            "message": f"無法開啟本機選擇器：{exc}",
            "paths": [],
        }
