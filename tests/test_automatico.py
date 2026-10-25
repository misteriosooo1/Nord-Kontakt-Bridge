import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from nordbridge.kontakt_auto import read_status, start_kontakt

class TestAutomatico(unittest.TestCase):
    def test_kontakt_status_pending_and_errors(self):
        with TemporaryDirectory() as temp:
            folder = Path(temp)
            log = folder / 'LOG.txt'
            nki = folder / 'Piano.nki'
            self.assertEqual(read_status(log, nki).state, 'waiting')
            log.write_text('2026-10-23 [Direto] LUA INICIADO no Kontakt\n', encoding='utf8')
            self.assertEqual(read_status(log, nki).state, 'running')
            log.write_text('2026-10-23 [Direto] ERRO: path doesn\'t exist\n', encoding='utf8')
            self.assertEqual(read_status(log, nki).state, 'error')
            log.write_text('2026-10-23 [Direto] SUCESSO MONOLITH: Piano.nki\n', encoding='utf8')
            self.assertEqual(read_status(log, nki).state, 'error')
            nki.write_bytes(b'x'*5000)
            self.assertEqual(read_status(log, nki).state, 'success')

    def test_nki_created_with_resource_warning(self):
        with TemporaryDirectory() as temp:
            folder = Path(temp)
            nki = folder / 'Piano.nki'
            log = folder / 'LOG.txt'
            nki.write_bytes(b'x' * 5000)
            log.write_text('2026 [Direto] AVISO NKR: nao criado\n'
                           '2026 [Direto] SUCESSO MONOLITH COM AVISO DE RECURSOS: Piano.nki (5000 bytes)\n', encoding='utf8')
            result = read_status(log, nki)
            self.assertEqual(result.state, 'success')
            self.assertIn('NKR', result.description)

    def test_missing_nkr_never_reports_success(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            log, nki, nkr = root/'log.txt', root/'Astoria.nki', root/'Astoria_Resources.nkr'
            nki.write_bytes(b'N' * 5000)
            log.write_text('2026 [Direto] SUCESSO MONOLITH: Astoria.nki\n', encoding='utf-8')
            self.assertEqual(read_status(log, nki, nkr).state, 'error')
            nkr.write_bytes(b'NKRDATA')
            self.assertEqual(read_status(log, nki, nkr).state, 'success')

    def test_fallback_nki_is_partial_not_full_success(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            nki, nkr, log = root/'A.nki', root/'A_Resources.nkr', root/'log.txt'
            nki.write_bytes(b'N' * 6000)
            log.write_text('2026 [Direto] SUCESSO MONOLITH SEM NKR: A.nki (6000 bytes)\n')
            st = read_status(log, nki, nkr)
            self.assertEqual(st.state, 'partial')
            self.assertIn('SEM wallpaper', st.description)

    def test_executable_guard(self):
        with TemporaryDirectory() as temp:
            folder = Path(temp)
            bad_exe = folder / 'Kontakt 8.exe'
            lua = folder / 'program.lua'
            with self.assertRaises(FileNotFoundError):
                start_kontakt(bad_exe, lua)
            bad_exe.write_text('not a real executable')
            with self.assertRaises(FileNotFoundError):
                start_kontakt(bad_exe, lua)

if __name__ == '__main__':
    unittest.main()
