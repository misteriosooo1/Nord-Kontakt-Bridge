import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from nordbridge.visual_assets import create_visual_pack, add_visual_ksp
from nordbridge.direct_export import build_direct_export


class TestVisuals(unittest.TestCase):
    def test_pack_resizes_images_without_cropping(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            art = root / 'wide.png'
            Image.new('RGB', (990, 80), (220, 20, 40)).save(art)
            pack = create_visual_pack(root / 'out', 'Meu Piano', wallpaper=art, icon=art, cover=art)
            with Image.open(pack.pictures / (pack.wallpaper_name + '.png')) as im:
                self.assertEqual(im.size, (633,320))
            with Image.open(pack.pictures / (pack.icon_name + '.png')) as im:
                self.assertEqual(im.size, (72,72))
            with Image.open(pack.cover) as im:
                self.assertEqual(im.size, (633,98))
            self.assertIn('Number of Animations: 0', (pack.pictures / (pack.icon_name + '.txt')).read_text())

    def test_ksp_added_inside_init_and_not_twice(self):
        with TemporaryDirectory() as tmp:
            pack = create_visual_pack(Path(tmp) / 'out', 'Piano', use_defaults=True)
            source = 'on init\n    set_control_par_str($INST_WALLPAPER_ID,$CONTROL_PAR_PICTURE,"Old")\nend on\non note\nend on\n'
            modified = add_visual_ksp(source, pack)
            self.assertIn('end on\non note', modified)
            self.assertNotIn('"Old"', modified)
            self.assertIn('$INST_ICON_ID', modified)
            self.assertEqual(modified.count('$INST_WALLPAPER_ID'), 1)
            with self.assertRaises(ValueError):
                add_visual_ksp('on init\n set_skin_offset(745)\nend on\n', pack)

    def test_generated_lua_links_real_nkr_and_has_cover(self):
        with TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / 'Samples').mkdir()
            (folder / 'Samples' / 'x.wav').write_bytes(b'RIFF' + bytes(60))
            doc = {'schema':1, 'name':'Piano', 'samples':[{'root':60,'bank':'attack','layer':0,
                   'filename':'x.wav','lo_vel':0,'hi_vel':127}], 'keys':[{'note':60,'root':60,'cents':0}]}
            (folder / 'instrument.json').write_text(json.dumps(doc))
            result = build_direct_export(folder/'instrument.json', folder/'nki', 'Piano', use_default_visuals=True)
            self.assertTrue(result.artwork)
            script = result.lua.read_text(encoding='utf-8')
            self.assertIn('pcall(K.create_resource_container, inst, nkr_path)', script)
            self.assertNotIn('K.create_resource_container("', script)
            self.assertIn('pcall(K.link_resource_container', script)
            self.assertIn('K.save_instrument', script)
            self.assertIn('NKR CONFIRMADO', script)
            self.assertTrue(result.artwork.cover.exists())
            self.assertFalse(result.artwork.nkr.exists(), 'NKR must only be created by Kontakt')

if __name__ == '__main__':
    unittest.main()
