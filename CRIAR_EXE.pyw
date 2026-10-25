"""Compilador sem BAT; requer Python e conexão para instalar PyInstaller se necessário."""
from __future__ import annotations
import importlib.util
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

ROOT = Path(__file__).resolve().parent


def build(status):
    try:
        if importlib.util.find_spec('PyInstaller') is None:
            status('Instalando PyInstaller pelo Python...')
            subprocess.run([sys.executable, '-m', 'pip', 'install', '--user', 'pyinstaller'],
                           check=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        if importlib.util.find_spec('PIL') is None:
            status('Instalando Pillow para arte gráfica...')
            subprocess.run([sys.executable, '-m', 'pip', 'install', '--user', 'pillow'],
                           check=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        command = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean', '--onefile',
                   '--windowed', '--name', 'Nord Kontakt Bridge',
                   '--distpath', str(ROOT / 'dist'), '--workpath', str(ROOT / 'build'),
                   '--specpath', str(ROOT / 'build')]
        assets = ROOT / 'assets'
        command += ['--add-data', f'{assets}{";" if sys.platform == "win32" else ":"}assets']
        if sys.platform == 'win32':
            command += ['--icon', str(assets / 'NordBridge.ico')]
        try:
            from nordbridge.direct_workflow import find_decoder
            nord = find_decoder()
        except Exception:
            nord = None
        if nord:
            command += ['--add-binary', f'{nord}{";" if sys.platform == "win32" else ":"}.']
        command.append(str(ROOT / 'Nord Kontakt Bridge.pyw'))
        status('Compilando executável...')
        subprocess.run(command, check=True, cwd=ROOT, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        status('EXE gerado em dist/Nord Kontakt Bridge.exe')
    except Exception as exc:
        status('Falha: ' + str(exc))


app = tk.Tk()
app.title('Compilar Nord Kontakt Bridge — EXE')
app.geometry('520x170')
info = tk.StringVar(value='Um clique para compilar o EXE usando seu Python. Nenhum BAT.')
tk.Label(app, textvariable=info, wraplength=490, justify='left').pack(padx=16, pady=18)

def start():
    btn.config(state='disabled')
    def send(text):
        app.after(0, info.set, text)
        if text.startswith('EXE gerado') or text.startswith('Falha'):
            app.after(0, btn.config, {'state':'normal'})
    threading.Thread(target=lambda: build(send), daemon=True).start()

btn = tk.Button(app, text='COMPILAR EXE', command=start)
btn.pack(pady=10)
app.mainloop()
