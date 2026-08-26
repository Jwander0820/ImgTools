import tempfile
import unittest
from pathlib import Path

from PIL import Image


class VerticalStackTests(unittest.TestCase):
    def _save(self, path: Path, size: tuple[int, int], color: str) -> None:
        Image.new("RGB", size, color).save(path)

    def test_stacks_images_top_to_bottom_without_resizing(self):
        from imgtools.core.merge import stack_vertical

        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            first = folder / "first.png"
            second = folder / "second.png"
            third = folder / "third.png"
            self._save(first, (4, 2), "red")
            self._save(second, (4, 3), "green")
            self._save(third, (4, 1), "blue")

            result = stack_vertical(
                {"input_paths": [str(first), str(second), str(third)]}
            )

            output = Path(result["outputs"]["files"][0])
            with Image.open(output) as image:
                self.assertEqual(image.size, (4, 6))
                self.assertEqual(image.getpixel((0, 0)), (255, 0, 0))
                self.assertEqual(image.getpixel((0, 2)), (0, 128, 0))
                self.assertEqual(image.getpixel((0, 5)), (0, 0, 255))
            self.assertEqual(result["outputs"]["image_count"], 3)
            self.assertEqual(result["outputs"]["width"], 4)
            self.assertEqual(result["outputs"]["height"], 6)

    def test_requires_two_to_nine_images(self):
        from imgtools.core.merge import stack_vertical

        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "one.png"
            self._save(image, (2, 2), "white")

            with self.assertRaisesRegex(ValueError, "2 to 9"):
                stack_vertical({"input_paths": [str(image)]})
            with self.assertRaisesRegex(ValueError, "2 to 9"):
                stack_vertical({"input_paths": [str(image)] * 10})

    def test_accepts_nine_images(self):
        from imgtools.core.merge import stack_vertical

        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "one.png"
            self._save(image, (2, 2), "white")

            result = stack_vertical({"input_paths": [str(image)] * 9})

            self.assertEqual(result["outputs"]["image_count"], 9)
            self.assertEqual(result["outputs"]["width"], 2)
            self.assertEqual(result["outputs"]["height"], 18)

    def test_rejects_mismatched_widths_instead_of_resizing(self):
        from imgtools.core.merge import stack_vertical

        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "first.png"
            second = Path(tmp) / "second.png"
            self._save(first, (4, 2), "white")
            self._save(second, (5, 2), "black")

            with self.assertRaisesRegex(ValueError, "same width"):
                stack_vertical({"input_paths": [str(first), str(second)]})

    def test_explicit_output_cannot_replace_an_input(self):
        from imgtools.core.merge import stack_vertical

        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "first.png"
            second = Path(tmp) / "second.png"
            self._save(first, (2, 2), "white")
            self._save(second, (2, 2), "black")

            with self.assertRaisesRegex(ValueError, "protected input"):
                stack_vertical(
                    {
                        "input_paths": [str(first), str(second)],
                        "output_path": str(first),
                        "overwrite": True,
                    }
                )

    def test_explicit_output_requires_png_extension(self):
        from imgtools.core.merge import stack_vertical

        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "first.png"
            second = Path(tmp) / "second.png"
            self._save(first, (2, 2), "white")
            self._save(second, (2, 2), "black")

            with self.assertRaisesRegex(ValueError, "end in .png"):
                stack_vertical(
                    {
                        "input_paths": [str(first), str(second)],
                        "output_path": str(Path(tmp) / "comparison.jpg"),
                    }
                )

    def test_source_naming_uses_last_image_stem_beside_first_image(self):
        from imgtools.core.merge import stack_vertical

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first_folder = root / "first-folder"
            last_folder = root / "last-folder"
            first_folder.mkdir()
            last_folder.mkdir()
            first = first_folder / "opening.png"
            last = last_folder / "ending.jpg"
            self._save(first, (2, 2), "white")
            self._save(last, (2, 2), "black")

            result = stack_vertical({
                "input_paths": [str(first), str(last)],
                "output_naming": "source",
            })

            self.assertEqual(
                Path(result["outputs"]["files"][0]),
                first_folder / "ending.png",
            )


if __name__ == "__main__":
    unittest.main()
