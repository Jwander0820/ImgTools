from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path
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
        result: dict[str, Any] = {"ok": True, "paths": paths}
        if bool(payload.get("include_previews")) and mode in {"file", "files"}:
            previews = []
            for path in paths[:24]:
                try:
                    previews.append({"path": path, **_preview_data(path)})
                except Exception as exc:
                    previews.append({"path": path, "error": str(exc)})
            result["previews"] = previews
        return result
    except Exception as exc:
        return {
            "ok": False,
            "error_code": exc.__class__.__name__,
            "message": f"無法開啟本機選擇器：{exc}",
            "paths": [],
        }


def _preview_data(path: str, *, max_width: int = 960) -> dict[str, Any]:
    """Encode an explicitly picker-selected image for the in-browser preview."""
    from PIL import Image, ImageOps

    input_path = Path(path).expanduser().resolve()
    if not input_path.is_file():
        raise FileNotFoundError(f"Preview image does not exist: {input_path}")

    with Image.open(input_path) as source:
        oriented = ImageOps.exif_transpose(source)
        original_width, original_height = oriented.size
        preview = oriented.convert("RGBA")
        try:
            if preview.width > max_width:
                height = max(1, round(preview.height * max_width / preview.width))
                rendered = preview.resize((max_width, height), Image.Resampling.LANCZOS)
            else:
                rendered = preview.copy()
        finally:
            preview.close()

    try:
        output = BytesIO()
        rendered.save(output, "PNG")
        encoded = base64.b64encode(output.getvalue()).decode("ascii")
        return {
            "data_url": f"data:image/png;base64,{encoded}",
            "width": original_width,
            "height": original_height,
        }
    finally:
        rendered.close()
