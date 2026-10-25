"""Nord Kontakt Bridge - interface independente, vermelha e sem BAT."""
from __future__ import annotations

import json
import os
import queue
import re
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk, colorchooser

from .direct_workflow import Prepared, find_decoder, find_kontakt8, prepare, safe_remove_work
from .kontakt_auto import read_status, running_kontakt_processes, start_kontakt
from .visual_assets import installed_assets_dir
from .fx_designer import FXDesign, EFFECTS, DEFAULT_LABELS, make_pages, make_knob_sheet, effect_positions, font_for

BG = '#0f0f14'
PANEL = '#1a181c'
RED = '#e12e3f'
DARK_RED = '#86202d'
FG = '#f8f5f4'
MUTED = '#a7a0a4'
ENTRY = '#282329'


def settings_path() -> Path:
    base = Path(os.environ.get('APPDATA') or Path.home() / '.nord_kontakt_bridge')
    return base / 'NordKontaktBridge' / 'settings.json'


class DirectApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Nord Kontakt Bridge')
        self.geometry('920x860')
        self.minsize(780, 710)
        self.configure(bg=BG)
        self.jobs = queue.Queue()
        self.busy = False
        self.prepared: Prepared | None = None
        self.kontakt_process = None
        self.monitor_started = None
        self.last_log_line = None
        defaults = self.load_settings()
        self.source = tk.StringVar(value='')
        self.name_var = tk.StringVar(value='')
        self.output = tk.StringVar(value='')  # A pessoa escolhe a pasta em cada nova sessão.
        self.kontakt = tk.StringVar(value=defaults.get('kontakt', ''))  # Sem caminho presumido para o executável.
        self.ksp = tk.StringVar(value='')  # Script opcional: sem seleção inicial.
        self.wallpaper = tk.StringVar(value='')  # Campo opcional inicia vazio.
        self.instrument_icon = tk.StringVar(value='')  # Campo opcional inicia vazio.
        self.library_cover = tk.StringVar(value='')  # Campo opcional inicia vazio.
        self.use_theme = tk.BooleanVar(value=True)  # Proteção obrigatória; não pode ser desmarcada.
        self.auto_fx = tk.BooleanVar(value=defaults.get('auto_fx', True))
        self.nkr_template = tk.StringVar(value=defaults.get('nkr_template', ''))
        self.fit_mode = tk.StringVar(value=defaults.get('fit_mode','cover'))
        self.button_image = tk.StringVar(value=defaults.get('button_image',''))
        self.button_text = tk.StringVar(value=defaults.get('button_text','REDEFINIR'))
        self.button_style = tk.StringVar(value=defaults.get('button_style','Nord Red'))
        self.fx_design = FXDesign.from_dict(defaults.get('fx_design'))
        self.fx_enabled = tk.BooleanVar(value=self.fx_design.enabled)
        self.fx_tabs = tk.BooleanVar(value=self.fx_design.tabs)
        self.fx_title = tk.StringVar(value=self.fx_design.title)
        self.fx_font = tk.StringVar(value=self.fx_design.font_family)
        self.fx_layout = tk.StringVar(value=self.fx_design.layout)
        self.fx_knob_style = tk.StringVar(value=self.fx_design.knob_style)
        self.fx_colors = {k: tk.StringVar(value=getattr(self.fx_design,k)) for k in ('title_color','label_color','accent','background')}
        self.fx_labels = [tk.StringVar(value=val) for val in self.fx_design.labels]
        self.fx_view_page = tk.StringVar(value='FX')
        self.prepare_library_manager = tk.BooleanVar(value=defaults.get('prepare_library_manager',True))
        self.status = tk.StringVar(value='Comece na aba Conversão: escolha um .npno Nord, o nome, o destino e Kontakt 8.exe.')
        self.hero_photo = None
        self.preview_images = []
        self._scrollable_canvases = {}
        self._setup()
        self.after(120, self._poll)

    @staticmethod
    def load_settings():
        try:
            return json.loads(settings_path().read_text(encoding='utf-8'))
        except (OSError, ValueError):
            return {}

    def save_settings(self):
        p = settings_path()
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps({
                'kontakt': self.kontakt.get(), 'output': self.output.get(),
                'ksp': self.ksp.get(), 'wallpaper': self.wallpaper.get(),
                'instrument_icon': self.instrument_icon.get(),
                'library_cover': self.library_cover.get(),
                'use_theme': True,
                'auto_fx': self.auto_fx.get(),
                'nkr_template': self.nkr_template.get(),
                'fit_mode': self.fit_mode.get(),
                'button_image': self.button_image.get(),
                'button_text': self.button_text.get(),
                'button_style': self.button_style.get(),
                'prepare_library_manager': self.prepare_library_manager.get(),
                'fx_design': self.collect_fx_design().to_dict(),
            }, indent=2, ensure_ascii=False), encoding='utf-8')
        except OSError:
            pass

    def _label(self, parent, text, hint=''):
        line = tk.Frame(parent, bg=PANEL)
        line.pack(fill='x', padx=22, pady=(7, 3))
        tk.Label(line, text=text, bg=PANEL, fg=FG, font=('Segoe UI', 10, 'bold')).pack(side='left')
        if hint:
            tk.Label(line, text=hint, bg=PANEL, fg=MUTED, font=('Segoe UI', 9)).pack(side='right')

    def _help(self, parent, text, *, highlight=False):
        """Explicação visível logo abaixo do campo, sem exigir abrir manual."""
        label = tk.Label(parent, text=text, bg=PANEL,
                         fg='#f0c8ce' if highlight else '#bfb5b9',
                         font=('Segoe UI', 9), justify='left', anchor='w', wraplength=725)
        label.pack(fill='x', padx=22, pady=(2, 10))
        label.bind('<Configure>', lambda event: label.configure(wraplength=max(300, event.width - 8)))

    def _intro(self, parent, text):
        label = tk.Label(parent, text=text, bg='#312128', fg='#f9e7e8',
                         font=('Segoe UI', 10), justify='left', anchor='w',
                         wraplength=715, padx=12, pady=10)
        label.pack(fill='x', padx=22, pady=(12, 12))
        label.bind('<Configure>', lambda event: label.configure(wraplength=max(300, event.width - 30)))

    def _scroll_frame(self, tab):
        """Monta o painel rolável e registra a sua aba para a roda do mouse."""
        canvas = tk.Canvas(tab, bg=PANEL, highlightthickness=0)
        scroll = ttk.Scrollbar(tab, orient='vertical', command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)
        inner = tk.Frame(canvas, bg=PANEL)
        item = canvas.create_window((0, 0), window=inner, anchor='nw')
        inner.bind('<Configure>', lambda _e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>', lambda event: canvas.itemconfigure(item, width=event.width))
        self._scrollable_canvases[str(tab)] = canvas
        return inner

    def _on_mousewheel(self, event):
        """Rola a aba visível mesmo com o cursor sobre labels, campos e prévias.

        O evento é acompanhado pela posição do mouse para não deslocar a aba
        quando a roda é usada sobre o cabeçalho, botões do rodapé ou diálogos.
        """
        if not self.notebook.winfo_exists():
            return
        canvas = self._scrollable_canvases.get(self.notebook.select())
        if canvas is None or not canvas.winfo_viewable():
            return
        x, y = event.x_root, event.y_root
        left, top = canvas.winfo_rootx(), canvas.winfo_rooty()
        if not (left <= x < left + canvas.winfo_width()
                and top <= y < top + canvas.winfo_height()):
            return
        if getattr(event, 'num', None) in (4, 5):
            steps = -1 if event.num == 4 else 1
        else:
            delta = getattr(event, 'delta', 0)
            if not delta:
                return
            steps = (-1 if delta > 0 else 1) * max(1, round(abs(delta) / 120))
        canvas.yview_scroll(steps, 'units')
        return 'break'

    def _row(self, parent, variable, browse, placeholder=''):
        row = tk.Frame(parent, bg=PANEL)
        row.pack(fill='x', padx=22, pady=(0, 2))
        entry = tk.Entry(row, textvariable=variable, bg=ENTRY, fg=FG,
                         insertbackground=FG, relief='flat', font=('Segoe UI', 10),
                         highlightthickness=1, highlightbackground='#373035', highlightcolor=RED)
        entry.pack(side='left', fill='x', expand=True, ipady=9)
        tk.Button(row, text='Selecionar', command=browse, bg='#4b343b', fg='white',
                  activebackground=DARK_RED, activeforeground='white', relief='flat',
                  font=('Segoe UI', 9, 'bold'), padx=12, pady=8, cursor='hand2').pack(side='right', padx=(7, 0))

    def _setup(self):
        frame = tk.Frame(self, bg=BG)
        frame.pack(fill='x', padx=20, pady=(12, 3))
        canvas = tk.Canvas(frame, height=145, bg='#3c0612', highlightthickness=0)
        canvas.pack(fill='x')
        try:
            self.hero_photo = tk.PhotoImage(file=str(installed_assets_dir() / 'hero_red.png'))
            canvas.create_image(0, 0, anchor='nw', image=self.hero_photo)
        except tk.TclError:
            pass
        canvas.create_text(25, 34, anchor='nw', text='NORD', fill='#ff5364', font=('Segoe UI', 12, 'bold'))
        canvas.create_text(25, 58, anchor='nw', text='KONTAKT BRIDGE', fill='white',
                           font=('Segoe UI', 25, 'bold'))
        canvas.create_text(26, 108, anchor='nw', text='PIANOS NORD .NPNO  •  PERSONALIZAR  •  CONVERTER EM .NKI',
                           fill='#ead5d8', font=('Segoe UI', 10))
        canvas.create_text(26, 130, anchor='nw', text='Aplicativo independente • não afiliado à Nord ou Native Instruments',
                           fill='#c4a5ab', font=('Segoe UI', 8))

        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('Nord.TNotebook', background=BG, borderwidth=0)
        style.configure('Nord.TNotebook.Tab', background='#34232a', foreground='#f1dfe3',
                        padding=(20, 10), font=('Segoe UI', 10, 'bold'))
        style.map('Nord.TNotebook.Tab', background=[('selected', RED)], foreground=[('selected', '#ffffff')])
        style.configure('Nord.Horizontal.TProgressbar', troughcolor='#35232a', background=RED, bordercolor=BG)

        self.notebook = ttk.Notebook(self, style='Nord.TNotebook')
        self.notebook.pack(fill='both', expand=True, padx=20, pady=(4, 6))
        self.page_convert = tk.Frame(self.notebook, bg=PANEL)
        self.page_visual = tk.Frame(self.notebook, bg=PANEL)
        self.notebook.add(self.page_convert, text='  01  CONVERSÃO  ')
        self.notebook.add(self.page_visual, text='  02  IDENTIDADE VISUAL  ')
        self.page_fx_editor = tk.Frame(self.notebook, bg=PANEL)
        self.notebook.add(self.page_fx_editor, text='  03  EDITOR FX  ')

        c = self._scroll_frame(self.page_convert)
        self._intro(c, 'BEM-VINDO! Este programa converte arquivos de piano .npno da Nord em instrumentos .nki para o Kontakt 8. Não converte arquivos de outras marcas nem outros formatos. Preencha os campos obrigatórios antes de iniciar.')
        self._label(c, 'Arquivo de piano Nord (.npno)', 'OBRIGATÓRIO')
        self._row(c, self.source, self.select_source)
        self._help(c, 'Selecione aqui o piano da Nord que você quer converter. Ele precisa estar no formato .npno, usado pela Nord Piano Library. O arquivo original não é apagado.')
        self._label(c, 'Nome do instrumento', 'OBRIGATÓRIO')
        tk.Entry(c, textvariable=self.name_var, bg=ENTRY, fg=FG, relief='flat',
                 insertbackground=FG, font=('Segoe UI', 10),
                 highlightthickness=1, highlightbackground='#373035', highlightcolor=RED).pack(fill='x', padx=22, ipady=9)
        self._help(c, 'Digite o nome que seu instrumento terá no Kontakt. Esse nome identifica a pasta e o arquivo .nki criados. Exemplo: Meu Piano Nord.')
        self._label(c, 'Pasta principal de saída', 'OBRIGATÓRIO • ESCOLHA ONDE SALVAR')
        self._row(c, self.output, self.select_output)
        self._help(c, 'Clique em Selecionar e escolha uma pasta do computador. O Nord Kontakt Bridge criará uma subpasta com o nome do instrumento, contendo o .nki e os arquivos de áudio em Samples. Este campo começa vazio.')
        self._label(c, 'Executável do Kontakt 8 (.exe)', 'OBRIGATÓRIO')
        self._row(c, self.kontakt, self.select_kontakt)
        self._help(c, 'Localize a pasta onde você instalou o Kontakt 8 e selecione Kontakt 8.exe (a versão independente/standalone). O Kontakt precisa estar fechado antes da conversão.')
        self._label(c, 'KSP personalizado', 'OPCIONAL')
        self._row(c, self.ksp, self.select_ksp)
        self._help(c, 'KSP é um script que controla recursos e comportamentos do instrumento dentro do Kontakt. Se você tiver um arquivo .ksp próprio, selecione-o. Caso contrário, deixe o campo vazio: não é necessário criar um script.')
        tk.Checkbutton(c, text='Adicionar automaticamente REVERB, DELAY, CHORUS, EQ e controles',
                       variable=self.auto_fx, bg=PANEL, fg=FG, activeforeground=FG,
                       activebackground=PANEL, selectcolor='#4a232c', font=('Segoe UI', 9, 'bold'),
                       wraplength=730, justify='left').pack(anchor='w', padx=22, pady=(5, 2))
        self._help(c, 'RECOMENDADO: mantenha marcado para criar controles básicos de efeitos automaticamente. Eles começam com configurações neutras. Se usar KSP próprio, ele será colocado em outro slot. Esta opção é diferente da preparação para Library Manager.', highlight=True)
        self._intro(c, 'RESULTADO: ao converter, o programa prepara as amostras em WAV e usa o Kontakt 8 para criar um instrumento .nki. Mantenha a pasta Samples junto do .nki. A geração final depende do Kontakt e deve ser conferida nele.')

        v = self._scroll_frame(self.page_visual)
        self._intro(v, 'IDENTIDADE VISUAL — OPCIONAL. Aqui você escolhe imagens e ajusta a aparência do instrumento. Se deixar os campos de imagens vazios, o programa utiliza o wallpaper e o ícone padrão automaticamente.')
        self._label(v, 'Wallpaper do instrumento', 'OPCIONAL • 633 × 320 px (área superior)')
        self._row(v, self.wallpaper, self.select_wallpaper)
        self._help(v, 'O wallpaper é a imagem de fundo exibida no instrumento dentro do Kontakt. Escolha uma imagem sua, ou deixe em branco para usar o wallpaper vermelho padrão.')
        self._label(v, 'Enquadramento', 'OPCIONAL • COMO EXIBIR A IMAGEM')
        choices=tk.Frame(v,bg=PANEL)
        choices.pack(anchor='w', padx=22)
        for value, label in [('cover','Preencher largura'),('contain','Mostrar imagem inteira')]:
            tk.Radiobutton(choices,text=label,variable=self.fit_mode,value=value,bg=PANEL,fg=FG,
                           activebackground=PANEL,activeforeground=FG,selectcolor='#4a232c').pack(side='left',padx=(0,22))
        self._help(v, 'Preencher largura amplia e recorta as bordas, se necessário. Mostrar imagem inteira mantém tudo visível, mas pode deixar espaços ao redor.')
        self._label(v, 'Ícone do instrumento', 'OPCIONAL • 72 × 72 px')
        self._row(v, self.instrument_icon, self.select_icon)
        self._help(v, 'O ícone identifica visualmente o instrumento no cabeçalho do Kontakt. Se não selecionar uma imagem, será usado o ícone padrão.')
        self._label(v, 'Capa da biblioteca', 'OPCIONAL • 633 × 98 px')
        self._row(v, self.library_cover, self.select_cover)
        self._help(v, 'A capa representa a biblioteca no pacote preparado para o Library Manager. Não é a mesma imagem que aparece no cabeçalho do instrumento. Você pode deixar este campo vazio.')
        self._label(v, 'Botão REDEFINIR — imagem personalizada', 'OPCIONAL')
        self._row(v,self.button_image,self.select_button)
        self._help(v, 'Este botão devolve os controles de efeitos às configurações iniciais. Você pode escolher outra imagem para ele, ou deixar vazio para usar o visual padrão. Personalizar é opcional; o botão continua funcional.')
        self._label(v, 'Texto do botão REDEFINIR', 'OPCIONAL')
        tk.Entry(v,textvariable=self.button_text,bg=ENTRY,fg=FG,relief='flat',
                 insertbackground=FG,font=('Segoe UI',10)).pack(fill='x',padx=22,ipady=7)
        self._help(v, 'Troque a palavra exibida no botão, se quiser. Se não alterar, o texto será REDEFINIR.')
        self._label(v, 'Estilo do botão', 'OPCIONAL')
        tk.OptionMenu(v,self.button_style,'Nord Red','Dourado','Cinza').pack(anchor='w',padx=22)
        self._help(v, 'Escolha uma das cores prontas para o botão. Você não precisa preparar animações ou imagens em vários estados: o programa cuida disso.')
        tk.Checkbutton(v,text='Preparar pasta para Library Manager v8.8.0 (*_info.nkx + wallpaper.png)',
                       variable=self.prepare_library_manager,bg=PANEL,fg=FG,activeforeground=FG,
                       activebackground=PANEL,selectcolor='#4a232c').pack(anchor='w',padx=22,pady=(8,3))
        self._help(v, 'RECOMENDADO: mantenha marcado para preparar os arquivos usados na etapa de ADD do Library Manager. Isso não adiciona a biblioteca sozinho, não registra licenças e não modifica o Windows.', highlight=True)
        self._label(v, 'Arquivo .nkr de recursos', 'MODELO EXISTENTE • SE DISPONÍVEL')
        self._row(v, self.nkr_template, self.select_nkr)
        self._help(v, 'O .nkr reúne recursos de imagem utilizados pelo Kontakt. Se você recebeu um .nkr junto com o programa, selecione o caminho dele aqui. ATENÇÃO: esta distribuição não inclui esse arquivo. O aplicativo também pode localizar um .nkr válido do seu próprio projeto; não cria um .nkr real do zero.', highlight=True)
        check = tk.Checkbutton(v, text='Usar wallpaper e ícone padrão quando não selecionar imagens',
                               variable=self.use_theme, bg=PANEL, fg='#f2e9eb', activebackground=PANEL,
                               activeforeground=FG, selectcolor='#4a232c', font=('Segoe UI', 9),
                               state='disabled', disabledforeground='#f2e9eb')
        check.pack(anchor='w', padx=22, pady=(10, 8))
        self._help(v, 'OBRIGATÓRIO: esta opção fica sempre marcada e não pode ser desativada. Assim, se você não escolher wallpaper ou ícone próprios, serão utilizadas as imagens padrão. Isso não dispensa um .nkr válido quando o Kontakt exigir contêiner de recursos.', highlight=True)
        self.preview_frame = tk.Frame(v, bg=PANEL)
        self.preview_frame.pack(fill='x', padx=22, pady=(9, 6))
        self.preview = tk.Label(self.preview_frame, bg='#150c0f', fg=MUTED,
                                text='Prévia do wallpaper padrão', height=5)
        self.preview.pack(fill='x')
        for var in (self.wallpaper, self.instrument_icon, self.library_cover, self.fit_mode):
            var.trace_add('write', lambda *_: self._update_preview())
        self._update_preview()
        self.button_preview = tk.Label(v, bg=PANEL)
        self.button_preview.pack(anchor='w', padx=22, pady=(7,8))
        for var in (self.button_image,self.button_text,self.button_style):
            var.trace_add('write', lambda *_: self._update_button_preview())
        self._update_button_preview()

        self._build_fx_editor()

        # Um único manipulador atende todas as abas, inclusive os controles
        # internos do Editor FX. Evita bind_all/unbind_all conflitantes ao
        # atravessar os elementos da interface com o mouse.
        self.bind_all('<MouseWheel>', self._on_mousewheel, add='+')
        self.bind_all('<Button-4>', self._on_mousewheel, add='+')
        self.bind_all('<Button-5>', self._on_mousewheel, add='+')

        footer = tk.Frame(self, bg=BG)
        footer.pack(fill='x', padx=20, pady=(4, 2))
        self.convert_btn = tk.Button(footer, text='CONVERTER PARA NKI', command=self.start,
                                     bg=RED, fg='white', activebackground='#ff5262',
                                     activeforeground='white', relief='flat', cursor='hand2',
                                     font=('Segoe UI', 11, 'bold'), padx=19, pady=13)
        self.convert_btn.pack(side='left')
        tk.Button(footer, text='Abrir Lua / logs', command=self.open_log_dir, bg='#422830', fg=FG,
                  relief='flat', padx=12, pady=13).pack(side='left', padx=(9, 0))
        tk.Button(footer, text='Limpar cache', command=self.clear_cache, bg='#422830', fg=FG,
                  relief='flat', padx=12, pady=13).pack(side='left', padx=(9, 0))
        self.progress = ttk.Progressbar(self, style='Nord.Horizontal.TProgressbar', mode='determinate', maximum=100)
        self.progress.pack(fill='x', padx=20, pady=(9, 5))
        tk.Label(self, textvariable=self.status, bg=BG, fg='#d6bac0', font=('Segoe UI', 9),
                 wraplength=840, justify='left', anchor='w').pack(fill='x', padx=20, pady=(0, 10))

    def collect_fx_design(self) -> FXDesign:
        base = FXDesign(
            enabled=self.fx_enabled.get(), tabs=self.fx_tabs.get(),
            title=self.fx_title.get().strip()[:35] or 'SOUND / FX',
            labels=tuple(v.get().strip()[:24] or d for v,d in zip(self.fx_labels,DEFAULT_LABELS)),
            font_family=self.fx_font.get(),
            knob_style=self.fx_knob_style.get(),layout=self.fx_layout.get(),
            reset_label=self.button_text.get().strip()[:22] or 'REDEFINIR',
            **{k:v.get() for k,v in self.fx_colors.items()})
        return base

    def _build_fx_editor(self):
        # Usa o mesmo sistema de rolagem das abas Conversão e Identidade Visual.
        inner = self._scroll_frame(self.page_fx_editor)

        self._intro(inner, 'EDITOR FX — OPCIONAL. Personalize os efeitos da maneira que preferir, sem precisar editar o código KSP manualmente. Se não quiser mudar nada, pode ignorar esta aba e manter o visual padrão.')
        top=tk.Frame(inner,bg=PANEL)
        top.pack(fill='x',padx=22,pady=(10,3))
        tk.Checkbutton(top,text='Ativar editor visual FX',variable=self.fx_enabled,
                       bg=PANEL,fg=FG,selectcolor='#5C2430',activeforeground=FG,
                       activebackground=PANEL,font=('Segoe UI',10,'bold')).pack(side='left')
        tk.Checkbutton(top,text='Duas abas PIANO / FX',variable=self.fx_tabs,
                       bg=PANEL,fg=FG,selectcolor='#5C2430',activeforeground=FG,
                       activebackground=PANEL,font=('Segoe UI',10,'bold')).pack(side='left',padx=(24,0))
        self._help(inner, 'Ativar editor visual FX: aplica as suas personalizações. Duas abas PIANO / FX: mostra botões para alternar entre as páginas do instrumento. Desmarque se não quiser essa apresentação. A prévia de fontes e cores é aproximada.')
        self._label(inner,'Título principal dos efeitos','OPCIONAL • Ex.: EFEITOS')
        tk.Entry(inner,textvariable=self.fx_title,bg=ENTRY,fg=FG,insertbackground=FG,relief='flat',
                 font=('Segoe UI',11)).pack(fill='x',padx=22,ipady=6)
        self._help(inner, 'Escolha o título que aparecerá na área dos efeitos. Você pode usar EFEITOS, SOUND / FX ou outro nome de sua preferência.')
        line=tk.Frame(inner,bg=PANEL);line.pack(fill='x',padx=22,pady=(10,0))
        for title,var,items in [
            ('Fonte dos títulos',self.fx_font,('Segoe UI','Arial','Georgia','Consolas','Trebuchet MS','Times New Roman')),
            ('Estilo dos knobs',self.fx_knob_style,('Nord Red','Dourado','Prata','Minimal')),
            ('Organização',self.fx_layout,('3 colunas','4 colunas'))]:
            block=tk.Frame(line,bg=PANEL);block.pack(side='left',fill='x',expand=True,padx=(0,12))
            tk.Label(block,text=title,bg=PANEL,fg=FG,font=('Segoe UI',9,'bold')).pack(anchor='w')
            ttk.Combobox(block,textvariable=var,values=items,state='readonly',width=17).pack(fill='x',pady=(4,0))
        self._help(inner, 'Fonte dos títulos: escolha o tipo de letra. Estilo dos knobs: escolha a aparência dos controles giratórios. Organização: escolha como os efeitos ficam distribuídos na tela.')
        self._label(inner,'Cores da interface','OPCIONAL • Escolha as cores')
        color_line=tk.Frame(inner,bg=PANEL);color_line.pack(fill='x',padx=22)
        for key,title in [('background','Fundo'),('accent','Detalhes'),('title_color','Título'),('label_color','Nomes')]:
            cell=tk.Frame(color_line,bg=PANEL);cell.pack(side='left',padx=(0,14),fill='x',expand=True)
            tk.Label(cell,text=title,fg=FG,bg=PANEL,font=('Segoe UI',9)).pack(anchor='w')
            var=self.fx_colors[key]
            swatch=tk.Button(cell,textvariable=var,bg=var.get(),fg='white',relief='flat',width=10,
                             command=lambda v=var:self._choose_fx_color(v))
            swatch.pack(fill='x',pady=(4,0))
            var.trace_add('write',lambda *_,b=swatch,v=var:b.configure(bg=v.get()))
        self._help(inner, 'Clique nas amostras para personalizar as cores do fundo, dos detalhes, do título e dos nomes dos efeitos. Você pode manter os valores padrão.')
        self._label(inner,'Nomes dos oito efeitos','OPCIONAL • Edite as legendas')
        effect_grid=tk.Frame(inner,bg=PANEL);effect_grid.pack(fill='x',padx=22)
        for i,(var,default) in enumerate(zip(self.fx_labels,DEFAULT_LABELS)):
            item=tk.Frame(effect_grid,bg=PANEL);item.grid(row=i//4,column=i%4,sticky='ew',padx=(0,12),pady=(0,9))
            tk.Label(item,text=default,bg=PANEL,fg=MUTED,font=('Segoe UI',8)).pack(anchor='w')
            tk.Entry(item,textvariable=var,bg=ENTRY,fg=FG,insertbackground=FG,relief='flat',
                     width=15,font=('Segoe UI',9)).pack(fill='x',ipady=5,pady=(2,0))
        for i in range(4):effect_grid.columnconfigure(i,weight=1)
        self._help(inner, 'Altere os nomes exibidos abaixo de cada knob, como REVERB, DELAY e CHORUS. Não é necessário escrever KSP: digite somente os nomes que deseja mostrar.')
        toggle=tk.Frame(inner,bg=PANEL);toggle.pack(fill='x',padx=22,pady=(9,4))
        tk.Label(toggle,text='PRÉVIA DO PAINEL:',fg=FG,bg=PANEL,font=('Segoe UI',9,'bold')).pack(side='left')
        for value in ('PIANO','FX'):
            tk.Radiobutton(toggle,text=value,value=value,variable=self.fx_view_page,
                           bg=PANEL,fg=FG,selectcolor='#762835',activebackground=PANEL,
                           activeforeground=FG).pack(side='left',padx=10)
        self.fx_preview=tk.Label(inner,text='Carregando prévia...',fg=FG,bg=BG)
        self.fx_preview.pack(anchor='center',padx=22,pady=(0,12))
        self._help(inner, 'A prévia alterna entre PIANO e FX para você visualizar a aparência antes da conversão. O resultado final deve ser verificado dentro do Kontakt 8.')
        btnrow=tk.Frame(inner,bg=PANEL);btnrow.pack(fill='x',padx=22,pady=(0,16))
        tk.Button(btnrow,text='Salvar preset visual (.json)',bg=DARK_RED,fg='white',relief='flat',
                  command=self._export_fx_preset,padx=10,pady=7).pack(side='left')
        tk.Button(btnrow,text='Carregar preset visual',bg='#48313A',fg='white',relief='flat',
                  command=self._import_fx_preset,padx=10,pady=7).pack(side='left',padx=(8,0))
        tk.Button(btnrow,text='VALIDAR KSP',bg='#67313B',fg='white',relief='flat',
                  command=self._validate_fx_ksp,padx=10,pady=7).pack(side='left',padx=(8,0))
        tk.Label(btnrow,text='Validacao preventiva; compilacao final no Kontakt.',bg=PANEL,fg=MUTED,
                 font=('Segoe UI',8)).pack(side='left',padx=12)
        self._help(inner, 'Salvar preset: guarda suas preferências de design em um .json. Carregar preset: restaura um design salvo. Validar KSP: procura erros comuns, mas não substitui a compilação no Kontakt.')
        vars_to_watch=[self.fx_enabled,self.fx_tabs,self.fx_title,self.fx_font,self.fx_layout,
                       self.fx_knob_style,self.fx_view_page,self.wallpaper,self.fit_mode,*self.fx_colors.values(),*self.fx_labels]
        for var in vars_to_watch:var.trace_add('write',lambda *_:self._update_fx_preview())
        self._update_fx_preview()

    def _choose_fx_color(self,var):
        c=colorchooser.askcolor(color=var.get(),title='Escolher cor da interface FX')[1]
        if c:var.set(c)

    def _export_fx_preset(self):
        path=filedialog.asksaveasfilename(title='Salvar design FX',defaultextension='.json',filetypes=[('JSON','*.json')])
        if path:
            from .fx_designer import save_design
            save_design(self.collect_fx_design(),Path(path))

    def _import_fx_preset(self):
        path=filedialog.askopenfilename(title='Carregar design FX',filetypes=[('JSON','*.json')])
        if not path:return
        try:
            conf=FXDesign.from_dict(json.loads(Path(path).read_text(encoding='utf-8')))
            self.fx_enabled.set(conf.enabled);self.fx_tabs.set(conf.tabs)
            self.fx_title.set(conf.title);self.fx_font.set(conf.font_family)
            self.fx_layout.set(conf.layout);self.fx_knob_style.set(conf.knob_style)
            for key,var in self.fx_colors.items():var.set(getattr(conf,key))
            for var,val in zip(self.fx_labels,conf.labels):var.set(val)
        except (OSError,ValueError,TypeError) as e:messagebox.showerror('Preset inválido',str(e))

    def _validate_fx_ksp(self):
        """Valida preventivamente o codigo do editor antes de converter audio."""
        from types import SimpleNamespace
        from .default_fx import build_default_fx_ksp
        from .fx_designer import design_ksp, validate_fx_design
        from .ksp_validation import require_valid_ksp
        from .visual_assets import add_button_graphic_ksp
        try:
            conf=self.collect_fx_design()
            validate_fx_design(conf)
            pack=SimpleNamespace(wallpaper_name='NB_VALIDACAO_WALL',button_name='NB_VALIDACAO_RESET')
            src=build_default_fx_ksp(self.name_var.get().strip() or 'INSTRUMENTO')
            if conf.enabled:
                src=design_ksp(add_button_graphic_ksp(src,pack),pack,conf)
            require_valid_ksp(src,'Editor FX')
            messagebox.showinfo('KSP - verificacao preventiva',
                'Sem erros identificados nas verificacoes de controles, callbacks e blocos.\n\n'
                'Ainda e preciso compilar no Kontakt para validar a API e a reproducao de audio.')
        except (ValueError, TypeError, AttributeError) as exc:
            messagebox.showerror('KSP invalido',str(exc))

    def _update_fx_preview(self):
        if not hasattr(self,'fx_preview'):return
        try:
            from PIL import Image,ImageTk
            from .fx_designer import preview_page
            conf=self.collect_fx_design()
            path=Path(self.wallpaper.get()) if self.wallpaper.get().strip() else installed_assets_dir()/'default_wallpaper.png'
            full=make_pages(path,conf)
            img=preview_page(full,conf,self.fx_view_page.get())
            thumb=img.resize((440,431),Image.Resampling.LANCZOS)
            self._fx_photo=ImageTk.PhotoImage(thumb)
            self.fx_preview.configure(image=self._fx_photo,text='')
        except Exception as e:
            self.fx_preview.configure(image='',text='Prévia indisponível: '+str(e))

    def _update_preview(self):
        file = self.wallpaper.get().strip()
        image = Path(file) if file else installed_assets_dir() / 'default_wallpaper.png'
        try:
            from PIL import Image, ImageTk, ImageOps
            with Image.open(image) as im:
                region = (540, 273)  # mesma proporção do wallpaper 633x320
                rgba = im.convert('RGBA')
                if self.fit_mode.get() == 'cover':
                    pic = ImageOps.fit(rgba, region)
                else:
                    pic = ImageOps.contain(rgba, region)
                composed = Image.new('RGBA', region, (22, 9, 15, 255))
                composed.alpha_composite(pic, ((region[0]-pic.width)//2,(region[1]-pic.height)//2))
            self.preview_image = ImageTk.PhotoImage(composed)
            self.preview.configure(image=self.preview_image, text='', height=273)
        except Exception:
            self.preview.configure(image='', text='Prévia indisponível (Pillow necessário para imagens personalizadas)', height=5)

    def select_source(self):
        path = filedialog.askopenfilename(title='Escolha um piano Nord (.npno)', filetypes=[('Nord Piano (.npno)', '*.npno')])
        if path:
            self.source.set(path)
            # O nome é obrigatório e deve ser escolhido pelo usuário.

    def select_output(self):
        path = filedialog.askdirectory(title='Onde salvar o NKI final?')
        if path:
            self.output.set(path)

    def select_kontakt(self):
        path = filedialog.askopenfilename(title='Selecione Kontakt 8.exe', filetypes=[('Executáveis', '*.exe')])
        if path:
            self.kontakt.set(path)

    def select_ksp(self):
        path = filedialog.askopenfilename(filetypes=[('KSP', '*.ksp')])
        if path:
            self.ksp.set(path)

    def _select_picture(self, var, title):
        path = filedialog.askopenfilename(title=title, filetypes=[('Imagens', '*.png *.jpg *.jpeg *.webp *.bmp')])
        if path:
            var.set(path)
            self.notebook.select(self.page_visual)

    def select_wallpaper(self):
        self._select_picture(self.wallpaper, 'Wallpaper do instrumento')

    def select_icon(self):
        self._select_picture(self.instrument_icon, 'Ícone do cabeçalho do NKI')

    def select_cover(self):
        self._select_picture(self.library_cover, 'Capa do Library Manager')

    def select_button(self):
        self._select_picture(self.button_image, 'Imagem do botão (PNG ou JPG)')

    def _update_button_preview(self):
        if not hasattr(self, 'button_preview'):
            return
        try:
            from PIL import ImageTk
            from .visual_assets import make_button_sheet
            path=Path(self.button_image.get()) if self.button_image.get().strip() else None
            sprite=make_button_sheet(self.button_text.get(),self.button_style.get(),path)
            self._button_preview_photo=ImageTk.PhotoImage(sprite.crop((0,0,144,40)))
            self.button_preview.configure(image=self._button_preview_photo,text='')
        except Exception:
            self.button_preview.configure(image='',text='Prévia indisponível')

    def select_nkr(self):
        path = filedialog.askopenfilename(title='Selecione um arquivo .nkr válido do seu projeto', filetypes=[('Resource Container', '*.nkr')])
        if path:
            self.nkr_template.set(path)

    def start(self):
        if self.busy:
            return
        if not self.source.get().strip():
            self.notebook.select(self.page_convert)
            messagebox.showwarning('Arquivo Nord obrigatório',
                'Selecione primeiro um arquivo de piano .npno da Nord. Este programa não converte outros formatos.')
            return
        if not self.name_var.get().strip():
            self.notebook.select(self.page_convert)
            messagebox.showwarning('Nome obrigatório',
                'Digite um nome para o instrumento antes de converter. Exemplo: Meu Piano Nord.')
            return
        if not self.output.get().strip():
            self.notebook.select(self.page_convert)
            messagebox.showwarning('Pasta de saída obrigatória',
                'Clique em Selecionar e escolha a pasta onde deseja salvar a biblioteca .nki.')
            return
        if not self.kontakt.get().strip():
            self.notebook.select(self.page_convert)
            messagebox.showwarning('Kontakt 8 obrigatório',
                'Clique em Selecionar e indique o arquivo Kontakt 8.exe da instalação standalone.')
            return
        path = Path(self.source.get().strip())
        if not path.is_file() or path.suffix.lower() != '.npno':
            messagebox.showwarning('Arquivo Nord inválido',
                'Selecione um arquivo .npno válido da Nord Piano Library. Arquivos .npmo não são compatíveis com este conversor.')
            return
        if not find_decoder():
            messagebox.showerror('Decoder Nord ausente',
                                 'Não encontrei nord.exe. Se você já instalou nord-cli, reinicie o programa.\n'
                                 'Também pode copiar nord.exe para a pasta do aplicativo.\n'
                                 'Não é necessário executar nenhum BAT.')
            return
        kontakt = Path(self.kontakt.get().strip())
        if not kontakt.is_file() or kontakt.suffix.lower() != '.exe' or 'kontakt' not in kontakt.stem.lower():
            messagebox.showerror('Kontakt não encontrado',
                                 'Selecione o executável Kontakt 8.exe completo na própria interface.\n'
                                 'O NKI será gerado automaticamente sem BAT nem F11.')
            return
        if running_kontakt_processes(kontakt):
            messagebox.showwarning('Feche o Kontakt antes de converter',
                                   'O Kontakt já está aberto. Feche-o normalmente, salvando seus trabalhos, '
                                   'e clique novamente em CONVERTER AUTOMATICAMENTE.\n\n'
                                   'O programa não vai fechar suas sessões nem fingir que executou o Lua.')
            return
        output = Path(self.output.get().strip()).expanduser()
        if output.exists() and not output.is_dir():
            messagebox.showwarning('Pasta inválida', 'O destino selecionado não é uma pasta. Escolha outra pasta.')
            return
        ksp = Path(self.ksp.get()) if self.ksp.get().strip() else None
        if ksp is not None and (not ksp.is_file() or ksp.suffix.lower() != '.ksp'):
            messagebox.showwarning('KSP opcional inválido', 'Escolha um arquivo .ksp existente ou deixe o campo em branco.')
            return
        self.use_theme.set(True)
        self.save_settings()
        self.busy = True
        self.convert_btn.configure(state='disabled')
        self.progress['value'] = 0
        self.status.set('Iniciando conversão interna...')
        def progress(i, total, note):
            self.jobs.put(('progress', i * 100 // max(total, 1), note))
        def run():
            try:
                prepared = prepare(path, output, self.name_var.get(), progress, ksp_source=ksp,
                                   wallpaper=Path(self.wallpaper.get()) if self.wallpaper.get().strip() else None,
                                   icon=Path(self.instrument_icon.get()) if self.instrument_icon.get().strip() else None,
                                   cover=Path(self.library_cover.get()) if self.library_cover.get().strip() else None,
                                   use_default_visuals=self.use_theme.get(),
                                   auto_fx=self.auto_fx.get(),
                                   nkr_template=Path(self.nkr_template.get()) if self.nkr_template.get().strip() else None,
                                   fit_mode=self.fit_mode.get(),
                                   button_image=Path(self.button_image.get()) if self.button_image.get().strip() else None,
                                   button_text=self.button_text.get(), button_style=self.button_style.get(),
                                   prepare_library_manager=self.prepare_library_manager.get(),
                                   fx_design=self.collect_fx_design())
                self.jobs.put(('done', prepared))
            except Exception as exc:
                self.jobs.put(('error', str(exc)))
        threading.Thread(target=run, daemon=True).start()

    def _poll(self):
        try:
            while True:
                typ, *data = self.jobs.get_nowait()
                if typ == 'progress':
                    self.progress['value'] = data[0]
                    self.status.set(data[1])
                elif typ == 'error':
                    self.busy = False
                    self.convert_btn.configure(state='normal')
                    self.status.set('Falhou: ' + data[0])
                    messagebox.showerror('Não foi possível gerar', data[0])
                elif typ == 'done':
                    self.progress['value'] = 70
                    self.prepared = data[0]
                    self._launch_or_guide(data[0])
        except queue.Empty:
            pass
        self._monitor_kontakt()
        self.after(600, self._poll)

    def _finish_job(self):
        self.busy = False
        self.convert_btn.configure(state='normal')
        self.kontakt_process = None
        self.monitor_started = None

    def _launch_or_guide(self, p: Prepared):
        kontakt = Path(self.kontakt.get().strip()) if self.kontakt.get().strip() else find_kontakt8()
        if not kontakt or not kontakt.is_file():
            self._finish_job()
            messagebox.showerror('Kontakt não localizado',
                                 'O arquivo Lua está preparado, mas não encontrei Kontakt 8.exe. '
                                 'Escolha o executável e tente novamente.')
            return
        try:
            # Descarta logs de execucoes anteriores para nao declarar sucesso antigo.
            p.export.log.write_text('', encoding='utf-8')
            self.kontakt_process = start_kontakt(
                kontakt, p.export.lua,
                terminal_log=p.export.log.with_name(p.export.log.stem + '_TERMINAL.txt'))
        except (OSError, RuntimeError, ValueError) as exc:
            self._finish_job()
            self.status.set('Nao foi possivel iniciar a conversao no Kontakt.')
            messagebox.showerror('Automação interrompida', str(exc))
            return
        self.monitor_started = time.monotonic()
        self.last_log_line = None
        self.status.set(f'Kontakt iniciado com Lua: {p.export.zones} zonas. Aguardando o NKI real...')

    def _monitor_kontakt(self):
        if not self.kontakt_process or not self.prepared or self.monitor_started is None:
            return
        status = read_status(self.prepared.export.log, self.prepared.export.nki, self.prepared.export.artwork.nkr if self.prepared.export.artwork else None)
        if status.description != self.last_log_line:
            self.status.set(status.description)
            self.last_log_line = status.description
            match = re.search(r'ZONAS IMPORTADAS:\s*(\d+)/(\d+)', status.description)
            if match and int(match.group(2)) > 0:
                self.progress['value'] = min(95, 70 + 25 * int(match.group(1)) / int(match.group(2)))
            elif 'SALVANDO NKI + SAMPLES' in status.description:
                self.progress['value'] = 97
        if status.state == 'partial':
            self.progress['value'] = 100
            self._finish_job()
            messagebox.showwarning('NKI gerado sem imagens',
                                   status.description + '\n\nO som e os efeitos precisam ser testados no Kontakt. '
                                   'O programa nao conseguiu criar o NKR; para ter wallpaper, crie/vincule o Resource Container no Kontakt antes de salvar uma nova copia.')
        elif status.state == 'success':
            self.progress['value'] = 100
            result = str(self.prepared.export.nki)
            self._finish_job()
            messagebox.showinfo('NKI criado!',
                                'Kontakt confirmou o salvamento do NKI com Samples locais.\n\n' + result + '\nKSP e Lua: ' + str(self.prepared.export.nki.parent) +
                                '\n\nMantenha a pasta Samples junto ao NKI. Teste o som antes de limpar o cache.\n' +
                                ('Arte: ' + str(self.prepared.export.artwork.nkr) + '\nCapa: ' + str(self.prepared.export.artwork.cover) + '\n' if self.prepared.export.artwork else ''))
        elif status.state == 'error':
            log = str(self.prepared.export.log)
            self._finish_job()
            messagebox.showerror('Erro real da API do Kontakt',
                                 status.description[:1600] + '\n\nLog completo em:\n' + log + '\nTerminal em:\n' + str(self.prepared.export.log.with_name(self.prepared.export.log.stem + '_TERMINAL.txt')))
        elif self.kontakt_process.poll() is not None:
            self._finish_job()
            messagebox.showerror('Kontakt encerrou',
                                 'O Kontakt foi fechado antes de confirmar o arquivo NKI. '
                                 'Confira o log em Abrir Lua / log.')
        elif status.state == 'waiting' and (time.monotonic() - self.monitor_started) > 45:
            self._finish_job()
            messagebox.showwarning('O Lua não iniciou',
                                   'O Kontakt abriu, mas nenhuma mensagem do Lua chegou ao log. '
                                   'Confirme que usou o executável standalone correto e que Developer Options está ativo.\n\n'
                                   'Não declarei o NKI como criado; veja Abrir Lua / log.')

    def open_log_dir(self):
        if self.prepared and self.prepared.work_dir.is_dir():
            os.startfile(str(self.prepared.work_dir)) if os.name == 'nt' else messagebox.showinfo('Diretório', str(self.prepared.work_dir))
        else:
            messagebox.showinfo('Arquivos', 'Primeiro prepare uma conversão para acessar o Lua e o log.')

    def clear_cache(self):
        if self.busy or not self.prepared:
            messagebox.showinfo('Cache', 'Finalize uma preparação antes de limpar o cache.')
            return
        if not self.prepared.export.nki.is_file():
            messagebox.showwarning('Atenção', 'O NKI ainda não existe. Os WAVs do cache são necessários para o Kontakt.')
            return
        samples_dir = self.prepared.export.samples_dir
        expected = self.prepared.export.sample_count
        actual = sum(1 for x in samples_dir.glob('*.wav') if x.is_file() and x.stat().st_size > 44) if samples_dir and samples_dir.is_dir() else 0
        if actual < expected:
            messagebox.showerror('Cache necessário',
                                 f'A pasta Samples final tem {actual}/{expected} WAVs. Não vou apagar o cache antes de confirmar os arquivos.')
            return
        if not messagebox.askyesno('Confirmar limpeza',
                                  'Reabra o .nki e confirme que ele toca com a pasta Samples local antes de limpar.\n'
                                  'Você já verificou que o NKI toca sem os WAVs temporários?'):
            return
        try:
            safe_remove_work(self.prepared.work_dir)
            self.status.set('Cache temporário removido. NKI final preservado.')
            self.prepared = None
        except Exception as exc:
            messagebox.showerror('Limpeza recusada', str(exc))


def main():
    app = DirectApp()
    app.mainloop()
