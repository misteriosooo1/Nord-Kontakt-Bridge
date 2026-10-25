"""Inicia o Kontakt standalone com Lua e acompanha a criacao real do NKI.

Nao tenta injetar comandos num Kontakt ja aberto. Nao utiliza BAT, shell ou teclas simuladas.
"""
from __future__ import annotations

import csv
import io
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class JobStatus:
    state: str  # waiting, running, success, error
    description: str


def running_kontakt_processes(executable: Path) -> bool:
    """Impede `Contato.exe script.lua` quando uma instancia ja esta aberta.

    Em Windows, `tasklist` faz parte do sistema; nao abre CMD ou .bat.
    Retorna False fora do Windows ou quando a verificacao nao e possivel.
    """
    if os.name != 'nt':
        return False
    name = Path(executable).name
    try:
        result = subprocess.run(
            ['tasklist.exe', '/FO', 'CSV', '/NH', '/FI', f'IMAGENAME eq {name}'],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, encoding='utf-8', errors='replace', timeout=5,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
        )
        if result.returncode:
            return False
        for row in csv.reader(io.StringIO(result.stdout)):
            if row and row[0].casefold() == name.casefold():
                return True
    except (OSError, subprocess.TimeoutExpired):
        pass
    return False


def start_kontakt(executable: Path, script: Path, terminal_log: Path | None = None) -> subprocess.Popen:
    """O Kontakt Lua API suporta executar `.lua` como argumento de inicializacao."""
    exe = Path(executable).resolve()
    script = Path(script).resolve()
    if not exe.is_file() or exe.suffix.lower() != '.exe':
        raise FileNotFoundError('Escolha o arquivo Kontakt 8.exe completo no aplicativo.')
    if not script.is_file() or script.suffix.lower() != '.lua':
        raise FileNotFoundError('O script Lua da conversao nao foi gerado.')
    if running_kontakt_processes(exe):
        raise RuntimeError(
            'O Kontakt ja esta aberto. Feche o Kontakt standalone e abra a conversao novamente. '
            'O Kontakt aberto pode ignorar o script passado na inicializacao. '
            'O programa nao fecha seu instrumento sem sua permissao.'
        )
    if terminal_log is not None:
        path = Path(terminal_log)
        path.parent.mkdir(parents=True, exist_ok=True)
        # stdout/stderr do Kontakt podem trazer a causa silenciosa da criacao do NKR.
        with path.open('wb') as f:
            return subprocess.Popen([str(exe), str(script)], shell=False,
                                    cwd=str(exe.parent), stdout=f, stderr=subprocess.STDOUT)
    return subprocess.Popen([str(exe), str(script)], shell=False, cwd=str(exe.parent))


def read_status(log: Path, nki: Path, nkr: Path | None = None) -> JobStatus:
    """Somente o log do proprio Lua confirma que o Kontakt salvou o NKI."""
    log = Path(log)
    nki = Path(nki)
    nkr = Path(nkr) if nkr is not None else None
    if not log.is_file():
        return JobStatus('waiting', 'Kontakt iniciado; aguardando a execucao do Lua...')
    try:
        lines = log.read_text(encoding='utf-8', errors='replace').splitlines()
    except OSError:
        return JobStatus('waiting', 'Aguardando acesso ao registro do Kontakt...')
    if not lines:
        return JobStatus('waiting', 'Aguardando a primeira mensagem do Lua...')
    for line in reversed(lines):
        if '[Direto] ERRO:' in line:
            return JobStatus('error', line.split('[Direto] ERRO:', 1)[1].strip())
        if '[Direto] SUCESSO NKI SAMPLES SEM NKR:' in line or '[Direto] SUCESSO NKI SAMPLES:' in line:
            try:
                samples_dir = nki.parent / 'Samples'
                wav_count = sum(1 for p in samples_dir.glob('*.wav') if p.is_file() and p.stat().st_size > 44)
                if not nki.is_file() or nki.stat().st_size <= 1024 or wav_count == 0:
                    return JobStatus('error', 'O Kontakt informou sucesso, mas NKI ou pasta Samples estao ausentes/incompletos.')
                if 'SEM NKR' in line:
                    return JobStatus('partial', f'NKI + {wav_count} WAVs em {samples_dir}. Imagens nao incorporadas: falta vincular NKR.')
                if nkr is not None and (not nkr.is_file() or nkr.stat().st_size == 0):
                    return JobStatus('error', 'NKI e WAVs criados, mas NKR nao encontrado: ' + str(nkr))
                return JobStatus('success', f'NKI com {wav_count} WAVs salvos em {samples_dir}')
            except OSError as e:
                return JobStatus('error', f'Falha ao verificar os WAVs copiados: {e}')
        if '[Direto] SUCESSO MONOLITH SEM NKR:' in line:
            try:
                if nki.is_file() and nki.stat().st_size > 1024:
                    return JobStatus('partial', f'NKI Monolith gerado com efeitos basicos, MAS SEM wallpaper/icone: {nki}. A criacao do NKR falhou; as imagens estao preparadas em Resources/pictures.')
            except OSError:
                pass
            return JobStatus('error', 'O Kontakt sinalizou a exportacao sem NKR, mas o NKI nao foi encontrado.')
        if '[Direto] SUCESSO MONOLITH COM AVISO DE RECURSOS:' in line:
            try:
                if nki.is_file() and nki.stat().st_size > 1024:
                    return JobStatus('success', f'NKI criado, mas o NKR/graficos precisam de verificacao: {nki}')
            except OSError:
                pass
            return JobStatus('error', 'O Kontakt registrou NKI com aviso, mas o arquivo NKI nao foi encontrado.')
        if '[Direto] SUCESSO MONOLITH:' in line:
            try:
                if nki.is_file() and nki.stat().st_size > 1024:
                    if nkr is not None and (not nkr.is_file() or nkr.stat().st_size == 0):
                        return JobStatus('error', f'NKI salvo, mas arquivo NKR obrigatorio nao encontrado: {nkr}. Nao mova a biblioteca ate corrigir.')
                    return JobStatus('success', f'NKI criado: {nki}' + (f' | Recursos: {nkr}' if nkr is not None else ''))
            except OSError:
                pass
            return JobStatus('error', 'O Kontakt registrou sucesso, mas o arquivo NKI nao foi encontrado.')
    last = next((ln.split('[Direto]', 1)[-1].strip() for ln in reversed(lines) if '[Direto]' in ln), '')
    return JobStatus('running', last or 'Kontakt em processamento...')
