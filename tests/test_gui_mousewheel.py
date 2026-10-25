"""A roda do mouse deve rolar todas as abas, inclusive a prévia e campos FX."""
import os
import sys
import tkinter as tk
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from nordbridge.direct_gui import DirectApp


@unittest.skipUnless(os.name == 'nt' or os.getenv('NKB_RUN_GUI_TESTS') == '1',
                     'Exige ambiente gráfico (no Linux: xvfb-run -a env NKB_RUN_GUI_TESTS=1).')
class MouseWheelTests(unittest.TestCase):
    def setUp(self):
        self.app = DirectApp()
        self.app.update()

    def tearDown(self):
        # Encerra callbacks agendados pelo monitor antes de destruir a janela.
        for after_id in self.app.tk.call('after', 'info'):
            self.app.after_cancel(after_id)
        self.app.destroy()

    def _active_canvas(self, tab):
        self.app.notebook.select(tab)
        self.app.update()
        return self.app._scrollable_canvases[str(tab)]

    def test_all_three_tabs_register_separate_scrolls(self):
        for tab in (self.app.page_convert, self.app.page_visual, self.app.page_fx_editor):
            canvas = self._active_canvas(tab)
            self.assertLess(canvas.yview()[0], canvas.yview()[1])
            self.assertLess(canvas.yview()[1], 1.0, 'Esperado conteúdo maior do que a área visível')

    def test_mousewheel_scrolls_fx_using_canvas_and_child(self):
        canvas = self._active_canvas(self.app.page_fx_editor)
        self.assertAlmostEqual(canvas.yview()[0], 0.0)
        # O evento funciona quando o cursor está diretamente sobre o Canvas.
        canvas.event_generate('<MouseWheel>', x=20, y=20, delta=-120)
        self.app.update()
        self.assertGreater(canvas.yview()[0], 0.0)
        # Voltar à posição inicial usando a roda para cima.
        canvas.event_generate('<MouseWheel>', x=20, y=20, delta=120)
        self.app.update()
        self.assertAlmostEqual(canvas.yview()[0], 0.0)
        # E também sobre o texto de ajuda que está dentro do Canvas.
        inner = canvas.winfo_children()[0]
        help_label = next(w for w in inner.winfo_children() if isinstance(w, tk.Label))
        help_label.event_generate('<MouseWheel>', x=12, y=12, delta=-120)
        self.app.update()
        self.assertGreater(canvas.yview()[0], 0.0)

    def test_linux_wheel_and_no_scrolling_over_header(self):
        canvas = self._active_canvas(self.app.page_fx_editor)
        canvas.event_generate('<Button-5>', x=20, y=20)
        self.app.update()
        self.assertGreater(canvas.yview()[0], 0.0)
        canvas.yview_moveto(0)
        self.app.update()
        # Fora da área da aba: não deve fazer o conteúdo rolar.
        self.app.event_generate('<MouseWheel>', x=15, y=15, delta=-120)
        self.app.update()
        self.assertAlmostEqual(canvas.yview()[0], 0.0)

    def test_switching_tabs_does_not_scroll_hidden_editor(self):
        fx_canvas = self._active_canvas(self.app.page_fx_editor)
        self._active_canvas(self.app.page_convert)
        convert_canvas = self.app._scrollable_canvases[str(self.app.page_convert)]
        convert_canvas.event_generate('<MouseWheel>', x=20, y=20, delta=-120)
        self.app.update()
        self.assertGreater(convert_canvas.yview()[0], 0.0)
        self.assertAlmostEqual(fx_canvas.yview()[0], 0.0)


if __name__ == '__main__':
    unittest.main()
