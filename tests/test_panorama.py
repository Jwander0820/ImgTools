import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import cv2
import numpy as np


def _write_image(path: Path, image: np.ndarray) -> None:
    ok, encoded = cv2.imencode(path.suffix, image)
    if not ok:
        raise AssertionError(f"Could not encode fixture: {path}")
    path.write_bytes(encoded.tobytes())


class PanoramaTranslationTests(unittest.TestCase):
    def test_estimate_translation_detects_horizontal_and_vertical_motion(self):
        from imgtools.core.merge import estimate_translation

        rng = np.random.default_rng(20260706)
        scene = rng.integers(0, 256, (220, 280, 3), dtype=np.uint8)
        first = scene[20:140, 30:190].copy()
        second = scene[55:175, 70:230].copy()

        match = estimate_translation(first, second, ignore_bottom_ratio=0.0)

        self.assertTrue(match.matched)
        self.assertAlmostEqual(match.dx, -40.0, delta=1.0)
        self.assertAlmostEqual(match.dy, -35.0, delta=1.0)
        self.assertGreaterEqual(match.inliers, 8)

        reverse = estimate_translation(second, first, ignore_bottom_ratio=0.0)
        self.assertTrue(reverse.matched)
        self.assertAlmostEqual(reverse.dx, 40.0, delta=1.0)
        self.assertAlmostEqual(reverse.dy, 35.0, delta=1.0)

    def test_bottom_overlay_is_ignored_for_matching_but_preserved_in_output(self):
        from imgtools.core.merge import panorama_translation

        rng = np.random.default_rng(17)
        scene = rng.integers(0, 220, (200, 240, 3), dtype=np.uint8)
        first = scene[0:120, 0:160].copy()
        second = scene[30:150, 20:180].copy()
        first[-24:] = (255, 255, 255)
        second[-24:] = (255, 255, 255)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first_path = root / "第一張.png"
            second_path = root / "第二張.png"
            _write_image(first_path, first)
            _write_image(second_path, second)

            result = panorama_translation(
                {
                    "input_paths": [str(first_path), str(second_path)],
                    "ignore_bottom_ratio": 0.2,
                    "crop_subtitles": False,
                }
            )

            output_path = Path(result["outputs"]["files"][0])
            output = cv2.imdecode(np.frombuffer(output_path.read_bytes(), np.uint8), cv2.IMREAD_COLOR)
            self.assertTrue(output_path.exists())
            self.assertEqual(output.shape[:2], (150, 180))
            self.assertTrue(np.any(np.all(output == 255, axis=2)))

    def test_weak_pair_outputs_only_largest_connected_segment(self):
        from imgtools.core.merge import PairMatch, panorama_translation

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = []
            for index in range(3):
                path = root / f"frame_{index}.png"
                _write_image(path, np.full((40, 60, 3), index * 60, dtype=np.uint8))
                paths.append(path)

            matches = [
                PairMatch(matched=False, inliers=2, candidates=20, inlier_ratio=0.1),
                PairMatch(matched=True, dx=0.0, dy=10.0, inliers=30, candidates=40, inlier_ratio=0.75),
            ]
            with patch("imgtools.core.merge.estimate_translation", side_effect=matches):
                result = panorama_translation(
                    {
                        "input_paths": [str(path) for path in paths],
                        "allow_low_confidence": False,
                    }
                )

            self.assertEqual(result["outputs"]["used_files"], [str(path.resolve()) for path in paths[1:]])
            self.assertEqual(result["outputs"]["skipped_files"], [str(paths[0].resolve())])
            self.assertEqual(len(result["outputs"]["pair_matches"]), 2)
            self.assertTrue(result["warnings"])

    def test_timestamp_fallback_includes_low_confidence_pair(self):
        from imgtools.core.merge import PairMatch, panorama_translation

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            names = ["shot_002240.000.png", "shot_002242.000.png", "shot_002243.000.png"]
            paths = []
            for index, name in enumerate(names):
                path = root / name
                _write_image(path, np.full((40, 60, 3), index * 60, dtype=np.uint8))
                paths.append(path)

            normal_matches = [
                PairMatch(matched=False, inliers=3, candidates=50, inlier_ratio=0.06),
                PairMatch(
                    matched=True,
                    dx=0.0,
                    dy=10.0,
                    inliers=30,
                    candidates=40,
                    inlier_ratio=0.75,
                ),
            ]
            recovered = PairMatch(
                matched=True,
                dx=0.0,
                dy=20.0,
                inliers=3,
                candidates=80,
                inlier_ratio=0.0375,
                method="timestamp_fallback",
                low_confidence=True,
            )
            with (
                patch("imgtools.core.merge.estimate_translation", side_effect=normal_matches),
                patch(
                    "imgtools.core.merge._estimate_translation_near_prediction",
                    return_value=recovered,
                ) as fallback,
            ):
                result = panorama_translation({"input_paths": [str(path) for path in paths]})

            self.assertEqual(result["outputs"]["used_files"], [str(path.resolve()) for path in paths])
            self.assertEqual(result["outputs"]["skipped_files"], [])
            self.assertEqual(result["outputs"]["pair_matches"][0]["method"], "timestamp_fallback")
            self.assertTrue(result["outputs"]["pair_matches"][0]["low_confidence"])
            self.assertIn("low-confidence", result["warnings"][0])
            predicted = fallback.call_args.args[2]
            self.assertAlmostEqual(predicted[0], 0.0)
            self.assertAlmostEqual(predicted[1], 20.0)

    def test_timestamp_fallback_can_be_disabled(self):
        from imgtools.core.merge import PairMatch, panorama_translation

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = []
            for index, timestamp in enumerate(("002240.000", "002242.000", "002243.000")):
                path = root / f"shot_{timestamp}.png"
                _write_image(path, np.full((40, 60, 3), index * 40, dtype=np.uint8))
                paths.append(path)
            matches = [
                PairMatch(matched=False, inliers=3, candidates=50, inlier_ratio=0.06),
                PairMatch(matched=True, dx=0.0, dy=10.0, inliers=20, candidates=20, inlier_ratio=1.0),
            ]

            with (
                patch("imgtools.core.merge.estimate_translation", side_effect=matches),
                patch("imgtools.core.merge._estimate_translation_near_prediction") as fallback,
            ):
                result = panorama_translation(
                    {
                        "input_paths": [str(path) for path in paths],
                        "allow_low_confidence": False,
                    }
                )

            fallback.assert_not_called()
            self.assertEqual(result["outputs"]["used_files"], [str(path.resolve()) for path in paths[1:]])

    def test_later_image_overwrites_earlier_image_in_overlap(self):
        from imgtools.core.merge import PairMatch, panorama_translation

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first_path = root / "first.png"
            second_path = root / "second.png"
            first = np.full((40, 60, 3), (10, 20, 30), dtype=np.uint8)
            second = np.full((40, 60, 3), (100, 150, 200), dtype=np.uint8)
            _write_image(first_path, first)
            _write_image(second_path, second)
            match = PairMatch(
                matched=True,
                dx=0.0,
                dy=10.0,
                inliers=20,
                candidates=20,
                inlier_ratio=1.0,
            )

            with patch("imgtools.core.merge.estimate_translation", return_value=match):
                result = panorama_translation(
                    {
                        "input_paths": [str(first_path), str(second_path)],
                        "crop_subtitles": False,
                    }
                )

            output_path = Path(result["outputs"]["files"][0])
            output = cv2.imdecode(np.frombuffer(output_path.read_bytes(), np.uint8), cv2.IMREAD_COLOR)
            # The second frame is placed above the first and must fully replace it in the overlap.
            np.testing.assert_array_equal(output[15, 30], second[15, 30])
            np.testing.assert_array_equal(output[45, 30], first[35, 30])

    def test_subtitle_seam_uses_lower_frame_before_upper_subtitle(self):
        from imgtools.core.merge import PairMatch, panorama_translation

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first_path = root / "first.png"
            second_path = root / "second.png"
            first = np.full((40, 60, 3), 30, dtype=np.uint8)
            second = np.full((40, 60, 3), 180, dtype=np.uint8)
            first[-12:-2] = 255
            second[-12:-2] = 255
            _write_image(first_path, first)
            _write_image(second_path, second)
            match = PairMatch(
                matched=True,
                dx=0.0,
                dy=10.0,
                inliers=20,
                candidates=20,
                inlier_ratio=1.0,
            )

            with patch("imgtools.core.merge.estimate_translation", return_value=match):
                result = panorama_translation(
                    {
                        "input_paths": [str(first_path), str(second_path)],
                        "ignore_bottom_ratio": 0.25,
                        "subtitle_crop_ratio": 0.25,
                        "crop_subtitles": True,
                    }
                )

            output_path = Path(result["outputs"]["files"][0])
            output = cv2.imdecode(np.frombuffer(output_path.read_bytes(), np.uint8), cv2.IMREAD_COLOR)
            self.assertEqual(output.shape[:2], (50, 60))
            self.assertEqual(result["outputs"]["subtitle_rows_removed"], 0)
            self.assertEqual(result["outputs"]["subtitle_seams_applied"], 1)
            np.testing.assert_array_equal(output[30, 30], first[20, 30])
            np.testing.assert_array_equal(output[42, 30], first[32, 30])

    def test_all_weak_pairs_raise_insufficient_overlap_without_output(self):
        from imgtools.core.merge import InsufficientOverlapError, PairMatch, panorama_translation

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = []
            for index in range(2):
                path = root / f"frame_{index}.png"
                _write_image(path, np.full((40, 60, 3), index * 20, dtype=np.uint8))
                paths.append(path)

            weak = PairMatch(matched=False, inliers=0, candidates=0, inlier_ratio=0.0)
            with patch("imgtools.core.merge.estimate_translation", return_value=weak):
                with self.assertRaises(InsufficientOverlapError):
                    panorama_translation({"input_paths": [str(path) for path in paths]})

            self.assertFalse((root / "stitched").exists())

    def test_rejects_too_few_images_and_mismatched_dimensions(self):
        from imgtools.core.merge import panorama_translation

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = root / "a.png"
            second = root / "b.png"
            _write_image(first, np.zeros((40, 60, 3), dtype=np.uint8))
            _write_image(second, np.zeros((50, 60, 3), dtype=np.uint8))

            with self.assertRaisesRegex(ValueError, "at least two"):
                panorama_translation({"input_paths": [str(first)]})
            with self.assertRaisesRegex(ValueError, "same dimensions"):
                panorama_translation({"input_paths": [str(first), str(second)]})

    def test_existing_default_output_gets_collision_free_name(self):
        from imgtools.core.merge import PairMatch, panorama_translation

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = [root / "a.png", root / "b.png"]
            for path in paths:
                _write_image(path, np.zeros((40, 60, 3), dtype=np.uint8))
            output = root / "stitched" / "output.png"
            output.parent.mkdir()
            output.write_bytes(b"existing")
            match = PairMatch(matched=True, dx=10.0, dy=0.0, inliers=20, candidates=20, inlier_ratio=1.0)

            with patch("imgtools.core.merge.estimate_translation", return_value=match):
                result = panorama_translation({"input_paths": [str(path) for path in paths]})

            self.assertEqual(Path(result["outputs"]["files"][0]), output.with_name("output-2.png"))
            self.assertEqual(output.read_bytes(), b"existing")


if __name__ == "__main__":
    unittest.main()
