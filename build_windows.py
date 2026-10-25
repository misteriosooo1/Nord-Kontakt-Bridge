"""Cria os executáveis Windows Portable e Installer do Nord Kontakt Bridge.

Executar no Windows: python build_windows.py ambos
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parent
DIST = ROOT / 'dist'
BUILD = ROOT / 'build'
APP_EXE = BUILD / 'windows' / 'Nord Kontakt Bridge.exe'
PORTABLE = DIST / 'Nord Kontakt Bridge Portable.exe'
INSTALLER = DIST / 'Nord Kontakt Bridge Installer.exe'
APP_NAME = 'Nord Kontakt Bridge'
INNO_DOCS = 'https://jrsoftware.org/isdl.php'


class BuildError(RuntimeError):
    """Erro de compilação com orientação legível para quem está começando."""


def say(message: str, status: Callable[[str], None] = print) -> None:
    status(message)


def require_windows() -> None:
    if sys.platform != 'win32':
        raise BuildError('A compilação de EXEs Windows precisa rodar no Windows. '
                         'Use GERAR_PORTABLE_E_INSTALLER.bat no seu PC ou o GitHub Actions incluído.')


def ensure_python_dependencies(status: Callable[[str], None]) -> None:
    missing = []
    for module, package in [('PyInstaller', 'pyinstaller'), ('PIL', 'pillow')]:
        if importlib.util.find_spec(module) is None:
            missing.append(package)
    if missing:
        say('Instalando dependências de compilação: ' + ', '.join(missing), status)
        subprocess.run([sys.executable, '-m', 'pip', 'install', *missing],
                       cwd=ROOT, check=True)


def pyinstaller_command() -> list[str]:
    """Usa os recursos e ícone originais. Decoder só é incorporado se fornecido."""
    sep = ';' if sys.platform == 'win32' else ':'
    cmd = [sys.executable, '-m', 'PyInstaller',
           '--noconfirm', '--clean', '--onefile', '--windowed',
           '--name', APP_NAME,
           '--icon', str(ROOT / 'assets' / 'NordBridge.ico'),
           '--distpath', str(APP_EXE.parent),
           '--workpath', str(BUILD / 'pyinstaller'),
           '--specpath', str(BUILD / 'pyinstaller'),
           '--add-data', f'{ROOT / "assets"}{sep}assets']
    decoder = ROOT / 'nord.exe'
    if decoder.is_file():
        cmd.extend(['--add-binary', f'{decoder}{sep}.'])
    cmd.append(str(ROOT / 'Nord Kontakt Bridge.pyw'))
    return cmd


def build_portable(status: Callable[[str], None] = print) -> Path:
    require_windows()
    ensure_python_dependencies(status)
    DIST.mkdir(exist_ok=True)
    say('Compilando o aplicativo Windows com PyInstaller...', status)
    say('O nord.exe será incorporado.' if (ROOT / 'nord.exe').is_file()
        else 'Aviso: nord.exe não está nesta pasta; a conversão exigirá o decoder separadamente.', status)
    subprocess.run(pyinstaller_command(), cwd=ROOT, check=True)
    if not APP_EXE.is_file() or not APP_EXE.stat().st_size:
        raise BuildError('O PyInstaller terminou sem criar o EXE esperado.')
    shutil.copy2(APP_EXE, PORTABLE)
    say(f'PORTABLE PRONTO: {PORTABLE}', status)
    return PORTABLE


def inno_candidates():
    """Caminhos padrão; não depende de winget para compilar."""
    override = os.environ.get('ISCC_PATH', '').strip().strip('"')
    if override:
        yield Path(override)
    for command in ('ISCC.exe', 'ISCC'):
        found = shutil.which(command)
        if found:
            yield Path(found)
    for base in (os.environ.get('ProgramFiles(x86)'), os.environ.get('ProgramFiles'),
                 os.environ.get('LOCALAPPDATA')):
        if base:
            for version in ('Inno Setup 6', 'Inno Setup 7'):
                yield Path(base) / version / 'ISCC.exe'
                yield Path(base) / 'Programs' / version / 'ISCC.exe'
    programdata = os.environ.get('ProgramData')
    if programdata:
        yield Path(programdata) / 'chocolatey' / 'bin' / 'ISCC.exe'


def find_inno_compiler() -> Path | None:
    return next((candidate for candidate in inno_candidates() if candidate.is_file()), None)


def build_installer(status: Callable[[str], None] = print, *, build_app: bool = True) -> Path:
    require_windows()
    iscc = find_inno_compiler()
    if not iscc:
        raise BuildError('Inno Setup não foi encontrado. Instale gratuitamente para uso pessoal '
                         f'a partir de {INNO_DOCS}, e execute a compilação novamente. '
                         'Se instalou em outro caminho, defina ISCC_PATH.')
    if build_app or not APP_EXE.is_file():
        build_portable(status)
    DIST.mkdir(exist_ok=True)
    say('Criando instalador Windows com Inno Setup...', status)
    subprocess.run([str(iscc), str(ROOT / 'Nord Kontakt Bridge Installer.iss')],
                   cwd=ROOT, check=True)
    if not INSTALLER.is_file() or not INSTALLER.stat().st_size:
        raise BuildError('O Inno Setup terminou sem criar o Installer.exe esperado.')
    say(f'INSTALLER PRONTO: {INSTALLER}', status)
    return INSTALLER


def build_both(status: Callable[[str], None] = print) -> tuple[Path, Path]:
    portable = build_portable(status)
    try:
        installer = build_installer(status, build_app=False)
    except Exception:
        say(f'O Portable já foi gerado: {portable}', status)
        raise
    say('As duas versões foram geradas na pasta dist!', status)
    return portable, installer


def main() -> int:
    parser = argparse.ArgumentParser(description='Cria Portable e Installer para Windows.')
    parser.add_argument('modo', nargs='?', choices=['portable', 'installer', 'ambos'], default='ambos')
    args = parser.parse_args()
    try:
        if args.modo == 'portable':
            build_portable()
        elif args.modo == 'installer':
            build_installer()
        else:
            build_both()
        return 0
    except (BuildError, OSError, subprocess.CalledProcessError) as exc:
        print(f'ERRO: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
