import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class FakePDFOperator:
    total_pages = 3

    def __init__(self, file_path, password=None):
        self.file_path = file_path
        self.password = password
        self.saved = []

    def save_page_as_image(self, page_number, file_name, dpi=None):
        self.saved.append((page_number, file_name, dpi))
        Path(file_name).write_text(f"page={page_number}, dpi={dpi}", encoding="utf-8")


class PDFTests(unittest.TestCase):
    def test_pdf_render_page_uses_one_based_page_number(self):
        from imgtools.core.pdf import render_page

        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "sample.pdf"
            output_path = Path(tmp) / "out.png"
            pdf_path.write_text("fake", encoding="utf-8")

            with patch("imgtools.core.pdf.PDFOperator", FakePDFOperator):
                result = render_page(
                    {
                        "pdf_path": str(pdf_path),
                        "page": 2,
                        "dpi": 200,
                        "output_path": str(output_path),
                    }
                )

            self.assertTrue(result["ok"])
            self.assertTrue(output_path.exists())
            self.assertEqual(output_path.read_text(encoding="utf-8"), "page=1, dpi=200")

    def test_pdf_render_page_out_of_range_returns_error(self):
        from imgtools.core.pdf import render_page

        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "sample.pdf"
            pdf_path.write_text("fake", encoding="utf-8")

            with patch("imgtools.core.pdf.PDFOperator", FakePDFOperator):
                with self.assertRaises(ValueError):
                    render_page({"pdf_path": str(pdf_path), "page": 9})


if __name__ == "__main__":
    unittest.main()

