import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "ImgTools.cmd"


class CmdLauncherTests(unittest.TestCase):
    def test_launcher_runs_the_ui_in_the_cmd_foreground(self):
        script = LAUNCHER.read_text(encoding="utf-8")
        normalized = script.replace("\r\n", "\n").lower()

        self.assertIn('cd /d "%~dp0"', normalized)
        self.assertIn(
            'set "python_exe=%localappdata%\\python\\bin\\python.exe"',
            normalized,
        )
        self.assertIn('"%python_exe%" "%~dp0main.py"', normalized)

        commands = [line.strip() for line in normalized.splitlines()]
        self.assertFalse(
            any(line == "start" or line.startswith("start ") for line in commands),
            "The UI process must stay attached to the CMD window.",
        )


if __name__ == "__main__":
    unittest.main()
