"""Interface simples para gerar Portable e Installer no Windows (sem console)."""
from __future__ import annotations
import sys
import threading
import tkinter as tk

from build_windows import build_both

root = tk.Tk()
root.title('Nord Kontakt Bridge — Compilar Portable e Installer')
root.geometry('610x220')
root.resizable(False, False)
message = tk.StringVar(value='Crie os dois EXEs para Windows com PyInstaller e Inno Setup.\nRequer Python e Inno Setup instalados apenas no computador de desenvolvimento.')
tk.Label(root, textvariable=message, wraplength=570, justify='left', anchor='w').pack(padx=18,pady=20,fill='x')

def start():
    button.configure(state='disabled')
    def status(text):
        root.after(0,lambda:message.set(text))
    def worker():
        try:
            build_both(status)
            status('Concluído! Os arquivos Portable.exe e Installer.exe estão na pasta dist.')
        except Exception as exc:
            status('ERRO na compilação: ' + str(exc))
        finally:
            root.after(0,lambda:button.configure(state='normal'))
    threading.Thread(target=worker,daemon=True).start()

button = tk.Button(root, text='GERAR PORTABLE E INSTALADOR (.EXE)', command=start)
button.pack(pady=12,ipadx=12,ipady=8)
root.mainloop()
