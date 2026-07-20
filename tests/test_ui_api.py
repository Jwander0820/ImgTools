import json
import unittest
from unittest.mock import patch


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

    def test_api_pick_validates_mode_and_returns_paths(self):
        from imgtools.ui.api import handle_pick

        self.assertFalse(handle_pick({"mode": "wrong"})["ok"])
        with patch("imgtools.ui.api.pick_paths", return_value=["D:/Images/a.png"]):
            result = handle_pick({"mode": "file"})

        self.assertTrue(result["ok"])
        self.assertEqual(result["paths"], ["D:/Images/a.png"])


if __name__ == "__main__":
    unittest.main()
