from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SENSITIVE_PARAM_NAMES = {"password", "token", "secret", "api_key"}


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def write_manifest(
    action: str,
    params: dict[str, Any],
    result: dict[str, Any],
    started_at: str,
    finished_at: str,
) -> str:
    manifest_dir = _manifest_dir()
    manifest_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    safe_action = action.replace(".", "_")
    manifest_path = manifest_dir / f"{stamp}_{safe_action}.manifest.json"
    data = {
        "tool": "ImgTools",
        "action": action,
        "started_at": started_at,
        "finished_at": finished_at,
        "params": _redact_sensitive(params),
        "ok": result.get("ok", False),
        "outputs": result.get("outputs", {}),
        "warnings": result.get("warnings", []),
        "error_code": result.get("error_code"),
        "message": result.get("message"),
    }
    manifest_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(manifest_path.resolve())


def _manifest_dir() -> Path:
    configured = os.environ.get("IMGTOOLS_STATE_DIR")
    if configured:
        state_root = Path(configured).expanduser().resolve()
    else:
        project_root = Path(__file__).resolve().parents[2]
        state_root = project_root / "data" / ".imgtools"
    return state_root / "manifests"


def _redact_sensitive(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "[REDACTED]" if str(key).lower() in SENSITIVE_PARAM_NAMES else _redact_sensitive(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact_sensitive(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_redact_sensitive(item) for item in value)
    return value
