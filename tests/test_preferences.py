import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


TOOLS = [
    {"action": "tool.default-a", "featured": True},
    {"action": "tool.default-b", "featured": True},
    {"action": "tool.other", "featured": False},
    {"action": "tool.pinned", "featured": False},
]


class PreferenceTests(unittest.TestCase):
    def test_repository_tracks_only_the_preferences_example(self):
        root = Path(__file__).resolve().parents[1]

        self.assertIn("/data/.imgtools/", (root / ".gitignore").read_text(encoding="utf-8"))
        example = root / "examples" / "preferences.example.json"
        self.assertTrue(example.is_file())
        data = json.loads(example.read_text(encoding="utf-8"))
        self.assertEqual(data["version"], 2)
        self.assertEqual(data["settings"]["pdf_default_dpi"], 192)

    def test_missing_file_uses_registry_defaults_without_creating_state(self):
        from imgtools.service.preferences import get_preferences_view

        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"IMGTOOLS_STATE_DIR": tmp}):
                result = get_preferences_view(TOOLS)

            self.assertEqual(
                [item["action"] for item in result["quick_actions"]],
                ["tool.default-a", "tool.default-b"],
            )
            self.assertTrue(all(item["source"] == "default" for item in result["quick_actions"]))
            self.assertFalse((Path(tmp) / "preferences.json").exists())

    def test_pinned_actions_are_first_and_preserve_user_order(self):
        from imgtools.service.preferences import get_preferences_view, update_pinned_actions

        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"IMGTOOLS_STATE_DIR": tmp}):
                update_pinned_actions(["tool.pinned", "tool.default-b"], TOOLS)
                result = get_preferences_view(TOOLS)

            self.assertEqual(result["pinned_actions"], ["tool.pinned", "tool.default-b"])
            self.assertEqual(
                [item["action"] for item in result["quick_actions"][:2]],
                ["tool.pinned", "tool.default-b"],
            )
            self.assertTrue(all(item["source"] == "pinned" for item in result["quick_actions"][:2]))

    def test_successful_usage_fills_before_system_defaults(self):
        from imgtools.service.preferences import get_preferences_view, record_successful_run

        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"IMGTOOLS_STATE_DIR": tmp}):
                with patch(
                    "imgtools.service.preferences._now_iso",
                    side_effect=["2026-07-20T10:00:00+08:00", "2026-07-20T11:00:00+08:00"],
                ):
                    record_successful_run("tool.other")
                    record_successful_run("tool.other")
                result = get_preferences_view(TOOLS)

            self.assertEqual(result["quick_actions"][0], {
                "action": "tool.other",
                "source": "frequent",
                "successful_runs": 2,
            })

    def test_preferences_are_written_to_private_state_file(self):
        from imgtools.service.preferences import update_pinned_actions

        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"IMGTOOLS_STATE_DIR": tmp}):
                update_pinned_actions(["tool.pinned"], TOOLS)

            path = Path(tmp) / "preferences.json"
            self.assertTrue(path.is_file())
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["version"], 2)
            self.assertEqual(data["pinned_actions"], ["tool.pinned"])
            self.assertEqual(data["usage"], {})
            self.assertEqual(data["settings"]["pdf_default_dpi"], 192)

    def test_pdf_default_dpi_is_persisted_without_resetting_pins(self):
        from imgtools.service.preferences import (
            update_pdf_default_dpi,
            update_pinned_actions,
        )

        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"IMGTOOLS_STATE_DIR": tmp}):
                update_pinned_actions(["tool.pinned"], TOOLS)
                result = update_pdf_default_dpi(300, TOOLS)

            data = json.loads((Path(tmp) / "preferences.json").read_text(encoding="utf-8"))
            self.assertEqual(result["pdf_default_dpi"], 300)
            self.assertEqual(data["settings"]["pdf_default_dpi"], 300)
            self.assertEqual(data["pinned_actions"], ["tool.pinned"])

    def test_legacy_preferences_gain_the_pdf_default_without_losing_data(self):
        from imgtools.service.preferences import get_preferences_view, update_pdf_default_dpi

        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "preferences.json"
            state_path.write_text(
                json.dumps({
                    "version": 1,
                    "pinned_actions": ["tool.pinned"],
                    "usage": {"tool.other": {"successful_runs": 2}},
                }),
                encoding="utf-8",
            )
            with patch.dict(os.environ, {"IMGTOOLS_STATE_DIR": tmp}):
                before = get_preferences_view(TOOLS)
                update_pdf_default_dpi(240, TOOLS)

            data = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(before["pdf_default_dpi"], 192)
            self.assertEqual(data["version"], 2)
            self.assertEqual(data["pinned_actions"], ["tool.pinned"])
            self.assertEqual(data["usage"]["tool.other"]["successful_runs"], 2)
            self.assertEqual(data["settings"]["pdf_default_dpi"], 240)

    def test_invalid_pdf_default_dpi_is_rejected(self):
        from imgtools.service.preferences import PreferenceValidationError, update_pdf_default_dpi

        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"IMGTOOLS_STATE_DIR": tmp}):
                for value in (True, 192.5, "not-a-number", 35, 1201):
                    with self.subTest(value=value), self.assertRaises(PreferenceValidationError):
                        update_pdf_default_dpi(value, TOOLS)

    def test_unknown_or_too_many_pins_are_rejected(self):
        from imgtools.service.preferences import PreferenceValidationError, update_pinned_actions

        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"IMGTOOLS_STATE_DIR": tmp}):
                with self.assertRaises(PreferenceValidationError):
                    update_pinned_actions(["tool.missing"], TOOLS)
                with self.assertRaises(PreferenceValidationError):
                    update_pinned_actions([f"tool.{index}" for index in range(9)], [
                        {"action": f"tool.{index}", "featured": False}
                        for index in range(9)
                    ])


if __name__ == "__main__":
    unittest.main()
