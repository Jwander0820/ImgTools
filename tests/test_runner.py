import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class RunnerTests(unittest.TestCase):
    def test_run_tool_accepts_windows_copy_as_path_quotes(self):
        from PIL import Image

        from imgtools.service.runner import run_tool

        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "source.tif"
            output_path = Path(tmp) / "extracted.tif"
            Image.new("RGB", (2, 2), "white").save(input_path)

            result = run_tool(
                "tif.extract_page",
                {
                    "input_path": f'"{input_path}"',
                    "output_path": f'"{output_path}"',
                },
                manifest=False,
            )

            self.assertTrue(result["ok"])
            self.assertTrue(output_path.is_file())
            self.assertEqual(result["outputs"]["files"], [str(output_path.resolve())])

    def test_run_tool_accepts_quoted_paths_in_multiline_path_input(self):
        from imgtools.service.runner import run_tool

        with tempfile.TemporaryDirectory() as tmp:
            first_path = Path(tmp) / "first.png"
            second_path = Path(tmp) / "second.png"
            copied_paths = f'"{first_path}"\n"{second_path}"'

            result = run_tool(
                "merge.panorama_translation",
                {"input_paths": copied_paths},
                manifest=False,
            )

            self.assertFalse(result["ok"])
            self.assertEqual(result["error_code"], "FileNotFoundError")
            self.assertEqual(
                result["message"],
                f"Input image does not exist: {first_path.resolve()}",
            )

    def test_prepare_params_preserves_valid_global_output_naming(self):
        from imgtools.service.registry import ToolParam
        from imgtools.service.runner import _prepare_params

        params = _prepare_params(
            (ToolParam("input_path", "path", True),),
            {"input_path": "photo.png", "output_naming": "source"},
        )

        self.assertEqual(params["output_naming"], "source")

    def test_prepare_params_rejects_unknown_global_output_naming(self):
        from imgtools.service.registry import ToolParam
        from imgtools.service.runner import ToolValidationError, _prepare_params

        with self.assertRaises(ToolValidationError):
            _prepare_params(
                (ToolParam("input_path", "path", True),),
                {"input_path": "photo.png", "output_naming": "surprise"},
            )

    def test_prepare_params_coerces_path_list_and_float(self):
        from imgtools.service.registry import ToolParam
        from imgtools.service.runner import _prepare_params

        params = _prepare_params(
            (
                ToolParam("input_paths", "path_list", True),
                ToolParam("ignore_bottom_ratio", "float", False, 0.15),
            ),
            {"input_paths": "a.png\nb.png", "ignore_bottom_ratio": "0.2"},
        )

        self.assertEqual(params["input_paths"], ["a.png", "b.png"])
        self.assertEqual(params["ignore_bottom_ratio"], 0.2)

    def test_panorama_error_code_is_preserved(self):
        from imgtools.service.runner import run_tool

        result = run_tool(
            "merge.panorama_translation",
            {"input_paths": ["missing-a.png", "missing-b.png"]},
            manifest=False,
        )

        self.assertFalse(result["ok"])
        self.assertEqual(result["error_code"], "FileNotFoundError")

    def test_panorama_insufficient_overlap_has_stable_error_code(self):
        from imgtools.core.merge import InsufficientOverlapError
        from imgtools.service.runner import run_tool

        with patch(
            "imgtools.core.merge.panorama_translation",
            side_effect=InsufficientOverlapError("not enough overlap"),
        ):
            result = run_tool(
                "merge.panorama_translation",
                {"input_paths": ["a.png", "b.png"]},
                manifest=False,
            )

        self.assertFalse(result["ok"])
        self.assertEqual(result["error_code"], "INSUFFICIENT_OVERLAP")

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
            state_root = root / "server-state"
            (root / "old-name.txt").write_text("x", encoding="utf-8")

            with patch.dict(os.environ, {"IMGTOOLS_STATE_DIR": str(state_root)}):
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
            self.assertEqual(manifest_path.parent, state_root / "manifests")
            self.assertFalse((root / ".imgtools").exists())
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

    def test_manifest_redacts_password_values(self):
        from imgtools.service.manifest import write_manifest

        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"IMGTOOLS_STATE_DIR": tmp}):
                manifest_path = write_manifest(
                    "pdf.render_page",
                    {"pdf_path": "input.pdf", "password": "top-secret"},
                    {"ok": False, "outputs": {}, "warnings": []},
                    "2026-07-20T00:00:00+08:00",
                    "2026-07-20T00:00:01+08:00",
                )

            manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
            self.assertEqual(manifest["params"]["password"], "[REDACTED]")
            self.assertNotIn("top-secret", Path(manifest_path).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
