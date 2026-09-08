from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from imgtools.service.runner import run_tool


class DialogueStackTests(unittest.TestCase):
    def test_preserves_first_frame_and_stacks_full_width_subtitle_bands(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            paths = []
            for index, color in enumerate(((220, 30, 30), (30, 200, 30), (30, 30, 220)), 1):
                path = root / f"frame-{index}.png"
                Image.new("RGB", (10, 10), color).save(path)
                paths.append(path)

            output = root / "dialogue.png"
            with patch("imgtools.service.runner.write_manifest", return_value=None):
                result = run_tool(
                    "merge.dialogue_stack",
                    {
                        "input_paths": [str(path) for path in paths],
                        "subtitle_top_ratio": 0.7,
                        "line_spacing": 2,
                        "output_path": str(output),
                    },
                )

            self.assertTrue(result["ok"])
            self.assertEqual(result["outputs"]["subtitle_top"], 7)
            self.assertEqual(result["outputs"]["subtitle_band_height"], 3)
            self.assertEqual(result["outputs"]["line_spacing"], 2)
            self.assertEqual(result["outputs"]["overlap"], 1)
            self.assertEqual(result["outputs"]["width"], 10)
            self.assertEqual(result["outputs"]["height"], 14)

            with Image.open(output) as image:
                self.assertEqual(image.size, (10, 14))
                self.assertEqual(image.getpixel((5, 6)), (220, 30, 30))
                self.assertEqual(image.getpixel((5, 7)), (220, 30, 30))
                self.assertEqual(image.getpixel((5, 9)), (30, 200, 30))
                self.assertEqual(image.getpixel((5, 11)), (30, 30, 220))
                self.assertEqual(image.getpixel((5, 13)), (30, 30, 220))

    def test_rejects_spacing_larger_than_subtitle_band(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            paths = []
            for index in range(2):
                path = root / f"frame-{index}.png"
                Image.new("RGB", (8, 10), "white").save(path)
                paths.append(path)

            with patch("imgtools.service.runner.write_manifest", return_value=None):
                result = run_tool(
                    "merge.dialogue_stack",
                    {
                        "input_paths": [str(path) for path in paths],
                        "subtitle_top_ratio": 0.8,
                        "line_spacing": 3,
                    },
                )
            self.assertFalse(result["ok"])
            self.assertIn("line_spacing", result["message"])

    def test_rejects_mismatched_dimensions(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            first = root / "first.png"
            second = root / "second.png"
            Image.new("RGB", (8, 10), "white").save(first)
            Image.new("RGB", (9, 10), "white").save(second)

            with patch("imgtools.service.runner.write_manifest", return_value=None):
                result = run_tool(
                    "merge.dialogue_stack",
                    {"input_paths": [str(first), str(second)]},
                )
            self.assertFalse(result["ok"])
            self.assertIn("same dimensions", result["message"])

    def test_source_naming_uses_last_image_stem_beside_first_image(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            first_folder = root / "first-folder"
            last_folder = root / "last-folder"
            first_folder.mkdir()
            last_folder.mkdir()
            first = first_folder / "opening.png"
            last = last_folder / "ending.jpg"
            Image.new("RGB", (8, 10), "white").save(first)
            Image.new("RGB", (8, 10), "black").save(last)

            with patch("imgtools.service.runner.write_manifest", return_value=None):
                result = run_tool(
                    "merge.dialogue_stack",
                    {
                        "input_paths": [str(first), str(last)],
                        "output_naming": "source",
                        "line_spacing": 1,
                    },
                )

            self.assertTrue(result["ok"], result)
            self.assertEqual(
                Path(result["outputs"]["files"][0]),
                first_folder / "ending.png",
            )


if __name__ == "__main__":
    unittest.main()
