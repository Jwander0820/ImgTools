import tempfile
import unittest
from pathlib import Path

from PIL import Image


class GifTests(unittest.TestCase):
    def test_images_to_gif_uses_sorted_supported_images(self):
        from imgtools.core.gif import images_to_gif

        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "frames"
            folder.mkdir()
            Image.new("RGB", (10, 10), "blue").save(folder / "02.png")
            Image.new("RGB", (10, 10), "red").save(folder / "01.png")
            output_path = Path(tmp) / "result.gif"

            result = images_to_gif({
                "folder_path": str(folder),
                "output_path": str(output_path),
                "duration": 80,
                "loop": 0,
            })

            self.assertTrue(result["ok"])
            with Image.open(output_path) as image:
                self.assertEqual(image.n_frames, 2)
                self.assertEqual(image.info["duration"], 80)

    def test_images_to_gif_rejects_empty_folder(self):
        from imgtools.core.gif import images_to_gif

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                images_to_gif({
                    "folder_path": tmp,
                    "output_path": str(Path(tmp) / "result.gif"),
                })

    def test_images_to_gif_defaults_to_collision_free_output_in_source_folder(self):
        from imgtools.core.gif import images_to_gif

        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "frames"
            folder.mkdir()
            Image.new("RGB", (8, 8), "blue").save(folder / "frame.png")

            first = images_to_gif({"folder_path": str(folder)})
            second = images_to_gif({"folder_path": str(folder)})

            self.assertEqual(Path(first["outputs"]["files"][0]), folder / "output.gif")
            self.assertEqual(Path(second["outputs"]["files"][0]), folder / "output-2.gif")
            self.assertTrue((folder / "output.gif").is_file())
            self.assertTrue((folder / "output-2.gif").is_file())


if __name__ == "__main__":
    unittest.main()
