import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from nordbridge.direct_export import build_direct_export


def create_project(root):
    (root / "Samples").mkdir()
    (root / "Samples" / "piano.wav").write_bytes(b"RIFF" + bytes(100))
    (root / "instrument.json").write_text(json.dumps({
        "schema":1, "name":"Piano", "samples":[{"root":60,"bank":"attack","layer":0,"filename":"piano.wav","lo_vel":0,"hi_vel":127}],
        "keys":[{"note":60,"root":60,"cents":0}]
    }))


class LuaDiagnosticsTests(unittest.TestCase):
    def test_graphics_fallback_is_automatic(self):
        with TemporaryDirectory() as t:
            root = Path(t)
            create_project(root)
            exp = build_direct_export(root / "instrument.json", root / "out", "Piano FX", use_default_visuals=True)
            lua = exp.lua.read_text("utf-8")
            self.assertIn('KSP COM ICONE FALHOU:', lua)
            self.assertIn('TENTATIVA AUTOMATICA DE PAINEL SEM REFERENCIAS GRAFICAS', lua)
            self.assertIn('instalar_ksp(0, fallback_ksp_path', lua)
            self.assertIn('KSP RESPOSTA ENVIO [', lua)
            self.assertIn('KSP RETORNO API [', lua)
            self.assertIn('texto:sub(1, 180):gsub("%s+", " ")', lua)
            self.assertIn('SALVANDO NKI + SAMPLES', lua)
            self.assertLess(lua.index('INSTALANDO KSP'), lua.index('SALVANDO NKI + SAMPLES'))

    def test_no_graphics_still_logs_detail(self):
        with TemporaryDirectory() as t:
            root=Path(t)
            create_project(root)
            exp=build_direct_export(root / "instrument.json", root / "out", "Piano FX", use_default_visuals=False)
            lua=exp.lua.read_text("utf-8")
            self.assertIn('PAINEL FX NAO FOI IMPORTADO:', lua)
            self.assertIn('tipo=', lua)
            self.assertNotIn('fallback_ksp_path', lua)

if __name__ == "__main__": unittest.main()
