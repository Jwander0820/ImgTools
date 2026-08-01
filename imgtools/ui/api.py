from __future__ import annotations

from typing import Any

from imgtools.service.registry import get_tool, list_tools
from imgtools.service.runner import run_tool
from imgtools.service.preferences import (
    PreferenceValidationError,
    get_preferences_view,
    record_successful_run,
    update_pdf_default_dpi,
    update_pinned_actions,
)
from imgtools.ui.picker import pick_paths


PICKER_MODES = {"file", "files", "folder", "save"}


def handle_get_tools() -> dict[str, Any]:
    return {"ok": True, "tools": list_tools()}


def handle_get_tool(action: str) -> dict[str, Any]:
    try:
        return {"ok": True, "tool": get_tool(action).to_dict()}
    except KeyError:
        return {
            "ok": False,
            "error_code": "UNKNOWN_ACTION",
            "message": f"Unknown action: {action}",
        }


def handle_get_preferences() -> dict[str, Any]:
    return {"ok": True, **get_preferences_view()}


def handle_update_preferences(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        if "pdf_default_dpi" in payload:
            view = update_pdf_default_dpi(payload["pdf_default_dpi"])
        elif "pinned_actions" in payload:
            view = update_pinned_actions(payload["pinned_actions"])
        else:
            raise PreferenceValidationError(
                "Provide pinned_actions or pdf_default_dpi"
            )
        return {"ok": True, **view}
    except PreferenceValidationError as exc:
        return {
            "ok": False,
            "error_code": "VALIDATION_ERROR",
            "message": str(exc),
        }


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
    action = str(action)
    result = run_tool(action, payload.get("params", {}))
    if result.get("ok"):
        try:
            record_successful_run(action)
        except Exception as exc:
            result.setdefault("warnings", []).append(f"無法保存常用功能紀錄：{exc}")
    return result


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
