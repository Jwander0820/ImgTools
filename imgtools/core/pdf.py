from __future__ import annotations

from pathlib import Path
from typing import Any

from .common import (
    abs_path,
    default_output_stem,
    ensure_not_exists,
    resolve_output_directory,
    resolve_output_path,
)


class PDFOperator:
    """Minimal PyMuPDF adapter used by the PDF actions."""

    STANDARD_DPI = 72.0

    def __init__(self, file_path: str, password: str | None = None):
        import fitz

        self.file_path = file_path
        self.doc = fitz.open(file_path)
        if self.doc.is_encrypted:
            if not password or not self.doc.authenticate(password):
                self.doc.close()
                raise ValueError("PDF 已加密或密碼錯誤。")
        self.total_pages = len(self.doc)

    def save_page_as_image(self, page_number: int, file_name: str, dpi: int | None = None) -> None:
        import fitz

        zoom = (dpi or self.STANDARD_DPI) / self.STANDARD_DPI
        pixmap = self.doc[page_number].get_pixmap(matrix=fitz.Matrix(zoom, zoom))
        pixmap.save(file_name)

    def close(self) -> None:
        self.doc.close()


def render_page(params: dict[str, Any]) -> dict[str, Any]:
    pdf_path = Path(str(params["pdf_path"])).expanduser().resolve()
    page = int(params.get("page", 1))
    dpi = int(params.get("dpi", 192))
    password = params.get("password") or None
    overwrite = bool(params.get("overwrite", False))

    operator = PDFOperator(str(pdf_path), password)
    try:
        real_page = page - 1
        if real_page < 0 or real_page >= operator.total_pages:
            raise ValueError(f"Page {page} is out of range. Total pages: {operator.total_pages}")

        output_path = params.get("output_path")
        if not output_path:
            width = len(str(operator.total_pages))
            output_path = pdf_path.with_name(
                f"{default_output_stem(params, pdf_path)}_page{str(page).zfill(width)}.png"
            )

        output_path = resolve_output_path(
            output_path if params.get("output_path") else None,
            output_path,
            overwrite=overwrite,
        )
        operator.save_page_as_image(real_page, str(output_path), dpi=dpi)
    finally:
        operator.close()
    return {
        "ok": True,
        "outputs": {
            "files": [abs_path(output_path)],
        },
        "warnings": [],
    }


def render_all_pages(params: dict[str, Any]) -> dict[str, Any]:
    pdf_path = Path(str(params["pdf_path"])).expanduser().resolve()
    dpi = int(params.get("dpi", 192))
    password = params.get("password") or None
    overwrite = bool(params.get("overwrite", False))
    output_stem = default_output_stem(params, pdf_path)
    output_dir = resolve_output_directory(
        params.get("output_dir"),
        pdf_path.with_name(f"{output_stem}_pages"),
        overwrite=overwrite,
    )

    operator = PDFOperator(str(pdf_path), password)
    try:
        width = len(str(operator.total_pages))
        output_paths = [
            output_dir / f"{output_stem}_page{str(page).zfill(width)}.png"
            for page in range(1, operator.total_pages + 1)
        ]
        for output_path in output_paths:
            ensure_not_exists(output_path, overwrite=overwrite)
        for page_number, output_path in enumerate(output_paths):
            operator.save_page_as_image(page_number, str(output_path), dpi=dpi)
    finally:
        operator.close()

    return {
        "ok": True,
        "outputs": {
            "files": [abs_path(path) for path in output_paths],
            "output_dir": abs_path(output_dir),
        },
        "warnings": [],
    }
