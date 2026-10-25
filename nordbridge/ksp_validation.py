"""Validador preventivo (nao substitui o compilador real do Kontakt)."""
from __future__ import annotations
import re
from collections import Counter

UI_DECL = re.compile(r'^\s*declare\s+ui_(\w+)\s+\$(\w+)\b', re.I)
SET_TEXT = re.compile(r'\bset_text\s*\(\s*\$(\w+)\s*,', re.I)
UI_ID = re.compile(r'\bget_ui_id\s*\(\s*\$(\w+)\s*\)', re.I)
UI_CALLBACK = re.compile(r'^\s*on\s+ui_control\s*\(\s*\$(\w+)\s*\)', re.I)
ON_START = re.compile(r'^\s*on\s+(?:init|note|release|controller|persistence_changed|listener|ui_control\s*\(.*\)|poly_at|rpn|nrpn|midi_in)', re.I)
ON_END = re.compile(r'^\s*end\s+on\s*$', re.I)
FUNC_START = re.compile(r'^\s*function\s+\w+', re.I)
FUNC_END = re.compile(r'^\s*end\s+function\s*$', re.I)

def check_ksp(source: str) -> list[str]:
    """Erros comuns de estrutura/tipo no KSP gerado; reporta linha e controle."""
    lines=source.splitlines()
    widgets={}
    issues=[]
    decls=Counter()
    for line_number,line in enumerate(lines,1):
        clean=line.split('{',1)[0].strip()
        m=UI_DECL.match(clean)
        if m:
            typ,name=m.groups()
            decls[name]+=1
            widgets[name]=typ.lower()
            if decls[name]>1:issues.append(f'Linha {line_number}: controle ${name} declarado mais de uma vez.')
    stack=[]
    callbacks=set()
    for line_number,line in enumerate(lines,1):
        clean=line.split('{',1)[0].strip()
        if not clean:continue
        for m in SET_TEXT.finditer(clean):
            name=m.group(1)
            if widgets.get(name)=='slider':
                issues.append(f'Linha {line_number}: set_text(${name}, ...) nao funciona em ui_slider. Use ui_label ou $CONTROL_PAR_LABEL.')
        for m in UI_ID.finditer(clean):
            name=m.group(1)
            if name not in widgets:
                issues.append(f'Linha {line_number}: get_ui_id(${name}) referencia controle UI nao declarado.')
        m=UI_CALLBACK.match(clean)
        if m:
            name=m.group(1)
            if name not in widgets:issues.append(f'Linha {line_number}: callback ui_control de ${name} sem controle declarado.')
            if name in callbacks:issues.append(f'Linha {line_number}: callback de ${name} repetido.')
            callbacks.add(name)
        if ON_START.match(clean):stack.append(('on',line_number))
        elif FUNC_START.match(clean):stack.append(('function',line_number))
        elif ON_END.match(clean) or FUNC_END.match(clean):
            expected='on' if ON_END.match(clean) else 'function'
            if not stack or stack[-1][0]!=expected:
                issues.append(f'Linha {line_number}: end {expected} sem bloco correspondente.')
            else:stack.pop()
    for kind,number in stack:
        issues.append(f'Linha {number}: bloco {kind} sem encerramento.')
    if not re.search(r'(?m)^\s*on init\s*$',source):
        issues.append('Falta o bloco on init.')
    return issues

def require_valid_ksp(source: str, filename: str='KSP') -> None:
    errors=check_ksp(source)
    if errors:
        raise ValueError(f'{filename}: validacao preventiva falhou:\n'+'\n'.join(errors[:12]))
