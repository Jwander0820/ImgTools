from __future__ import annotations

from pathlib import Path

from imgtools.service.safety import ensure_output_allowed


def abs_path(path: str | Path) -> str:
    return str(Path(path).expanduser().resolve())


def ensure_parent(path: str | Path) -> None:
    Path(path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)


def ensure_not_exists(path: str | Path, overwrite: bool = False) -> None:
    ensure_output_allowed(path, overwrite=overwrite)
