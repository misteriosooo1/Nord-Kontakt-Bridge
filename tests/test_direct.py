import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from nordbridge.direct_export import build_direct_export
from nordbridge.direct_workflow import prepare, safe_remove_work, valid_cached_project
from nordbridge.core import Stroke, Key


class FakeDecoder:
    def inspect(self, source):
        return ([Stroke(0, 60, 'attack', 0, 500), Stroke(1, 60, 'attack', 1, 500)],
                [Key(60, 60, 0.0), Key(61, 60, -1.5)])

    def decode(self, path, idx, output):
        output.write_bytes(b'RIFF' + bytes(64 + idx))


class TestDirect(unittest.TestCase):
    def test_end_to_end_fake_decoder_and_patch_samples(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'Meu Piano.npno'
            source.write_bytes(b'fake test nord bytes')
            output = root / 'saida'
            cache = root / 'cache'
            p = prepare(source, output, 'Astoria Grand XL', lambda a, b, c: None,
                        decoder=FakeDecoder(), work_root=cache)
            self.assertEqual(p.export.zones, 4)
            self.assertFalse(p.export.nki.exists())
            self.assertTrue(p.export.lua.is_file())
            self.assertFalse(any(output.glob('*.wav')))
            lua = p.export.lua.read_text(encoding='utf-8')
            self.assertIn('mode="patch", absolute_paths=false', lua)
            self.assertNotIn('samples_sub_dir="Samples"', lua)
            self.assertEqual(p.export.samples_dir, output / 'Astoria Grand XL' / 'Samples')
            self.assertEqual(p.export.sample_count, 2)
            self.assertEqual(len(list(p.export.samples_dir.glob("*.wav"))), 2)
            self.assertIn((p.export.samples_dir / "060-b0-l00.wav").as_posix(), lua)
            self.assertNotIn((p.work_dir / "Samples" / "060-b0-l00.wav").as_posix(), lua)
            self.assertIn('WAVS CONFERIDOS:', lua)
            self.assertIn('ZONAS IMPORTADAS', lua)
            self.assertIn('CRIANDO INSTRUMENTO', lua)
            self.assertNotIn('mode="monolith"', lua)
            self.assertEqual(lua.count('sample='), 4)
            second = prepare(source, output, 'Astoria Grand XL', lambda a, b, c: None,
                             decoder=FakeDecoder(), work_root=cache)
            self.assertTrue(second.cached)
            self.assertEqual(p.work_dir, second.work_dir)
            self.assertTrue(valid_cached_project(p.work_dir))
            p.export.nki.write_bytes(b'validated nki placeholder')
            third = build_direct_export(p.work_dir / 'instrument.json', output, 'Astoria Grand XL')
            self.assertNotEqual(third.nki, p.export.nki)
            self.assertEqual(third.nki.parent.name, 'Astoria Grand XL (3)')
            safe_remove_work(p.work_dir, cache)
            self.assertFalse(p.work_dir.exists())

    def test_guards(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(ValueError):
                safe_remove_work(root, root / 'cache')
            source = root / 'wrong.wav'
            source.write_bytes(b'RIFF')
            with self.assertRaises(ValueError):
                prepare(source, root / 'out', 'Piano', lambda *_: None, work_root=root / 'cache')

    def test_title_quotes_escaped(self):
        with TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / 'Samples').mkdir()
            (folder / 'Samples' / '060-b0-l00.wav').write_bytes(b'RIFF' + bytes(60))
            doc = {'schema':1, 'name':'Piano', 'samples':[{'root':60,'bank':'attack','layer':0,
                   'filename':'060-b0-l00.wav','lo_vel':0,'hi_vel':127}],
                   'keys':[{'note':60,'root':60,'cents':0}]}
            (folder / 'instrument.json').write_text(json.dumps(doc))
            out = build_direct_export(folder / 'instrument.json', folder / 'dest', 'Grand "TEST"')
            self.assertNotIn('"TEST"', out.lua.read_text(encoding='utf-8'))
            self.assertIn('Grand _TEST_', out.lua.read_text(encoding='utf-8'))

if __name__ == '__main__':
    unittest.main()
