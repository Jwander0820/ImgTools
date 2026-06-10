import unittest
from unittest.mock import patch


class RegistryTests(unittest.TestCase):
    def test_list_tools_returns_known_actions(self):
        from imgtools.service.registry import list_tools

        actions = {tool["action"] for tool in list_tools()}

        self.assertIn("metadata.read_tif_tags", actions)
        self.assertIn("rename.files_replace", actions)
        self.assertIn("rename.folders_replace", actions)
        self.assertIn("pdf.render_page", actions)
        self.assertIn("merge.images_to_pdf", actions)

    def test_get_tool_unknown_action_raises_error(self):
        from imgtools.service.registry import get_tool

        with self.assertRaises(KeyError):
            get_tool("missing.action")

    def test_every_tool_has_required_metadata(self):
        from imgtools.service.registry import list_tools

        for tool in list_tools():
            with self.subTest(action=tool.get("action")):
                self.assertTrue(tool.get("action"))
                self.assertTrue(tool.get("title"))
                self.assertTrue(tool.get("category"))
                self.assertIsInstance(tool.get("params"), list)
                self.assertIn(tool.get("danger_level"), {"low", "medium", "high"})

    def test_metadata_pil_reader_does_not_import_optional_readers(self):
        import builtins

        from imgtools.core.metadata import read_tif_tags

        original_import = builtins.__import__

        def guarded_import(name, *args, **kwargs):
            if name in {"tifftools", "exifread"}:
                raise ModuleNotFoundError(name)
            return original_import(name, *args, **kwargs)

        with self.assertRaises(FileNotFoundError):
            with patch("builtins.__import__", side_effect=guarded_import):
                read_tif_tags({"input_path": "missing.tif", "method": "pil"})


if __name__ == "__main__":
    unittest.main()
