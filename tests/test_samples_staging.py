import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from nordbridge.direct_export import build_direct_export


class StagingTests(unittest.TestCase):
    def test_final_samples_exist_before_kontakt_and_use_relative_saving(self):
        with TemporaryDirectory() as t:
            root=Path(t)
            work=root/'work'
            (work/'Samples').mkdir(parents=True)
            source=work/'Samples'/'piano.wav'
            source.write_bytes(b'RIFF' + bytes(77))
            document={'schema':1,'name':'Piano', 'samples':[{'root':60,'bank':'attack','layer':0,'filename':'piano.wav','lo_vel':1,'hi_vel':127}], 'keys':[{'note':60,'root':60,'cents':0}]}
            manifest=work/'instrument.json'
            manifest.write_text(json.dumps(document))
            result=build_direct_export(manifest, root/'out', 'Meu Piano', auto_fx=False)
            dest=result.samples_dir/'piano.wav'
            self.assertEqual(dest.read_bytes(), source.read_bytes())
            self.assertFalse(result.nki.exists())
            lua=result.lua.read_text()
            self.assertIn('mode="patch", absolute_paths=false', lua)
            self.assertIn(dest.as_posix(), lua)
            self.assertNotIn(source.as_posix(), lua)
            self.assertFalse(list(result.samples_dir.glob('*.nkb-part')))

    def test_missing_source_fails_before_contacting_kontakt(self):
        with TemporaryDirectory() as t:
            root=Path(t)
            work=root/'work'
            (work/'Samples').mkdir(parents=True)
            source=work/'Samples'/'piano.wav'
            source.write_bytes(b'RIFF' + bytes(77))
            manifest=work/'instrument.json'
            manifest.write_text(json.dumps({'schema':1,'name':'Piano','samples':[{'root':60,'bank':'attack','layer':0,'filename':'piano.wav','lo_vel':1,'hi_vel':127}], 'keys':[{'note':60,'root':60,'cents':0}]}))
            source.unlink()
            with self.assertRaises(FileNotFoundError):
                build_direct_export(manifest, root/'out', 'Meu Piano', auto_fx=False)

if __name__=='__main__': unittest.main()
