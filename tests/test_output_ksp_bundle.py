"""Evita regressao de KSP apontando para cache e instalacao sem validacao."""
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from nordbridge.direct_export import build_direct_export


def create_manifest(root: Path):
    cache = root / 'cache'
    (cache / 'Samples').mkdir(parents=True)
    (cache / 'Samples' / 'sample.wav').write_bytes(b'RIFF' + bytes(512))
    manifest = cache / 'instrument.json'
    manifest.write_text(json.dumps({
        'schema':1, 'name':'Piano',
        'samples':[{'root':60,'bank':'attack','layer':0,'filename':'sample.wav','lo_vel':1,'hi_vel':127}],
        'keys':[{'note':60,'root':60,'cents':0}],
    }), encoding='utf-8')
    return manifest


class ScriptOutputTests(unittest.TestCase):
    def test_lua_ksp_and_log_live_next_to_nki(self):
        with TemporaryDirectory() as t:
            root=Path(t)
            m=create_manifest(root)
            e=build_direct_export(m, root / 'destino', 'Piano Nord')
            for p in (e.lua, e.source_ksp, e.log):
                self.assertEqual(p.parent, e.nki.parent)
            self.assertEqual(e.samples_dir.parent, e.nki.parent)
            script=e.lua.read_text(encoding='utf-8')
            self.assertIn(str(e.source_ksp.as_posix()),script)
            self.assertIn(str(e.log.as_posix()),script)
            self.assertNotIn(str((m.parent / 'PAINEL_KONTAKT').as_posix()),script)
            self.assertIn('local codigo = f:read("*a")',script)
            self.assertIn('get_instrument_script_source',script)
            self.assertIn('KSP RETORNO API [',script)
            self.assertLess(script.index('KSP IMPORTADO E TEXTO PRESENTE NO SLOT'), script.index('SALVANDO NKI + SAMPLES'))

    def test_visual_fallback_ksp_and_custom_in_output(self):
        with TemporaryDirectory() as t:
            root=Path(t)
            m=create_manifest(root)
            custom=root/'my.ksp'
            custom.write_text('on init\n  message("")\nend on\n', encoding='utf-8')
            e=build_direct_export(m, root/'destino', 'Nord Piano', auto_fx=True,
                                  use_default_visuals=True, ksp_source=custom)
            lua=e.lua.read_text(encoding='utf-8')
            self.assertIn('fallback_ksp_path',lua)
            self.assertIn('instalar_ksp(1,',lua)
            self.assertIn('local function instalar_ksp',lua)
            self.assertTrue((e.nki.parent/'PAINEL_SEM_NKR_Nord Piano.ksp').is_file())
            self.assertTrue((e.nki.parent/'PERSONALIZADO_Nord Piano.ksp').is_file())
            self.assertTrue((e.nki.parent/'Resources'/'pictures').is_dir())
            self.assertNotIn(str((m.parent/'PERSONALIZADO_').as_posix()),lua)

if __name__ == '__main__': unittest.main()
