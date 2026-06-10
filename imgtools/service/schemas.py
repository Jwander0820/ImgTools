from __future__ import annotations

from typing import Any

from imgtools.service.registry import ToolSpec


def action_schema(spec: ToolSpec) -> dict[str, Any]:
    return {
        "type": "object",
        "action": spec.action,
        "title": spec.title,
        "category": spec.category,
        "description": spec.description,
        "danger_level": spec.danger_level,
        "params": [param.to_dict() for param in spec.params],
        "result": result_schema(),
    }


def result_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": ["ok", "action", "outputs", "warnings"],
        "properties": {
            "ok": {"type": "boolean"},
            "action": {"type": "string"},
            "outputs": {"type": "object"},
            "warnings": {"type": "array", "items": {"type": "string"}},
            "error_code": {"type": "string"},
            "message": {"type": "string"},
            "manifest_path": {"type": "path"},
        },
    }

