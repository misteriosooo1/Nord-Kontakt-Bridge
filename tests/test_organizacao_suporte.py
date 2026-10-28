import unittest
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / 'SUPORTE_RECUPERACAO' / 'FERRAMENTAS_COMPILACAO'

class OrganizacaoSuporteTests(unittest.TestCase):
    def test_resources_stay_in_root(self):
        for name in ('NKR GERAL.nkr','KSP_FX_BASICO_CORRIGIDO_v0.6.1.ksp','Nord Kontakt Bridge.pyw','bin/nord.exe'):
            self.assertTrue((ROOT / name).exists(), name)
    def test_tools_can_import_without_changing_root(self):
        for name in ('build_windows.py','CRIAR_EXE.pyw'):
            ast.parse((TOOLS/name).read_text('utf-8'))
        self.assertIn("parents[2]", (TOOLS/'build_windows.py').read_text('utf-8'))
        self.assertIn('..\\..', (TOOLS/'GERAR_PORTABLE_E_INSTALLER.bat').read_text('utf-8'))
    def test_inno_source_paths(self):
        setup = (TOOLS/'Nord Kontakt Bridge Installer.iss').read_text('utf-8')
        self.assertIn('SourcePath', setup)
        self.assertIn('bin\\nord.exe', setup)
        self.assertIn('DOCUMENTACAO\\LICENCAS_TERCEIROS.txt', setup)
        self.assertIn('Excludes:', setup)

if __name__ == '__main__': unittest.main()
