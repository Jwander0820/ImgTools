import unittest
from unittest.mock import patch


class MainEntryTests(unittest.TestCase):
    def test_main_entry_starts_local_ui_and_opens_browser(self):
        import main

        with patch("main.serve") as serve:
            main.main()

        serve.assert_called_once_with("127.0.0.1", 8765, open_browser=True)


if __name__ == "__main__":
    unittest.main()
