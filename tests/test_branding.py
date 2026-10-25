"""Verifica o nome público do Nord Kontakt Bridge."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class BrandingTests(unittest.TestCase):
    def test_title_only_product_name(self):
        source = (ROOT / 'nordbridge' / 'direct_gui.py').read_text(encoding='utf-8')
        self.assertIn("self.title('Nord Kontakt Bridge')", source)
        self.assertNotIn('Guia integrado', source)
        self.assertNotIn('v0.7.2', source)

    def test_compilation_output_brand(self):
        source = (ROOT / 'CRIAR_EXE.pyw').read_text(encoding='utf-8')
        self.assertIn("'--name', 'Nord Kontakt Bridge'", source)
        self.assertIn('dist/Nord Kontakt Bridge.exe', source)
        self.assertTrue((ROOT / 'Nord Kontakt Bridge.pyw').is_file())
        for mod in ['CRIAR_EXE.pyw', 'Nord Kontakt Bridge.pyw', 'nordbridge/direct_gui.py']:
            ast.parse((ROOT / mod).read_text(encoding='utf-8'))

    def test_readme_heading(self):
        self.assertEqual((ROOT / 'README.md').read_text(encoding='utf-8').splitlines()[0], '# Nord Kontakt Bridge')

if __name__ == '__main__':
    unittest.main()
