from __future__ import annotations

from pathlib import Path
from typing import Any

from .common import (
    abs_path,
    default_output_stem,
    default_sequence_output_stem,
    ensure_not_exists,
    resolve_output_directory,
    resolve_output_path,
)


SUPPORTED_IMAGE_SUFFIXES = {".tif", ".tiff", ".png", ".jpg", ".jpeg", ".bmp", ".webp"}


def split_pages(params: dict[str, Any]) -> dict[str, Any]:
    from PIL import Image

    input_path = Path(str(params["input_path"])).expanduser().resolve()
    if not input_path.is_file():
        raise FileNotFoundError(f"Input TIF does not exist: {input_path}")
    overwrite = bool(params.get("overwrite", False))
    output_stem = default_output_stem(params, input_path)
    output_dir = resolve_output_directory(
        params.get("output_dir"),
        input_path.with_name(f"{output_stem}_pages"),
        overwrite=overwrite,
    )

    with Image.open(input_path) as image:
        output_paths = [
            output_dir / f"{output_stem}_page{page:03d}.tif"
            for page in range(1, image.n_frames + 1)
        ]
        for output_path in output_paths:
            ensure_not_exists(output_path, overwrite=overwrite)
        for frame_index, output_path in enumerate(output_paths):
            image.seek(frame_index)
            image.copy().save(output_path, compression="tiff_lzw")

    return {
        "ok": True,
        "outputs": {
            "files": [abs_path(path) for path in output_paths],
            "output_dir": abs_path(output_dir),
        },
        "warnings": [],
    }


def extract_page(params: dict[str, Any]) -> dict[str, Any]:
    from PIL import Image

    input_path = Path(str(params["input_path"])).expanduser().resolve()
    if not input_path.is_file():
        raise FileNotFoundError(f"Input TIF does not exist: {input_path}")
    page = int(params.get("page", 1))
    output_path = resolve_output_path(
        params.get("output_path"),
        input_path.with_name(
            f"{default_output_stem(params, input_path)}_page{page:03d}.tif"
        ),
        overwrite=bool(params.get("overwrite", False)),
    )

    with Image.open(input_path) as image:
        if page < 1 or page > image.n_frames:
            raise ValueError(f"Page {page} is out of range. Total pages: {image.n_frames}")
        image.seek(page - 1)
        image.copy().save(output_path, compression="tiff_lzw")

    return {
        "ok": True,
        "outputs": {"files": [abs_path(output_path)]},
        "warnings": [],
    }


def images_to_tif(params: dict[str, Any]) -> dict[str, Any]:
    from PIL import Image

    folder_path = Path(str(params["folder_path"])).expanduser().resolve()
    if not folder_path.is_dir():
        raise NotADirectoryError(f"Input folder does not exist: {folder_path}")

    requested_output = params.get("output_path")
    using_default_output = not requested_output
    explicit_output = (
        Path(str(requested_output)).expanduser().resolve()
        if requested_output
        else None
    )
    input_paths = sorted(
        path
        for path in folder_path.iterdir()
        if path.is_file()
        and path.suffix.lower() in SUPPORTED_IMAGE_SUFFIXES
        and path.resolve() != explicit_output
        and not (using_default_output and _is_generated_default_tif(path))
    )
    if not input_paths:
        raise ValueError(f"No supported images found in: {folder_path}")

    overwrite = bool(params.get("overwrite", False))
    output_path = resolve_output_path(
        requested_output,
        folder_path / f"{default_sequence_output_stem(params, input_paths)}.tif",
        overwrite=overwrite,
        protected_paths=tuple(input_paths),
    )

    color_mode = str(params.get("color_mode", "RGB"))
    compression = str(params.get("compression", "tiff_lzw"))
    frames = []
    for input_path in input_paths:
        with Image.open(input_path) as image:
            frames.append(image.convert(color_mode).copy())
    try:
        frames[0].save(
            output_path,
            format="TIFF",
            save_all=True,
            append_images=frames[1:],
            compression=compression,
        )
    finally:
        for frame in frames:
            frame.close()

    return {
        "ok": True,
        "outputs": {
            "files": [abs_path(output_path)],
            "source_files": [abs_path(path) for path in input_paths],
            "page_count": len(input_paths),
        },
        "warnings": [],
    }


def _is_generated_default_tif(path: Path) -> bool:
    stem = path.stem
    return path.suffix.lower() in {".tif", ".tiff"} and (
        stem == "output" or stem.startswith("output-") and stem[7:].isdigit()
    )
