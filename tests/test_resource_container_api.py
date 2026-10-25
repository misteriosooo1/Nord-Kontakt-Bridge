import json
import re
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from nordbridge.direct_export import build_direct_export

class ResourceContainerAPITests(unittest.TestCase):
    def test_generated_lua_uses_two_documented_parameters(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'Samples').mkdir()
            (root/'Samples'/'a.wav').write_bytes(b'RIFF'+bytes(80))
            (root/'instrument.json').write_text(json.dumps({
                'schema':1, 'name':'Astoria Grand',
                'samples':[{'root':60,'bank':'attack','layer':0,'filename':'a.wav','lo_vel':1,'hi_vel':127}],
                'keys':[{'note':60,'root':60,'cents':0}]
            }))
            result=build_direct_export(root/'instrument.json',root/'dest','Astoria Grand',use_default_visuals=True)
            lua=result.lua.read_text(encoding='utf-8')
            self.assertRegex(lua, r'local nkr_path = "[^"\n]+\.nkr"')
            self.assertIn('if nkr_exists() then', lua)
            self.assertIn('RECRIANDO INSTRUMENTO LIMPO:', lua)
            self.assertLess(lua.index('SALVANDO PATCH TEMPORARIO'), lua.index('NKR AUSENTE: solicitando criacao'))
            self.assertGreater(lua.index('RECRIANDO INSTRUMENTO LIMPO:'), lua.index('ZONAS:'))
            self.assertNotIn('SUCESSO MONOLITH COM AVISO DE RECURSOS:', lua)
            self.assertIn('pcall(K.create_resource_container, inst, nkr_path)', lua)
            self.assertIn('pcall(K.link_resource_container, inst, nkr_path)', lua)
            self.assertLess(lua.index('local inst = K.add_instrument()'),lua.index('pcall(K.create_resource_container, inst, nkr_path)'))
            self.assertLess(lua.index('K.save_instrument(inst, setup_path'),lua.index('pcall(K.create_resource_container, inst, nkr_path)'))
            self.assertLess(lua.index('pcall(K.create_resource_container, inst, nkr_path)'),lua.index('pcall(K.save_instrument, inst, nki_path'))
            self.assertIn('GRAVACAO NA PASTA: OK',lua)

if __name__=='__main__':
    unittest.main()
