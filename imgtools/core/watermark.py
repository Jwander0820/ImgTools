from __future__ import annotations

from pathlib import Path
from typing import Any

from .common import abs_path, default_output_stem, resolve_output_path


def add_text(params: dict[str, Any]) -> dict[str, Any]:
    from PIL import Image, ImageDraw

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
    rotation = float(params.get("rotation", 45))
    opacity = int(params.get("opacity", 100))
    if not 0 <= opacity <= 255:
        raise ValueError("opacity must be between 0 and 255")

    with Image.open(input_path) as source:
        base = source.convert("RGBA")
    font_size = int(params.get("font_size", 0)) or max(12, int(min(base.size) * 0.2))
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
    draw.text((padding - bbox[0], padding - bbox[1]), text, font=font, fill=(0, 0, 0, opacity))
    rotated = layer.rotate(rotation, resample=Image.Resampling.BICUBIC, expand=True)
    position = ((base.width - rotated.width) // 2, (base.height - rotated.height) // 2)
    base.alpha_composite(rotated, position)

    output_suffix = output_path.suffix.lower()
    if output_suffix in {".jpg", ".jpeg"}:
        base.convert("RGB").save(output_path)
    elif output_suffix in {".tif", ".tiff"}:
        base.save(output_path, compression="tiff_lzw")
    else:
        base.save(output_path)

    return {
        "ok": True,
        "outputs": {"files": [abs_path(output_path)]},
        "warnings": [],
    }


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
