from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .common import abs_path


def files_replace(params: dict[str, Any]) -> dict[str, Any]:
    return _replace(params, include_files=True, include_dirs=False)


def folders_replace(params: dict[str, Any]) -> dict[str, Any]:
    return _replace(params, include_files=False, include_dirs=True)


def _replace(params: dict[str, Any], *, include_files: bool, include_dirs: bool) -> dict[str, Any]:
    target_folder = Path(str(params["target_folder"])).expanduser().resolve()
    target = str(params["target"])
    replacement = str(params["replacement"])
    confirm = bool(params.get("confirm", False))

    if not target:
        raise ValueError("target cannot be empty")
    if not target_folder.exists():
        raise FileNotFoundError(str(target_folder))

    operations: list[dict[str, str]] = []
    conflicts: list[dict[str, str]] = []

    for root, dirs, files in os.walk(target_folder, topdown=False):
        items: list[tuple[str, bool]] = []
        if include_files:
            items.extend((name, False) for name in files)
        if include_dirs:
            items.extend((name, True) for name in dirs)

        for name, _is_dir in items:
            if target not in name:
                continue
            source = Path(root) / name
            destination = Path(root) / name.replace(target, replacement)
            operation = {
                "source": abs_path(source),
                "destination": abs_path(destination),
            }
            if destination.exists():
                conflicts.append(operation)
            else:
                operations.append(operation)

    if confirm and not conflicts:
        for operation in operations:
            os.rename(operation["source"], operation["destination"])

    return {
        "ok": not conflicts,
        "outputs": {
            "dry_run": not confirm,
            "changed": confirm and not conflicts,
            "operations": operations,
            "conflicts": conflicts,
            "count": len(operations),
        },
        "warnings": ["Conflicts found; no changes were applied."] if conflicts else [],
    }

