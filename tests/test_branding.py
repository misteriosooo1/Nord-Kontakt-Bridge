"""Verifica o nome público do Nord Kontakt Bridge."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / 'SUPORTE_RECUPERACAO' / 'FERRAMENTAS_COMPILACAO'

class BrandingTests(unittest.TestCase):
    def test_title_only_product_name(self):
        source = (ROOT / 'nordbridge' / 'direct_gui.py').read_text(encoding='utf-8')
        self.assertIn("self.title('Nord Kontakt Bridge')", source)
        self.assertNotIn('Guia integrado', source)
        self.assertNotIn('v0.7.2', source)

    def test_compilation_output_brand(self):
        source = (TOOLS / 'CRIAR_EXE.pyw').read_text(encoding='utf-8')
        self.assertIn('build_both', source)
        builder = (TOOLS / 'build_windows.py').read_text(encoding='utf-8')
        self.assertIn("APP_NAME = 'Nord Kontakt Bridge'", builder)
        self.assertIn("APP_EXE = BUILD / 'windows' / 'Nord Kontakt Bridge.exe'", builder)
        self.assertTrue((ROOT / 'Nord Kontakt Bridge.pyw').is_file())
        for mod in [TOOLS / 'CRIAR_EXE.pyw', ROOT / 'Nord Kontakt Bridge.pyw', ROOT / 'nordbridge/direct_gui.py']:
            ast.parse(mod.read_text(encoding='utf-8'))

    def test_readme_heading(self):
        self.assertEqual((ROOT / 'README.md').read_text(encoding='utf-8').splitlines()[0], '# Nord Kontakt Bridge')

if __name__ == '__main__':
    unittest.main()
