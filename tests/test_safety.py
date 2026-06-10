import tempfile
import unittest
from pathlib import Path


class SafetyTests(unittest.TestCase):
    def test_reject_existing_output_without_overwrite(self):
        from imgtools.service.safety import ensure_output_allowed

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "out.txt"
            output.write_text("exists", encoding="utf-8")

            with self.assertRaises(FileExistsError):
                ensure_output_allowed(output, overwrite=False)

    def test_allow_existing_output_with_overwrite(self):
        from imgtools.service.safety import ensure_output_allowed

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "out.txt"
            output.write_text("exists", encoding="utf-8")

            self.assertIsNone(ensure_output_allowed(output, overwrite=True))

    def test_high_risk_tool_requires_dry_run_by_default(self):
        from imgtools.service.registry import get_tool
        from imgtools.service.safety import default_params_for_safety

        spec = get_tool("rename.files_replace")
        params = default_params_for_safety(spec, {})

        self.assertFalse(params["confirm"])


if __name__ == "__main__":
    unittest.main()

