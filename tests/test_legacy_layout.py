import importlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class LegacyLayoutTests(unittest.TestCase):
    def test_legacy_tools_are_moved_under_legacy_package(self):
        expected = [
            "legacy/merge_img.py",
            "legacy/pdf_tools/pdf_dpi_conversion_tools.py",
            "legacy/tif_tools/tif_tools.py",
            "legacy/gif_tools/gif_tools.py",
            "legacy/crop_text/crop_text.py",
            "legacy/watermark/add_watermark.py",
            "legacy/read_img_exif/read_img_exif.py",
            "legacy/rename_file_and_folder/raname_file_and_folder.py",
            "legacy/research/test_cv_minarearect_logic/test_cv_minarearect_logic.py",
            "legacy/research/test_multiple_rotated/test_the_effect_of_multiple_rotated.py",
        ]

        for relative_path in expected:
            with self.subTest(path=relative_path):
                self.assertTrue((ROOT / relative_path).exists())

    def test_root_legacy_tool_locations_are_removed(self):
        old_locations = [
            "merge_img.py",
            "pdf_tools",
            "tif_tools",
            "gif_tools",
            "crop_text",
            "watermark",
            "read_img_exif",
            "rename_file_and_folder",
            "research",
        ]

        for relative_path in old_locations:
            with self.subTest(path=relative_path):
                self.assertFalse((ROOT / relative_path).exists())

    def test_core_modules_match_target_architecture(self):
        for module_name in ["pdf", "tif", "gif", "merge", "crop", "watermark", "metadata", "rename"]:
            with self.subTest(module=module_name):
                module = importlib.import_module(f"imgtools.core.{module_name}")
                self.assertIsNotNone(module)

    def test_runtime_directories_have_placeholders(self):
        self.assertTrue((ROOT / "imgtools/ui/static/.gitkeep").exists())
        self.assertTrue((ROOT / "data/outputs/.gitkeep").exists())


if __name__ == "__main__":
    unittest.main()
