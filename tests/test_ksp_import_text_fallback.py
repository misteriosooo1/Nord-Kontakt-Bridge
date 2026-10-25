import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from nordbridge.direct_export import build_direct_export

class KSPSourceFallbackTests(unittest.TestCase):
    def test_lua_tries_filepath_then_full_source(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'Samples').mkdir()
            (root / 'Samples' / 'piano.wav').write_bytes(b'RIFF'+bytes(100))
            (root / 'instrument.json').write_text(json.dumps({
                'schema':1, 'name':'Nord',
                'samples':[{'root':60,'bank':'attack','layer':0,'filename':'piano.wav','lo_vel':0,'hi_vel':127}],
                'keys':[{'note':60,'root':60,'cents':0}]
            }), encoding='utf8')
            exp=build_direct_export(root/'instrument.json', root/'out', 'Nord Piano', auto_fx=True)
            lua=exp.lua.read_text(encoding='utf8')
            self.assertIn('K.set_instrument_script_source, inst, slot, arquivo',lua)
            self.assertIn('K.set_instrument_script_source, inst, slot, codigo',lua)
            self.assertIn('KSP RETORNO API [',lua)
            self.assertIn('KSP CAMINHO NAO IMPORTOU O CODIGO',lua)
            self.assertIn('if not confirmado then',lua)
            self.assertLess(lua.index('slot, arquivo'), lua.index('slot, codigo'))
            self.assertLess(lua.index('CODIGO KSP NAO INSTALADO'),lua.index('SALVANDO NKI + SAMPLES'))
            self.assertIn('on init',exp.source_ksp.read_text())

if __name__ == '__main__': unittest.main()
