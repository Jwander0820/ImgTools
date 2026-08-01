import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageChops


class WatermarkTests(unittest.TestCase):
    def test_text_watermark_can_be_placed_at_bottom_right(self):
        from imgtools.service.runner import run_tool

        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "input.png"
            output_path = Path(tmp) / "output.png"
            Image.new("RGB", (240, 140), "white").save(input_path)

            result = run_tool(
                "watermark.text",
                {
                    "input_path": str(input_path),
                    "output_path": str(output_path),
                    "text": "TEST",
                    "font_size": 24,
                    "rotation": 0,
                    "opacity": 255,
                    "position": "bottom_right",
                    "margin": 8,
                },
                manifest=False,
            )

            self.assertTrue(result["ok"], result)
            with Image.open(input_path) as source, Image.open(output_path) as marked:
                changed = ImageChops.difference(source.convert("RGB"), marked.convert("RGB"))
                bounds = changed.getbbox()
            self.assertIsNotNone(bounds)
            self.assertGreater(bounds[0], 120)
            self.assertGreater(bounds[1], 70)

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

    def test_text_watermark_source_mode_never_overwrites_same_format_input(self):
        from imgtools.core.watermark import add_text

        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "photo.png"
            Image.new("RGB", (80, 60), "white").save(input_path)

            first = add_text({
                "input_path": str(input_path),
                "text": "TEST",
                "output_naming": "source",
            })
            second = add_text({
                "input_path": str(input_path),
                "text": "TEST",
                "output_naming": "source",
            })

            self.assertEqual(Path(first["outputs"]["files"][0]), Path(tmp) / "photo-2.png")
            self.assertEqual(Path(second["outputs"]["files"][0]), Path(tmp) / "photo-3.png")
            with Image.open(input_path) as image:
                self.assertEqual(image.convert("RGB").getpixel((0, 0)), (255, 255, 255))

    def test_text_watermark_source_mode_protects_input_even_with_overwrite(self):
        from imgtools.core.watermark import add_text

        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "photo.png"
            Image.new("RGB", (80, 60), "white").save(input_path)

            result = add_text({
                "input_path": str(input_path),
                "text": "TEST",
                "output_naming": "source",
                "overwrite": True,
            })

            self.assertEqual(Path(result["outputs"]["files"][0]), Path(tmp) / "photo-2.png")
            with Image.open(input_path) as image:
                self.assertEqual(image.convert("RGB").getpixel((0, 0)), (255, 255, 255))


if __name__ == "__main__":
    unittest.main()
