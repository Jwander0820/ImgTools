from __future__ import annotations

from pathlib import Path

from imgtools.service.safety import ensure_output_allowed


def abs_path(path: str | Path) -> str:
    return str(Path(path).expanduser().resolve())


def ensure_parent(path: str | Path) -> None:
    Path(path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)


def ensure_not_exists(path: str | Path, overwrite: bool = False) -> None:
    ensure_output_allowed(path, overwrite=overwrite)


def resolve_output_path(
    value: str | Path | None,
    default_path: str | Path,
    *,
    overwrite: bool = False,
) -> Path:
    """Resolve an explicit output or choose a collision-free default output."""
    if value:
        resolved = Path(value).expanduser().resolve()
        ensure_parent(resolved)
        ensure_not_exists(resolved, overwrite=overwrite)
        return resolved

    resolved = Path(default_path).expanduser().resolve()
    ensure_parent(resolved)
    if overwrite or not resolved.exists():
        return resolved

    counter = 2
    while True:
        candidate = resolved.with_name(f"{resolved.stem}-{counter}{resolved.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1
