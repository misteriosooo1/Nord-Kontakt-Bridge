"""Validação da integração: nenhuma chamada ao Kontakt real é simulada como sucesso."""
import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from nordbridge.default_fx import build_default_fx_ksp
from nordbridge.direct_export import build_direct_export
from nordbridge.visual_assets import create_visual_pack


def project(root):
    (root / 'Samples').mkdir()
    (root / 'Samples' / 'piano.wav').write_bytes(b'RIFF' + bytes(60))
    (root / 'instrument.json').write_text(json.dumps({
        'schema': 1, 'name': 'Piano',
        'samples': [{'root':60, 'bank':'attack', 'layer':0,'filename':'piano.wav', 'lo_vel':0,'hi_vel':127}],
        'keys':[{'note':60,'root':60,'cents':0}]
    }))


class FXTests(unittest.TestCase):
    def test_default_fx_has_all_eight_controls_and_bypass(self):
        ksp = build_default_fx_ksp('Piano Grand')
        for control in ('Reverb','Delay','Chorus','Brilho','Volume','Dinamica','Tune','Pan'):
            self.assertIn(f'ui_knob ${control}', ksp)
        self.assertIn('set_text($Redefinir,"REDEFINIR")',ksp)
        self.assertIn('$Volume := $OriginalVolume',ksp)
        self.assertIn('on persistence_changed',ksp)
        self.assertNotIn('wait_async(', ksp)
        self.assertEqual(ksp.count('set_engine_par($ENGINE_PAR_EFFECT_BYPASS,1,-1,'), 8)
        self.assertNotIn('call aplicar_reverb\nend on\nfunction',ksp)

    def test_lua_installs_fx_by_default(self):
        with TemporaryDirectory() as t:
            root = Path(t)
            project(root)
            exp = build_direct_export(root / 'instrument.json', root / 'nki', 'Piano')
            ksp = exp.source_ksp.read_text()
            self.assertIn('NORD BRIDGE | FX',ksp)
            self.assertIn('ui_button $Redefinir',ksp)
            self.assertIn('ENGINE_PAR_EFFECT_TYPE',ksp)
            script = exp.lua.read_text()
            self.assertIn('instalar_ksp(0, ksp_path,',script)
            self.assertIn('set_instrument_script_source, inst, slot, arquivo', script)
            self.assertIn('get_instrument_script_source, inst, slot',script)
            self.assertIn('K.set_instrument_script_name(inst, slot, titulo)', script)
            self.assertIn('mode="patch", absolute_paths=false', script)
            self.assertFalse(exp.nki.exists())

    def test_can_disable_fx(self):
        with TemporaryDirectory() as t:
            root = Path(t)
            project(root)
            exp = build_direct_export(root / 'instrument.json', root / 'nki', 'Piano', auto_fx=False)
            self.assertNotIn('ui_knob $Reverb', exp.source_ksp.read_text())
            self.assertIn('PERFORMANCE', exp.source_ksp.read_text())

    def test_custom_ksp_goes_into_second_slot(self):
        with TemporaryDirectory() as t:
            root = Path(t)
            project(root)
            custom = root / 'outro.ksp'
            custom.write_text('on init\n message("")\nend on\n')
            exp = build_direct_export(root / 'instrument.json', root / 'nki', 'Piano', ksp_source=custom)
            self.assertIn('ui_knob $Reverb',exp.source_ksp.read_text())
            script = exp.lua.read_text()
            self.assertIn('instalar_ksp(1, ',script)
            self.assertIn('INSTALANDO KSP PERSONALIZADO NO SLOT 2',script)

    def test_visual_pack_default_fx_has_full_height(self):
        from PIL import Image
        with TemporaryDirectory() as t:
            pack = create_visual_pack(Path(t),'Piano', use_defaults=True, fx_panel=True)
            with Image.open(pack.pictures / (pack.wallpaper_name+'.png')) as image:
                self.assertEqual(image.size,(633,620))
                self.assertNotEqual(image.getpixel((50,100)), image.getpixel((50,400)))

if __name__ == '__main__':
    unittest.main()
