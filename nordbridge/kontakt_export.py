"""Geração de projeto para NKI REAL via API oficial Lua do Kontakt 8.

O Python prepara Lua + KSP; somente o Kontakt licenciado escreve o .nki.
Não se produz um .nki artificial e não se finge que o arquivo já foi exportado.
"""
from __future__ import annotations

import json
import re
import struct
import zlib
from pathlib import Path

from .fx_natural import build_fx_upgrade


DOC_URL = "https://docs.native-instruments.com/online-guides/kontakt-api-reference-manual/en/introduction-and-setup"


def _lua_quote(value: str) -> str:
    """Strings double-quoted aceitas pelo Lua 5.x, sem injeção de script."""
    value = str(value).replace('\\', '/')
    return '"' + (value.replace('"', '\\"').replace('\n', '\\n')
                .replace('\r', '\\r').replace('\t', '\\t')) + '"'


def _ksp_quote(value: str) -> str:
    """Texto exibido no KSP, sem aspas/linhas que invalidem source."""
    return value.replace('"', "'").replace('\n', ' ').replace('\r', ' ')[:58]


def _filename(value: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', value).strip().rstrip('. ')
    return (cleaned[:75] or 'Meu Instrumento')


def _write_wallpaper(path: Path) -> None:
    """Fundo decorativo PNG 633x260, sem bibliotecas extras."""
    width, height = 633, 260
    pixels = bytearray()
    for y in range(height):
        pixels.append(0)  # PNG filter 0
        for x in range(width):
            fade = y / (height - 1)
            r = int(15 + 17 * fade)
            g = int(22 + 19 * fade)
            b = int(39 + 23 * fade)
            # Faixa vertical em vermelho coral, detalhes sutis em azul.
            if x < 8:
                r, g, b = (230, 66, 88)
            elif 10 < x < 623 and y in (69, 70, 250, 251):
                r, g, b = (47, 77, 106)
            elif y > 237 and ((x - 12) % 24) < 1:
                r, g, b = (46, 55, 74)
            elif 19 < x < 614 and 87 <= y <= 89:
                r, g, b = (42, 59, 80)
            pixels.extend((r, g, b, 255))
    def chunk(kind: bytes, data: bytes) -> bytes:
        return (struct.pack('>I', len(data)) + kind + data
                + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff))
    png = (b'\x89PNG\r\n\x1a\n' +
           chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)) +
           chunk(b'IDAT', zlib.compress(pixels, level=7)) +
           chunk(b'IEND', b''))
    path.write_bytes(png)


def _mapping_rows(doc: dict, folder: Path) -> list[dict]:
    """Agrupa notas vizinhas com a mesma raiz e afinação em zonas contínuas."""
    samples = {}
    for s in doc.get('samples', []):
        if s.get('bank') != 'attack':
            continue
        filename = Path(str(s.get('filename', ''))).name
        wav = (folder / 'Samples' / filename).resolve()
        if not wav.is_file():
            raise FileNotFoundError(f'Sample não encontrado: {wav}')
        root = int(s['root'])
        lo = max(1, int(s['lo_vel']))
        hi = min(127, int(s['hi_vel']))
        if hi < lo:
            continue  # uma faixa exclusiva de velocity MIDI zero é inaudível
        samples.setdefault(root, []).append({'wav': wav, 'root': root, 'layer': int(s['layer']),
                                               'lo_vel': lo, 'hi_vel': hi})
    if not samples:
        raise ValueError('Projeto sem samples de ataque para exportar ao Kontakt')
    keys = sorted(doc.get('keys', []), key=lambda x: int(x['note']))
    chunks = []
    for k in keys:
        note = int(k['note'])
        root = int(k['root'])
        cents = float(k.get('cents', 0.0))
        if not 0 <= note <= 127 or not -3600 <= cents <= 3600 or root not in samples:
            continue
        # O arredondamento evita unir afinações com valores diferentes por engano.
        if chunks and chunks[-1]['root'] == root and chunks[-1]['hi_key'] + 1 == note and chunks[-1]['cents'] == cents:
            chunks[-1]['hi_key'] = note
        else:
            chunks.append({'root': root, 'lo_key': note, 'hi_key': note, 'cents': cents})
    if not chunks:
        raise ValueError('Nenhuma tecla do mapeamento corresponde aos WAVs')
    rows = []
    for chunk in chunks:
        for s in sorted(samples[chunk['root']], key=lambda item: item['layer']):
            rows.append({**s, **chunk})
    return rows


def _ksp_script(name: str) -> str:
    label = _ksp_quote(name)
    return f'''{{ Nord Kontakt Bridge 0.2.2 - painel nativo Kontakt via KSP }}
on init
    message("")
    make_perfview
    set_script_title("NORD BRIDGE | PERFORMANCE")
    set_ui_height_px(190)

    declare ui_label $Nome (6, 1)
    move_control($Nome, 1, 1)
    set_text($Nome, "{label}  |  PERFORMANCE")

    declare ui_knob $Volume (0, 1000000, 1000000)
    move_control($Volume, 1, 3)
    set_text($Volume, "VOLUME")
    $Volume := get_engine_par($ENGINE_PAR_VOLUME, -1, -1, -1)
    make_persistent($Volume)

    declare ui_knob $Dinamica (0, 200, 1)
    move_control($Dinamica, 2, 3)
    set_text($Dinamica, "DINAMICA")
    $Dinamica := 100
    make_persistent($Dinamica)

    declare ui_knob $Tune (-12, 12, 1)
    move_control($Tune, 4, 3)
    set_text($Tune, "TUNE")
    $Tune := 0
    make_persistent($Tune)

    declare ui_knob $Pan (-100, 100, 1)
    move_control($Pan, 5, 3)
    set_text($Pan, "PAN")
    $Pan := 0
    make_persistent($Pan)
    declare $vel_out
end on

on ui_control ($Volume)
    set_engine_par($ENGINE_PAR_VOLUME, $Volume, -1, -1, -1)
end on

on note
    if ($Dinamica # 100)
        $vel_out := 64 + (($EVENT_VELOCITY - 64) * $Dinamica / 100)
        if ($vel_out < 1)
            $vel_out := 1
        end if
        if ($vel_out > 127)
            $vel_out := 127
        end if
        change_velo($EVENT_ID, $vel_out)
    end if
    if ($Tune # 0)
        change_tune($EVENT_ID, $Tune * 100000, 1)
    end if
    if ($Pan # 0)
        change_pan($EVENT_ID, $Pan * 10, 1)
    end if
end on
'''


def build_kontakt_package(project: str | Path, name: str | None = None) -> Path:
    """Prepara scripts para o Kontakt sem tentar gravar NKI fora dele.

    O script gerado cria instrumento, grupos, zonas e script KSP, e solicita ao
    Kontakt salvamento NKI+Samples. Os arquivos originais NÃO são apagados.
    """
    manifest = Path(project).resolve()
    if manifest.is_dir():
        manifest /= 'instrument.json'
    doc = json.loads(manifest.read_text(encoding='utf-8'))
    if doc.get('schema') != 1:
        raise ValueError('instrument.json incompatível')
    folder = manifest.parent
    title = (name or doc.get('name') or 'Meu Piano Nord').strip()
    if not title:
        title = 'Meu Piano Nord'
    export_dir = folder / 'KONTAKT_8'
    export_dir.mkdir(exist_ok=True)
    base = _filename(title)
    chosen = base
    suffix = 2
    # Nunca gerar script que substitui silenciosamente um NKI criado antes.
    while (export_dir / chosen / f'{chosen}.nki').is_file():
        chosen = f'{base}_{suffix}'
        suffix += 1
    dest = export_dir / chosen
    dest.mkdir(exist_ok=True)
    (dest / "Samples").mkdir(exist_ok=True)  # Kontakt: Patch + Samples pode exigir a subpasta
    nki_path = dest / f'{chosen}.nki' 
    ksp_path = export_dir / 'PAINEL_INSTRUMENTO.ksp'
    lua_path = export_dir / 'CRIAR_INSTRUMENTO_NKI.lua'
    log_path = export_dir / 'LOG_EXECUCAO_KONTAKT.txt'
    probe_path = export_dir / 'TESTAR_LUA_KONTAKT.lua'
    rescue_path = export_dir / 'SALVAR_INSTRUMENTO_ABERTO.lua'
    wallpaper = export_dir / 'WALLPAPER.png'
    build_fx_upgrade(export_dir, title)
    _write_wallpaper(wallpaper)
    ksp_path.write_text(_ksp_script(title), encoding='utf-8')
    rows = _mapping_rows(doc, folder)
    lines = [
        '-- Criado por Nord Kontakt Bridge 0.2.2. Execute SOMENTE no Kontakt 8 completo.',
        '-- ATENCAO: o Kontakt cria e salva o .nki; Python nao grava arquivo .nki.',
        'local K = Kontakt',
        'local log_file = ' + _lua_quote(log_path.as_posix()),
        'local function log(msg)',
        '    local line = "[Nord Bridge] " .. tostring(msg)',
        '    print(line)',
        '    local fh = io.open(log_file, "a")',
        '    if fh then fh:write(os.date("%Y-%m-%d %H:%M:%S") .. " " .. line .. "\\n"); fh:close() end',
        'end',
        'local function main()',
        'log("INICIANDO. Se nao apareceu instrumento, consulte o arquivo LOG_EXECUCAO_KONTAKT.txt")',
        'assert(type(K) == "table", "A API Kontakt nao esta habilitada. Ative Options > Developer.")',
        'local target_file = ' + _lua_quote(nki_path.as_posix()),
        'local target_dir = ' + _lua_quote(dest.as_posix()),
        'local samples_dir = ' + _lua_quote((dest / 'Samples').as_posix()),
        'local script_file = ' + _lua_quote(ksp_path.as_posix()),
        'local wallpaper_file = ' + _lua_quote(wallpaper.as_posix()),
        'log("Criando instrumento")',
        'local inst = K.add_instrument()',
        'assert(inst ~= nil, "Nao foi possivel criar instrumento Kontakt")',
        'K.set_instrument_name(inst, ' + _lua_quote(title) + ')',
        'K.set_instrument_midi_channel(inst, 0)',
        'K.set_instrument_polyphony(inst, 96)',
        '-- Opcional: papel de parede personalizado. Falha nao impede NKI.',
        'local skin_ok, skin_err = pcall(K.set_instrument_options, inst, {wallpaper=wallpaper_file})',
        'if not skin_ok then print("Aviso: wallpaper nao aplicado: " .. tostring(skin_err)) end',
        'log("Criando grupo de samples")',
        'local group = K.add_group(inst)',
        'assert(group ~= nil, "Nao foi possivel criar grupo")',
        'K.set_group_name(inst, group, "Nord Piano - ataque")',
        'K.set_group_playback_mode(inst, group, "sampler")',
        'local zones = {',
    ]
    for row in rows:
        lines.append('    {' + ', '.join([
            'sample=' + _lua_quote(row['wav'].as_posix()),
            'root=' + str(row['root']),
            'lo=' + str(row['lo_key']),
            'hi=' + str(row['hi_key']),
            'vlo=' + str(row['lo_vel']),
            'vhi=' + str(row['hi_vel']),
            'tune=' + f'{row["cents"] / 100.0:.5f}',
        ]) + '},')
    lines.extend([
        '}',
        'log("Adicionando " .. #zones .. " zonas. Para pianos grandes pode demorar.")',
        'for i, z in ipairs(zones) do',
        '    local zi = K.add_zone(inst, group, z.sample)',
        '    assert(zi ~= nil, "Erro ao adicionar WAV: " .. z.sample)',
        '    K.set_zone_geometry(inst, zi, {',
        '        root_key=z.root, low_key=z.lo, high_key=z.hi,',
        '        low_velocity=z.vlo, high_velocity=z.vhi',
        '    })',
        '    if z.tune ~= 0 then K.set_zone_tune(inst, zi, z.tune) end',
        '    if i % 50 == 0 then log("Zonas carregadas: " .. i .. "/" .. #zones) end',
        'end',
        '-- Script KSP alimenta a interface do instrumento ao abrir .nki.',
        'log("Montando painel KSP")',
        'K.set_instrument_script_source(inst, 0, script_file)',
        '-- A API salva no caminho existente. Alguns sistemas requerem diretorio Samples ja criado.',
        'log("VERIFICANDO DESTINO: " .. target_dir)',
        'if type(Filesystem) == "table" and type(Filesystem.exists) == "function" then',
        '    assert(Filesystem.exists(target_dir), "Pasta de destino ausente: " .. target_dir)',
        '    log("Diretorio confirmado pelo Kontakt")',
        'end',
        'local probe_path = target_dir .. "/.nord_bridge_write_test"',
        'local probe, probe_err = io.open(probe_path, "wb")',
        'assert(probe, "Sem permissao para gravar no destino: " .. tostring(probe_err))',
        'probe:close(); os.remove(probe_path)',
        '-- Omite samples_sub_dir: assim Kontakt usa a subpasta padrao.',
        'log("SALVANDO NKI (Patch + Samples). Nao feche o Kontakt: " .. target_file)',
        'local saved, save_err = pcall(K.save_instrument, inst, target_file, {mode="samples", compress_samples=false})',
        'if saved then',
        '    log("SALVAMENTO SOLICITADO: Patch + Samples")',
        'else',
        '    log("FALHA Patch + Samples: " .. tostring(save_err))',
        '    log("TENTANDO PATCH ONLY com caminhos absolutos para preservar o instrumento")',
        '    local patch_ok, patch_err = pcall(K.save_instrument, inst, target_file, {mode="patch", absolute_paths=true})',
        '    if patch_ok then',
        '        log("SALVO PATCH ONLY: os WAVs continuam na pasta original; NAO mova os samples.")',
        '        log("Abra o NKI e use Save As > Patch + Samples para torná-lo portatil.")',
        '    else',
        '        error("Falharam ambos os salvamentos. Samples: " .. tostring(save_err) .. " | Patch: " .. tostring(patch_err))',
        '    end',
        'end',
        'local f = io.open(target_file, "rb")',
        'if f then f:close(); log("SUCESSO: arquivo NKI encontrado em " .. target_file)',
        'else log("AVISO: NKI nao apareceu no destino apos tentativa de salvar.") end',
        'end',
        'local ok, err = xpcall(main, function(e) return debug and debug.traceback(e, 2) or tostring(e) end)',
        'if not ok then log("ERRO: " .. tostring(err)); print("ERRO AO CRIAR NKI: " .. tostring(err)) end',
    ])
    lua_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    probe_path.write_text('\n'.join([
        '-- Teste minimalista para confirmar a API Lua do Kontakt 8.9.0',
        'local log_file = ' + _lua_quote(log_path.as_posix()),
        'local f = io.open(log_file, "a")',
        'if f then f:write("\\nTESTE LUA - iniciado\\n"); f:close() end',
        'local ok, err = pcall(function()',
        '  assert(type(Kontakt) == "table", "API Kontakt indisponivel")',
        '  local inst = Kontakt.add_instrument()',
        '  assert(inst ~= nil, "add_instrument retornou nil")',
        '  Kontakt.set_instrument_name(inst, "TESTE LUA - NORD BRIDGE")',
        '  print("TESTE LUA OK - instrumento adicionado ao rack")',
        'end)',
        'local g = io.open(log_file, "a")',
        'if g then g:write(ok and "TESTE LUA - SUCESSO\\n" or ("TESTE LUA - ERRO: " .. tostring(err) .. "\\n")); g:close() end',
        'if not ok then print("TESTE LUA - ERRO: " .. tostring(err)) end',
        '',
    ]), encoding='utf-8')
    # Salvamento do instrumento JA CRIADO no Kontakt: evita reimportar centenas de zonas.
    rescue = [
        '-- Nord Kontakt Bridge 0.2.2: recuperacao para instrumento existente no rack.',
        '-- NAO cria outro instrumento e NAO importa WAVs novamente.',
        'local K = Kontakt',
        'local title = ' + _lua_quote(title),
        'local target_file = ' + _lua_quote(nki_path.as_posix()),
        'local target_dir = ' + _lua_quote(dest.as_posix()),
        'local log_file = ' + _lua_quote(log_path.as_posix()),
        'local function log(s)',
        '  local msg = "[Resgate NKI] " .. tostring(s)',
        '  print(msg)',
        '  local f = io.open(log_file, "a")',
        '  if f then f:write(os.date("%Y-%m-%d %H:%M:%S") .. " " .. msg .. "\\n"); f:close() end',
        'end',
        'local function run()',
        '  local idx = nil',
        '  for _, id in ipairs(K.get_instrument_indices()) do',
        '    if K.get_instrument_name(id) == title then idx = id end',
        '  end',
        '  assert(idx ~= nil, "Instrumento ' + _filename(title).replace('"', '') + ' nao esta aberto no Kontakt. Execute o script principal.")',
        '  log("Encontrado instrumento indice " .. idx .. ": " .. title)',
        '  if type(Filesystem) == "table" and type(Filesystem.exists) == "function" then',
        '    assert(Filesystem.exists(target_dir), "Pasta de destino ausente: " .. target_dir)',
        '  end',
        '  local w, err = io.open(target_dir .. "/.nord_bridge_write_test", "wb")',
        '  assert(w, "Pasta sem permissao de gravacao: " .. tostring(err))',
        '  w:close(); os.remove(target_dir .. "/.nord_bridge_write_test")',
        '  log("Tentando Patch + Samples (pasta Samples ja criada pelo app)")',
        '  local ok, e = pcall(K.save_instrument, idx, target_file, {mode="samples", compress_samples=false})',
        '  if not ok then',
        '    log("Patch + Samples falhou: " .. tostring(e))',
        '    log("Tentando Patch Only com caminhos absolutos")',
        '    local ok2, e2 = pcall(K.save_instrument, idx, target_file, {mode="patch", absolute_paths=true})',
        '    assert(ok2, "Patch Only falhou: " .. tostring(e2))',
        '    log("PATCH ONLY SALVO: mantenha WAVs na pasta de origem, ou Save As > Patch + Samples")',
        '  end',
        '  local f = io.open(target_file, "rb")',
        '  if f then f:close(); log("SUCESSO: arquivo NKI: " .. target_file)',
        '  else log("ERRO: API retornou sem erro, mas arquivo NKI nao foi localizado") end',
        'end',
        'local ok, err = xpcall(run, function(e) return debug and debug.traceback(e,2) or tostring(e) end)',
        'if not ok then log("ERRO: " .. tostring(err)) end',
    ]
    rescue_path.write_text("\n".join(rescue) + "\n", encoding="utf-8")
    # Arquivos executados localmente pelo Windows para ver os logs e os arquivos do projeto.
    bat_logs = export_dir / 'ABRIR_LOG_DO_KONTAKT.bat'
    bat_logs.write_text('@echo off\r\nsetlocal\r\nif exist "%~dp0LOG_EXECUCAO_KONTAKT.txt" (\r\n  notepad "%~dp0LOG_EXECUCAO_KONTAKT.txt"\r\n) else (\r\n  echo O log ainda nao existe. Execute F11 no Kontakt com TESTAR_LUA_KONTAKT.lua.\r\n  pause\r\n)\r\n', encoding='utf-8')
    bat = export_dir / 'ABRIR_NO_KONTAKT_8.bat'
    bat.write_text('''@echo off\nsetlocal\nset "KONTAKT=%ProgramFiles%\\Native Instruments\\Kontakt 8\\Kontakt 8.exe"\nif not exist "%KONTAKT%" (\n  echo Kontakt 8 nao encontrado no caminho padrao.\n  echo Abra Kontakt 8 completo e pressione F11, selecionando:\n  echo "%~dp0CRIAR_INSTRUMENTO_NKI.lua"\n  pause\n  exit /b 1\n)\necho Iniciando Kontakt 8 com script de criacao NKI...\necho Se ja estiver aberto, execute F11 dentro do Kontakt.\nstart "" "%KONTAKT%" "%~dp0CRIAR_INSTRUMENTO_NKI.lua"\n''', encoding='utf-8')
    guide = export_dir / 'LEIA_COMO_CRIAR_NKI.txt'
    guide.write_text(f'''NORD KONTAKT BRIDGE 0.3.0 - EXPORTAR NKI REAL

Timbre: {title}
Zonas geradas: {len(rows)}

1. Precisa do KONTAKT 8 COMPLETO (o Kontakt Player pode usar modo demo).
2. Abra Kontakt 8 STANDALONE (nao o plugin VST dentro do DAW), e ative
   Options > Developer > Enable Developer Features.
3. Primeiramente pressione F11 e selecione TESTAR_LUA_KONTAKT.lua.
   Deve aparecer um instrumento TESTE LUA - NORD BRIDGE.
   Verifique LOG_EXECUCAO_KONTAKT.txt na pasta KONTAKT_8.
4. Agora pressione F11 (Run Lua script...) e selecione:
   {lua_path}
   Como alternativa, feche o Kontakt e execute ABRIR_NO_KONTAKT_8.bat.
5. O script monta um instrumento com notas/camadas e interface KSP.
6. O proprio Kontakt tentara gravar o NKI em:
   {nki_path}
   Verifique que existem tanto .NKI quanto a pasta Samples.
7. Abra o NKI salvo no Kontakt 8 e teste o teclado, a dinamica e os controles.

RESGATAR SEM REIMPORTAR 694 ZONAS:
Se o instrumento ja foi criado mas falhou no salvamento, MANTENHA O KONTAKT
ABERTO e execute via F11: SALVAR_INSTRUMENTO_ABERTO.lua.
Ele busca o instrumento pelo nome, tenta Patch + Samples e se falhar
salva como Patch Only com caminhos absolutos. O log registra o resultado.
Se o Kontakt ja foi fechado, execute o script principal normalmente.

Se o NKI foi salvo em Patch Only, nao mova a pasta original Samples;
para tornar o timbre portatil, salve outra vez pelo Kontakt com Patch + Samples.

INTERFACE: VOLUME, DINAMICA, TUNE e PAN. O painel e gerado por KSP;
a aparencia corresponde aos widgets padrao da sua versao de Kontakt.
O script de automacao pode requerer ajustes dependendo da sua versao.

Se nao surgir o .NKI, abra LOG_EXECUCAO_KONTAKT.txt com ABRIR_LOG_DO_KONTAKT.bat.
Nao volte a converter o .npno: utilize o instrument.json original.
O Lua pode demorar para importar muitas zonas e WAVs. Aguarde finalizar a mensagem SALVANDO NKI.
Nao renomeie .lua/.sfz para .nki: apenas Kontakt pode gerar um NKI valido.
Nao e possivel testar o Kontakt a partir do ambiente onde o projeto foi criado.

LIMITACOES: samples release/pedal, resonancias e curvas Nord proprietarias
nao sao recriados; o resultado pode soar diferente do teclado Nord.

Documentacao oficial: {DOC_URL}
''', encoding='utf-8')
    return export_dir
