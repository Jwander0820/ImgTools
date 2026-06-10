import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch


class CLITests(unittest.TestCase):
    def test_cli_list_prints_tools(self):
        from imgtools.cli import main

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            main(["list"])

        self.assertIn("metadata.read_tif_tags", stdout.getvalue())

    def test_cli_ui_delegates_to_server(self):
        from imgtools.cli import main

        with patch("imgtools.ui.server.serve") as serve:
            main(["ui", "--host", "127.0.0.1", "--port", "9000", "--no-browser"])

        serve.assert_called_once_with("127.0.0.1", 9000, open_browser=False)


if __name__ == "__main__":
    unittest.main()

