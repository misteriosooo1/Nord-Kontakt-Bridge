"""Exportação Kontakt 8 via Lua com WAVs locais e patch referenciado.

O Python copia os WAVs de forma segura para Samples ANTES do Kontakt iniciar.
O Kontakt importa somente caminhos de samples que ja existem e salva o NKI.
"""
from __future__ import annotations

import json
import uuid
import shutil
import os
from dataclasses import dataclass
from pathlib import Path

from .kontakt_export import _filename, _ksp_script, _lua_quote, _mapping_rows
from .visual_assets import VisualPack, create_visual_pack, add_visual_ksp, add_button_graphic_ksp, make_library_manager_pack
from .default_fx import build_default_fx_ksp
from .nkr_templates import find_local_template
from .fx_designer import FXDesign, install_fx_graphics, design_ksp, save_design, preview_page, validate_fx_design
from .ksp_validation import require_valid_ksp


@dataclass(frozen=True)
class DirectExport:
    nki: Path
    lua: Path
    log: Path
    source_ksp: Path
    zones: int
    artwork: VisualPack | None = None
    samples_dir: Path | None = None
    sample_count: int = 0


def build_direct_export(manifest: Path, output_dir: Path, title: str, *,
                        ksp_source: Path | None = None,
                        wallpaper: Path | None = None, icon: Path | None = None,
                        cover: Path | None = None, use_default_visuals: bool = False, auto_fx: bool = True,
                        nkr_template: Path | None = None, fit_mode: str = 'cover',
                        button_image: Path | None = None, button_text: str = 'REDEFINIR',
                        button_style: str = 'Nord Red', prepare_library_manager: bool = True,
                        fx_design: FXDesign | None = None) -> DirectExport:
    """Prepara os WAVs locais e gera Lua para criar NKI referenciando Samples.

    Somente o Kontakt cria o NKI, mas o aplicativo ja prepara os WAVs.
    """
    manifest = Path(manifest).resolve()
    output_dir = Path(output_dir).resolve()
    if not manifest.is_file():
        raise FileNotFoundError(f'Manifesto ausente: {manifest}')
    doc = json.loads(manifest.read_text(encoding='utf-8'))
    if doc.get('schema') != 1:
        raise ValueError('Manifesto Nord Bridge incompatível.')
    # Parametros invalidos sao detectados antes de copiar centenas de WAVs.
    if auto_fx and fx_design is not None and fx_design.enabled:
        validate_fx_design(fx_design)
    rows = _mapping_rows(doc, manifest.parent)
    output_dir.mkdir(parents=True, exist_ok=True)
    base = _filename(title.strip() or doc['name'])
    name = base
    idx = 2
    # Cada timbre possui pasta propria para evitar colisao de nomes de WAVs.
    while (output_dir / name).exists() or (output_dir / f'{name}.nki').exists():
        name = f'{base} ({idx})'
        idx += 1
    output_dir = output_dir / name
    output_dir.mkdir(parents=True, exist_ok=False)
    nki = output_dir / f'{name}.nki'
    sample_dir = output_dir / 'Samples'
    sample_dir.mkdir(parents=True, exist_ok=True)
    # Nunca depender de o Kontakt criar/copyar a subpasta Samples: ele pode
    # devolver "path doesn't exist" no modo samples quando ela nao existe.
    # Copiamos em streaming e fazemos rename atomico para evitar WAV parcial.
    # O NKI sempre utiliza esses arquivos ja presentes no destino.
    source_samples: dict[str, Path] = {}
    for row in rows:
        source = Path(row['wav']).resolve()
        existing = source_samples.get(source.name)
        if existing is not None and existing != source:
            raise ValueError('Samples diferentes possuem mesmo nome: ' + source.name)
        source_samples[source.name] = source
    for filename, source in sorted(source_samples.items()):
        target = sample_dir / filename
        if not source.is_file() or source.stat().st_size <= 44:
            raise FileNotFoundError('WAV ausente ou incompleto no cache: ' + str(source))
        # So reaproveita WAV final se sua assinatura de tamanho coincidir.
        if target.is_file() and target.stat().st_size == source.stat().st_size:
            continue
        temp = target.with_name(target.name + '.nkb-part')
        try:
            with source.open('rb') as inp, temp.open('wb') as dest:
                shutil.copyfileobj(inp, dest, length=1024 * 1024)
                dest.flush()
                os.fsync(dest.fileno())
            if temp.stat().st_size != source.stat().st_size:
                raise OSError('A copia ficou incompleta: ' + filename)
            os.replace(temp, target)
        finally:
            if temp.exists():
                temp.unlink()
    unique_samples = sorted(source_samples)
    staged_rows = [{**row, 'wav': sample_dir / Path(row['wav']).name} for row in rows]
    if not all((sample_dir / name).is_file() and (sample_dir / name).stat().st_size > 44 for name in unique_samples):
        raise RuntimeError('Nem todos os WAVs estao disponiveis na pasta Samples.')
    # Tudo que pertence ao instrumento (Lua, KSP, log) viaja com ele.
    # O cache continua contendo SOMENTE a decodificacao reutilizavel.
    work = output_dir
    lua = output_dir / f'CRIAR_NKI_{name}.lua'
    log = output_dir / f'LOG_KONTAKT_{name}.txt'
    ksp = output_dir / f'PAINEL_KONTAKT_{name}.ksp'
    temporary_setup = output_dir / f'._NKB_SETUP_{uuid.uuid4().hex[:12]}.nki'
    write_probe = output_dir / f'._NKB_WRITE_TEST_{uuid.uuid4().hex[:12]}.tmp'
    artwork = create_visual_pack(output_dir, name, wallpaper=wallpaper, icon=icon, cover=cover,
                                 use_defaults=(use_default_visuals or (auto_fx and fx_design is not None and fx_design.enabled)), fx_panel=auto_fx,
                                 fit_mode=fit_mode, button_image=button_image,
                                 button_text=button_text, button_style=button_style)
    if fx_design is not None and fx_design.enabled and auto_fx and artwork is not None:
        install_fx_graphics(artwork, fx_design)
        save_design(fx_design, output_dir / 'DESIGN_FX.json')
        # Prévia PNG em tamanho nativo, sem precisar executar Kontakt.
        from PIL import Image
        with Image.open(artwork.pictures/(artwork.wallpaper_name + '.png')) as full:
            preview_page(full,fx_design,'FX').save(output_dir/'PREVIA_FX.png')
            preview_page(full,fx_design,'PIANO').save(output_dir/'PREVIA_PIANO.png')
    if artwork:
        # Metodo automatico: reutilizar um NKR real criado anteriormente pelo Kontakt.
        # A pasta Resources/pictures ao lado do novo NKR prevalece sobre os dados
        # antigos dentro do monolith, conforme documentacao oficial NI.
        template = find_local_template(output_dir, nkr_template)
        if template and template.resolve() != artwork.nkr.resolve():
            shutil.copy2(template, artwork.nkr)
        if template:
            (work / f'MODELO_NKR_{name}.txt').write_text(
                f'Modelo NKR reutilizado automaticamente: {template}\nDestino: {artwork.nkr}\n',
                encoding='utf-8')
        assets = [artwork.wallpaper_name, artwork.icon_name, artwork.button_name]
        if fx_design is not None and fx_design.enabled and auto_fx:
            assets.extend([artwork.wallpaper_name+'_KNOB', artwork.wallpaper_name+'_TAB_PIANO', artwork.wallpaper_name+'_TAB_FX'])
        for img in assets:
            for suffix in ('.png', '.txt'):
                resource_file = artwork.pictures / (img + suffix)
                if not resource_file.is_file() or resource_file.stat().st_size == 0:
                    raise RuntimeError(f'Recurso grafico ausente antes de iniciar Kontakt: {resource_file}')
    make_library_manager_pack(output_dir, name, artwork.cover if artwork else None,
                              prepare=prepare_library_manager)
    if ksp_source is not None:
        custom = Path(ksp_source).resolve()
        if not custom.is_file() or custom.suffix.lower() != '.ksp':
            raise ValueError('Selecione um script KSP existente.')
        custom_text = custom.read_text(encoding='utf-8-sig')
    else:
        custom_text = None
    # O painel de efeitos e o modelo padrao sao verificados ANTES de chamar o Kontakt.
    ksp_text = build_default_fx_ksp(name) if auto_fx else (custom_text or _ksp_script(name))
    if fx_design is not None and fx_design.enabled and auto_fx and artwork is not None:
        visual_ksp = design_ksp(add_button_graphic_ksp(ksp_text, artwork), artwork, fx_design)
    else:
        visual_ksp = add_visual_ksp(add_button_graphic_ksp(ksp_text, artwork), artwork, include_wallpaper=False)
    require_valid_ksp(visual_ksp, 'Painel FX gerado')
    require_valid_ksp(ksp_text, 'Painel de contingencia')
    if custom_text is not None:
        require_valid_ksp(custom_text, 'KSP personalizado')
    ksp.write_text(visual_ksp, encoding='utf-8')
    # Reserva um KSP sem referencias graficas para quando a API nao criar o NKR.
    # Isso impede que o NKI final fique referenciando imagens/conteudo ausentes.
    fallback_ksp = work / f'PAINEL_SEM_NKR_{name}.ksp' if artwork else None
    if fallback_ksp is not None:
        fallback_ksp.write_text(ksp_text, encoding='utf-8')
    custom_ksp = None
    if auto_fx and custom_text:
        # KSP personalizado em outro slot, preservando sempre os FX padrão.
        custom_ksp = work / f'PERSONALIZADO_{name}.ksp'
        custom_ksp.write_text(custom_text, encoding='utf-8')

    lines = [
        '-- NORD KONTAKT BRIDGE NORD RED v0.6.4 | KSP com fallback de importacao por texto',
        '-- Este arquivo e executado pela API Lua do Kontakt 8 completo.',
        '-- O Python coloca os WAVs no destino antes da abertura do Kontakt.',
        'local K = Kontakt',
        'local log_path = ' + _lua_quote(log.as_posix()),
        'local nki_path = ' + _lua_quote(nki.as_posix()),
        'local samples_path = ' + _lua_quote(sample_dir.as_posix()),
        'local expected_samples = {' + ', '.join(_lua_quote(x) for x in unique_samples) + '}',
        'local ksp_path = ' + _lua_quote(ksp.as_posix()),
        *(['local fallback_ksp_path = ' + _lua_quote(fallback_ksp.as_posix())] if fallback_ksp else []),
        'local graphics_ok = true',
        'local function log(msg)',
        '  local line = os.date("%Y-%m-%d %H:%M:%S") .. " [Direto] " .. tostring(msg)',
        '  print(line)',
        '  local f = io.open(log_path, "a")',
        '  if f then f:write(line .. "\\n"); f:close() end',
        'end',
        'log("LUA INICIADO no Kontakt: Samples ja preparados no destino")',
        'local function main()',
        '  assert(type(K) == "table", "API Lua nao disponivel. Ative Developer Options no Kontakt 8 completo")',
        '  local fh = io.open(nki_path, "rb")',
        '  if fh then fh:close(); error("NKI ja existe. Nao sobrescrevi: " .. nki_path) end',
        '  log("CRIANDO INSTRUMENTO")',
        '  local inst = K.add_instrument()',
        '  assert(inst ~= nil, "Nao foi possivel adicionar instrumento")',
        '  K.set_instrument_name(inst, ' + _lua_quote(name) + ')',
        '  K.set_instrument_midi_channel(inst, 0)',
        '  K.set_instrument_polyphony(inst, 96)',
        '  local group = K.add_group(inst)',
        '  assert(group ~= nil, "Falha ao criar grupo")',
        '  K.set_group_name(inst, group, "Nord Piano - ataque")',
        '  K.set_group_playback_mode(inst, group, "sampler")',
        '  local zones = {',
    ]
    for row in staged_rows:
        lines.append('    {' + ', '.join([
            'sample=' + _lua_quote(row['wav'].as_posix()),
            'root=' + str(int(row['root'])),
            'lo=' + str(int(row['lo_key'])),
            'hi=' + str(int(row['hi_key'])),
            'vlo=' + str(int(row['lo_vel'])),
            'vhi=' + str(int(row['hi_vel'])),
            'tune=' + f'{float(row["cents"]) / 100.0:.5f}',
        ]) + '},')
    lines.extend([
        '  }',
        '  -- Checagem antes de instanciar as zonas: nao iniciar com WAVs ausentes.',
        '  for _, file in ipairs(expected_samples) do',
        '    local f = io.open(samples_path .. "/" .. file, "rb")',
        '    assert(f, "SAMPLE AUSENTE ANTES DA IMPORTACAO: " .. samples_path .. "/" .. file)',
        '    f:close()',
        '  end',
        '  log("SAMPLES LOCAIS VALIDOS: " .. #expected_samples)',
        '  log("ZONAS: " .. #zones)', 
        '  for i, zone in ipairs(zones) do',
        '    local zi = K.add_zone(inst, group, zone.sample)',
        '    assert(zi ~= nil, "Nao foi possivel importar: " .. zone.sample)',
        '    K.set_zone_geometry(inst, zi, {root_key=zone.root, low_key=zone.lo, high_key=zone.hi, low_velocity=zone.vlo, high_velocity=zone.vhi})',
        '    if zone.tune ~= 0 then K.set_zone_tune(inst, zi, zone.tune) end',
        '    if i % 50 == 0 then log("ZONAS IMPORTADAS: " .. i .. "/" .. #zones) end',
        '  end',
        *([
            '  log("PREPARANDO RECURSOS GRAFICOS")',
            '  local setup_path = ' + _lua_quote(temporary_setup.as_posix()),
            '  local probe_path = ' + _lua_quote(write_probe.as_posix()),
            '  local probe, probe_err = io.open(probe_path, "wb")',
            '  assert(probe, "FALHA DE GRAVACAO NA PASTA DE DESTINO: " .. tostring(probe_err))',
            '  probe:write("teste"); probe:close(); os.remove(probe_path)',
            '  log("GRAVACAO NA PASTA: OK")',
            '  log("SALVANDO PATCH TEMPORARIO ANTES DO RESOURCE CONTAINER: " .. setup_path)',
            '  K.save_instrument(inst, setup_path, {mode="patch", absolute_paths=true})',
            '  local sf = io.open(setup_path, "rb")',
            '  assert(sf, "NAO FOI POSSIVEL SALVAR PATCH TEMPORARIO")',
            '  sf:close()',

            '  local nkr_path = ' + _lua_quote(artwork.nkr.as_posix()),
            '  local function nkr_exists()',
            '    local file = io.open(nkr_path, "rb")',
            '    if not file then return false end',
            '    local size = file:seek("end")',
            '    file:close()',
            '    return size ~= nil and size > 0',
            '  end',
            '  if nkr_exists() then',
            '    log("NKR EXISTENTE: vinculando " .. nkr_path)',
            '    local linked, reason = pcall(K.link_resource_container, inst, nkr_path)',
            '    graphics_ok = linked and nkr_exists()',
            '    if not graphics_ok then log("AVISO NKR: vinculacao falhou: " .. tostring(reason)) end',
            '  else',
            '    log("NKR AUSENTE: solicitando criacao " .. nkr_path)',
            '    local created, reason = pcall(K.create_resource_container, inst, nkr_path)',
            '    graphics_ok = created and nkr_exists()',
            '    if not graphics_ok then log("AVISO NKR: API nao criou o arquivo. Detalhe Lua: " .. tostring(reason)) end',
            '  end',
            '  if graphics_ok then',
            '    log("NKR CONFIRMADO: " .. nkr_path)',
            '  else',
            '    -- Importante: nao salvar o instrumento que tentou associar um NKR ausente.',
            '    -- A API pode ter registrado uma referencia incompleta. Remontar um instrumento limpo.',
            '    log("RECRIANDO INSTRUMENTO LIMPO: evitando Content Missing e preservando a conversao")',
            '    K.remove_instrument(inst)',
            '    inst = K.add_instrument()',
            '    assert(inst ~= nil, "Falha ao recriar instrumento limpo")',
            '    K.set_instrument_name(inst, ' + _lua_quote(name) + ')',
            '    K.set_instrument_midi_channel(inst, 0)',
            '    K.set_instrument_polyphony(inst, 96)',
            '    group = K.add_group(inst)',
            '    assert(group ~= nil, "Falha ao criar grupo limpo")',
            '    K.set_group_name(inst, group, "Nord Piano - ataque")',
            '    K.set_group_playback_mode(inst, group, "sampler")',
            '    for i, zone in ipairs(zones) do',
            '      local zi = K.add_zone(inst, group, zone.sample)',
            '      assert(zi ~= nil, "Falha ao reimportar: " .. zone.sample)',
            '      K.set_zone_geometry(inst, zi, {root_key=zone.root, low_key=zone.lo, high_key=zone.hi, low_velocity=zone.vlo, high_velocity=zone.vhi})',
            '      if zone.tune ~= 0 then K.set_zone_tune(inst, zi, zone.tune) end',
            '    end',
            '    log("PAINEL GRAFICO ADIADO: NKI tera efeitos e controles nativos, sem vinculo a NKR faltante")',
            '  end',
        ] if artwork else []),
        '  -- Importar o KSP a partir do ARQUIVO, nunca apenas colar seu caminho no Script Editor.',
        '  -- A API pode nao gerar excecao mesmo que o slot nao aceite o script.',
        '  -- Por isso mostramos a resposta real e tentamos o KSP sem imagens, se necessario.',
        '  local function instalar_ksp(slot, arquivo, titulo)',
        '    local f, err = io.open(arquivo, "rb")',
        '    if not f then return false, "ARQUIVO KSP AUSENTE: " .. tostring(err) end',
        '    local codigo = f:read("*a")',
        '    f:close()',
        '    codigo = codigo:gsub("^" .. string.char(239,187,191), "")',
        '    if not (codigo:find("on init", 1, true) and codigo:find("end on", 1, true)) then',
        '      return false, "KSP NAO TEM BLOCOS INIT/END: " .. arquivo',
        '    end',
        '    log("IMPORTANDO KSP: slot=" .. slot .. " arquivo=" .. arquivo .. " bytes=" .. #codigo)',
        '    -- Alguns builds do Kontakt podem guardar o caminho como TEXTO no slot.',
        '    -- Tentamos primeiro o caminho da API documentada. Se o conteudo devolvido',
        '    -- nao corresponder ao codigo KSP, tentamos enviar o texto completo.',
        '    local function verificar_fonte(metodo)',
        '      local lido, texto = pcall(K.get_instrument_script_source, inst, slot)',
        '      local tam = (lido and type(texto) == "string") and #texto or 0',
        '      local trecho = (type(texto) == "string") and texto:sub(1, 180):gsub("%s+", " ") or tostring(texto)',
        '      log("KSP RETORNO API [" .. metodo .. "]: leitura=" .. tostring(lido) .. " tipo=" .. type(texto) .. " bytes=" .. tam .. " trecho=" .. tostring(trecho))',
        '      if not lido or type(texto) ~= "string" then return false end',
        '      local normalizado = texto:gsub("\\r\\n", "\\n"):gsub("\\r", "\\n")',
        '      local esperado = codigo:gsub("\\r\\n", "\\n"):gsub("\\r", "\\n")',
        '      -- Igualdade do codigo completo: impede aprovar apenas texto ou filepath.',
        '      if normalizado == esperado then return true end',
        '      -- Alguns builds alteram a linha final. Verifique blocos e tamanho aproximado.',
        '      return #normalizado > 500 and math.abs(#normalizado - #esperado) < 30 and',
        '        normalizado:find("on init", 1, true) ~= nil and normalizado:find("end on", 1, true) ~= nil',
        '    end',
        '    local ok, resposta = pcall(K.set_instrument_script_source, inst, slot, arquivo)',
        '    log("KSP RESPOSTA ENVIO [CAMINHO]: chamada=" .. tostring(ok) .. " retorno=" .. tostring(resposta))',
        '    local confirmado = verificar_fonte("CAMINHO")',
        '    if not confirmado then',
        '      log("KSP CAMINHO NAO IMPORTOU O CODIGO; TENTANDO FONTE COMPLETA NO SLOT")',
        '      local ok_texto, resposta_texto = pcall(K.set_instrument_script_source, inst, slot, codigo)',
        '      log("KSP RESPOSTA ENVIO [TEXTO]: chamada=" .. tostring(ok_texto) .. " retorno=" .. tostring(resposta_texto))',
        '      confirmado = verificar_fonte("TEXTO")',
        '    end',
        '    if not confirmado then',
        '      return false, "CODIGO KSP NAO INSTALADO. A API nao confirmou nem caminho nem texto; consulte KSP RETORNO API no log e erros do compilador no terminal"',
        '    end',
        '    if titulo then K.set_instrument_script_name(inst, slot, titulo) end',
        '    log("KSP IMPORTADO E TEXTO PRESENTE NO SLOT " .. slot)',
        '    return true, "OK"',
        '  end',
        '  log("INSTALANDO KSP")',
        *(['  if graphics_ok then',
           '    local ok_fx, err_fx = instalar_ksp(0, ksp_path, "NORD | FX NATURAL")',
           '    if not ok_fx then',
           '      log("KSP COM ICONE FALHOU: " .. tostring(err_fx))',
           '      log("TENTATIVA AUTOMATICA DE PAINEL SEM REFERENCIAS GRAFICAS")',
           '      local ok_basico, err_basico = instalar_ksp(0, fallback_ksp_path, "NORD | FX NATURAL")',
           '      assert(ok_basico, "PAINEL FX NAO FOI IMPORTADO. COM ICONE: " .. tostring(err_fx) .. " | SEM ICONE: " .. tostring(err_basico) .. " | Confira o terminal do Kontakt para erros de compilacao")',
           '    end',
           '  else',
           '    local ok_basico, err_basico = instalar_ksp(0, fallback_ksp_path, "NORD | FX NATURAL")',
           '    assert(ok_basico, "PAINEL FX BASICO NAO FOI IMPORTADO: " .. tostring(err_basico) .. " | Confira o terminal do Kontakt")',
           '  end'] if artwork else [
           '  local ok_basico, err_basico = instalar_ksp(0, ksp_path, "NORD | FX NATURAL")',
           '  assert(ok_basico, "PAINEL FX NAO FOI IMPORTADO: " .. tostring(err_basico) .. " | Confira o terminal do Kontakt")']),
        *(['  log("INSTALANDO KSP PERSONALIZADO NO SLOT 2")',
           '  local ok_custom, err_custom = instalar_ksp(1, ' + _lua_quote(custom_ksp.as_posix()) + ', "PERSONALIZADO")',
           '  assert(ok_custom, "KSP PERSONALIZADO NAO FOI IMPORTADO: " .. tostring(err_custom))'] if custom_ksp else []),

        *([
            '  -- API Lua oficial: o Instrument Wallpaper nao precisa depender do KSP/NKR.',
            '  -- O PNG permanece no destino, ao lado do NKI em Resources/pictures.',
            '  local wallpaper_path = ' + _lua_quote((artwork.pictures / (artwork.wallpaper_name + '.png')).as_posix()),
            '  local imagem = io.open(wallpaper_path, "rb")',
            '  assert(imagem, "WALLPAPER PNG AUSENTE: " .. wallpaper_path)',
            '  imagem:close()',
            '  local ok_wall, err_wall = pcall(K.set_instrument_options, inst, {wallpaper=wallpaper_path})',
            '  if ok_wall then',
            '    local ok_info, opt = pcall(K.get_instrument_options, inst)',
            '    if ok_info and type(opt) == "table" then',
            '      log("WALLPAPER APLICADO VIA API, VALOR LIDO: " .. tostring(opt.wallpaper))',
            '    else',
            '      log("WALLPAPER APLICADO VIA API (consulta de opcoes indisponivel)")',
            '    end',
            '  else',
            '    log("AVISO WALLPAPER: API rejeitou imagem: " .. tostring(err_wall))',
            '  end',
        ] if artwork else []),
        '  log("SALVANDO NKI + SAMPLES LOCAIS (PATCH RELATIVO): " .. nki_path)',
        '  -- mode=patch evita falha "path doesnt exist" na criacao de Samples.',
        '  -- As zonas JA referenciam os WAVs locais em Samples e nao o cache.',
        '  -- absolute_paths=false orienta o Kontakt a salvar caminhos relativos.',
        '  local saved, save_err = pcall(K.save_instrument, inst, nki_path, {mode="patch", absolute_paths=false})',
        '  assert(saved, "FALHA AO SALVAR NKI com Samples ja locais: " .. tostring(save_err) .. " | NKI: " .. nki_path .. " | Samples: " .. samples_path)',
        '  local f = io.open(nki_path, "rb")',
        '  assert(f, "O Kontakt nao criou o arquivo NKI")',
        '  local size = f:seek("end"); f:close()',
        '  assert(size and size > 1024, "O arquivo NKI foi criado vazio ou incompleto")',
        '  local count = 0',
        '  local missing = {}',
        '  for _, file in ipairs(expected_samples) do',
        '    local handle = io.open(samples_path .. "/" .. file, "rb")',
        '    if handle then',
        '      local bytes = handle:seek("end")',
        '      handle:close()',
        '      if bytes and bytes > 44 then count = count + 1 else table.insert(missing, file .. " (incompleto)") end',
        '    else',
        '      table.insert(missing, file)',
        '    end',
        '  end',
        '  log("WAVS CONFERIDOS: " .. count .. "/" .. #expected_samples)',
        '  assert(#missing == 0, "SAMPLES AUSENTES apos salvar NKI: " .. table.concat(missing, ", ", 1, math.min(8, #missing)))',
        *(['  if graphics_ok then',
           '    assert(nkr_exists(), "NKR SUMIU APOS SALVAR: " .. nkr_path)',
           '    log("NKR CONFIRMADO DEPOIS DO SALVAMENTO: " .. nkr_path)',
           '  end'] if artwork else []),
        *(['  if os.remove(setup_path) then log("PATCH TEMPORARIO REMOVIDO") end'] if artwork else []),
        *(['  if not graphics_ok then',
           '    log("SUCESSO NKI SAMPLES SEM NKR: " .. nki_path .. " (" .. count .. " wavs)")',
           '  else',
           '    log("SUCESSO NKI SAMPLES: " .. nki_path .. " (" .. count .. " wavs)")',
           '  end'] if artwork else ['  log("SUCESSO NKI SAMPLES: " .. nki_path .. " (" .. count .. " wavs)")']),
        'end',
        'local ok, err = xpcall(main, function(e) return debug and debug.traceback(e, 2) or tostring(e) end)',
        'if not ok then log("ERRO: " .. tostring(err)); print("NORD KONTAKT BRIDGE ERRO: " .. tostring(err)) end',
        '',
    ])
    lua.write_text('\n'.join(lines), encoding='utf-8')
    return DirectExport(nki=nki, lua=lua, log=log, source_ksp=ksp, zones=len(rows), artwork=artwork, samples_dir=sample_dir, sample_count=len(unique_samples))
