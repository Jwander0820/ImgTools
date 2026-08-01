import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ArchitectureTests(unittest.TestCase):
    def test_legacy_source_tree_is_absent(self):
        self.assertFalse((ROOT / "legacy").exists())

    def test_runtime_code_does_not_import_legacy_modules(self):
        for path in (ROOT / "imgtools").rglob("*.py"):
            with self.subTest(path=path.relative_to(ROOT)):
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
                imported = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        imported.extend(alias.name for alias in node.names)
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        imported.append(node.module)
                self.assertFalse(
                    any(name == "legacy" or name.startswith("legacy.") for name in imported),
                    imported,
                )


if __name__ == "__main__":
    unittest.main()
