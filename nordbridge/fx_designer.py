"""Editor FX: fundo rasterizado; controles, titulo e legendas no KSP.

Nao se deve desenhar legendas na imagem de fundo: o wallpaper do Kontakt
pode comecar sob o cabecalho enquanto controles KSP usam a area de
performance, gerando deslocamento mesmo com coordenadas aparentemente iguais.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

EFFECTS = ('Reverb','Delay','Chorus','Brilho','Volume','Dinamica','Tune','Pan')
DEFAULT_LABELS = ('REVERB','DELAY','CHORUS','EQ BRILHO','VOLUME','DINÂMICA','TUNE','PAN')
# Coordenadas de controls na Performance View de 633x620.
# Nunca desenhar texto essencial no wallpaper: espacos de origem diferentes.
PAGE_STRIDE = 705  # quadro PIANO e quadro FX no wallpaper empilhado
UI_HEIGHT = 620
W = 633

@dataclass
class FXDesign:
    enabled: bool = True
    tabs: bool = True
    title: str = 'SOUND / FX'
    labels: tuple[str, ...] = DEFAULT_LABELS
    font_family: str = 'Segoe UI'
    title_color: str = '#F4D4BD'
    label_color: str = '#EEE5E6'
    accent: str = '#E43A50'
    background: str = '#1D1118'
    knob_style: str = 'Nord Red'
    layout: str = '3 colunas'
    reset_label: str = 'REDEFINIR'

    @classmethod
    def from_dict(cls, value: dict[str, Any] | None) -> 'FXDesign':
        if not isinstance(value, dict):
            return cls()
        allowed={name for name in cls.__dataclass_fields__}
        safe={k:v for k,v in value.items() if k in allowed}
        if 'labels' in safe:
            labels=list(safe['labels'])
            safe['labels']=tuple((str(labels[i]).strip()[:24] or DEFAULT_LABELS[i]) if i<len(labels) else DEFAULT_LABELS[i] for i in range(8))
        return cls(**safe)

    def to_dict(self):
        d=asdict(self);d['labels']=list(self.labels)
        return d


def hex_rgb(x: str) -> tuple[int,int,int]:
    if not re.fullmatch(r'#[0-9a-fA-F]{6}', x or ''):
        raise ValueError('Cor hexadecimal invalida: '+repr(x))
    return tuple(int(x[j:j+2],16) for j in (1,3,5))


def font_for(family: str, pixels: int):
    from PIL import ImageFont
    paths={
        'Segoe UI':('C:/Windows/Fonts/segoeui.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),
        'Arial':('C:/Windows/Fonts/arial.ttf','/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf'),
        'Georgia':('C:/Windows/Fonts/georgia.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'),
        'Consolas':('C:/Windows/Fonts/consola.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'),
        'Times New Roman':('C:/Windows/Fonts/times.ttf','/usr/share/fonts/truetype/liberation2/LiberationSerif-Regular.ttf'),
        'Trebuchet MS':('C:/Windows/Fonts/trebuc.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),
    }
    for p in paths.get(family,paths['Segoe UI']):
        try:return ImageFont.truetype(p,pixels)
        except OSError:pass
    return ImageFont.load_default()


def effect_positions(config: FXDesign):
    if config.layout=='4 colunas':
        return [(60+i*147,221) for i in range(4)]+[(60+i*147,405) for i in range(4)]
    return [(100+i*190,183) for i in range(3)]+[(100+i*190,324) for i in range(3)]+[(100+i*190,465) for i in range(2)]


def make_knob_sheet(config: FXDesign, width=76):
    from PIL import Image, ImageDraw
    import math
    width=max(60,min(96,width));height=width
    sheet=Image.new('RGBA',(width,height*101),(0,0,0,0))
    accent=hex_rgb(config.accent)
    if config.knob_style=='Dourado':accent=(203,157,91)
    elif config.knob_style=='Prata':accent=(187,192,203)
    elif config.knob_style=='Minimal':accent=(238,238,238)
    for value in range(101):
        im=Image.new('RGBA',(width,height),(0,0,0,0));d=ImageDraw.Draw(im)
        pad=8;box=(pad,pad,width-pad-1,height-pad-1)
        d.ellipse(box,fill=(19,22,27),outline=(83,75,83),width=2)
        d.arc((pad+2,pad+2,width-pad-3,height-pad-3),start=130,end=410,fill=accent,width=3)
        if config.knob_style!='Minimal':d.ellipse((pad+8,pad+8,width-pad-9,height-pad-9),outline=(45,47,53),width=1)
        angle=math.radians(130+value*2.8)
        cx=width/2; cy=height/2;r=(width-2*pad)/2-11
        d.line((cx,cy,cx+math.cos(angle)*r,cy+math.sin(angle)*r),fill=(248,231,217),width=3)
        d.ellipse((cx-2,cy-2,cx+2,cy+2),fill=accent)
        sheet.alpha_composite(im,(0,value*height))
    return sheet


def _center_text(draw,x,y,text,font,color):
    bb=draw.textbbox((0,0),text,font=font)
    draw.text((x-(bb[2]-bb[0])/2-bb[0],y-(bb[3]-bb[1])/2-bb[1]),text,font=font,fill=color)


def make_pages(photo: Path, config: FXDesign):
    """Retorna uma tira vertical com telas PIANO / FX de 633x705 cada."""
    from PIL import Image,ImageDraw,ImageOps
    with Image.open(photo) as inp:
        src=inp.convert('RGBA')
        upper=ImageOps.fit(src,(W,320),method=Image.Resampling.LANCZOS)
    bg=hex_rgb(config.background)
    sheets=[]
    for page in (0,1):
        canvas=Image.new('RGBA',(W,PAGE_STRIDE),bg+(255,))
        dr=ImageDraw.Draw(canvas)
        if page==0:
            canvas.alpha_composite(upper,(0,0))
            dr.rectangle((0,320,W,619),fill=bg+(255,))
            dr.line((22,320,611,320),fill=hex_rgb(config.accent)+(255,),width=2)
            _center_text(dr, W/2, 427, 'PIANO',font_for(config.font_family,26),hex_rgb(config.title_color))
            _center_text(dr, W/2, 461, 'SOM ORIGINAL • CONTROLES NA ABA FX',font_for(config.font_family,13),hex_rgb(config.label_color))
        else:
            dr.rectangle((0,0,W,619),fill=bg+(255,))
            # Sem textos aqui: titulo/nomes acompanham os widgets KSP.
            # Linhas na imagem podem ficar visualmente deslocadas dos widgets
            # porque o wallpaper inclui a area sob o cabecalho do instrumento.
        sheets.append(canvas)
    long=Image.new('RGBA',(W,PAGE_STRIDE*2),bg+(255,))
    long.alpha_composite(sheets[0],(0,0));long.alpha_composite(sheets[1],(0,PAGE_STRIDE))
    return long


def install_fx_graphics(pack,config:FXDesign)->str:
    """Muda somente os recursos visuais do pack em disco, retornando prefixo."""
    from .visual_assets import standard_picture_txt, make_button_sheet
    wallpaper=pack.pictures/(pack.wallpaper_name+'.png')
    pages=make_pages(wallpaper,config)
    pages.save(wallpaper)
    prefix=pack.wallpaper_name
    knob=prefix+'_KNOB'
    make_knob_sheet(config).save(pack.pictures/(knob+'.png'))
    (pack.pictures/(knob+'.txt')).write_text(standard_picture_txt().replace('Number of Animations: 0','Number of Animations: 101'),encoding='utf-8')
    for tab in ('PIANO','FX'):
        name=prefix+'_TAB_'+tab
        make_button_sheet(tab,'Dourado' if config.knob_style=='Dourado' else 'Nord Red').save(pack.pictures/(name+'.png'))
        (pack.pictures/(name+'.txt')).write_text(standard_picture_txt().replace('Number of Animations: 0','Number of Animations: 6'),encoding='utf-8')
    return knob



def validate_fx_design(config: FXDesign) -> None:
    """Valida campos que o usuario pode alterar antes de gerar PNG e KSP."""
    if not isinstance(config.title,str) or not config.title.strip():
        raise ValueError('Editor FX: informe um titulo para o painel.')
    if len(config.title) > 80:
        raise ValueError('Editor FX: o titulo deve ter ate 80 caracteres.')
    if not isinstance(config.labels,(list,tuple)) or len(config.labels)!=len(EFFECTS):
        raise ValueError('Editor FX: forneca exatamente oito nomes de efeitos.')
    if any(not isinstance(v,str) or not v.strip() or len(v)>50 for v in config.labels):
        raise ValueError('Editor FX: cada nome de efeito deve ter entre 1 e 50 caracteres.')
    if config.layout not in ('3 colunas','4 colunas'):
        raise ValueError('Editor FX: organizacao invalida. Use 3 ou 4 colunas.')
    if config.knob_style not in ('Nord Red','Dourado','Prata','Minimal'):
        raise ValueError('Editor FX: visual de knob nao reconhecido.')
    if config.font_family not in ('Segoe UI','Arial','Georgia','Consolas','Times New Roman','Trebuchet MS'):
        raise ValueError('Editor FX: fonte nao suportada pelo gerador.')
    for field in ('title_color','label_color','accent','background'):
        hex_rgb(getattr(config,field))
    if not isinstance(config.reset_label,str) or not config.reset_label.strip():
        raise ValueError('Editor FX: informe o texto do botao REDEFINIR.')
    for x,y in effect_positions(config):
        lx,ly,lw,lh=label_geometry(x,y)
        if lx<0 or lx+lw>W or ly+lh>UI_HEIGHT:
            raise ValueError('Editor FX: nomes nao cabem dentro da area do painel.')


def ksp_str(s: str) -> str:
    """Escape quote/control chars in generated string literals, preserving UTF-8."""
    return str(s).replace('\\','/').replace('"', "'").replace('\n',' ').replace('\r',' ').strip()


def label_geometry(x: int, y: int) -> tuple[int,int,int,int]:
    """Label under value, aligned to knob center. Fixed bounding width."""
    return x-22, y+107, 120, 20


def design_ksp(base: str,pack,config:FXDesign) -> str:
    """Mantem a logica de audio/callbacks, modifica somente a camada UI.

    Titulo e nomes sao ui_label do KSP para acompanhar posicoes e zoom.
    O wallpaper nao possui textos FX para evitar sobreposicao.
    """
    if not pack or not config.enabled:return base
    validate_fx_design(config)
    knob=pack.wallpaper_name+'_KNOB'
    positions=effect_positions(config)
    # Original e mantido como plano B quando NKR inexistente.
    base=base.replace('set_ui_height_px(620)','set_ui_height_px(620)')
    # O titulo usa coordenadas KSP, nao o PNG (evita colidir com as abas).
    # ui_label funciona mesmo se o Kontakt alterar a escala de visualizacao.
    extra=[
        '    set_control_par_str($INST_WALLPAPER_ID,$CONTROL_PAR_PICTURE,"'+pack.wallpaper_name+'")',
        '    declare ui_label $TituloFX (3,1)',
        '    move_control_px($TituloFX,32,67)',
        '    set_control_par(get_ui_id($TituloFX),$CONTROL_PAR_WIDTH,264)',
        '    set_control_par(get_ui_id($TituloFX),$CONTROL_PAR_HEIGHT,32)',
        '    set_control_par(get_ui_id($TituloFX),$CONTROL_PAR_HIDE,$HIDE_PART_BG)',
        '    set_control_par(get_ui_id($TituloFX),$CONTROL_PAR_TEXT_ALIGNMENT,0)',
        '    set_text($TituloFX,"'+ksp_str(config.title[:32])+'")',
    ]
    if config.tabs:
        extra += [
            '    declare $PaginaAtual := 0',
            '    make_persistent($PaginaAtual)',
            '    declare ui_button $AbaPiano',
            '    move_control_px($AbaPiano,329,62)',
            '    set_text($AbaPiano,"")',
            '    set_control_par_str(get_ui_id($AbaPiano),$CONTROL_PAR_PICTURE,"'+pack.wallpaper_name+'_TAB_PIANO")',
            '    set_control_par(get_ui_id($AbaPiano),$CONTROL_PAR_WIDTH,136)',
            '    set_control_par(get_ui_id($AbaPiano),$CONTROL_PAR_HEIGHT,40)',
            '    declare ui_button $AbaFX',
            '    move_control_px($AbaFX,480,62)',
            '    set_text($AbaFX,"")',
            '    set_control_par_str(get_ui_id($AbaFX),$CONTROL_PAR_PICTURE,"'+pack.wallpaper_name+'_TAB_FX")',
            '    set_control_par(get_ui_id($AbaFX),$CONTROL_PAR_WIDTH,136)',
            '    set_control_par(get_ui_id($AbaFX),$CONTROL_PAR_HEIGHT,40)',
        ]
    base=base.replace('    set_ui_height_px(620)\n','    set_ui_height_px(620)\n'+'\n'.join(extra)+'\n',1)
    # Remover label antigo; o titulo do editor e declarado acima como $TituloFX.
    base=re.sub(r'(?m)^\s*declare ui_label \$Titulo \(6,1\)\n\s*move_control_px\(\$Titulo,22,330\)\n\s*set_text\(\$Titulo,[^\n]+\)\n','',base,count=1)
    for var,(x,y) in zip(EFFECTS,positions):
        pattern=r'declare ui_knob \$'+var+r' \((-?\d+),(-?\d+),(?:\d+)\)\n\s*move_control_px\(\$'+var+r',\d+,\d+\)\n\s*set_text\(\$'+var+r',"[^"]*"\)'
        def substitute(m):
            return ('declare ui_slider $'+var+' ('+m.group(1)+','+m.group(2)+')\n'
                '    move_control_px($'+var+f',{x},{y})\n'
                '    set_control_par_str(get_ui_id($'+var+'),$CONTROL_PAR_LABEL,"'+var.upper()+'")\n'
                '    set_control_par_str(get_ui_id($'+var+'),$CONTROL_PAR_PICTURE,"'+knob+'")\n'
                '    set_control_par(get_ui_id($'+var+'),$CONTROL_PAR_WIDTH,76)\n'
                '    set_control_par(get_ui_id($'+var+'),$CONTROL_PAR_HEIGHT,76)\n'
                '    set_control_par(get_ui_id($'+var+'),$CONTROL_PAR_MOUSE_BEHAVIOUR,-500)')
        base,count=re.subn(pattern,substitute,base,count=1)
        if count!=1:raise ValueError('Controle nao encontrado no KSP base: '+var)
    # reubica botao para layout fx e esconde seu texto KSP (ja rasterizado)
    if config.layout=='4 colunas':bx,by=435,562
    else:bx,by=432,514
    base=base.replace('move_control_px($Redefinir,465,567)',f'move_control_px($Redefinir,{bx},{by})')
    # atualiza o texto do botao no sprite
    # bloco criado no init, depois dos knobs e antes de 'declare $vel_out'
    labels=[]
    for var,caption,(x,y) in zip(EFFECTS,config.labels,positions):
        lx,ly,lw,lh=label_geometry(x,y)
        labels.extend([
            '    declare ui_label $Nome'+var+' (2,1)',
            f'    move_control_px($Nome{var},{lx},{ly})',
            f'    set_control_par(get_ui_id($Nome{var}),$CONTROL_PAR_WIDTH,{lw})',
            f'    set_control_par(get_ui_id($Nome{var}),$CONTROL_PAR_HEIGHT,{lh})',
            f'    set_control_par(get_ui_id($Nome{var}),$CONTROL_PAR_TEXT_ALIGNMENT,1)',
            f'    set_control_par(get_ui_id($Nome{var}),$CONTROL_PAR_HIDE,$HIDE_PART_BG)',
            f'    set_text($Nome{var},"{ksp_str(caption[:24])}")',
            '    declare ui_label $Valor'+var+' (1,1)',
            f'    move_control_px($Valor{var},{x},{y+79})',
            f'    set_control_par(get_ui_id($Valor{var}),$CONTROL_PAR_WIDTH,76)',
            f'    set_control_par(get_ui_id($Valor{var}),$CONTROL_PAR_HEIGHT,19)',
            f'    set_control_par(get_ui_id($Valor{var}),$CONTROL_PAR_TEXT_ALIGNMENT,1)',
            f'    set_control_par(get_ui_id($Valor{var}),$CONTROL_PAR_HIDE,$HIDE_PART_BG)',
            '    set_text($Valor'+var+', '+('$Volume / 10000' if var=='Volume' else '$'+var)+')',
        ])
    base=base.replace('    declare $vel_out','\n'.join(labels)+'\n    declare $vel_out',1)
    updates=[]
    for var in EFFECTS:
        value='$Volume / 10000' if var=='Volume' else '$'+var
        updates.append('    set_text($Valor'+var+','+value+')')
    # updated value to ui_control callbacks
    for var in EFFECTS:
        base=base.replace('on ui_control ($'+var+')\n','on ui_control ($'+var+')\n'+updates[EFFECTS.index(var)]+'\n',1) if 'on ui_control ($'+var+')\n' in base else base
    base=base.replace('    $Redefinir := 0\nend on','\n'.join(updates)+'\n    $Redefinir := 0\nend on',1)
    # O KSP base nao possui callbacks para dinamica, tune e pan; adicionar.
    for var in ('Dinamica','Tune','Pan'):
        base+='\non ui_control ($'+var+')\n'+updates[EFFECTS.index(var)]+'\nend on\n'
    block='\n'.join(updates)+'\n'
    if config.tabs:
        h=['        set_control_par(get_ui_id($TituloFX),$CONTROL_PAR_HIDE,$HIDE_WHOLE_CONTROL)']
        for var in EFFECTS:
            for c in ('$'+var,'$Valor'+var,'$Nome'+var):
                h.append('        set_control_par(get_ui_id('+c+'),$CONTROL_PAR_HIDE,$HIDE_WHOLE_CONTROL)')
        h.append('        set_control_par(get_ui_id($Redefinir),$CONTROL_PAR_HIDE,$HIDE_WHOLE_CONTROL)')
        s=['        set_control_par(get_ui_id($TituloFX),$CONTROL_PAR_HIDE,$HIDE_PART_BG)']
        for var in EFFECTS:
            s.append('        set_control_par(get_ui_id($'+var+'),$CONTROL_PAR_HIDE,$HIDE_PART_NOTHING)')
            s.append('        set_control_par(get_ui_id($Valor'+var+'),$CONTROL_PAR_HIDE,$HIDE_PART_BG)')
            s.append('        set_control_par(get_ui_id($Nome'+var+'),$CONTROL_PAR_HIDE,$HIDE_PART_BG)')
        s.append('        set_control_par(get_ui_id($Redefinir),$CONTROL_PAR_HIDE,$HIDE_PART_NOTHING)')
        pages='''
function mostrar_pagina
    if ($PaginaAtual = 0)
        set_skin_offset(0)
'''+ '\n'.join(h)+'''
    else
        set_skin_offset('''+str(PAGE_STRIDE)+''')
'''+ '\n'.join(s)+'''
    end if
end function

on ui_control ($AbaPiano)
    $PaginaAtual := 0
    call mostrar_pagina
    $AbaPiano := 0
end on
on ui_control ($AbaFX)
    $PaginaAtual := 1
    call mostrar_pagina
    $AbaFX := 0
end on
'''
        # nao chamar funcoes no on init; use persistence_changed
        base=base.replace('on persistence_changed\n','on persistence_changed\n    call mostrar_pagina\n'+block,1)
        base=base.replace('on persistence_changed\n',pages+'\non persistence_changed\n',1)
    else:
        # Sem abas, FX sempre na segunda area da imagem
        base=base.replace('end on\n\nfunction aplicar_reverb','    set_skin_offset('+str(PAGE_STRIDE)+')\nend on\n\nfunction aplicar_reverb',1)
    return base


def save_design(config:FXDesign,output:Path):
    import json
    output.write_text(json.dumps(config.to_dict(),ensure_ascii=False,indent=2),encoding='utf-8')

def preview_page(image, config: FXDesign, page: str='FX'):
    """Simulacao estatica do GUI, para ver os knobs e valores antes da exportacao."""
    from PIL import Image, ImageDraw
    if page not in ('PIANO','FX'):raise ValueError('Pagina invalida')
    offset=PAGE_STRIDE if page=='FX' else 0
    im=image.crop((0,offset,W,offset+UI_HEIGHT)).copy()
    d=ImageDraw.Draw(im)
    if page=='FX':
        film=make_knob_sheet(config)
        d.text((32,67),config.title[:32],font=font_for(config.font_family,18),fill=hex_rgb(config.title_color))
        for (x,y),value,name in zip(effect_positions(config),(0,0,0,50,50,100,0,0),config.labels):
            im.alpha_composite(film.crop((0,76*value,76,76*(value+1))),(x,y))
            _center_text(d,x+38,y+88,str(value),font_for(config.font_family,12),(240,238,236))
            _center_text(d,x+38,y+117,name[:24],font_for(config.font_family,13),hex_rgb(config.label_color))
        bx,by=(435,562) if config.layout=='4 colunas' else (432,514)
        d.rounded_rectangle((bx,by,bx+144,by+40),radius=7,fill=(33,22,27),outline=hex_rgb(config.accent),width=2)
        _center_text(d,bx+72,by+20,config.reset_label,font_for(config.font_family,12),(246,232,237))
    if config.tabs:
        for title,x in (('PIANO',329),('FX',480)):
            selected=title==page
            d.rounded_rectangle((x,62,x+136,102),radius=7,fill=(81,30,42) if selected else (32,23,28),
                                outline=hex_rgb(config.accent),width=2)
            _center_text(d,x+68,82,title,font_for(config.font_family,15),(246,233,234))
    return im
