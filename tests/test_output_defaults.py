import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class OutputDefaultTests(unittest.TestCase):
    def test_images_to_pdf_defaults_output_beside_source_folder(self):
        from imgtools.core.merge import images_to_pdf

        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "images"
            folder.mkdir()

            def fake_merge(_folder_path, output_path):
                Path(output_path).write_bytes(b"pdf")
                return output_path

            with patch("legacy.merge_img.merge_img_to_one_pdf", side_effect=fake_merge):
                result = images_to_pdf({"folder_path": str(folder)})

            self.assertEqual(Path(result["outputs"]["files"][0]), folder / "output.pdf")
            self.assertTrue((folder / "output.pdf").is_file())


if __name__ == "__main__":
    unittest.main()
