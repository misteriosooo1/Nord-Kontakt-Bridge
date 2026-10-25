import json
import unittest
from pathlib import Path
from unittest.mock import patch
from tempfile import TemporaryDirectory
from nordbridge.nkr_templates import find_local_template, valid_template
from nordbridge.direct_export import build_direct_export


class ReuseNKR(unittest.TestCase):
    def test_explicit_template_copied_and_linked(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'Samples').mkdir()
            (root/'Samples'/'a.wav').write_bytes(b'RIFF'+bytes(80))
            (root/'instrument.json').write_text(json.dumps({
                'schema':1,'name':'Piano',
                'samples':[{'root':60,'bank':'attack','layer':0,'filename':'a.wav','lo_vel':1,'hi_vel':127}],
                'keys':[{'note':60,'root':60,'cents':0}]}),encoding='utf-8')
            original=root/'Astoria_Resources.nkr'
            original.write_bytes(b'NKR-FROM-KONTAKT' + bytes(256))
            result=build_direct_export(root/'instrument.json',root/'saida','Piano',
                                       use_default_visuals=True,nkr_template=original)
            self.assertEqual(result.artwork.nkr.read_bytes(),original.read_bytes())
            self.assertIn('if nkr_exists() then',result.lua.read_text(encoding='utf-8'))
            self.assertEqual(original.read_bytes()[:3],b'NKR')

    def test_invalid_template_is_rejected(self):
        with TemporaryDirectory() as tmp:
            p=Path(tmp)/'falso.nkr'
            p.touch()
            self.assertFalse(valid_template(p))
            with self.assertRaises(ValueError): find_local_template(Path(tmp),p)

    def test_auto_discovers_own_nkr_in_documents(self):
        with TemporaryDirectory() as tmp:
            home = Path(tmp)
            own = home/'Documents'/'NordKontaktBridge'/'Astoria'/'Astoria_Resources.nkr'
            own.parent.mkdir(parents=True)
            own.write_bytes(b'CREATED-BY-KONTAKT' + bytes(2048))
            dest=home/'Documents'/'teste'
            dest.mkdir()
            with patch.dict('os.environ', {'USERPROFILE': str(home)}):
                self.assertEqual(find_local_template(dest), own)

    def test_no_template_does_not_fake_nkr(self):
        with TemporaryDirectory() as tmp:
            d=Path(tmp)/'vazio';d.mkdir()
            self.assertIsNone(find_local_template(d))

if __name__ == '__main__': unittest.main()
