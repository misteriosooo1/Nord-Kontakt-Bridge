"""Testes da pasta de recuperacao opcional, sem invocar o binario Windows em Linux."""
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, Mock

from nordbridge.core import find_nord_exe, find_nord_support_exe, NordCli
from nordbridge.visual_assets import installed_assets_dir

class SuporteRecuperacaoTests(unittest.TestCase):
    def test_fallback_decoder_when_primary_missing(self):
        with TemporaryDirectory() as td:
            base = Path(td)
            reserve = base / 'SUPORTE_RECUPERACAO' / 'bin' / 'nord.exe'
            reserve.parent.mkdir(parents=True)
            reserve.write_bytes(b'MZ')
            with patch.object(sys, 'executable', str(base / 'Nord Kontakt Bridge.exe')):
                with patch.object(sys, '_MEIPASS', str(base / 'bundle'), create=True):
                    with patch('nordbridge.core.__file__', str(base / 'src' / 'nordbridge' / 'core.py')):
                        self.assertEqual(find_nord_support_exe(), reserve)
                        self.assertEqual(find_nord_exe(), reserve)

    def test_primary_decoder_prioritized(self):
        with TemporaryDirectory() as td:
            base = Path(td)
            (base/'bin').mkdir()
            primary = base/'bin'/'nord.exe'
            primary.write_bytes(b'MZ')
            reserve = base/'SUPORTE_RECUPERACAO'/'bin'/'nord.exe'
            reserve.parent.mkdir(parents=True)
            reserve.write_bytes(b'MZ')
            with patch.object(sys, 'executable', str(base / 'Nord Kontakt Bridge.exe')):
                with patch.object(sys, '_MEIPASS', str(base / 'bundle'), create=True):
                    self.assertEqual(find_nord_exe(), primary)

    def test_visual_assets_uses_backup_if_bundle_incomplete(self):
        with TemporaryDirectory() as td:
            base=Path(td)
            support=base/'SUPORTE_RECUPERACAO'/'assets'
            support.mkdir(parents=True)
            for name in ('hero_red.png','default_icon.png','default_wallpaper.png'):
                (support/name).write_bytes(b'png')
            with patch.object(sys, 'executable', str(base/'Nord Kontakt Bridge.exe')):
                with patch.object(sys, '_MEIPASS', str(base/'bundle'), create=True):
                    with patch('nordbridge.visual_assets.__file__', str(base / 'src' / 'nordbridge' / 'visual_assets.py')):
                        self.assertEqual(installed_assets_dir(), support)

    def test_decoder_runs_backup_if_primary_cannot_start(self):
        with TemporaryDirectory() as td:
            base = Path(td)
            primary = base/'bin'/'nord.exe'
            primary.parent.mkdir(parents=True)
            primary.write_bytes(b'MZ')
            backup = base/'SUPORTE_RECUPERACAO'/'bin'/'nord.exe'
            backup.parent.mkdir(parents=True)
            backup.write_bytes(b'MZ')
            success = Mock(returncode=0, stdout='nord 1.0', stderr='')
            with patch.object(sys, 'executable', str(base/'Nord Kontakt Bridge.exe')):
                with patch('nordbridge.core.subprocess.run', side_effect=[OSError('broken'), success]) as run:
                    cli = NordCli(executable=primary)
                    self.assertEqual(cli.run('--version'), 'nord 1.0')
                    self.assertEqual(Path(run.call_args.args[0][0]), backup)

    def test_decoder_does_not_mask_nord_cli_input_errors(self):
        with TemporaryDirectory() as td:
            base = Path(td)
            primary = base/'nord.exe'
            primary.write_bytes(b'MZ')
            failure = Mock(returncode=2, stdout='', stderr='invalid input')
            with patch('nordbridge.core.subprocess.run', return_value=failure) as run:
                with self.assertRaisesRegex(RuntimeError, 'invalid input'):
                    NordCli(executable=primary).run('piano', 'decode')
                self.assertEqual(run.call_count, 1)

    def test_inno_installs_support_folder(self):
        script = (Path(__file__).resolve().parents[1]/'SUPORTE_RECUPERACAO'/'FERRAMENTAS_COMPILACAO'/'Nord Kontakt Bridge Installer.iss').read_text('utf-8')
        self.assertIn('SUPORTE_RECUPERACAO',script)
        self.assertIn('recursesubdirs',script)

if __name__ == '__main__': unittest.main()
