from __future__ import annotations

from typing import Any

from .common import abs_path, ensure_not_exists, ensure_parent


def images_to_pdf(params: dict[str, Any]) -> dict[str, Any]:
    from legacy.merge_img import merge_img_to_one_pdf

    output_path = params["output_path"]
    overwrite = bool(params.get("overwrite", False))
    ensure_parent(output_path)
    ensure_not_exists(output_path, overwrite=overwrite)
    result = merge_img_to_one_pdf(params["folder_path"], output_path)
    return {
        "ok": True,
        "outputs": {"files": [abs_path(result)]},
        "warnings": [],
    }
