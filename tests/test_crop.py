import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw


class CropTextRegionsTests(unittest.TestCase):
    def test_text_regions_extracts_transparent_outputs_in_reading_order(self):
        from imgtools.service.runner import run_tool

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / "stamps.png"
            image = Image.new("RGB", (160, 80), "white")
            draw = ImageDraw.Draw(image)
            draw.rectangle((12, 18, 42, 58), fill="black")
            draw.rectangle((96, 22, 140, 54), fill="black")
            image.save(input_path)

            result = run_tool(
                "crop.text_regions",
                {
                    "input_path": str(input_path),
                    "dilate_iterations": 2,
                    "min_area": 100,
                },
                manifest=False,
            )

            self.assertTrue(result["ok"], result)
            outputs = [Path(path) for path in result["outputs"]["files"]]
            self.assertEqual([path.name for path in outputs], [
                "output_region_001.png",
                "output_region_002.png",
            ])
            self.assertEqual(result["outputs"]["region_count"], 2)
            for output in outputs:
                with Image.open(output) as region:
                    self.assertEqual(region.mode, "RGBA")
                    self.assertEqual(region.getchannel("A").getextrema(), (0, 255))


if __name__ == "__main__":
    unittest.main()
