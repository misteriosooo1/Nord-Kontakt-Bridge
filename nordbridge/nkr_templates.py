"""Seleciona automaticamente um Resource Container autentico de projeto anterior.

Nunca cria NKR vazio, nunca varre bibliotecas comerciais instaladas.
O arquivo encontrado deve ter sido criado pelo proprio Kontakt e pertencer ao usuario.
"""
from __future__ import annotations
import os
from pathlib import Path

MIN_SIZE = 128


def valid_template(path: Path) -> bool:
    try:
        p = Path(path)
        return p.is_file() and p.suffix.casefold() == '.nkr' and p.stat().st_size >= MIN_SIZE
    except (OSError, ValueError):
        return False


def find_local_template(output: Path, explicit: Path | None = None) -> Path | None:
    """Busca somente pastas de trabalho locais, nunca Program Files/VSTs comerciais.

    Preferencia: arquivo selecionado uma vez, seguido por NKR no destino e por
    bibliotecas da pasta do NordKontaktBridge existente em Documentos.
    """
    if explicit is not None:
        path = Path(explicit).expanduser().resolve()
        if not valid_template(path):
            raise ValueError('O modelo NKR escolhido nao existe ou esta vazio/invalido: ' + str(path))
        return path
    output = Path(output).resolve()
    paths = [output]
    home = Path(os.environ.get('USERPROFILE') or Path.home())
    docs = [home / 'Documents', home / 'OneDrive' / 'Documents', home / 'Documentos']
    for document in docs:
        paths.append(document / 'NordKontaktBridge')
    # A pasta-pai fica por ultimo, para nao gastar a varredura em Downloads/Documents.
    paths.append(output.parent)
    candidates = []
    inspected = 0
    for root in paths:
        if not root.is_dir():
            continue
        # Escopo limitado a projetos da propria pessoa: max 4 niveis, max 2000 pastas.
        for cur, dirs, files in os.walk(root):
            curpath=Path(cur)
            depth=len(curpath.relative_to(root).parts)
            dirs[:]=sorted(x for x in dirs if x not in ('node_modules','.git','.venv','venv','Work') and depth < 4)
            inspected += 1
            if inspected > 2000:
                break
            for file in files:
                if not file.casefold().endswith('.nkr'):
                    continue
                # NKR do projeto, e nao qualquer NKR comercial.
                lower=file.casefold()
                if not (('astoria' in lower) or ('nord' in lower) or ('resources' in lower)):
                    continue
                path=curpath/file
                if valid_template(path):
                    candidates.append(path)
        if inspected > 2000:
            break
    if not candidates:
        return None
    # Prioriza original do usuario e evita templates do proprio NKI atualmente sendo gerado.
    candidates.sort(key=lambda p: (not (p.name.casefold() == 'astoria_resources.nkr'), p.stat().st_size, str(p).lower()))
    return candidates[0]
