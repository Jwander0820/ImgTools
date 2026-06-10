from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def write_manifest(
    action: str,
    params: dict[str, Any],
    result: dict[str, Any],
    started_at: str,
    finished_at: str,
) -> str:
    manifest_dir = _manifest_dir(params, result)
    manifest_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    safe_action = action.replace(".", "_")
    manifest_path = manifest_dir / f"{stamp}_{safe_action}.manifest.json"
    data = {
        "tool": "ImgTools",
        "action": action,
        "started_at": started_at,
        "finished_at": finished_at,
        "params": params,
        "ok": result.get("ok", False),
        "outputs": result.get("outputs", {}),
        "warnings": result.get("warnings", []),
        "error_code": result.get("error_code"),
        "message": result.get("message"),
    }
    manifest_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(manifest_path.resolve())


def _manifest_dir(params: dict[str, Any], result: dict[str, Any]) -> Path:
    outputs = result.get("outputs", {})
    files = outputs.get("files") or []
    if files:
        return Path(files[0]).expanduser().resolve().parent / ".imgtools"

    for key in ("output_path", "output_dir", "target_folder", "folder_path"):
        value = params.get(key)
        if value:
            path = Path(str(value)).expanduser().resolve()
            base = path if path.suffix == "" else path.parent
            return base / ".imgtools"

    return Path.cwd() / "data" / ".imgtools"

