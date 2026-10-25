"""Janela de compilação dos EXEs Portable e Installer no Windows."""
from __future__ import annotations

import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk

from build_windows import build_portable, build_installer, build_both

ROOT = Path(__file__).resolve().parent


class BuildApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Nord Kontakt Bridge')
        self.geometry('700x360')
        self.minsize(620, 320)
        self.configure(bg='#151217')
        self._icon = None
        self._apply_icon()
        self.messages = queue.Queue()
        self.running = False
        self.buttons = []
        tk.Label(self, text='GERADOR DE EXECUTÁVEIS WINDOWS',
                 font=('Segoe UI', 14, 'bold'), fg='white', bg='#151217').pack(pady=(22, 6))
        tk.Label(self, text='Escolha Portable, Installer ou gere ambos de uma vez.',
                 font=('Segoe UI', 10), fg='#d4cdd1', bg='#151217').pack(pady=(0, 8))
        row = tk.Frame(self, bg='#151217')
        row.pack(padx=18, pady=8)
        for title, mode in [('GERAR PORTABLE', 'portable'), ('GERAR INSTALLER', 'installer'),
                            ('GERAR OS DOIS', 'ambos')]:
            button = tk.Button(row, text=title, width=18, font=('Segoe UI', 9, 'bold'),
                               bg='#ad2635', fg='white', relief='flat', padx=8, pady=10,
                               command=lambda m=mode: self.start(m))
            button.pack(side='left', padx=5)
            self.buttons.append(button)
        self.log = tk.Text(self, bg='#211b21', fg='#eee5e8', font=('Consolas', 9),
                           relief='flat', wrap='word', height=8, state='disabled')
        self.log.pack(fill='both', expand=True, padx=20, pady=(4, 16))
        self._append('Os arquivos serão salvos na pasta dist. O Installer exige Inno Setup instalado.\n')
        self.after(150, self.poll)

    def _apply_icon(self):
        ico = ROOT / 'assets' / 'NordBridge.ico'
        png = ROOT / 'assets' / 'default_icon.png'
        try:
            if ico.is_file():
                self.iconbitmap(default=str(ico))
        except Exception:
            pass
        try:
            if png.is_file():
                self._icon = tk.PhotoImage(file=str(png))
                self.iconphoto(True, self._icon)
        except Exception:
            pass

    def _append(self, text):
        self.log.configure(state='normal')
        self.log.insert('end', text)
        self.log.see('end')
        self.log.configure(state='disabled')

    def start(self, mode):
        if self.running:
            return
        self.running = True
        for button in self.buttons:
            button.configure(state='disabled')
        self._append('\nIniciando compilação...\n')

        def worker():
            try:
                work = {'portable': build_portable, 'installer': build_installer,
                        'ambos': build_both}[mode]
                work(status=lambda msg: self.messages.put(str(msg)))
                self.messages.put('Concluído. Abra a pasta dist para encontrar o(s) EXE(s).')
            except Exception as exc:
                self.messages.put('Falha na compilação: ' + str(exc))
            finally:
                self.messages.put(None)

        threading.Thread(target=worker, daemon=True).start()

    def poll(self):
        try:
            while True:
                message = self.messages.get_nowait()
                if message is None:
                    self.running = False
                    for button in self.buttons:
                        button.configure(state='normal')
                else:
                    self._append(message + '\n')
        except queue.Empty:
            pass
        self.after(150, self.poll)


if __name__ == '__main__':
    BuildApp().mainloop()
