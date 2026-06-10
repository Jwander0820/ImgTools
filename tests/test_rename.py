import tempfile
import unittest
from pathlib import Path


class RenameTests(unittest.TestCase):
    def test_rename_files_dry_run_does_not_modify_files(self):
        from imgtools.core.rename import files_replace

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            original = root / "old-name.txt"
            original.write_text("x", encoding="utf-8")

            result = files_replace(
                {
                    "target_folder": str(root),
                    "target": "old",
                    "replacement": "new",
                    "confirm": False,
                }
            )

            self.assertTrue(result["ok"])
            self.assertTrue(original.exists())
            self.assertFalse((root / "new-name.txt").exists())
            self.assertTrue(result["outputs"]["dry_run"])
            self.assertEqual(result["outputs"]["count"], 1)

    def test_rename_folders_dry_run_does_not_modify_folders(self):
        from imgtools.core.rename import folders_replace

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            original = root / "old-folder"
            original.mkdir()

            result = folders_replace(
                {
                    "target_folder": str(root),
                    "target": "old",
                    "replacement": "new",
                    "confirm": False,
                }
            )

            self.assertTrue(result["ok"])
            self.assertTrue(original.exists())
            self.assertFalse((root / "new-folder").exists())
            self.assertTrue(result["outputs"]["dry_run"])

    def test_rename_conflict_blocks_all_changes(self):
        from imgtools.core.rename import files_replace

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "old-name.txt").write_text("x", encoding="utf-8")
            (root / "new-name.txt").write_text("y", encoding="utf-8")

            result = files_replace(
                {
                    "target_folder": str(root),
                    "target": "old",
                    "replacement": "new",
                    "confirm": True,
                }
            )

            self.assertFalse(result["ok"])
            self.assertTrue((root / "old-name.txt").exists())
            self.assertTrue((root / "new-name.txt").exists())
            self.assertEqual(len(result["outputs"]["conflicts"]), 1)

    def test_rename_confirm_applies_expected_changes(self):
        from imgtools.core.rename import files_replace

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "old-name.txt").write_text("x", encoding="utf-8")

            result = files_replace(
                {
                    "target_folder": str(root),
                    "target": "old",
                    "replacement": "new",
                    "confirm": True,
                }
            )

            self.assertTrue(result["ok"])
            self.assertFalse((root / "old-name.txt").exists())
            self.assertTrue((root / "new-name.txt").exists())
            self.assertTrue(result["outputs"]["changed"])


if __name__ == "__main__":
    unittest.main()

