from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .registry import list_tools
from .state import state_root


PREFERENCES_VERSION = 1
MAX_PINNED_ACTIONS = 8
_WRITE_LOCK = threading.Lock()


class PreferenceValidationError(ValueError):
    pass


def get_preferences_view(tools: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    tool_list = list_tools() if tools is None else tools
    actions = [str(tool["action"]) for tool in tool_list]
    known = set(actions)
    data = _read_preferences()
    pinned = [action for action in data["pinned_actions"] if action in known]
    usage = {
        action: item
        for action, item in data["usage"].items()
        if action in known and _successful_runs(item) > 0
    }

    quick_actions: list[dict[str, Any]] = []
    added: set[str] = set()

    def add(action: str, source: str) -> None:
        if action in known and action not in added and len(quick_actions) < MAX_PINNED_ACTIONS:
            quick_actions.append({
                "action": action,
                "source": source,
                "successful_runs": _successful_runs(usage.get(action, {})),
            })
            added.add(action)

    for action in pinned:
        add(action, "pinned")

    action_order = {action: index for index, action in enumerate(actions)}
    frequent = sorted(
        usage,
        key=lambda action: (
            _successful_runs(usage[action]),
            str(usage[action].get("last_used_at", "")),
            -action_order[action],
        ),
        reverse=True,
    )
    for action in frequent:
        add(action, "frequent")

    for tool in tool_list:
        if bool(tool.get("featured", False)):
            add(str(tool["action"]), "default")

    return {
        "pinned_actions": pinned,
        "usage": {
            action: {
                "successful_runs": _successful_runs(item),
                "last_used_at": str(item.get("last_used_at", "")),
            }
            for action, item in usage.items()
        },
        "quick_actions": quick_actions,
        "max_pinned": MAX_PINNED_ACTIONS,
    }


def update_pinned_actions(
    pinned_actions: list[str],
    tools: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    tool_list = list_tools() if tools is None else tools
    known = {str(tool["action"]) for tool in tool_list}
    if not isinstance(pinned_actions, list) or any(
        not isinstance(action, str) for action in pinned_actions
    ):
        raise PreferenceValidationError("pinned_actions must be a list of action names")
    unique = list(dict.fromkeys(pinned_actions))
    if len(unique) > MAX_PINNED_ACTIONS:
        raise PreferenceValidationError(
            f"pinned_actions cannot contain more than {MAX_PINNED_ACTIONS} actions"
        )
    unknown = [action for action in unique if action not in known]
    if unknown:
        raise PreferenceValidationError(f"Unknown action: {unknown[0]}")

    with _WRITE_LOCK:
        data = _read_preferences()
        data["pinned_actions"] = unique
        _write_preferences(data)
    return get_preferences_view(tool_list)


def record_successful_run(action: str) -> None:
    with _WRITE_LOCK:
        data = _read_preferences()
        current = data["usage"].get(action, {})
        data["usage"][action] = {
            "successful_runs": _successful_runs(current) + 1,
            "last_used_at": _now_iso(),
        }
        _write_preferences(data)


def preferences_path() -> Path:
    return state_root() / "preferences.json"


def _read_preferences() -> dict[str, Any]:
    path = preferences_path()
    if not path.is_file():
        return _empty_preferences()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _empty_preferences()
    if not isinstance(raw, dict):
        return _empty_preferences()
    pinned = raw.get("pinned_actions", [])
    usage = raw.get("usage", {})
    return {
        "version": PREFERENCES_VERSION,
        "pinned_actions": pinned if isinstance(pinned, list) else [],
        "usage": usage if isinstance(usage, dict) else {},
    }


def _write_preferences(data: dict[str, Any]) -> None:
    path = preferences_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _empty_preferences() -> dict[str, Any]:
    return {"version": PREFERENCES_VERSION, "pinned_actions": [], "usage": {}}


def _successful_runs(item: Any) -> int:
    if not isinstance(item, dict):
        return 0
    try:
        return max(0, int(item.get("successful_runs", 0)))
    except (TypeError, ValueError):
        return 0


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
