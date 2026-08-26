import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image


class UIAPITests(unittest.TestCase):
    def test_api_tools_returns_registry(self):
        from imgtools.ui.api import handle_get_tools

        result = handle_get_tools()

        self.assertTrue(result["ok"])
        self.assertIn("tools", result)
        actions = {tool["action"] for tool in result["tools"]}
        self.assertTrue({
            "video.extract_frames",
            "gif.mp4_to_gif",
            "gif.gif_to_mp4",
            "merge.images_to_tif",
        }.issubset(actions))

    def test_api_run_validates_payload(self):
        from imgtools.ui.api import handle_run

        result = handle_run({})

        self.assertFalse(result["ok"])
        self.assertEqual(result["error_code"], "VALIDATION_ERROR")

    def test_api_run_rejects_non_object_params_with_structured_error(self):
        from imgtools.ui.api import handle_run

        result = handle_run({"action": "pdf.render_page", "params": None})

        self.assertFalse(result["ok"])
        self.assertEqual(result["error_code"], "VALIDATION_ERROR")
        self.assertEqual(result["outputs"], {})
        self.assertEqual(result["warnings"], [])

    def test_api_run_returns_structured_result(self):
        from imgtools.ui.api import handle_run

        fake_result = {"ok": True, "action": "test.action", "outputs": {}, "warnings": []}
        with patch("imgtools.ui.api.run_tool", return_value=fake_result), patch(
            "imgtools.ui.api.record_successful_run"
        ) as record:
            result = handle_run({"action": "test.action", "params": {}})

        self.assertEqual(result, fake_result)
        record.assert_called_once_with("test.action")
        json.dumps(result)

    def test_api_run_does_not_record_failed_attempt(self):
        from imgtools.ui.api import handle_run

        fake_result = {"ok": False, "action": "test.action", "outputs": {}, "warnings": []}
        with patch("imgtools.ui.api.run_tool", return_value=fake_result), patch(
            "imgtools.ui.api.record_successful_run"
        ) as record:
            handle_run({"action": "test.action", "params": {}})

        record.assert_not_called()

    def test_api_reads_and_updates_quick_action_preferences(self):
        from imgtools.ui.api import handle_get_preferences, handle_update_preferences

        fake = {"pinned_actions": ["gif.images_to_gif"], "quick_actions": []}
        with patch("imgtools.ui.api.get_preferences_view", return_value=fake):
            result = handle_get_preferences()
        self.assertTrue(result["ok"])
        self.assertEqual(result["pinned_actions"], ["gif.images_to_gif"])

        with patch("imgtools.ui.api.update_pinned_actions", return_value=fake) as update:
            result = handle_update_preferences({"pinned_actions": ["gif.images_to_gif"]})
        self.assertTrue(result["ok"])
        update.assert_called_once_with(["gif.images_to_gif"])

    def test_api_updates_output_naming_preference(self):
        from imgtools.ui.api import handle_update_preferences

        with patch(
            "imgtools.ui.api.update_output_naming",
            return_value={"output_naming": "source"},
        ) as update:
            result = handle_update_preferences({"output_naming": "source"})

        update.assert_called_once_with("source")
        self.assertTrue(result["ok"])
        self.assertEqual(result["output_naming"], "source")

    def test_api_updates_pdf_default_dpi_without_requiring_pins(self):
        from imgtools.ui.api import handle_update_preferences

        fake = {
            "pinned_actions": [],
            "usage": {},
            "quick_actions": [],
            "max_pinned": 8,
            "pdf_default_dpi": 300,
        }
        with patch(
            "imgtools.ui.api.update_pdf_default_dpi",
            return_value=fake,
        ) as update:
            result = handle_update_preferences({"pdf_default_dpi": 300})

        self.assertTrue(result["ok"])
        self.assertEqual(result["pdf_default_dpi"], 300)
        update.assert_called_once_with(300)

    def test_api_pick_validates_mode_and_returns_paths(self):
        from imgtools.ui.api import handle_pick

        self.assertFalse(handle_pick({"mode": "wrong"})["ok"])
        with patch("imgtools.ui.api.pick_paths", return_value=["D:/Images/a.png"]):
            result = handle_pick({"mode": "file"})

        self.assertTrue(result["ok"])
        self.assertEqual(result["paths"], ["D:/Images/a.png"])

    def test_api_picker_can_return_browser_safe_previews_for_selected_images(self):
        from imgtools.ui.api import handle_pick

        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "source.tif"
            Image.new("RGB", (1600, 900), "navy").save(source)
            with patch("imgtools.ui.api.pick_paths", return_value=[str(source)]):
                result = handle_pick({"mode": "files", "include_previews": True})

        self.assertTrue(result["ok"])
        self.assertEqual(result["paths"], [str(source)])
        self.assertEqual(len(result["previews"]), 1)
        self.assertEqual(result["previews"][0]["path"], str(source))
        self.assertTrue(result["previews"][0]["data_url"].startswith("data:image/png;base64,"))

    def test_api_preview_accepts_a_directly_pasted_path(self):
        from imgtools.ui.api import handle_preview

        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "pasted source.png"
            Image.new("RGB", (1200, 700), "purple").save(source)
            result = handle_preview({"path": f'"{source}"'})

        self.assertTrue(result["ok"])
        self.assertEqual(result["paths"], [str(source)])
        self.assertEqual(len(result["previews"]), 1)
        self.assertEqual(result["previews"][0]["width"], 1200)
        self.assertEqual(result["previews"][0]["height"], 700)
        self.assertTrue(result["previews"][0]["data_url"].startswith("data:image/png;base64,"))

    def test_api_preview_returns_item_error_for_missing_path(self):
        from imgtools.ui.api import handle_preview

        result = handle_preview({"paths": ["D:/Images/missing-image.png"]})

        self.assertTrue(result["ok"])
        self.assertEqual(result["previews"][0]["path"], "D:/Images/missing-image.png")
        self.assertIn("error", result["previews"][0])

    def test_api_preview_validates_paths(self):
        from imgtools.ui.api import handle_preview

        result = handle_preview({"paths": [123]})

        self.assertFalse(result["ok"])
        self.assertEqual(result["error_code"], "VALIDATION_ERROR")


if __name__ == "__main__":
    unittest.main()
