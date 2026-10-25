import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from nordbridge.visual_assets import create_visual_pack, make_button_sheet, make_library_manager_pack
from nordbridge.direct_export import build_direct_export

class ButtonAndLibraryTests(unittest.TestCase):
    def test_six_frames_and_text(self):
        s=make_button_sheet('REDEFINIR','Dourado')
        self.assertEqual(s.size,(144,240))
        self.assertNotEqual(s.getpixel((0,0)),s.getpixel((8,8)))
        self.assertEqual(make_button_sheet('RESET','Nord Red').size,(144,240))
    def test_crop_fills_top_area(self):
        with TemporaryDirectory() as d:
            root=Path(d)
            img=root/'square.png'; Image.new('RGBA',(100,100),(200,40,50,255)).save(img)
            pack=create_visual_pack(root/'out','Piano',wallpaper=img,fit_mode='cover',fx_panel=True,
                                    button_text='RESET',button_style='Dourado')
            with Image.open(pack.pictures/(pack.wallpaper_name+'.png')) as w:
                self.assertEqual(w.size,(633,620))
                self.assertEqual(w.getpixel((0,30)),(200,40,50,255))
            with Image.open(pack.pictures/(pack.button_name+'.png')) as b:
                self.assertEqual(b.size,(144,240))
            self.assertIn('Animations: 6',(pack.pictures/(pack.button_name+'.txt')).read_text())
    def test_marker_cover_and_complete_ksp(self):
        with TemporaryDirectory() as d:
            root=Path(d); manifest=root/'instrument.json'
            (root/'Samples').mkdir()
            (root/'Samples'/'x.wav').write_bytes(b'RIFF'+bytes(60))
            manifest.write_text(json.dumps({'schema':1,'name':'Piano','samples':[{'root':60,'bank':'attack','layer':0,
                  'filename':'x.wav','lo_vel':0,'hi_vel':127}], 'keys':[{'note':60,'root':60,'cents':0}]}))
            result=build_direct_export(manifest,root/'out','Piano XL',auto_fx=True,
                                       use_default_visuals=True,prepare_library_manager=True)
            folder=result.nki.parent
            marker=folder/'Piano XL_info.nkx'
            self.assertTrue(marker.exists())
            self.assertEqual(marker.stat().st_size,0)
            with Image.open(folder/'wallpaper.png') as img:
                self.assertEqual(img.size,(633,98))
            text=result.source_ksp.read_text()
            self.assertIn('set_control_par_str(get_ui_id($Redefinir)',text)
            self.assertIn('set_text($Redefinir,"")',text)
            self.assertTrue((folder/'COMO_ADICIONAR_NO_LIBRARY_MANAGER.txt').exists())
            self.assertEqual(result.artwork.nkr.exists(),False)

if __name__=='__main__':unittest.main()
