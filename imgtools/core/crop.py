from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from .common import (
    abs_path,
    default_output_stem,
    ensure_not_exists,
    resolve_output_directory,
)


def text_regions(params: dict[str, Any]) -> dict[str, Any]:
    """Extract dark regions from a light background as transparent PNG files."""
    import cv2
    import numpy as np
    from PIL import Image

    input_path = Path(str(params["input_path"])).expanduser().resolve()
    if not input_path.is_file():
        raise FileNotFoundError(f"Input image does not exist: {input_path}")

    dilate_iterations = int(params.get("dilate_iterations", 10))
    min_area = int(params.get("min_area", 64))
    padding_ratio = float(params.get("padding_ratio", 0.1))
    canvas_size = int(params.get("canvas_size", 0))
    overwrite = bool(params.get("overwrite", False))
    if dilate_iterations < 0:
        raise ValueError("dilate_iterations must be 0 or greater")
    if min_area <= 0:
        raise ValueError("min_area must be greater than 0")
    if not 0 <= padding_ratio <= 1:
        raise ValueError("padding_ratio must be between 0 and 1")
    if canvas_size < 0:
        raise ValueError("canvas_size must be 0 or greater")

    with Image.open(input_path) as source:
        rgb = np.asarray(source.convert("RGB"))
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    _, alpha = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU,
    )
    detected = alpha
    if dilate_iterations:
        detected = cv2.dilate(
            detected,
            np.ones((3, 3), np.uint8),
            iterations=dilate_iterations,
        )
    contours, _ = cv2.findContours(
        detected,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )
    boxes = sorted(
        (
            (x, y, width, height)
            for contour in contours
            for x, y, width, height in (cv2.boundingRect(contour),)
            if width * height >= min_area
        ),
        key=lambda box: (box[1], box[0]),
    )
    if not boxes:
        raise ValueError("No text-like regions were found")
    if canvas_size and any(
        width > canvas_size or height > canvas_size
        for _, _, width, height in boxes
    ):
        raise ValueError("canvas_size must fit every detected region")

    output_stem = default_output_stem(params, input_path)
    output_dir = resolve_output_directory(
        params.get("output_dir"),
        input_path.with_name(f"{output_stem}_regions"),
        overwrite=overwrite,
    )
    output_paths = [
        output_dir / f"{output_stem}_region_{index:03d}.png"
        for index in range(1, len(boxes) + 1)
    ]
    for output_path in output_paths:
        ensure_not_exists(output_path, overwrite=overwrite)

    for box, output_path in zip(boxes, output_paths):
        x, y, width, height = box
        region_rgb = rgb[y:y + height, x:x + width]
        region_alpha = alpha[y:y + height, x:x + width]
        region = np.dstack((region_rgb, region_alpha))
        if canvas_size:
            canvas_width = canvas_height = canvas_size
        else:
            canvas_width = max(width, math.ceil(width * (1 + padding_ratio * 2)))
            canvas_height = max(height, math.ceil(height * (1 + padding_ratio * 2)))
        canvas = np.zeros((canvas_height, canvas_width, 4), dtype=np.uint8)
        offset_x = (canvas_width - width) // 2
        offset_y = (canvas_height - height) // 2
        canvas[offset_y:offset_y + height, offset_x:offset_x + width] = region
        Image.fromarray(canvas).save(output_path)

    return {
        "ok": True,
        "outputs": {
            "files": [abs_path(path) for path in output_paths],
            "output_dir": abs_path(output_dir),
            "region_count": len(output_paths),
        },
        "warnings": [],
    }
