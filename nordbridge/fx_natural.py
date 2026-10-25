"""Upgrade de efeitos KSP nao destrutivo para NKI ja carregado no Kontakt 8.

Cria painel FX com efeito inicial 100% em bypass. O Lua NAO salva o NKI
nem altera o projeto Nord: o usuario testa e salva uma copia no Kontakt.
"""
from __future__ import annotations
from pathlib import Path


def build_fx_ksp(name: str = 'Astoria Grand XL 6.1') -> str:
    clean = name.replace('"', "'").replace('\n',' ').replace('\r', ' ')[:50]
    return '''{ Nord Kontakt Bridge 0.3 - Som natural por padrao; FX somente pela interface }
on init
    message("")
    make_perfview
    set_script_title("ASTORIA | FX NATURAL")
    set_ui_height_px(270)

    declare ui_label $Titulo (6,1)
    move_control($Titulo,1,1)
    set_text($Titulo,"__NAME__ - NATURAL / FX")

    declare ui_knob $Reverb (0,100,1)
    move_control($Reverb,1,3)
    set_text($Reverb,"REVERB")
    $Reverb := 0
    make_persistent($Reverb)

    declare ui_knob $Delay (0,100,1)
    move_control($Delay,2,3)
    set_text($Delay,"DELAY")
    $Delay := 0
    make_persistent($Delay)

    declare ui_knob $Chorus (0,100,1)
    move_control($Chorus,3,3)
    set_text($Chorus,"CHORUS")
    $Chorus := 0
    make_persistent($Chorus)

    declare ui_knob $Brilho (0,100,1)
    move_control($Brilho,4,3)
    set_text($Brilho,"EQ BRILHO")
    $Brilho := 50
    make_persistent($Brilho)

    declare ui_knob $Volume (0,1000000,1000000)
    move_control($Volume,5,3)
    set_text($Volume,"VOLUME")
    $Volume := get_engine_par($ENGINE_PAR_VOLUME,-1,-1,-1)
    make_persistent($Volume)

    declare ui_button $Natural
    move_control($Natural,6,3)
    set_text($Natural,"NATURAL")

    declare ui_knob $Dinamica (0,200,1)
    move_control($Dinamica,1,5)
    set_text($Dinamica,"DINAMICA")
    $Dinamica := 100
    make_persistent($Dinamica)

    declare ui_knob $Tune (-12,12,1)
    move_control($Tune,2,5)
    set_text($Tune,"TUNE")
    $Tune := 0
    make_persistent($Tune)

    declare ui_knob $Pan (-100,100,1)
    move_control($Pan,3,5)
    set_text($Pan,"PAN")
    $Pan := 0
    make_persistent($Pan)

    declare $vel_out

    { FX inseridos apenas em slots vazios; efeitos existentes nao sao substituidos. }
    { Slot 0 = EQ de 3 bandas (brilho); 1 = chorus; 2 = delay; 3 = reverb. }
    if (get_engine_par($ENGINE_PAR_EFFECT_TYPE,-1,0,$NI_INSERT_BUS) = $EFFECT_TYPE_NONE)
        wait_async(set_engine_par($ENGINE_PAR_EFFECT_TYPE,$EFFECT_TYPE_FILTER,-1,0,$NI_INSERT_BUS))
        wait_async(set_engine_par($ENGINE_PAR_EFFECT_SUBTYPE,$FILTER_TYPE_EQ3BAND,-1,0,$NI_INSERT_BUS))
    end if
    if (get_engine_par($ENGINE_PAR_EFFECT_TYPE,-1,1,$NI_INSERT_BUS) = $EFFECT_TYPE_NONE)
        wait_async(set_engine_par($ENGINE_PAR_EFFECT_TYPE,$EFFECT_TYPE_CHORUS,-1,1,$NI_INSERT_BUS))
    end if
    if (get_engine_par($ENGINE_PAR_EFFECT_TYPE,-1,2,$NI_INSERT_BUS) = $EFFECT_TYPE_NONE)
        wait_async(set_engine_par($ENGINE_PAR_EFFECT_TYPE,$EFFECT_TYPE_DELAY,-1,2,$NI_INSERT_BUS))
    end if
    if (get_engine_par($ENGINE_PAR_EFFECT_TYPE,-1,3,$NI_INSERT_BUS) = $EFFECT_TYPE_NONE)
        wait_async(set_engine_par($ENGINE_PAR_EFFECT_TYPE,$EFFECT_TYPE_REVERB2,-1,3,$NI_INSERT_BUS))
    end if

    { Desligados no primeiro carregamento. As configuracoes salvas sao reaplicadas abaixo. }
    set_engine_par($ENGINE_PAR_EFFECT_BYPASS,1,-1,0,$NI_INSERT_BUS)
    set_engine_par($ENGINE_PAR_EFFECT_BYPASS,1,-1,1,$NI_INSERT_BUS)
    set_engine_par($ENGINE_PAR_EFFECT_BYPASS,1,-1,2,$NI_INSERT_BUS)
    set_engine_par($ENGINE_PAR_EFFECT_BYPASS,1,-1,3,$NI_INSERT_BUS)
end on

function apply_reverb
    if ($Reverb = 0)
        set_engine_par($ENGINE_PAR_EFFECT_BYPASS,1,-1,3,$NI_INSERT_BUS)
    else
        set_engine_par($ENGINE_PAR_SEND_EFFECT_OUTPUT_GAIN,$Reverb * 10000,-1,3,$NI_INSERT_BUS)
        set_engine_par($ENGINE_PAR_EFFECT_BYPASS,0,-1,3,$NI_INSERT_BUS)
    end if
end function

function apply_delay
    if ($Delay = 0)
        set_engine_par($ENGINE_PAR_EFFECT_BYPASS,1,-1,2,$NI_INSERT_BUS)
    else
        set_engine_par($ENGINE_PAR_SEND_EFFECT_OUTPUT_GAIN,$Delay * 10000,-1,2,$NI_INSERT_BUS)
        set_engine_par($ENGINE_PAR_EFFECT_BYPASS,0,-1,2,$NI_INSERT_BUS)
    end if
end function

function apply_chorus
    if ($Chorus = 0)
        set_engine_par($ENGINE_PAR_EFFECT_BYPASS,1,-1,1,$NI_INSERT_BUS)
    else
        set_engine_par($ENGINE_PAR_SEND_EFFECT_OUTPUT_GAIN,$Chorus * 10000,-1,1,$NI_INSERT_BUS)
        set_engine_par($ENGINE_PAR_EFFECT_BYPASS,0,-1,1,$NI_INSERT_BUS)
    end if
end function

function apply_brilho
    if ($Brilho = 50)
        set_engine_par($ENGINE_PAR_EFFECT_BYPASS,1,-1,0,$NI_INSERT_BUS)
    else
        set_engine_par($ENGINE_PAR_GAIN3,$Brilho * 10000,-1,0,$NI_INSERT_BUS)
        set_engine_par($ENGINE_PAR_EFFECT_BYPASS,0,-1,0,$NI_INSERT_BUS)
    end if
end function

on persistence_changed
    call apply_reverb
    call apply_delay
    call apply_chorus
    call apply_brilho
end on

on ui_control ($Reverb)
    call apply_reverb
end on
on ui_control ($Delay)
    call apply_delay
end on
on ui_control ($Chorus)
    call apply_chorus
end on
on ui_control ($Brilho)
    call apply_brilho
end on
on ui_control ($Volume)
    set_engine_par($ENGINE_PAR_VOLUME,$Volume,-1,-1,-1)
end on
on ui_control ($Natural)
    $Reverb := 0
    $Delay := 0
    $Chorus := 0
    $Brilho := 50
    call apply_reverb
    call apply_delay
    call apply_chorus
    call apply_brilho
    $Natural := 0
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
        change_velo($EVENT_ID,$vel_out)
    end if
    if ($Tune # 0)
        change_tune($EVENT_ID,$Tune * 100000,1)
    end if
    if ($Pan # 0)
        change_pan($EVENT_ID,$Pan * 10,1)
    end if
end on
'''.replace('__NAME__',clean)


def build_fx_upgrade(out_dir: str | Path, name: str='Astoria Grand XL 6.1') -> Path:
    folder = Path(out_dir)
    folder.mkdir(parents=True,exist_ok=True)
    (folder/'PAINEL_FX_NATURAL.ksp').write_text(build_fx_ksp(name),encoding='utf-8')
    # Lua descobre o proprio diretorio no Windows: mesmo arquivo serve em qualquer caminho.
    lua = r'''-- Nord Kontakt Bridge v0.3.0 - Instala painel FX no instrumento JA CARREGADO
-- NAO cria novas zonas e NAO salva/sobrescreve o .nki automaticamente.
local K = Kontakt
local titulo = __TITLE__
local source = (debug and debug.getinfo(1, "S") or {}).source or ""
assert(source:sub(1,1) == "@", "Execute este arquivo via F11 no Kontakt. Nao cole em KSP.")
local folder = source:sub(2):gsub("\\", "/"):match("^(.*)/[^/]+$")
assert(folder, "Nao foi possivel identificar a pasta do script")
local ksp = folder .. "/PAINEL_FX_NATURAL.ksp"
local log_path = folder .. "/LOG_FX_NATURAL.txt"
local function log(message)
    local msg = "[Nord FX] " .. tostring(message)
    print(msg)
    local h = io.open(log_path, "a")
    if h then h:write(os.date("%Y-%m-%d %H:%M:%S") .. " " .. msg .. "\n"); h:close() end
end
local function run()
    local t = io.open(ksp, "rb")
    assert(t, "Arquivo PAINEL_FX_NATURAL.ksp nao esta na mesma pasta do Lua")
    t:close()
    local indices = K.get_instrument_indices()
    local matches = {}
    for _, id in ipairs(indices) do
        if K.get_instrument_name(id) == titulo then matches[#matches + 1] = id end
    end
    assert(#matches > 0, "Abra primeiro no Kontakt o NKI: " .. titulo)
    assert(#matches == 1, "Ha " .. #matches .. " instrumentos com o mesmo nome no rack. Remova as duplicatas antes de instalar os efeitos.")
    local inst = matches[1]
    log("Instrumento selecionado: " .. titulo .. " (indice " .. inst .. ")")
    local previous = K.get_instrument_script_source(inst, 0) or ""
    if #previous > 0 then
        local backup = folder .. "/BACKUP_PAINEL_ANTERIOR.ksp"
        local f, err = io.open(backup, "wb")
        assert(f, "Nao foi possivel fazer o backup do painel anterior: " .. tostring(err))
        f:write(previous)
        f:close()
        log("Backup do script KSP anterior salvo em " .. backup)
    end
    K.set_instrument_script_source(inst, 0, ksp)
    K.set_instrument_script_name(inst, 0, "ASTORIA FX NATURAL")
    log("Painel FX enviado ao Kontakt. Confira se o Script Editor apresenta erros.")
    log("FX inativos por padrao. Teste tocando; ajuste knobs para ativar efeitos.")
    log("Salve pelo Kontakt com SAVE AS para criar uma NOVA copia .nki; original preservado.")
end
local ok, err = xpcall(run, function(e) return debug and debug.traceback(e,2) or tostring(e) end)
if not ok then log("ERRO: " .. tostring(err)) end
'''.replace('__TITLE__',__import__('json').dumps(name,ensure_ascii=False))
    (folder/'INSTALAR_FX_NO_ASTORIA_ABERTO.lua').write_text(lua,encoding='utf-8')
    guide=f'''NORD KONTAKT BRIDGE 0.3.0 - FX NATURAL (KONTAKT 8.9.0)

Objetivo: o piano abre no som natural. Nenhum efeito e ativado por padrao.
O painel tem Reverb, Delay, Chorus, EQ Brilho, Volume, Dinamica, Tune e Pan.
O botao NATURAL desliga Reverb, Delay, Chorus e EQ de uma vez.

IMPORTANTE: ESTE KIT NAO PRECISA DO .npno, NEM DE REPROCESSAR 694 ZONAS.

1) FACA COPIA do seu .nki e mantenha os samples na pasta.
2) Abra o Kontakt 8 COMPLETO e carregue o instrumento: {name}
3) Deixe apenas UM instrumento com esse nome no rack (remova duplicatas).
4) Extraia estes 2 scripts (.lua e .ksp) NA MESMA PASTA.
5) Execute F11 / Run Lua script... / INSTALAR_FX_NO_ASTORIA_ABERTO.lua
6) Confira LOG_FX_NATURAL.txt para ver se a importacao do script ocorreu.
7) Abra o Classic View (F10), expanda o instrumento e veja a aba de performance.
8) Se o painel nao aparecer, abra Script Editor, primeiro slot, e confira erros KSP.
9) Teste som seco (natural) e ajuste cada knob de efeito.
10) Quando tudo funcionar, no Kontakt escolha Save As > Instrument e
    SALVE COM OUTRO NOME, ex.: Astoria Grand XL 6.1 FX.nki.
    Use Patch + Samples para copiar amostras, se desejar portabilidade.

O codigo KSP adiciona FX em slots vazios de Instrument Insert Effects.
Slots: 0 EQ, 1 Chorus, 2 Delay, 3 Reverb. Se ja houver efeitos nesses
slots, NAO substituiremos automaticamente o tipo; teste primeiro com
uma copia limpa do instrumento.

O Lua apenas instala o KSP no instrumento aberto; NAO cria novo .nki
nem faz mudancas permanentes ate voce SALVAR manualmente no Kontakt.
Testado em nivel de arquivos e sintaxe KSP por inspecao; necessita validacao
no Kontakt 8.9.0 real, que nao roda neste ambiente.
'''
    (folder/'LEIA_FX_NATURAL.txt').write_text(guide,encoding='utf-8')
    return folder
