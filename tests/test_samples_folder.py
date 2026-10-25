import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from nordbridge.kontakt_auto import read_status

class SamplesFolderTests(unittest.TestCase):
    def test_missing_wavs_is_not_success(self):
        with TemporaryDirectory() as t:
            root=Path(t)
            nki=root/'Piano'/'Piano.nki'
            nki.parent.mkdir()
            nki.write_bytes(b'x' * 2048)
            log=root/'log.txt'
            log.write_text('2026 [Direto] SUCESSO NKI SAMPLES: '+str(nki)+' (3 wavs)\n')
            self.assertEqual(read_status(log,nki).state,'error')
            folder=nki.parent/'Samples'
            folder.mkdir()
            (folder/'1.wav').write_bytes(b'RIFF'+bytes(128))
            self.assertEqual(read_status(log,nki).state,'success')
    def test_missing_nkr_reports_partial(self):
        with TemporaryDirectory() as t:
            root=Path(t)
            nki=root/'Piano'/'Piano.nki'
            nki.parent.mkdir()
            nki.write_bytes(b'x' * 2048)
            folder=nki.parent/'Samples'
            folder.mkdir()
            (folder/'1.wav').write_bytes(b'RIFF'+bytes(128))
            log=root/'log.txt'
            log.write_text('2026 [Direto] SUCESSO NKI SAMPLES SEM NKR: '+str(nki)+' (1 wavs)\n')
            self.assertEqual(read_status(log,nki).state,'partial')

if __name__ == '__main__': unittest.main()
