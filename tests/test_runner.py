import json
import tempfile
import unittest
from pathlib import Path


class RunnerTests(unittest.TestCase):
    def test_run_tool_missing_required_param_returns_validation_error(self):
        from imgtools.service.runner import run_tool

        result = run_tool("rename.files_replace", {}, manifest=False)

        self.assertFalse(result["ok"])
        self.assertEqual(result["error_code"], "VALIDATION_ERROR")

    def test_run_tool_unknown_action_returns_unknown_action(self):
        from imgtools.service.runner import run_tool

        result = run_tool("missing.action", {}, manifest=False)

        self.assertFalse(result["ok"])
        self.assertEqual(result["error_code"], "UNKNOWN_ACTION")

    def test_run_tool_success_writes_manifest(self):
        from imgtools.service.runner import run_tool

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "old-name.txt").write_text("x", encoding="utf-8")

            result = run_tool(
                "rename.files_replace",
                {
                    "target_folder": str(root),
                    "target": "old",
                    "replacement": "new",
                },
            )

            self.assertTrue(result["ok"])
            manifest_path = Path(result["manifest_path"])
            self.assertTrue(manifest_path.exists())
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["action"], "rename.files_replace")
            self.assertTrue(manifest["ok"])

    def test_run_tool_failure_has_error_code(self):
        from imgtools.service.runner import run_tool

        result = run_tool(
            "rename.files_replace",
            {
                "target_folder": "Z:/definitely/missing/folder",
                "target": "old",
                "replacement": "new",
            },
            manifest=False,
        )

        self.assertFalse(result["ok"])
        self.assertTrue(result["error_code"])


if __name__ == "__main__":
    unittest.main()

