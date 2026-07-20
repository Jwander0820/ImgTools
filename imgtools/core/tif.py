from __future__ import annotations

from pathlib import Path
from typing import Any

from .common import abs_path, ensure_not_exists


def split_pages(params: dict[str, Any]) -> dict[str, Any]:
    from PIL import Image

    input_path = Path(str(params["input_path"])).expanduser().resolve()
    if not input_path.is_file():
        raise FileNotFoundError(f"Input TIF does not exist: {input_path}")
    output_dir = Path(
        str(params.get("output_dir") or input_path.with_name(f"{input_path.stem}_pages"))
    ).expanduser().resolve()
    overwrite = bool(params.get("overwrite", False))

    with Image.open(input_path) as image:
        output_paths = [
            output_dir / f"{input_path.stem}_page{page:03d}.tif"
            for page in range(1, image.n_frames + 1)
        ]
        for output_path in output_paths:
            ensure_not_exists(output_path, overwrite=overwrite)
        output_dir.mkdir(parents=True, exist_ok=True)
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
    output_path = Path(
        str(
            params.get("output_path")
            or input_path.with_name(f"{input_path.stem}_page{page:03d}.tif")
        )
    ).expanduser().resolve()

    with Image.open(input_path) as image:
        if page < 1 or page > image.n_frames:
            raise ValueError(f"Page {page} is out of range. Total pages: {image.n_frames}")
        ensure_not_exists(output_path, overwrite=bool(params.get("overwrite", False)))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.seek(page - 1)
        image.copy().save(output_path, compression="tiff_lzw")

    return {
        "ok": True,
        "outputs": {"files": [abs_path(output_path)]},
        "warnings": [],
    }
