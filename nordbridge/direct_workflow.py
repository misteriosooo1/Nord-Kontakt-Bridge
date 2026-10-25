"""Orquestração .npno -> WAVs em cache -> Samples finais -> Kontakt -> NKI."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .core import convert_npno, find_nord_exe
from .direct_export import DirectExport, build_direct_export
from .fx_designer import FXDesign


def cache_home() -> Path:
    base = Path(os.environ.get('LOCALAPPDATA') or Path.home() / '.nord_kontakt_bridge')
    return base / 'NordKontaktBridge' / 'Work'


def file_digest(source: Path) -> str:
    h = hashlib.sha256()
    with source.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()[:20]


def valid_cached_project(folder: Path) -> bool:
    path = folder / 'instrument.json'
    if not path.is_file():
        return False
    try:
        doc = json.loads(path.read_text(encoding='utf-8'))
        samples = doc.get('samples', [])
        return bool(samples) and all(
            (folder / 'Samples' / Path(str(x['filename'])).name).is_file()
            and (folder / 'Samples' / Path(str(x['filename'])).name).stat().st_size > 44
            for x in samples
        )
    except (ValueError, KeyError, OSError):
        return False


@dataclass(frozen=True)
class Prepared:
    export: DirectExport
    work_dir: Path
    cached: bool


def prepare(source: Path, target: Path, name: str, progress: Callable[[int, int, str], None],
            *, decoder=None, work_root: Path | None = None, ksp_source: Path | None = None,
            wallpaper: Path | None = None, icon: Path | None = None,
            cover: Path | None = None, use_default_visuals: bool = False, auto_fx: bool = True,
            nkr_template: Path | None = None, fit_mode: str = 'cover',
            button_image: Path | None = None, button_text: str = 'REDEFINIR',
            button_style: str = 'Nord Red', prepare_library_manager: bool = True,
            fx_design: FXDesign | None = None) -> Prepared:
    source = Path(source).resolve()
    target = Path(target).resolve()
    if not source.is_file() or source.suffix.lower() != '.npno':
        raise ValueError('Escolha um arquivo .npno válido.')
    if not name.strip():
        raise ValueError('O nome do instrumento é obrigatório. Informe um nome para gerar o arquivo .nki.')
    root = (work_root or cache_home()).resolve()
    root.mkdir(parents=True, exist_ok=True)
    progress(0, 1, 'Identificando o arquivo Nord...')
    folder = root / file_digest(source)
    cached = valid_cached_project(folder)
    if not cached:
        # Somente remove dados no diretório de cache gerido pelo próprio app.
        if folder.exists():
            shutil.rmtree(folder)
        progress(0, 1, 'Decodificando áudio internamente (serão copiados para Samples)...')
        convert_npno(source, folder, progress, decoder=decoder)
        if not valid_cached_project(folder):
            raise RuntimeError('Conversão interrompida: samples temporários incompletos.')
    else:
        progress(1, 1, 'Amostras temporárias encontradas; reutilizando cache.')
    progress(1, 1, 'Copiando WAVs para Samples e criando Lua do Kontakt...')
    export = build_direct_export(folder / 'instrument.json', target, name, ksp_source=ksp_source,
                                 wallpaper=wallpaper, icon=icon, cover=cover,
                                 use_default_visuals=use_default_visuals, auto_fx=auto_fx, nkr_template=nkr_template,
                                 fit_mode=fit_mode, button_image=button_image,
                                 button_text=button_text, button_style=button_style,
                                 prepare_library_manager=prepare_library_manager, fx_design=fx_design)
    return Prepared(export=export, work_dir=folder, cached=cached)


def find_kontakt8() -> Path | None:
    if os.name != 'nt':
        return None
    bases = [os.environ.get('ProgramFiles'), os.environ.get('ProgramW6432'), os.environ.get('ProgramFiles(x86)')]
    for base in bases:
        if not base:
            continue
        p = Path(base) / 'Native Instruments' / 'Kontakt 8' / 'Kontakt 8.exe'
        if p.is_file():
            return p
    return None


def find_decoder() -> Path | None:
    return find_nord_exe()


def safe_remove_work(folder: Path, root: Path | None = None) -> None:
    """Limpeza explícita; não apaga fora do cache do aplicativo."""
    root = (root or cache_home()).resolve()
    folder = Path(folder).resolve()
    if folder.parent != root or len(folder.name) != 20 or any(c not in '0123456789abcdef' for c in folder.name):
        raise ValueError('Recusado: a pasta não pertence ao cache Nord Bridge.')
    if folder.is_dir():
        shutil.rmtree(folder)
