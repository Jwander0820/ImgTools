from __future__ import annotations

from pathlib import Path

from imgtools.service.safety import ensure_output_allowed


OUTPUT_NAMING_FIXED = "fixed"
OUTPUT_NAMING_SOURCE = "source"
OUTPUT_NAMING_MODES = {OUTPUT_NAMING_FIXED, OUTPUT_NAMING_SOURCE}


def abs_path(path: str | Path) -> str:
    return str(Path(path).expanduser().resolve())


def ensure_parent(path: str | Path) -> None:
    Path(path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)


def ensure_not_exists(path: str | Path, overwrite: bool = False) -> None:
    ensure_output_allowed(path, overwrite=overwrite)


def default_output_stem(params: dict[str, object], source_path: str | Path) -> str:
    """Return the shared base name for an implicit output path."""
    source = Path(source_path)
    if params.get("output_naming", OUTPUT_NAMING_FIXED) == OUTPUT_NAMING_SOURCE:
        return source.stem or source.name
    return "output"


def resolve_output_path(
    value: str | Path | None,
    default_path: str | Path,
    *,
    overwrite: bool = False,
    protected_paths: tuple[str | Path, ...] = (),
) -> Path:
    """Resolve an explicit output or choose a collision-free default output."""
    protected = {Path(path).expanduser().resolve() for path in protected_paths}
    if value:
        resolved = Path(value).expanduser().resolve()
        if resolved in protected:
            raise ValueError(f"Output path would overwrite a protected input: {resolved}")
        ensure_parent(resolved)
        ensure_not_exists(resolved, overwrite=overwrite)
        return resolved

    resolved = Path(default_path).expanduser().resolve()
    ensure_parent(resolved)
    if resolved not in protected and (overwrite or not resolved.exists()):
        return resolved

    counter = 2
    while True:
        candidate = resolved.with_name(f"{resolved.stem}-{counter}{resolved.suffix}")
        if candidate not in protected and (overwrite or not candidate.exists()):
            return candidate
        counter += 1


def resolve_output_directory(
    value: str | Path | None,
    default_path: str | Path,
    *,
    overwrite: bool = False,
) -> Path:
    """Resolve an explicit directory or choose a collision-free default directory."""
    if value:
        resolved = Path(value).expanduser().resolve()
    else:
        resolved = Path(default_path).expanduser().resolve()
        if resolved.exists() and not overwrite:
            counter = 2
            while True:
                candidate = resolved.with_name(f"{resolved.name}-{counter}")
                if not candidate.exists():
                    resolved = candidate
                    break
                counter += 1
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved
