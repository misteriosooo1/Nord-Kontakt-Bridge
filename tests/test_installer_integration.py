"""Testes do instalador e da resolução do decoder empacotado."""
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]

class InstallerIntegrationTests(unittest.TestCase):
    def test_decoder_exists_and_is_windows_binary(self):
        nord = ROOT / 'bin' / 'nord.exe'
        self.assertTrue(nord.is_file())
        self.assertEqual(nord.read_bytes()[:2], b'MZ')

    def test_build_embeds_decoder_in_bin(self):
        import build_windows as b
        command = b.pyinstaller_command()
        idx = command.index('--add-binary')
        self.assertEqual(command[idx + 1].split(';')[-1] if sys.platform == 'win32' else command[idx + 1].split(':')[-1], 'bin')
        self.assertIn('nord.exe', command[idx + 1])

    def test_decoder_resolution_uses_installed_bin(self):
        from nordbridge.core import find_nord_exe
        with TemporaryDirectory() as td:
            root = Path(td)
            exedir = root / 'installed'
            (exedir / 'bin').mkdir(parents=True)
            decoder = exedir / 'bin' / 'nord.exe'
            decoder.write_bytes(b'MZ')
            with patch.object(sys, 'executable', str(exedir / 'Nord Kontakt Bridge.exe')):
                with patch.object(sys, '_MEIPASS', root / 'anybundle', create=True):
                    self.assertEqual(find_nord_exe(), decoder)

    def test_decoder_resolution_uses_onefile_bundle(self):
        from nordbridge.core import find_nord_exe
        with TemporaryDirectory() as td:
            root = Path(td)
            bundled = root / 'bundle'
            (bundled / 'bin').mkdir(parents=True)
            decoder = bundled / 'bin' / 'nord.exe'
            decoder.write_bytes(b'MZ')
            with patch.object(sys, 'executable', str(root / 'portable' / 'Nord Kontakt Bridge Portable.exe')):
                with patch.object(sys, '_MEIPASS', str(bundled), create=True):
                    self.assertEqual(find_nord_exe(), decoder)

    def test_inno_installs_decoder_in_bin_and_creates_shortcuts(self):
        data = (ROOT / 'SUPORTE_RECUPERACAO' / 'FERRAMENTAS_COMPILACAO' / 'Nord Kontakt Bridge Installer.iss').read_text('utf-8')
        for term in ('bin\\nord.exe', '{app}\\bin', '[Icons]', '[Run]', '[Files]', 'PrivilegesRequired=lowest'):
            self.assertIn(term, data)

if __name__ == '__main__':
    unittest.main()
