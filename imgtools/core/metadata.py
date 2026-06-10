from __future__ import annotations

from typing import Any


def read_tif_tags(params: dict[str, Any]) -> dict[str, Any]:
    method = params.get("method", "pil")
    path = params["input_path"]
    if method == "pil":
        from PIL import Image

        with Image.open(path) as img:
            tags = img.tag_v2
    elif method == "tifftools":
        import tifftools

        tags = tifftools.read_tiff(path)["ifds"][0]["tags"]
    elif method == "exifread":
        import exifread

        with open(path, "rb") as file:
            tags = exifread.process_file(file)
    else:
        raise ValueError(f"Unsupported metadata method: {method}")

    data = {str(key): _short_repr(value) for key, value in dict(tags).items()}
    return {
        "ok": True,
        "outputs": {
            "metadata": data,
            "count": len(data),
        },
        "warnings": [],
    }


def _short_repr(value: Any) -> str:
    text = repr(value)
    return text if len(text) <= 1000 else text[:1000] + "...<truncated>"
