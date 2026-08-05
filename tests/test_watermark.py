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

    def test_text_watermark_clamps_oversized_position_to_canvas(self):
        from imgtools.core.watermark import add_text

        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "small.png"
            output_path = Path(tmp) / "output.png"
            Image.new("RGB", (80, 60), "white").save(input_path)

            result = add_text({
                "input_path": str(input_path),
                "output_path": str(output_path),
                "text": "A very long watermark label",
                "font_size": 40,
                "rotation": 45,
                "opacity": 120,
                "position": "bottom_right",
            })

            self.assertTrue(result["ok"])
            with Image.open(output_path) as image:
                self.assertEqual(image.size, (80, 60))

    def test_text_watermark_supports_custom_color(self):
        from imgtools.core.watermark import add_text

        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "input.png"
            output_path = Path(tmp) / "red.png"
            Image.new("RGB", (180, 100), "white").save(input_path)

            add_text({
                "input_path": str(input_path),
                "output_path": str(output_path),
                "text": "RED",
                "font_size": 28,
                "rotation": 0,
                "opacity": 255,
                "color": "#ff0000",
                "position": "top_left",
                "margin": 0,
            })

            with Image.open(output_path) as image:
                pixels = list(image.convert("RGB").getdata())
            self.assertTrue(any(red > 200 and green < 100 and blue < 100 for red, green, blue in pixels))

    def test_text_watermark_repeat_covers_more_of_the_canvas(self):
        from imgtools.core.watermark import add_text

        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "input.png"
            single_path = Path(tmp) / "single.png"
            repeat_path = Path(tmp) / "repeat.png"
            Image.new("RGB", (320, 240), "white").save(input_path)
            common = {
                "input_path": str(input_path),
                "text": "X",
                "font_size": 28,
                "rotation": 0,
                "opacity": 255,
                "color": "#ff0000",
                "position": "top_left",
                "margin": 0,
            }
            add_text({**common, "output_path": str(single_path)})
            add_text({**common, "output_path": str(repeat_path), "repeat": True, "repeat_spacing": 20})

            with Image.open(single_path) as single, Image.open(repeat_path) as repeated:
                single_changed = sum(pixel != (255, 255, 255) for pixel in single.convert("RGB").getdata())
                repeat_changed = sum(pixel != (255, 255, 255) for pixel in repeated.convert("RGB").getdata())
            self.assertGreater(repeat_changed, single_changed * 3)

    def test_batch_text_watermark_writes_one_result_per_input(self):
        from imgtools.core.watermark import add_text_batch

        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "first.png"
            second = Path(tmp) / "second.jpg"
            output_dir = Path(tmp) / "results"
            Image.new("RGB", (120, 80), "white").save(first)
            Image.new("RGB", (100, 70), "white").save(second)

            result = add_text_batch({
                "input_paths": [str(first), str(second)],
                "output_dir": str(output_dir),
                "text": "BATCH",
                "font_size": 18,
                "opacity": 255,
                "color": "#4f46e5",
                "rotation": 30,
            })

            output_paths = [Path(path) for path in result["outputs"]["files"]]
            self.assertEqual(len(output_paths), 2)
            self.assertEqual({path.parent for path in output_paths}, {output_dir.resolve()})
            self.assertEqual({path.name for path in output_paths}, {"first-watermarked.png", "second-watermarked.jpg"})
            self.assertTrue(all(path.is_file() for path in output_paths))

    def test_text_action_accepts_multiple_input_paths(self):
        from imgtools.service.runner import run_tool

        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "first.png"
            second = Path(tmp) / "second.png"
            Image.new("RGB", (120, 80), "white").save(first)
            Image.new("RGB", (100, 70), "white").save(second)

            result = run_tool(
                "watermark.text",
                {
                    "input_paths": [str(first), str(second)],
                    "text": "BATCH",
                    "font_size": 18,
                    "opacity": 255,
                    "rotation": 30,
                },
                manifest=False,
            )

            self.assertTrue(result["ok"], result)
            self.assertEqual(len(result["outputs"]["files"]), 2)
            self.assertTrue(all(Path(path).is_file() for path in result["outputs"]["files"]))


if __name__ == "__main__":
    unittest.main()
