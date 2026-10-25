"""Regressão da preparação dos dois executáveis Windows."""
import ast
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]

class WindowsBuildTests(unittest.TestCase):
    def test_windows_output_names_and_branding(self):
        import build_windows as b
        self.assertEqual(b.PORTABLE.name, 'Nord Kontakt Bridge Portable.exe')
        self.assertEqual(b.INSTALLER.name, 'Nord Kontakt Bridge Installer.exe')
        self.assertEqual(b.APP_EXE.name, 'Nord Kontakt Bridge.exe')
        self.assertIn('--onefile', b.pyinstaller_command())
        self.assertIn('--windowed', b.pyinstaller_command())
        self.assertIn('--icon', b.pyinstaller_command())
        self.assertIn('NordBridge.ico', ' '.join(b.pyinstaller_command()))
        self.assertIn('assets', ' '.join(b.pyinstaller_command()))

    def test_inno_installer_includes_uninstaller_and_shortcuts(self):
        s = (ROOT / 'Nord Kontakt Bridge Installer.iss').read_text(encoding='utf-8')
        for token in ('AppName=Nord Kontakt Bridge', 'AppVerName=Nord Kontakt Bridge',
                      'OutputBaseFilename=Nord Kontakt Bridge Installer',
                      'PrivilegesRequired=lowest', 'UninstallDisplayName=', '[Icons]',
                      '[Files]', 'Nord Kontakt Bridge.exe', 'BrazilianPortuguese.isl'):
            self.assertIn(token, s)

    def test_scripts_parse(self):
        for name in ['build_windows.py', 'CRIAR_EXE.pyw', 'Nord Kontakt Bridge.pyw']:
            ast.parse((ROOT / name).read_text(encoding='utf-8'))

    def test_workflow_generates_both(self):
        s = (ROOT / '.github/workflows/build-windows.yml').read_text(encoding='utf-8')
        self.assertIn('runs-on: windows-latest', s)
        self.assertIn('build_windows.py ambos', s)
        self.assertIn('Nord Kontakt Bridge Portable.exe', s)
        self.assertIn('Nord Kontakt Bridge Installer.exe', s)

    def test_linux_does_not_pretend_to_create_windows_exe(self):
        import build_windows as b
        with patch.object(b.sys, 'platform', 'linux'):
            with self.assertRaises(b.BuildError):
                b.require_windows()

if __name__ == '__main__':
    unittest.main()
