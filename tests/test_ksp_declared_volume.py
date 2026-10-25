"""Regressoes: fontes KSP precisam separar declaracao e atribuicao por funcao."""
import re
import unittest
from nordbridge.default_fx import build_default_fx_ksp
from nordbridge.visual_assets import add_visual_ksp, create_visual_pack
from pathlib import Path
from tempfile import TemporaryDirectory

class DeclaredVolumeTests(unittest.TestCase):
    def test_original_volume_declared_and_then_assigned(self):
        text=build_default_fx_ksp("Nord Piano")
        self.assertIn("declare $OriginalVolume\n",text)
        self.assertIn("$OriginalVolume := get_engine_par($ENGINE_PAR_VOLUME,-1,-1,-1)",text)
        self.assertNotRegex(text,r"declare\s+\$OriginalVolume\s*:=")
        self.assertLess(text.index("declare $OriginalVolume"),text.index("$Volume := $OriginalVolume"))
        self.assertIn("on ui_control ($Redefinir)",text)

    def test_visual_variant_also_uses_safe_declaration(self):
        with TemporaryDirectory() as d:
            pack=create_visual_pack(Path(d),"Piano Nord",use_defaults=True,fx_panel=True)
            text=add_visual_ksp(build_default_fx_ksp("Piano Nord"),pack)
            self.assertIn("declare $OriginalVolume\n",text)
            self.assertNotIn("declare $OriginalVolume :=",text)
            self.assertIn("$INST_WALLPAPER_ID",text)

if __name__ == '__main__': unittest.main()
