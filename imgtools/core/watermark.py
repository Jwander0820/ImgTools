from __future__ import annotations

from pathlib import Path
from typing import Any

from .common import abs_path, default_output_stem, resolve_output_directory, resolve_output_path


DEFAULT_ROTATION = 30
DEFAULT_OPACITY = round(255 * 0.25)
DEFAULT_COLOR = "#000000"
DEFAULT_REPEAT_SPACING = 100


def add_text(params: dict[str, Any]) -> dict[str, Any]:
    from PIL import Image, ImageDraw

    if "input_paths" in params:
        input_paths = params.get("input_paths")
        if not isinstance(input_paths, (list, tuple)) or not input_paths:
            raise ValueError("input_paths must contain at least one image")
        if len(input_paths) > 1:
            return add_text_batch(params)
        params = dict(params)
        params["input_path"] = input_paths[0]
        params.pop("input_paths", None)

    input_path = Path(str(params["input_path"])).expanduser().resolve()
    if not input_path.is_file():
        raise FileNotFoundError(f"Input image does not exist: {input_path}")
    suffix = input_path.suffix or ".png"
    output_path = resolve_output_path(
        params.get("output_path"),
        input_path.with_name(f"{default_output_stem(params, input_path)}{suffix}"),
        overwrite=bool(params.get("overwrite", False)),
        protected_paths=(input_path,),
    )

    text = str(params["text"])
    if not text:
        raise ValueError("text must not be empty")
    rotation = float(params.get("rotation", DEFAULT_ROTATION))
    opacity = int(params.get("opacity", DEFAULT_OPACITY))
    if not 0 <= opacity <= 255:
        raise ValueError("opacity must be between 0 and 255")
    color = _parse_color(params.get("color", DEFAULT_COLOR))
    position_mode = str(params.get("position", "center"))
    margin = int(params.get("margin", 16))
    if margin < 0:
        raise ValueError("margin must be 0 or greater")
    repeat = bool(params.get("repeat", False))
    repeat_spacing = int(params.get("repeat_spacing", DEFAULT_REPEAT_SPACING))
    if repeat_spacing < 0:
        raise ValueError("repeat_spacing must be 0 or greater")

    with Image.open(input_path) as source:
        base = source.convert("RGBA")
    requested_font_size = int(params.get("font_size", 0))
    if requested_font_size < 0:
        raise ValueError("font_size must be 0 or greater")
    font_size = requested_font_size or max(12, int(min(base.size) * 0.2))
    font = _load_font(params.get("font_path"), font_size)
    probe = ImageDraw.Draw(base)
    bbox = probe.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    padding = max(8, font_size // 3)
    layer = Image.new(
        "RGBA",
        (max(1, text_width + padding * 2), max(1, text_height + padding * 2)),
        (0, 0, 0, 0),
    )
    draw = ImageDraw.Draw(layer)
    draw.text(
        (padding - bbox[0], padding - bbox[1]),
        text,
        font=font,
        fill=(*color, opacity),
    )
    rotated = layer.rotate(rotation, resample=Image.Resampling.BICUBIC, expand=True)
    max_x = max(0, base.width - rotated.width)
    max_y = max(0, base.height - rotated.height)
    positions = {
        "center": (max(0, max_x // 2), max(0, max_y // 2)),
        "top_left": (
            0 if rotated.width > base.width else margin,
            0 if rotated.height > base.height else margin,
        ),
        "top_right": (
            max(0, max_x - margin),
            0 if rotated.height > base.height else margin,
        ),
        "bottom_left": (
            0 if rotated.width > base.width else margin,
            max(0, max_y - margin),
        ),
        "bottom_right": (max(0, max_x - margin), max(0, max_y - margin)),
        "custom": (
            min(max(0, int(params.get("position_x", 0))), max_x),
            min(max(0, int(params.get("position_y", 0))), max_y),
        ),
    }
    if position_mode not in positions:
        raise ValueError(f"Unsupported watermark position: {position_mode}")
    position = positions[position_mode]
    if repeat:
        _composite_repeated(base, rotated, position, repeat_spacing)
    else:
        _alpha_composite_clipped(base, rotated, *position)

    _save_image(base, output_path)
    return {
        "ok": True,
        "outputs": {"files": [abs_path(output_path)]},
        "warnings": [],
    }


def add_text_batch(params: dict[str, Any]) -> dict[str, Any]:
    input_values = params.get("input_paths")
    if not isinstance(input_values, (list, tuple)) or not input_values:
        raise ValueError("input_paths must contain at least one image")
    input_paths = [Path(str(value)).expanduser().resolve() for value in input_values]
    missing = [path for path in input_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Input image does not exist: {missing[0]}")

    overwrite = bool(params.get("overwrite", False))
    output_dir = resolve_output_directory(
        params.get("output_dir"),
        input_paths[0].parent / "watermarked",
        overwrite=overwrite,
    )
    outputs: list[str] = []
    for input_path in input_paths:
        suffix = input_path.suffix or ".png"
        output_path = resolve_output_path(
            None,
            output_dir / f"{input_path.stem}-watermarked{suffix}",
            overwrite=overwrite,
            protected_paths=(input_path,),
        )
        child_params = dict(params)
        child_params.pop("input_paths", None)
        child_params.pop("output_dir", None)
        child_params.update({"input_path": str(input_path), "output_path": str(output_path)})
        result = add_text(child_params)
        outputs.extend(result.get("outputs", {}).get("files", []))

    return {"ok": True, "outputs": {"files": outputs}, "warnings": []}


def _parse_color(value: Any) -> tuple[int, int, int]:
    raw = str(value or DEFAULT_COLOR).strip().lstrip("#")
    if len(raw) == 3:
        raw = "".join(char * 2 for char in raw)
    if len(raw) != 6:
        raise ValueError("color must be a hex RGB value such as #6d45ff")
    try:
        return tuple(int(raw[index : index + 2], 16) for index in (0, 2, 4))
    except ValueError as error:
        raise ValueError("color must be a hex RGB value such as #6d45ff") from error


def _alpha_composite_clipped(base: Any, overlay: Any, x: int | float, y: int | float) -> None:
    origin_x = int(round(x))
    origin_y = int(round(y))
    left = max(0, origin_x)
    top = max(0, origin_y)
    right = min(base.width, origin_x + overlay.width)
    bottom = min(base.height, origin_y + overlay.height)
    if left >= right or top >= bottom:
        return
    crop = overlay.crop((left - origin_x, top - origin_y, right - origin_x, bottom - origin_y))
    try:
        base.alpha_composite(crop, (left, top))
    finally:
        crop.close()


def _composite_repeated(base: Any, overlay: Any, position: tuple[int, int], spacing: int) -> None:
    step_x = max(1, overlay.width + spacing)
    step_y = max(1, overlay.height + spacing)
    start_x = position[0] % step_x - step_x
    start_y = position[1] % step_y - step_y
    for y in range(start_y, base.height, step_y):
        for x in range(start_x, base.width, step_x):
            _alpha_composite_clipped(base, overlay, x, y)


def _save_image(base: Any, output_path: Path) -> None:
    output_suffix = output_path.suffix.lower()
    if output_suffix in {".jpg", ".jpeg"}:
        base.convert("RGB").save(output_path)
    elif output_suffix in {".tif", ".tiff"}:
        base.save(output_path, compression="tiff_lzw")
    else:
        base.save(output_path)


def _load_font(font_path: Any, font_size: int) -> Any:
    from PIL import ImageFont

    if font_path:
        path = Path(str(font_path)).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Font file does not exist: {path}")
        return ImageFont.truetype(str(path), font_size)

    for candidate in (
        Path("C:/Windows/Fonts/msjhbd.ttc"),
        Path("C:/Windows/Fonts/msjh.ttc"),
        Path("C:/Windows/Fonts/arial.ttf"),
    ):
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), font_size)
    return ImageFont.load_default(size=font_size)
