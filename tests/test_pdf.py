import os
import importlib.util
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

    def close(self):
        pass


class PDFTests(unittest.TestCase):
    @unittest.skipUnless(importlib.util.find_spec("fitz"), "PyMuPDF is not installed")
    def test_pdf_render_page_uses_the_migrated_pymupdf_adapter(self):
        import fitz
        from PIL import Image
        from imgtools.core.pdf import render_page

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pdf_path = root / "sample.pdf"
            output_path = root / "page.png"
            document = fitz.open()
            document.new_page(width=72, height=36)
            document.save(pdf_path)
            document.close()

            result = render_page({
                "pdf_path": str(pdf_path),
                "output_path": str(output_path),
                "dpi": 144,
            })

            self.assertTrue(result["ok"], result)
            with Image.open(output_path) as image:
                self.assertEqual(image.size, (144, 72))

    def test_pdf_actions_use_server_default_dpi_when_task_omits_it(self):
        from imgtools.service.preferences import update_pdf_default_dpi
        from imgtools.service.runner import run_tool

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pdf_path = root / "sample.pdf"
            output_path = root / "out.png"
            pdf_path.write_text("fake", encoding="utf-8")

            with patch.dict(os.environ, {"IMGTOOLS_STATE_DIR": str(root / "state")}):
                update_pdf_default_dpi(300)
                with patch("imgtools.core.pdf.PDFOperator", FakePDFOperator):
                    result = run_tool(
                        "pdf.render_page",
                        {
                            "pdf_path": str(pdf_path),
                            "output_path": str(output_path),
                        },
                        manifest=False,
                    )

            self.assertTrue(result["ok"], result)
            self.assertEqual(output_path.read_text(encoding="utf-8"), "page=0, dpi=300")

    def test_explicit_task_dpi_overrides_the_server_default(self):
        from imgtools.service.preferences import update_pdf_default_dpi
        from imgtools.service.runner import run_tool

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pdf_path = root / "sample.pdf"
            output_path = root / "out.png"
            pdf_path.write_text("fake", encoding="utf-8")

            with patch.dict(os.environ, {"IMGTOOLS_STATE_DIR": str(root / "state")}):
                update_pdf_default_dpi(300)
                with patch("imgtools.core.pdf.PDFOperator", FakePDFOperator):
                    result = run_tool(
                        "pdf.render_page",
                        {
                            "pdf_path": str(pdf_path),
                            "output_path": str(output_path),
                            "dpi": 144,
                        },
                        manifest=False,
                    )

            self.assertTrue(result["ok"], result)
            self.assertEqual(output_path.read_text(encoding="utf-8"), "page=0, dpi=144")

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

    def test_pdf_render_all_pages_outputs_every_page(self):
        from imgtools.core.pdf import render_all_pages

        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "sample.pdf"
            output_dir = Path(tmp) / "rendered"
            pdf_path.write_text("fake", encoding="utf-8")

            with patch("imgtools.core.pdf.PDFOperator", FakePDFOperator):
                result = render_all_pages(
                    {"pdf_path": str(pdf_path), "dpi": 144, "output_dir": str(output_dir)}
                )

            files = [Path(path) for path in result["outputs"]["files"]]
            self.assertEqual([path.name for path in files], [
                "output_page1.png", "output_page2.png", "output_page3.png"
            ])
            self.assertTrue(all(path.exists() for path in files))

    def test_pdf_render_all_pages_source_mode_uses_original_stem(self):
        from imgtools.core.pdf import render_all_pages

        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "sample.pdf"
            pdf_path.write_text("fake", encoding="utf-8")

            with patch("imgtools.core.pdf.PDFOperator", FakePDFOperator):
                result = render_all_pages(
                    {"pdf_path": str(pdf_path), "output_naming": "source"}
                )

            files = [Path(path) for path in result["outputs"]["files"]]
            self.assertEqual(files[0].parent.name, "sample_pages")
            self.assertEqual(files[0].name, "sample_page1.png")


if __name__ == "__main__":
    unittest.main()
