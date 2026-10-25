import json, sys, unittest
from pathlib import Path
from tempfile import TemporaryDirectory
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from nordbridge.direct_export import build_direct_export
from nordbridge.visual_assets import add_visual_ksp, create_visual_pack

class WallpaperFallbackTests(unittest.TestCase):
    def test_lua_wallpaper_independent_of_nkr(self):
        with TemporaryDirectory() as t:
            folder=Path(t); (folder/'Samples').mkdir()
            (folder/'Samples'/'x.wav').write_bytes(b'RIFF'+bytes(60))
            doc={'schema':1, 'name':'Test Piano','samples':[{'root':60,'bank':'attack','layer':0,'filename':'x.wav','lo_vel':0,'hi_vel':127}], 'keys':[{'note':60,'root':60,'cents':0}]}
            (folder/'instrument.json').write_text(json.dumps(doc),encoding='utf8')
            result=build_direct_export(folder/'instrument.json',folder/'dest','Test Piano',use_default_visuals=True)
            lua=result.lua.read_text(encoding='utf8'); ksp=result.source_ksp.read_text(encoding='utf8')
            self.assertIn('pcall(K.set_instrument_options, inst, {wallpaper=wallpaper_path})',lua)
            self.assertIn('WALLPAPER APLICADO VIA API',lua)
            self.assertIn('INST_ICON_ID',ksp)
            self.assertNotIn('INST_WALLPAPER_ID',ksp)
            self.assertTrue((result.artwork.pictures / (result.artwork.wallpaper_name+'.png')).is_file())
    def test_legacy_ksp_remains_compatible(self):
        with TemporaryDirectory() as t:
            p=create_visual_pack(Path(t),'Piano',use_defaults=True)
            ksp=add_visual_ksp('on init\nmake_perfview\nend on\n',p)
            self.assertIn('INST_WALLPAPER_ID',ksp)
