import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from PIL import Image


def _ffmpeg_executable():
    executable = os.environ.get("IMGTOOLS_FFMPEG") or shutil.which("ffmpeg")
    if not executable:
        try:
            import imageio_ffmpeg

            executable = imageio_ffmpeg.get_ffmpeg_exe()
        except (ImportError, RuntimeError):
            executable = None
    if not executable:
        raise unittest.SkipTest("ffmpeg is required for video integration tests")
    return executable


def _make_three_frame_mp4(path):
    subprocess.run(
        [
            _ffmpeg_executable(),
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=size=16x12:rate=3:duration=1",
            "-frames:v",
            "3",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


class VideoTests(unittest.TestCase):
    def test_extract_frames_writes_all_frames_to_default_sibling_folder(self):
        from imgtools.service.runner import run_tool

        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "sample.mp4"
            _make_three_frame_mp4(input_path)

            result = run_tool(
                "video.extract_frames", {"input_path": str(input_path)}, manifest=False
            )

            self.assertTrue(result["ok"], result)
            files = [Path(path) for path in result["outputs"]["files"]]
            self.assertEqual([path.name for path in files], [
                "output_frame_000001.png", "output_frame_000002.png", "output_frame_000003.png"
            ])
            self.assertEqual(Path(result["outputs"]["output_dir"]), input_path.with_name("output_frames"))
            self.assertEqual(result["outputs"]["frame_count"], 3)
            with Image.open(files[0]) as image:
                self.assertEqual(image.size, (16, 12))

    def test_extract_frames_source_mode_uses_original_stem(self):
        from imgtools.service.runner import run_tool

        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "sample.mp4"
            _make_three_frame_mp4(input_path)

            result = run_tool(
                "video.extract_frames",
                {"input_path": str(input_path), "output_naming": "source"},
                manifest=False,
            )

            files = [Path(path) for path in result["outputs"]["files"]]
            self.assertEqual(files[0].parent.name, "sample_frames")
            self.assertEqual(files[0].name, "sample_frame_000001.png")

    def test_mp4_to_gif_uses_simple_collision_free_output(self):
        from imgtools.service.runner import run_tool

        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "sample.mp4"
            _make_three_frame_mp4(input_path)

            first = run_tool(
                "gif.mp4_to_gif", {"input_path": str(input_path), "fps": 3}, manifest=False
            )
            second = run_tool(
                "gif.mp4_to_gif", {"input_path": str(input_path), "fps": 3}, manifest=False
            )

            self.assertTrue(first["ok"], first)
            self.assertTrue(second["ok"], second)
            first_path = Path(first["outputs"]["files"][0])
            second_path = Path(second["outputs"]["files"][0])
            self.assertEqual(first_path, input_path.with_name("output.gif"))
            self.assertEqual(second_path, input_path.with_name("output-2.gif"))
            with Image.open(first_path) as image:
                self.assertEqual(image.n_frames, 3)
                self.assertEqual(image.size, (16, 12))

    def test_gif_to_mp4_uses_simple_collision_free_output(self):
        from imgtools.service.runner import run_tool

        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "source.gif"
            frames = [Image.new("RGB", (15, 13), color) for color in ("red", "green", "blue")]
            frames[0].save(
                input_path,
                format="GIF",
                save_all=True,
                append_images=frames[1:],
                duration=200,
                loop=0,
            )

            first = run_tool(
                "gif.gif_to_mp4", {"input_path": str(input_path), "fps": 5}, manifest=False
            )
            second = run_tool(
                "gif.gif_to_mp4", {"input_path": str(input_path), "fps": 5}, manifest=False
            )

            self.assertTrue(first["ok"], first)
            self.assertTrue(second["ok"], second)
            first_path = Path(first["outputs"]["files"][0])
            second_path = Path(second["outputs"]["files"][0])
            self.assertEqual(first_path, input_path.with_name("output.mp4"))
            self.assertEqual(second_path, input_path.with_name("output-2.mp4"))
            extracted = run_tool(
                "video.extract_frames", {"input_path": str(first_path)}, manifest=False
            )
            self.assertTrue(extracted["ok"], extracted)
            self.assertGreaterEqual(extracted["outputs"]["frame_count"], 3)
            with Image.open(extracted["outputs"]["files"][0]) as image:
                self.assertEqual(image.size, (16, 14))


if __name__ == "__main__":
    unittest.main()
