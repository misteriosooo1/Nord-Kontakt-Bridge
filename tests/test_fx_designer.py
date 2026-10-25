import sys, json, unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from nordbridge.direct_export import build_direct_export
from nordbridge.fx_designer import FXDesign,make_knob_sheet,design_ksp,make_pages,effect_positions

class DesignerTests(unittest.TestCase):
    def create_project(self,root):
        manifest=root/'instrument.json'
        (root/'Samples').mkdir()
        (root/'Samples'/'x.wav').write_bytes(b'RIFF'+bytes(60))
        manifest.write_text(json.dumps({'schema':1,'name':'Piano','samples':[{'root':60,'bank':'attack','layer':0,'filename':'x.wav','lo_vel':0,'hi_vel':127}], 'keys':[{'note':60,'root':60,'cents':0}]}))
        return manifest
    def test_png_and_two_pages_with_fx_styles(self):
        with TemporaryDirectory() as d:
            p=Path(d); f=p/'photo.png'; Image.new('RGBA',(230,300),(204,100,40,255)).save(f)
            c=FXDesign(title='MEUS EFEITOS',font_family='Georgia',accent='#D5AE7D',knob_style='Dourado')
            frame=make_pages(f,c)
            self.assertEqual(frame.size,(633,1410))
            self.assertEqual(frame.getpixel((1,1)),(204,100,40,255))
            self.assertNotEqual(frame.getpixel((1,710)),(204,100,40,255))
            self.assertEqual(make_knob_sheet(c).size,(76,7676))
    def test_output_contains_editor_data_and_dynamic_ksp(self):
        with TemporaryDirectory() as d:
            root=Path(d); m=self.create_project(root)
            conf=FXDesign(title='PAD FX',labels=('SPACE','ECHO','MOD','EQ','GAIN','TOUCH','TUNE','BAL'),layout='4 colunas',knob_style='Dourado')
            result=build_direct_export(m,root/'out','Piano',auto_fx=True,fx_design=conf,use_default_visuals=True)
            target=result.nki.parent
            self.assertEqual(json.loads((target/'DESIGN_FX.json').read_text())['title'],'PAD FX')
            with Image.open(result.artwork.pictures/(result.artwork.wallpaper_name+'.png')) as pic:self.assertEqual(pic.size,(633,1410))
            with Image.open(result.artwork.pictures/(result.artwork.wallpaper_name+'_KNOB.png')) as pic:self.assertEqual(pic.size,(76,7676))
            ksp=result.source_ksp.read_text()
            self.assertIn('set_skin_offset(705)',ksp)
            self.assertIn('declare ui_label $TituloFX',ksp)
            self.assertIn('declare ui_label $NomeReverb',ksp)
            self.assertIn('get_ui_id($NomeReverb)',ksp)
            self.assertIn('function mostrar_pagina',ksp)
            self.assertIn('on ui_control ($AbaFX)',ksp)
            self.assertIn('declare ui_slider $Reverb',ksp)
            self.assertIn('declare ui_slider $Brilho',ksp)
            self.assertIn('set_control_par_str($INST_WALLPAPER_ID',ksp)
            self.assertIn('$CONTROL_PAR_MOUSE_BEHAVIOUR,-500',ksp)
            self.assertIn('on ui_control ($Redefinir)',ksp)
            self.assertIn('set_text($ValorReverb,$Reverb)',ksp)
            self.assertNotIn('call mostrar_pagina\nend on\n\nfunction',ksp)
            self.assertTrue((target/'PREVIA_FX.png').exists())
            self.assertIn('declare ui_knob $Reverb',(target/'PAINEL_SEM_NKR_Piano.ksp').read_text())
    def test_design_off_does_not_modify_existing_generator(self):
        with TemporaryDirectory() as d:
            root=Path(d); m=self.create_project(root)
            result=build_direct_export(m,root/'out','Piano',auto_fx=True,fx_design=FXDesign(enabled=False),use_default_visuals=True)
            self.assertNotIn('set_skin_offset(705)',result.source_ksp.read_text())
if __name__=='__main__':unittest.main()
