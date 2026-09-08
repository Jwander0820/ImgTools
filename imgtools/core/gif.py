from __future__ import annotations

from pathlib import Path
from typing import Any

from .common import abs_path, default_sequence_output_stem, resolve_output_path


SUPPORTED_IMAGE_SUFFIXES = {".tif", ".tiff", ".png", ".jpg", ".jpeg", ".bmp", ".webp"}


def images_to_gif(params: dict[str, Any]) -> dict[str, Any]:
    from PIL import Image

    folder_path = Path(str(params["folder_path"])).expanduser().resolve()
    if not folder_path.is_dir():
        raise NotADirectoryError(f"Input folder does not exist: {folder_path}")
    input_paths = sorted(
        path for path in folder_path.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_SUFFIXES
    )
    if not input_paths:
        raise ValueError(f"No supported images found in: {folder_path}")

    output_path = resolve_output_path(
        params.get("output_path"),
        folder_path / f"{default_sequence_output_stem(params, input_paths)}.gif",
        overwrite=bool(params.get("overwrite", False)),
        protected_paths=tuple(input_paths),
    )
    duration = int(params.get("duration", 40))
    loop = int(params.get("loop", 0))
    color_mode = str(params.get("color_mode", "RGBA"))
    if duration <= 0:
        raise ValueError("duration must be greater than 0")
    if loop < 0:
        raise ValueError("loop must be 0 or greater")

    frames = []
    for input_path in input_paths:
        with Image.open(input_path) as image:
            frames.append(image.convert(color_mode).copy())
    try:
        frames[0].save(
            output_path,
            format="GIF",
            save_all=True,
            append_images=frames[1:],
            duration=duration,
            loop=loop,
            disposal=2,
        )
    finally:
        for frame in frames:
            frame.close()

    return {
        "ok": True,
        "outputs": {
            "files": [abs_path(output_path)],
            "source_files": [abs_path(path) for path in input_paths],
            "frame_count": len(input_paths),
        },
        "warnings": [],
    }
