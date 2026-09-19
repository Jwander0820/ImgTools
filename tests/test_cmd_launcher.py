import unittest
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "ImgTools.cmd"


class CmdLauncherTests(unittest.TestCase):
    @unittest.skipUnless(os.name == 'nt', 'Windows launcher')
    def test_launcher_prefers_project_venv_and_falls_back_to_global(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            launcher = root / 'ImgTools.cmd'
            shutil.copyfile(LAUNCHER, launcher)
            local = root / '.venv' / 'Scripts' / 'python.exe'
            fallback = root / 'LocalAppData' / 'Python' / 'bin' / 'python.exe'
            local.parent.mkdir(parents=True)
            fallback.parent.mkdir(parents=True)
            local.touch()
            fallback.touch()
            env = {**os.environ, 'LOCALAPPDATA': str(root / 'LocalAppData')}
            def check():
                return subprocess.run(['cmd', '/d', '/c', str(launcher), '--check'],
                                      capture_output=True, text=True, env=env, timeout=5)
            first = check()
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertIn(str(local), first.stdout)
            local.unlink()
            second = check()
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertIn(str(fallback), second.stdout)

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
