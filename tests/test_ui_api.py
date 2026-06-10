import json
import unittest
from unittest.mock import patch


class UIAPITests(unittest.TestCase):
    def test_api_tools_returns_registry(self):
        from imgtools.ui.api import handle_get_tools

        result = handle_get_tools()

        self.assertTrue(result["ok"])
        self.assertIn("tools", result)

    def test_api_run_validates_payload(self):
        from imgtools.ui.api import handle_run

        result = handle_run({})

        self.assertFalse(result["ok"])
        self.assertEqual(result["error_code"], "VALIDATION_ERROR")

    def test_api_run_returns_structured_result(self):
        from imgtools.ui.api import handle_run

        fake_result = {"ok": True, "action": "test.action", "outputs": {}, "warnings": []}
        with patch("imgtools.ui.api.run_tool", return_value=fake_result):
            result = handle_run({"action": "test.action", "params": {}})

        self.assertEqual(result, fake_result)
        json.dumps(result)


if __name__ == "__main__":
    unittest.main()

