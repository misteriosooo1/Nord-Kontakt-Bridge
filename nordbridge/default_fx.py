"""Painel FX padrão do conversor Nord -> Kontakt.

Gerado para instrumentos novos e separado de qualquer .nki já existente.
O piano começa seco: módulos presentes, mas em bypass até o usuário movê-los.
"""
from __future__ import annotations


def _safe_title(text: str) -> str:
    return text.replace('"', "'").replace('\n', ' ').replace('\r', ' ')[:48]


def build_default_fx_ksp(title: str) -> str:
    """Gera fonte KSP para importar no primeiro slot via Lua oficial.

    Compatibilidade específica de compilação/áudio exige teste no Kontakt 8.9.0.
    """
    return '''{ Nord Kontakt Bridge 0.6.1 - FX EMBUTIDOS }
{ Criacao automatica: som natural quando efeitos estao zerados. }
on init
    message("")
    make_perfview
    set_script_title("NORD BRIDGE | FX")
    set_ui_width_px(633)
    set_ui_height_px(620)

    declare ui_label $Titulo (6,1)
    move_control_px($Titulo,22,330)
    set_text($Titulo,"__TITLE__  |  FX")

    declare ui_knob $Reverb (0,100,1)
    move_control_px($Reverb,42,367)
    set_text($Reverb,"REVERB")
    $Reverb := 0
    make_persistent($Reverb)

    declare ui_knob $Delay (0,100,1)
    move_control_px($Delay,187,367)
    set_text($Delay,"DELAY")
    $Delay := 0
    make_persistent($Delay)

    declare ui_knob $Chorus (0,100,1)
    move_control_px($Chorus,332,367)
    set_text($Chorus,"CHORUS")
    $Chorus := 0
    make_persistent($Chorus)

    declare ui_knob $Brilho (0,100,1)
    move_control_px($Brilho,477,367)
    set_text($Brilho,"EQ BRILHO")
    $Brilho := 50
    make_persistent($Brilho)

    declare ui_knob $Volume (0,1000000,10000)
    move_control_px($Volume,42,472)
    set_text($Volume,"VOLUME")
    declare $OriginalVolume
    $OriginalVolume := get_engine_par($ENGINE_PAR_VOLUME,-1,-1,-1)
    $Volume := $OriginalVolume
    make_persistent($Volume)

    declare ui_knob $Dinamica (0,200,1)
    move_control_px($Dinamica,187,472)
    set_text($Dinamica,"DINAMICA")
    $Dinamica := 100
    make_persistent($Dinamica)

    declare ui_knob $Tune (-12,12,1)
    move_control_px($Tune,332,472)
    set_text($Tune,"TUNE")
    $Tune := 0
    make_persistent($Tune)

    declare ui_knob $Pan (-100,100,1)
    move_control_px($Pan,477,472)
    set_text($Pan,"PAN")
    $Pan := 0
    make_persistent($Pan)

    declare ui_button $Redefinir
    move_control_px($Redefinir,465,567)
    set_text($Redefinir,"REDEFINIR")

    declare $vel_out

    { 4 insert FX: EQ, Chorus, Delay, Reverb. }
    { Inicializacao sincrona: sem wait_async no init. }
    set_engine_par($ENGINE_PAR_EFFECT_TYPE,$EFFECT_TYPE_FILTER,-1,0,$NI_INSERT_BUS)
    set_engine_par($ENGINE_PAR_EFFECT_SUBTYPE,$FILTER_TYPE_EQ3BAND,-1,0,$NI_INSERT_BUS)
    set_engine_par($ENGINE_PAR_EFFECT_TYPE,$EFFECT_TYPE_CHORUS,-1,1,$NI_INSERT_BUS)
    set_engine_par($ENGINE_PAR_EFFECT_TYPE,$EFFECT_TYPE_DELAY,-1,2,$NI_INSERT_BUS)
    set_engine_par($ENGINE_PAR_EFFECT_TYPE,$EFFECT_TYPE_REVERB2,-1,3,$NI_INSERT_BUS)

    { Nenhum FX interfere no timbre inicialmente. }
    set_engine_par($ENGINE_PAR_EFFECT_BYPASS,1,-1,0,$NI_INSERT_BUS)
    set_engine_par($ENGINE_PAR_EFFECT_BYPASS,1,-1,1,$NI_INSERT_BUS)
    set_engine_par($ENGINE_PAR_EFFECT_BYPASS,1,-1,2,$NI_INSERT_BUS)
    set_engine_par($ENGINE_PAR_EFFECT_BYPASS,1,-1,3,$NI_INSERT_BUS)
end on

function aplicar_reverb
    if ($Reverb = 0)
        set_engine_par($ENGINE_PAR_EFFECT_BYPASS,1,-1,3,$NI_INSERT_BUS)
    else
        set_engine_par($ENGINE_PAR_SEND_EFFECT_DRY_LEVEL,1000000,-1,3,$NI_INSERT_BUS)
        set_engine_par($ENGINE_PAR_SEND_EFFECT_OUTPUT_GAIN,$Reverb * 10000,-1,3,$NI_INSERT_BUS)
        set_engine_par($ENGINE_PAR_EFFECT_BYPASS,0,-1,3,$NI_INSERT_BUS)
    end if
end function

function aplicar_delay
    if ($Delay = 0)
        set_engine_par($ENGINE_PAR_EFFECT_BYPASS,1,-1,2,$NI_INSERT_BUS)
    else
        set_engine_par($ENGINE_PAR_SEND_EFFECT_DRY_LEVEL,1000000,-1,2,$NI_INSERT_BUS)
        set_engine_par($ENGINE_PAR_SEND_EFFECT_OUTPUT_GAIN,$Delay * 10000,-1,2,$NI_INSERT_BUS)
        set_engine_par($ENGINE_PAR_EFFECT_BYPASS,0,-1,2,$NI_INSERT_BUS)
    end if
end function

function aplicar_chorus
    if ($Chorus = 0)
        set_engine_par($ENGINE_PAR_EFFECT_BYPASS,1,-1,1,$NI_INSERT_BUS)
    else
        set_engine_par($ENGINE_PAR_SEND_EFFECT_DRY_LEVEL,1000000,-1,1,$NI_INSERT_BUS)
        set_engine_par($ENGINE_PAR_SEND_EFFECT_OUTPUT_GAIN,$Chorus * 10000,-1,1,$NI_INSERT_BUS)
        set_engine_par($ENGINE_PAR_EFFECT_BYPASS,0,-1,1,$NI_INSERT_BUS)
    end if
end function

function aplicar_brilho
    if ($Brilho = 50)
        set_engine_par($ENGINE_PAR_EFFECT_BYPASS,1,-1,0,$NI_INSERT_BUS)
    else
        set_engine_par($ENGINE_PAR_GAIN3,$Brilho * 10000,-1,0,$NI_INSERT_BUS)
        set_engine_par($ENGINE_PAR_EFFECT_BYPASS,0,-1,0,$NI_INSERT_BUS)
    end if
end function

on persistence_changed
    call aplicar_reverb
    call aplicar_delay
    call aplicar_chorus
    call aplicar_brilho
end on

on ui_control ($Reverb)
    call aplicar_reverb
end on
on ui_control ($Delay)
    call aplicar_delay
end on
on ui_control ($Chorus)
    call aplicar_chorus
end on
on ui_control ($Brilho)
    call aplicar_brilho
end on
on ui_control ($Volume)
    set_engine_par($ENGINE_PAR_VOLUME,$Volume,-1,-1,-1)
end on
on ui_control ($Redefinir)
    $Reverb := 0
    $Delay := 0
    $Chorus := 0
    $Brilho := 50
    $Volume := $OriginalVolume
    $Dinamica := 100
    $Tune := 0
    $Pan := 0
    call aplicar_reverb
    call aplicar_delay
    call aplicar_chorus
    call aplicar_brilho
    set_engine_par($ENGINE_PAR_VOLUME,$Volume,-1,-1,-1)
    $Redefinir := 0
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
'''.replace('__TITLE__', _safe_title(title))
