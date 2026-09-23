import builtins
import contextlib
import io
from pathlib import Path
import runpy
import subprocess
import sys
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / 'technicians_toolkit.py'


class VersionTests(unittest.TestCase):
    def test_version_from_terminal(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), '--version'],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "REGTeches Technician's Toolkit Pro Suite 4.0\n")
        self.assertEqual(result.stderr, '')

    def test_version_needs_no_gui_or_companion_imports(self):
        original_import = builtins.__import__

        def guarded_import(name, *args, **kwargs):
            if name.split('.')[0] in ('tkinter', 'appforge', 'backuppro'):
                raise AssertionError(f'Version query imported {name}')
            return original_import(name, *args, **kwargs)

        for flags in (['--version'], ['--appforge', '--version'],
                      ['--version', '--backuppro']):
            with self.subTest(flags=flags), \
                    patch.object(sys, 'argv', [str(SCRIPT), *flags]), \
                    patch('builtins.__import__', side_effect=guarded_import), \
                    contextlib.redirect_stdout(io.StringIO()) as output:
                with self.assertRaises(SystemExit) as result:
                    runpy.run_path(str(SCRIPT), run_name='__main__')
                self.assertEqual(result.exception.code, 0)
                self.assertEqual(output.getvalue(), "REGTeches Technician's Toolkit Pro Suite 4.0\n")


if __name__ == '__main__':
    unittest.main()
