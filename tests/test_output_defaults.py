import tempfile
import unittest
import sys
from types import ModuleType
from pathlib import Path
from unittest.mock import patch


class OutputDefaultTests(unittest.TestCase):
    def test_source_naming_uses_source_stem(self):
        from imgtools.core.common import default_output_stem

        self.assertEqual(
            default_output_stem({"output_naming": "source"}, Path("D:/images/photo.png")),
            "photo",
        )
        self.assertEqual(
            default_output_stem({"output_naming": "fixed"}, Path("D:/images/photo.png")),
            "output",
        )

    def test_same_format_source_naming_resolves_collision_before_writing(self):
        from imgtools.core.common import default_output_stem, resolve_output_path

        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "photo.png"
            source.write_bytes(b"source")
            (Path(tmp) / "photo-2.png").write_bytes(b"older output")

            default_path = source.with_name(
                f"{default_output_stem({'output_naming': 'source'}, source)}.png"
            )
            output = resolve_output_path(None, default_path)

            self.assertEqual(output, Path(tmp) / "photo-3.png")
            self.assertEqual(source.read_bytes(), b"source")

    def test_explicit_output_cannot_overwrite_a_protected_input(self):
        from imgtools.core.common import resolve_output_path

        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "photo.png"
            source.write_bytes(b"source")

            with self.assertRaisesRegex(ValueError, "protected input"):
                resolve_output_path(
                    source,
                    source.with_name("output.png"),
                    overwrite=True,
                    protected_paths=(source,),
                )

            self.assertEqual(source.read_bytes(), b"source")

    def test_images_to_pdf_defaults_output_beside_source_folder(self):
        from imgtools.core.merge import images_to_pdf

        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "images"
            folder.mkdir()

            def fake_merge(_folder_path, output_path):
                Path(output_path).write_bytes(b"pdf")
                return output_path

            fake_module = ModuleType("legacy.merge_img")
            fake_module.merge_img_to_one_pdf = fake_merge
            with patch.dict(sys.modules, {"legacy.merge_img": fake_module}):
                result = images_to_pdf({"folder_path": str(folder)})

            self.assertEqual(Path(result["outputs"]["files"][0]), folder / "output.pdf")
            self.assertTrue((folder / "output.pdf").is_file())

    def test_images_to_pdf_source_mode_uses_folder_name(self):
        from imgtools.core.merge import images_to_pdf

        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "holiday"
            folder.mkdir()

            def fake_merge(_folder_path, output_path):
                Path(output_path).write_bytes(b"pdf")
                return output_path

            fake_module = ModuleType("legacy.merge_img")
            fake_module.merge_img_to_one_pdf = fake_merge
            with patch.dict(sys.modules, {"legacy.merge_img": fake_module}):
                result = images_to_pdf({"folder_path": str(folder), "output_naming": "source"})

            self.assertEqual(Path(result["outputs"]["files"][0]), folder / "holiday.pdf")


if __name__ == "__main__":
    unittest.main()
