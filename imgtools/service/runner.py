from __future__ import annotations

from typing import Any

from imgtools.core.common import OUTPUT_NAMING_FIXED, OUTPUT_NAMING_MODES

from .manifest import now_iso, write_manifest
from .registry import ToolParam, get_tool
from .safety import default_params_for_safety


class ToolValidationError(ValueError):
    pass


def run_tool(action: str, raw_params: dict[str, Any], *, manifest: bool = True) -> dict[str, Any]:
    started_at = now_iso()
    params = dict(raw_params)
    try:
        spec = get_tool(action)
        params = _prepare_params(spec.params, raw_params)
        params = default_params_for_safety(spec, params)
        result = spec.handler(params)
        result.setdefault("ok", True)
        result.setdefault("action", action)
        result.setdefault("outputs", {})
        result.setdefault("warnings", [])
    except ToolValidationError as exc:
        result = _error(action, "VALIDATION_ERROR", str(exc))
    except KeyError as exc:
        result = _error(action, "UNKNOWN_ACTION", str(exc))
    except Exception as exc:
        result = _error(action, getattr(exc, "error_code", exc.__class__.__name__), str(exc))

    result["action"] = action
    finished_at = now_iso()
    if manifest:
        try:
            result["manifest_path"] = write_manifest(action, params, result, started_at, finished_at)
        except Exception as exc:
            result.setdefault("warnings", []).append(f"Manifest write failed: {exc}")
    return result


def _prepare_params(spec_params: tuple[ToolParam, ...], raw_params: dict[str, Any]) -> dict[str, Any]:
    params: dict[str, Any] = {}
    for param in spec_params:
        value = raw_params.get(param.name, param.default)
        if param.required and _is_empty(value):
            raise ToolValidationError(f"Missing required parameter: {param.name}")
        if _is_empty(value) and param.default is None:
            continue
        value = _coerce(param, value)
        if param.choices and value not in param.choices:
            choices = ", ".join(param.choices)
            raise ToolValidationError(f"{param.name} must be one of: {choices}")
        params[param.name] = value
    output_naming = raw_params.get("output_naming")
    if not _is_empty(output_naming):
        output_naming = str(output_naming)
        if output_naming not in OUTPUT_NAMING_MODES:
            choices = ", ".join(sorted(OUTPUT_NAMING_MODES))
            raise ToolValidationError(f"output_naming must be one of: {choices}")
        params["output_naming"] = output_naming
    else:
        params["output_naming"] = OUTPUT_NAMING_FIXED
    return params


def _coerce(param: ToolParam, value: Any) -> Any:
    if _is_empty(value):
        return value
    if param.type == "int":
        return int(value)
    if param.type == "float":
        return float(value)
    if param.type == "bool":
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}
    if param.type == "path_list":
        if isinstance(value, (list, tuple)):
            return [str(item).strip() for item in value if str(item).strip()]
        return [line.strip() for line in str(value).splitlines() if line.strip()]
    return str(value)


def _is_empty(value: Any) -> bool:
    return value is None or value == "" or isinstance(value, (list, tuple)) and not value


def _error(action: str, code: str, message: str) -> dict[str, Any]:
    return {
        "ok": False,
        "action": action,
        "error_code": code,
        "message": message,
        "outputs": {},
        "warnings": [],
    }
