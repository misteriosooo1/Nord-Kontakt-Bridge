"""Preparação local e opcional da arte para Kontakt: wallpaper, ícone e capa.

.nkr é criado pelo Kontakt, nunca simulamos ser um .nkr em Python.
"""
from __future__ import annotations
import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path


def installed_assets_dir() -> Path:
    """Recursos empacotados primeiro; copia offline se o pacote estiver incompleto."""
    executable_dir = Path(sys.executable).resolve().parent
    project_dir = Path(__file__).resolve().parents[1]
    bundle = Path(getattr(sys, '_MEIPASS', project_dir))
    required = ('default_icon.png', 'default_wallpaper.png', 'hero_red.png')
    candidates = (
        bundle / 'assets',
        executable_dir / 'assets',
        project_dir / 'assets',
        executable_dir / 'SUPORTE_RECUPERACAO' / 'assets',
        bundle / 'SUPORTE_RECUPERACAO' / 'assets',
        project_dir / 'SUPORTE_RECUPERACAO' / 'assets',
    )
    for folder in candidates:
        if all((folder / name).is_file() for name in required):
            return folder
    return candidates[0]


@dataclass(frozen=True)
class VisualPack:
    nkr: Path
    wallpaper_name: str
    icon_name: str
    cover: Path
    pictures: Path
    button_name: str = ""


def standard_picture_txt() -> str:
    return ('Has Alpha Channel: yes\nNumber of Animations: 0\n'
            'Horizontal Animation: no\nVertical Resizable: no\n'
            'Horizontal Resizable: no\nFixed Top: 0\nFixed Bottom: 0\n'
            'Fixed Left: 0\nFixed Right: 0\n\n')


def _process_image(source: Path, dest: Path, size: tuple[int, int], *, fx_panel: bool = False, fit_mode: str = "cover") -> None:
    """Preenche a área sem barras (cover), ou mantém a imagem inteira (contain)."""
    try:
        from PIL import Image, ImageOps
    except ImportError as exc:
        raise RuntimeError('Instale Pillow (python -m pip install pillow) para usar imagens personalizadas.') from exc
    if not source.is_file():
        raise FileNotFoundError(f'Imagem não encontrada: {source}')
    with Image.open(source) as original:
        rgb = original.convert('RGBA')
        canvas = Image.new('RGBA', size, (22, 9, 15, 255))
        image_region = (size[0], 320) if fx_panel else size
        if fit_mode == 'cover':
            adapted = ImageOps.fit(rgb, image_region, method=Image.Resampling.LANCZOS, centering=(.5,.5))
        elif fit_mode == 'contain':
            adapted = ImageOps.contain(rgb, image_region, method=Image.Resampling.LANCZOS)
        else:
            raise ValueError('Modo de enquadramento inválido: '+fit_mode)
        x = (image_region[0] - adapted.width) // 2
        y = (image_region[1] - adapted.height) // 2
        canvas.alpha_composite(adapted, dest=(x, y))
        if fx_panel:
            from PIL import ImageDraw
            draw = ImageDraw.Draw(canvas)
            # A área 320..620 foi reservada aos oito controles; a arte escolhida
            # permanece inteiramente na metade superior, sem cortes.
            for py in range(320, size[1]):
                shade = min(35, 15 + (py - 320) // 40)
                draw.line([(0, py), (size[0], py)], fill=(shade, 13, 19, 255))
            draw.line([(16, 321), (size[0]-16, 321)], fill=(131, 34, 49, 255), width=2)
        dest.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(dest, format='PNG')


def _load_button_font(size: int):
    from PIL import ImageFont
    for path in (r'C:\Windows\Fonts\arialbd.ttf',
                 '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default()


def make_button_sheet(button_text: str = 'REDEFINIR', style: str = 'Nord Red',
                      source: Path | None = None):
    """Seis estados verticais de um botão de 144x40 para ui_button KSP."""
    from PIL import Image, ImageDraw, ImageOps
    label = button_text.strip()[:22] or 'REDEFINIR'
    palette = {
        'Nord Red': ((31, 18, 22), (207, 47, 64), (247, 223, 225)),
        'Dourado': ((32, 22, 18), (190, 144, 82), (242, 221, 178)),
        'Cinza': ((31, 33, 38), (143, 147, 156), (238, 238, 239)),
    }
    if style not in palette:
        raise ValueError('Tema de botão desconhecido: '+style)
    base_color, outline, ink = palette[style]
    external = None
    if source is not None:
        if not Path(source).is_file():
            raise FileNotFoundError('Imagem do botão não localizada: '+str(source))
        with Image.open(source) as inp:
            external = inp.convert('RGBA').copy()
    frames=[]
    for i in range(6):
        frame=Image.new('RGBA', (144,40),(0,0,0,0))
        d=ImageDraw.Draw(frame)
        active=i in (1,2,4)
        disabled=i==5
        fill=tuple(min(255, x+(16 if active else 0)) for x in base_color)+(255,)
        stroke=tuple(max(0, x-(35 if disabled else 0)) for x in outline)+(255,)
        d.rounded_rectangle((1,1,142,38), radius=8, fill=fill, outline=stroke, width=2)
        if external is not None:
            # Aceita imagem unica ou sprite vertical de seis quadros.
            one_height=external.height//6 if external.height >= 6*30 and external.height>external.width else external.height
            if one_height != external.height:
                patch=external.crop((0,i*one_height,external.width,(i+1)*one_height))
            else:
                patch=external
            patch=ImageOps.fit(patch,(136,32),method=Image.Resampling.LANCZOS)
            frame.alpha_composite(patch,(4,4))
        d=ImageDraw.Draw(frame)
        font=_load_button_font(12)
        bbox=d.textbbox((0,0), label, font=font)
        tw=bbox[2]-bbox[0]; th=bbox[3]-bbox[1]
        d.text(((144-tw)/2-bbox[0],(40-th)/2-bbox[1]),label,font=font,fill=ink)
        frames.append(frame)
    sheet=Image.new('RGBA',(144,240),(0,0,0,0))
    for i,im in enumerate(frames): sheet.alpha_composite(im,(0,i*40))
    return sheet


def make_library_manager_pack(output: Path, library_name: str, cover: Path | None,
                              *, prepare: bool = True) -> Path | None:
    """Gera marcador vazio documentado na tela do gerenciador externo; nao registra SO."""
    if not prepare:
        return None
    output=Path(output)
    output.mkdir(parents=True, exist_ok=True)
    marker=output / f'{library_name}_info.nkx'
    if not marker.exists(): marker.touch()
    if marker.stat().st_size != 0:
        raise ValueError('O arquivo identificador do Library Manager deve ter 0 bytes: '+str(marker))
    if cover is not None and Path(cover).is_file():
        shutil_copy_cover(cover,output/'wallpaper.png')
    (output/'COMO_ADICIONAR_NO_LIBRARY_MANAGER.txt').write_text(
        'CADASTRO NO LIBRARY MANAGER EXTERNO v8.8.0\n'
        '1. Em Options > Libraries, ative Add unencoded libraries created by the empty registration file method.\n'
        '2. Clique em ADD e selecione ESTA pasta (a que possui *_info.nkx).\n'
        '3. Se reconhecida, selecione a biblioteca e importe a capa no comando Wallpaper.\n'
        '4. Clique SAVE no Library Manager. A imagem wallpaper.png e uma sugestao.\n\n'
        'O marcador de 0 bytes nao e uma licenca e nao registra produto no Native Access.\n'
        'Alternativa oficial: Kontakt 8 > Import Content > Custom Libraries > Add.\n',
        encoding='utf-8')
    return marker


def shutil_copy_cover(source: Path, dest: Path) -> None:
    import shutil
    shutil.copyfile(source,dest)


def create_visual_pack(output: Path, identifier: str, *, wallpaper: Path | None = None,
                       icon: Path | None = None, cover: Path | None = None,
                       use_defaults: bool = True, fx_panel: bool = False,
                       fit_mode: str = 'cover', button_image: Path | None = None,
                       button_text: str = 'REDEFINIR', button_style: str = 'Nord Red') -> VisualPack | None:
    """Imagens e txt adjacentes ao .nkr; a criação REAL do .nkr fica no Lua.

    Atenção: a imagem da biblioteca é independente de instrument icon (72x72).
    """
    if not use_defaults and not any((wallpaper, icon, cover)):
        return None
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    prefix = 'NB_' + hashlib.sha256(identifier.encode('utf-8')).hexdigest()[:10]
    path = output / 'Resources' / 'pictures'
    path.mkdir(parents=True, exist_ok=True)
    bundled = installed_assets_dir()
    wsrc = Path(wallpaper) if wallpaper else bundled / 'default_wallpaper.png'
    isrc = Path(icon) if icon else bundled / 'default_icon.png'
    csrc = Path(cover) if cover else wsrc
    wpname = prefix + '_WALL'
    icname = prefix + '_ICON'
    wallpaper_size = (633, 620) if fx_panel else (633, 320)
    _process_image(wsrc, path / f'{wpname}.png', wallpaper_size, fx_panel=fx_panel, fit_mode=fit_mode)
    _process_image(isrc, path / f'{icname}.png', (72, 72))
    (path / f'{wpname}.txt').write_text(standard_picture_txt(), encoding='utf-8')
    (path / f'{icname}.txt').write_text(standard_picture_txt(), encoding='utf-8')
    coverpath = output / f'{identifier}_CAPA_LIBRARY_633x98.png'
    _process_image(csrc, coverpath, (633, 98), fit_mode=fit_mode)
    btnname = prefix + '_RESET'
    make_button_sheet(button_text, button_style, button_image).save(path / f'{btnname}.png')
    (path / f'{btnname}.txt').write_text(standard_picture_txt().replace('Number of Animations: 0','Number of Animations: 6'), encoding='utf-8')
    return VisualPack(nkr=output / f'{identifier}_Resources.nkr', wallpaper_name=wpname,
                      icon_name=icname, cover=coverpath, pictures=path, button_name=btnname)


def add_button_graphic_ksp(code: str, pack: VisualPack | None) -> str:
    """Atualiza SOMENTE o botão REDEFINIR, com sprite; fallback sem NKR fica nativo."""
    if not pack or not pack.button_name or 'declare ui_button $Redefinir' not in code:
        return code
    import re
    code=re.sub(r'(?m)^(\s*)set_text\(\$Redefinir,\s*"REDEFINIR"\)',
                lambda m:m.group(1)+'set_text($Redefinir,"")',code,count=1)
    needle=r'(?m)^(\s*move_control_px\(\$Redefinir,[^\n]*\)\n)'
    additions = ('    set_control_par_str(get_ui_id($Redefinir),$CONTROL_PAR_PICTURE,"'+pack.button_name+'")\n'
                 '    set_control_par(get_ui_id($Redefinir),$CONTROL_PAR_WIDTH,144)\n'
                 '    set_control_par(get_ui_id($Redefinir),$CONTROL_PAR_HEIGHT,40)\n')
    updated,n=re.subn(needle,lambda m:m.group(1)+additions,code,count=1)
    if n!=1: raise ValueError('Nao foi possivel personalizar o botao Redefinir no KSP')
    return updated


def add_visual_ksp(ksp_source: str, pack: VisualPack | None, *, include_wallpaper: bool = True) -> str:
    """Adiciona references em on init; não sobrescreve o restante do som/KSP."""
    if pack is None:
        return ksp_source
    import re
    # Se o KSP original já possuía uma foto/icon, a escolha atual da interface prevalece.
    original = re.sub(r'^\s*set_control_par_str\s*\(\s*\$INST_(?:WALLPAPER|ICON)_ID\s*,[^\n]*\n',
                      '', ksp_source, flags=re.M)
    if re.search(r'\bset_skin_offset\s*\(', original):
        raise ValueError('Este KSP usa wallpaper multipágina (set_skin_offset). Para não quebrar as abas, use o KSP padrão nesta conversão ou adapte a arte multipágina manualmente.')
    # Na conversao automatica, o wallpaper pode ser aplicado pelas opcoes Lua
    # independentemente do NKR. O icone KSP continua opcional, exigindo NKR valido.
    directive = ('' if not include_wallpaper else
                 f'    set_control_par_str($INST_WALLPAPER_ID,$CONTROL_PAR_PICTURE,"{pack.wallpaper_name}")\n')
    directive += f'    set_control_par_str($INST_ICON_ID,$CONTROL_PAR_PICTURE,"{pack.icon_name}")\n'
    if not re.search(r'^on init[ \t]*$', original, flags=re.M):
        raise ValueError('O arquivo KSP precisa ter um bloco "on init" válido.')
    # Wallpaper e ícone são configurados após make_perfview, quando disponível.
    init_end = re.search(r'^end on[ \t]*$', original, flags=re.M)
    if init_end:
        begin = re.search(r'^on init[ \t]*$', original, flags=re.M)
        segment = original[begin.end():init_end.start()]
        m = re.search(r'^[ \t]*make_perfview[ \t]*$', segment, flags=re.M)
        if m:
            offset = begin.end() + m.end()
            return original[:offset] + '\n' + directive.rstrip('\n') + original[offset:]
    merged, occurrences = re.subn(r'(^on init[ \t]*\n)', lambda m: m.group(1) + directive,
                                   original, count=1, flags=re.M)
    if occurrences != 1:
        raise ValueError('Não foi possível colocar as referências gráficas no KSP.')
    return merged
