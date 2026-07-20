import tempfile
import unittest
from pathlib import Path

from PIL import Image


class TifTests(unittest.TestCase):
    def _make_multipage_tif(self, path):
        frames = [Image.new("RGB", (8, 6), color) for color in ("red", "green", "blue")]
        frames[0].save(path, save_all=True, append_images=frames[1:])

    def test_split_pages_writes_one_based_named_files(self):
        from imgtools.core.tif import split_pages

        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "sample.tif"
            output_dir = Path(tmp) / "pages"
            self._make_multipage_tif(input_path)

            result = split_pages({"input_path": str(input_path), "output_dir": str(output_dir)})

            files = [Path(path) for path in result["outputs"]["files"]]
            self.assertEqual([path.name for path in files], [
                "sample_page001.tif", "sample_page002.tif", "sample_page003.tif"
            ])
            self.assertTrue(all(path.exists() for path in files))

    def test_extract_page_uses_one_based_page_number(self):
        from imgtools.core.tif import extract_page

        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "sample.tif"
            output_path = Path(tmp) / "picked.tif"
            self._make_multipage_tif(input_path)

            result = extract_page({
                "input_path": str(input_path), "page": 2, "output_path": str(output_path)
            })

            self.assertTrue(result["ok"])
            self.assertTrue(output_path.exists())
            with Image.open(output_path) as image:
                self.assertEqual(image.n_frames, 1)

    def test_extract_page_rejects_out_of_range_page(self):
        from imgtools.core.tif import extract_page

        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "sample.tif"
            self._make_multipage_tif(input_path)
            with self.assertRaises(ValueError):
                extract_page({"input_path": str(input_path), "page": 4})

    def test_images_to_tif_sorts_images_and_uses_collision_free_default(self):
        from imgtools.service.runner import run_tool

        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "images"
            folder.mkdir()
            Image.new("RGB", (8, 6), "blue").save(folder / "02.png")
            Image.new("RGB", (8, 6), "red").save(folder / "01.png")

            first = run_tool("merge.images_to_tif", {"folder_path": str(folder)}, manifest=False)
            second = run_tool("merge.images_to_tif", {"folder_path": str(folder)}, manifest=False)

            self.assertTrue(first["ok"], first)
            self.assertTrue(second["ok"], second)
            first_path = Path(first["outputs"]["files"][0])
            second_path = Path(second["outputs"]["files"][0])
            self.assertEqual(first_path, folder / "output.tif")
            self.assertEqual(second_path, folder / "output-2.tif")
            self.assertEqual(first["outputs"]["page_count"], 2)
            with Image.open(first_path) as image:
                self.assertEqual(image.n_frames, 2)
                image.seek(0)
                self.assertEqual(image.convert("RGB").getpixel((0, 0)), (255, 0, 0))
                image.seek(1)
                self.assertEqual(image.convert("RGB").getpixel((0, 0)), (0, 0, 255))


if __name__ == "__main__":
    unittest.main()
