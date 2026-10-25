"""Testes de regressão para as descrições integradas do Nord Red ."""
import os
import sys
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from nordbridge.direct_gui import DirectApp


@unittest.skipUnless(os.name == 'nt' or os.getenv('NKB_RUN_GUI_TESTS') == '1',
                     'Testes Tk fora do Windows: use xvfb-run -a env NKB_RUN_GUI_TESTS=1 python -m unittest')
class IntegratedGuideTests(unittest.TestCase):
    def setUp(self):
        self.app = DirectApp()
        self.app.withdraw()

    def tearDown(self):
        # Cancela o monitor periódico antes de destruir a instância Tk.
        for after_id in self.app.tk.call('after', 'info'):
            self.app.after_cancel(after_id)
        self.app.destroy()

    def test_required_blank_and_optional_blank(self):
        self.assertEqual(self.app.source.get(), '')
        self.assertEqual(self.app.name_var.get(), '')
        for var in (self.app.output, self.app.wallpaper,
                    self.app.instrument_icon, self.app.library_cover, self.app.ksp):
            self.assertEqual(var.get(), '')
        self.assertTrue(self.app.use_theme.get())

    def test_default_fallback_is_checked_and_disabled(self):
        checks = []
        def walk(parent):
            for widget in parent.winfo_children():
                if isinstance(widget, tk.Checkbutton):
                    checks.append(widget)
                walk(widget)
        walk(self.app)
        matches = [w for w in checks if 'Usar wallpaper e ícone padrão' in w.cget('text')]
        self.assertEqual(len(matches), 1)
        self.assertEqual(str(matches[0].cget('state')), 'disabled')
        self.assertTrue(self.app.use_theme.get())

    def test_missing_name_and_output_warnings(self):
        with patch('nordbridge.direct_gui.messagebox.showwarning') as warning:
            self.app.start()
            self.assertIn('Arquivo Nord obrigatório', warning.call_args.args[0])
            self.app.source.set('piano.npno')
            self.app.start()
            self.assertEqual('Nome obrigatório', warning.call_args.args[0])
            self.app.name_var.set('Meu piano')
            self.app.start()
            self.assertEqual('Pasta de saída obrigatória', warning.call_args.args[0])
            self.app.output.set(str(Path.home()))
            self.app.start()
            self.assertEqual('Kontakt 8 obrigatório', warning.call_args.args[0])

    def test_npmo_not_advertised_as_supported(self):
        self.app.source.set('algum_piano.npmo')
        self.app.name_var.set('Teste')
        self.app.output.set(str(Path.home()))
        self.app.kontakt.set('Kontakt 8.exe')
        with patch('nordbridge.direct_gui.messagebox.showwarning') as warning:
            self.app.start()
            self.assertEqual('Arquivo Nord inválido', warning.call_args.args[0])
            self.assertIn('.npmo', warning.call_args.args[1])


if __name__ == '__main__':
    unittest.main()
