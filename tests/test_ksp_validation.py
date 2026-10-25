import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from nordbridge.default_fx import build_default_fx_ksp
from nordbridge.fx_designer import FXDesign, design_ksp, validate_fx_design
from nordbridge.ksp_validation import check_ksp, require_valid_ksp
from nordbridge.direct_export import build_direct_export
import json

class KSPValidation(unittest.TestCase):
    def test_slider_set_text_is_rejected(self):
        source='on init\n declare ui_slider $Pan (-100,100)\n set_text($Pan,"")\nend on'
        issues=check_ksp(source)
        self.assertTrue(any('set_text($Pan' in i and 'ui_slider' in i for i in issues))
        with self.assertRaisesRegex(ValueError,'Pan'):
            require_valid_ksp(source)

    def test_missing_ui_declaration_and_duplicate_callback(self):
        source=('on init\n declare ui_slider $Pan (-100,100)\n'
                ' set_control_par(get_ui_id($Inexistente),$CONTROL_PAR_WIDTH,76)\nend on\n'
                'on ui_control ($Pan)\nend on\non ui_control ($Pan)\nend on')
        msg='\n'.join(check_ksp(source))
        self.assertIn('Inexistente',msg)
        self.assertIn('repetido',msg)

    def test_configs_with_arbitrary_labels_are_in_the_ksp(self):
        with TemporaryDirectory() as d:
            root=Path(d)
            (root/'Samples').mkdir()
            (root/'Samples'/'x.wav').write_bytes(b'RIFF'+bytes(60))
            manifest=root/'instrument.json'
            manifest.write_text(json.dumps({'schema':1,'name':'Piano','samples':[{'root':60,'bank':'attack','layer':0,'filename':'x.wav','lo_vel':0,'hi_vel':127}], 'keys':[{'note':60,'root':60,'cents':0}]}))
            for i,(layout,font) in enumerate([('3 colunas','Segoe UI'),('4 colunas','Georgia')]):
                config=FXDesign(layout=layout,font_family=font,labels=('ECO \" / OLA', 'REVERB 1', 'MOD / CHORUS', 'BRILHO', 'GANHO', 'TOQUE', 'AFINAÇÃO', 'BALANÇO'))
                out=build_direct_export(manifest,root/('saida'+str(i)),'Meu Piano',auto_fx=True,fx_design=config,use_default_visuals=True)
                source=out.source_ksp.read_text(encoding='utf-8')
                require_valid_ksp(source)
                for variable in ('Reverb','Delay','Chorus','Brilho','Volume','Dinamica','Tune','Pan'):
                    self.assertIn('declare ui_slider $'+variable,source)
                    self.assertNotIn('set_text($'+variable+',',source)
                    self.assertIn('$CONTROL_PAR_LABEL,"'+variable.upper()+'"',source)
                self.assertIn('on ui_control ($AbaFX)',source)
                self.assertIn('declare ui_label $TituloFX',source)
                for variable,label in zip(('Reverb','Delay','Chorus','Brilho','Volume','Dinamica','Tune','Pan'),config.labels):
                    self.assertIn('declare ui_label $Nome'+variable,source)
                    self.assertIn('set_text($Nome'+variable+',"'+label.replace('\"',"'")+'")',source)
                self.assertTrue((out.nki.parent/'PREVIA_FX.png').is_file())

    def test_wrong_color_or_layout_fails_before_kontakt(self):
        for config in (FXDesign(accent='not-color'),FXDesign(layout='7 colunas'),FXDesign(labels=('Only One',))):
            with self.assertRaises(ValueError):validate_fx_design(config)

    def test_standard_ksp_passes(self):
        require_valid_ksp(build_default_fx_ksp('Piano'))

if __name__=='__main__':unittest.main()
