import tempfile
import unittest
from pathlib import Path

from PIL import Image


class WatermarkTests(unittest.TestCase):
    def test_text_watermark_writes_same_size_image(self):
        from imgtools.core.watermark import add_text

        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "input.png"
            output_path = Path(tmp) / "output.png"
            Image.new("RGB", (120, 80), "white").save(input_path)

            result = add_text({
                "input_path": str(input_path),
                "output_path": str(output_path),
                "text": "TEST",
                "font_size": 20,
                "rotation": 30,
                "opacity": 100,
            })

            self.assertTrue(result["ok"])
            with Image.open(output_path) as image:
                self.assertEqual(image.size, (120, 80))

    def test_text_watermark_defaults_output_beside_input(self):
        from imgtools.core.watermark import add_text

        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "input.png"
            Image.new("RGB", (80, 60), "white").save(input_path)

            result = add_text({"input_path": str(input_path), "text": "TEST"})

            self.assertEqual(Path(result["outputs"]["files"][0]), Path(tmp) / "output.png")
            self.assertTrue((Path(tmp) / "output.png").is_file())


if __name__ == "__main__":
    unittest.main()
