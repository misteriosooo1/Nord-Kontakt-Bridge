"""Conversão .npno -> WAV/SFZ e dados de mapeamento para Kontakt.

O decoder é o nord-cli (jmoo/drawbar, BSD-3-Clause), instalado à parte.
Este módulo NUNCA presume que .npno seja um WAV renomeado.
"""
from __future__ import annotations

import csv
import json
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

PITCHES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
NOTE_RE = re.compile(r"^([A-G])([#b]?)(-?\d+)$", re.I)
STROKE_RE = re.compile(r"^\s*(\d+)\s+([A-G][#b]?-?\d+)\s+(\w+)\s+(\d+)\s+(\d+)\s+([\d.]+)\s+", re.I)
KEY_RE = re.compile(r"^\s*([A-G][#b]?-?\d+)\s+([A-G][#b]?-?\d+)\s+([+-]?\d+)\s+([+-]?\d+(?:\.\d+)?)\s*$", re.I)
WAV_RE = re.compile(r"^(\d{2,3})-b(\d+)-l(\d+)\.wav$", re.I)
Progress = Callable[[int, int, str], None]


def note_name(midi: int) -> str:
    if not 0 <= midi <= 127:
        raise ValueError("Nota MIDI fora de 0..127")
    return f"{PITCHES[midi % 12]}{midi // 12 - 1}"


def midi_number(name: str) -> int:
    m = NOTE_RE.fullmatch(name.strip())
    if not m:
        raise ValueError(f"Nome de nota inválido: {name}")
    letter, accidental, octave = m.groups()
    semitone = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}[letter.upper()]
    semitone += 1 if accidental == "#" else (-1 if accidental == "b" else 0)
    result = (int(octave) + 1) * 12 + semitone
    if not 0 <= result <= 127:
        raise ValueError(f"Nota fora do MIDI: {name}")
    return result


@dataclass(frozen=True)
class Stroke:
    index: int
    root: int
    bank: str
    layer: int
    frames: int


@dataclass(frozen=True)
class Key:
    note: int
    root: int
    cents: float = 0.0


def parse_strokes(output: str) -> list[Stroke]:
    result = []
    for line in output.splitlines():
        m = STROKE_RE.match(line)
        if m:
            idx, root, bank, layer, frames, _seconds = m.groups()
            result.append(Stroke(int(idx), midi_number(root), bank.lower(), int(layer), int(frames)))
    return result


def parse_keys(output: str) -> list[Key]:
    result = []
    for line in output.splitlines():
        m = KEY_RE.match(line)
        if m:
            note, root, _units, cents = m.groups()
            result.append(Key(midi_number(note), midi_number(root), float(cents)))
    return result


def find_nord_support_exe() -> Path | None:
    """Busca somente a copia local de emergencia, nunca baixa executaveis."""
    executable_dir = Path(sys.executable).resolve().parent
    project_dir = Path(__file__).resolve().parents[1]
    bundle_dir = Path(getattr(sys, '_MEIPASS', executable_dir))
    for base in (executable_dir, bundle_dir, project_dir):
        candidate = base / 'SUPORTE_RECUPERACAO' / 'bin' / 'nord.exe'
        if candidate.is_file():
            return candidate
    return None


def find_nord_exe() -> Path | None:
    """Busca o decoder empacotado, instalado ou local (sem instalar Cargo).

    Portable PyInstaller onefile: sys._MEIPASS/bin/nord.exe.
    Installer Inno Setup: pasta do EXE/bin/nord.exe.
    Desenvolvimento: projeto/bin/nord.exe.
    Cargo/PATH continuam como compatibilidade para quem executa pelo Python.
    """
    executable_dir = Path(sys.executable).resolve().parent
    project_dir = Path(__file__).resolve().parents[1]
    bundle_dir = Path(getattr(sys, '_MEIPASS', executable_dir))
    candidates = [
        executable_dir / 'bin' / 'nord.exe',
        bundle_dir / 'bin' / 'nord.exe',
        project_dir / 'bin' / 'nord.exe',
    ]
    # O suporte offline vem antes do Cargo, para nao depender de outra instalacao.
    fallback = find_nord_support_exe()
    if fallback is not None:
        candidates.append(fallback)
    # Compatibilidade com distribuicoes anteriores.
    candidates.extend((
        executable_dir / 'nord.exe',
        bundle_dir / 'nord.exe',
        project_dir / 'nord.exe',
        Path.home() / '.cargo' / 'bin' / 'nord.exe',
    ))
    which = shutil.which('nord')
    if which:
        candidates.append(Path(which))
    return next((p for p in candidates if p.is_file()), None)


class NordCli:
    def __init__(self, executable: str | Path | None = None):
        self.path = Path(executable) if executable else find_nord_exe()
        if not self.path or not self.path.is_file():
            raise RuntimeError(
                "Decoder nord-cli não encontrado. Verifique se bin\\nord.exe "
                "está junto do aplicativo ou reinstale o Nord Kontakt Bridge."
            )

    def run(self, *args: str, timeout: int = 180) -> str:
        flags = [str(self.path), "--color=never", *map(str, args)]
        def execute(command: list[str]):
            return subprocess.run(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, encoding="utf-8", errors="replace", timeout=timeout,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )

        try:
            completed = execute(flags)
        except OSError as exc:
            # Se o decoder principal nao puder ser iniciado (arquivo danificado,
            # acesso negado etc.), tente a copia offline. Erros de conversao
            # (codigo de retorno diferente de zero) NAO sao encobertos.
            fallback = find_nord_support_exe()
            if not fallback or fallback.resolve() == self.path.resolve():
                raise RuntimeError(f"Falha ao iniciar nord.exe: {exc}. Consulte SUPORTE_RECUPERACAO.") from exc
            try:
                completed = execute([str(fallback), '--color=never', *map(str, args)])
            except OSError as backup_exc:
                raise RuntimeError(f"Decoder principal e copia de recuperacao falharam: {backup_exc}") from backup_exc
        if completed.returncode:
            details = (completed.stderr or completed.stdout).strip()
            raise RuntimeError(f"nord-cli: {details[-1800:] or 'erro não especificado'}")
        return completed.stdout

    def inspect(self, path: Path) -> tuple[list[Stroke], list[Key]]:
        strokes = parse_strokes(self.run("piano", "inspect", str(path), "--strokes"))
        keys = parse_keys(self.run("piano", "inspect", str(path), "--keys"))
        if not strokes:
            raise RuntimeError("Nenhuma amostra identificada no .npno. Verifique formato e versão do nord-cli.")
        if not keys:
            raise RuntimeError("Arquivo sem mapa de teclas reconhecível pelo nord-cli.")
        return strokes, keys

    def decode(self, path: Path, index: int, output: Path) -> None:
        self.run("piano", "decode", str(path), "--stroke", str(index), "-o", str(output), timeout=300)
        if not output.is_file() or output.stat().st_size < 44:
            raise RuntimeError(f"O decoder não criou WAV válido para o stroke {index}")


def _assign_velocities(samples: list[dict]) -> None:
    """Layer 0 = forte; distribuição linear aproximada (a curva Nord exata é proprietária)."""
    grouped: dict[tuple[int, str], list[dict]] = {}
    for sample in samples:
        grouped.setdefault((sample["root"], sample["bank"]), []).append(sample)
    for group in grouped.values():
        order = sorted(group, key=lambda s: s["layer"], reverse=True)
        for i, sample in enumerate(order):
            sample["lo_vel"] = (i * 128) // len(order)
            sample["hi_vel"] = ((i + 1) * 128) // len(order) - 1


def _sfz_text(samples: list[dict], keys: list[dict]) -> str:
    attacks: dict[int, list[dict]] = {}
    for item in samples:
        if item["bank"] == "attack":
            attacks.setdefault(item["root"], []).append(item)
    lines = ["// Nord Kontakt Bridge: instrumento para players SFZ (sfizz, sforzando).",
             "// KONTAKT 6/7/8 NÃO IMPORTA .SFZ: use os WAVs e o CSV no Mapping Editor.",
             "<control>", "default_path=Samples/", "", "<global>", "ampeg_release=0.35", ""]
    for key in keys:
        for sample in attacks.get(key["root"], []):
            lines.extend((
                "<region>",
                f"sample={sample['filename']}",
                f"lokey={key['note']} hikey={key['note']} pitch_keycenter={key['root']}",
                f"lovel={sample['lo_vel']} hivel={sample['hi_vel']}",
                f"tune={key.get('cents', 0.0):g}",
                "",
            ))
    return "\n".join(lines)


def _write_project(folder: Path, name: str, samples: list[dict], keys: list[dict], source: str) -> Path:
    _assign_velocities(samples)
    (folder / "Instrumento.sfz").write_text(_sfz_text(samples, keys), encoding="utf-8")
    with (folder / "MAPEAMENTO_KONTAKT.csv").open("w", newline="", encoding="utf-8-sig") as fp:
        writer = csv.writer(fp, delimiter=";")
        writer.writerow(["arquivo_WAV", "nota_MIDI", "nota", "raiz_MIDI", "raiz", "vel_de", "vel_ate", "ajuste_cents"])
        for key in keys:
            for sample in samples:
                if sample["bank"] == "attack" and sample["root"] == key["root"]:
                    writer.writerow([
                        "Samples/" + sample["filename"], key["note"], note_name(key["note"]),
                        key["root"], note_name(key["root"]), sample["lo_vel"], sample["hi_vel"],
                        key.get("cents", 0.0),
                    ])
    meta = {"schema": 1, "name": name, "source": source, "samples": samples, "keys": keys,
            "note": "Apenas ataque exportado. Ressonâncias e samples de soltar tecla ainda não são reproduzidos."}
    (folder / "instrument.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    (folder / "INSTRUCOES_KONTAKT.txt").write_text(
        "COMO USAR COM KONTAKT 7/8 FULL\n\n"
        "1. Abra Kontakt FULL (não apenas o Player) e crie 'New Instrument'.\n"
        "2. Abra o Mapping Editor e arraste os arquivos WAV da pasta Samples.\n"
        "3. Ajuste as zonas usando o arquivo MAPEAMENTO_KONTAKT.csv:\n"
        "   nota_MIDI, raiz_MIDI, vel_de, vel_ate e ajuste_cents.\n"
        "4. Salve o instrumento via 'Save as...' > .nki, de preferência Patch + Samples.\n\n"
        "OBS: a geração automática de arquivo .NKI não é suportada neste projeto.\n"
        "O arquivo Instrumento.sfz pode ser aberto diretamente em um player VST SFZ como sfizz.\n"
        "O timbre original pode soar diferente: layers velocity foram aproximados, e\n"
        "resonância de pedal/release não foram implementados.\n\n"
        "Use exclusivamente com material para o qual tem direitos/permissão.\n",
        encoding="utf-8",
    )
    return folder


def convert_npno(source: str | Path, target: str | Path, progress: Progress | None = None,
                 decoder: NordCli | None = None, max_layers: int = 0) -> Path:
    """Converte TODAS as notas-raiz/camadas attack; 0 = todas, 1..N = N mais fortes.

    Falhas propagadas sem declarar sucesso. Todos os produtos ficam em target.
    """
    source, target = Path(source).resolve(), Path(target).resolve()
    if source.suffix.lower() != ".npno" or not source.is_file():
        raise ValueError("Selecione um arquivo Nord Piano .npno existente")
    if target.exists() and any(target.iterdir()):
        raise FileExistsError(f"Pasta de saída não está vazia: {target}. Selecione outra pasta.")
    cli = decoder or NordCli()
    strokes, keys = cli.inspect(source)
    strokes = [s for s in strokes if s.bank == "attack"]
    if max_layers:
        by_root: dict[int, list[Stroke]] = {}
        for item in strokes:
            by_root.setdefault(item.root, []).append(item)
        strokes = [x for group in by_root.values() for x in sorted(group, key=lambda s: s.layer)[:max_layers]]
    if not strokes:
        raise RuntimeError("O arquivo não contém samples de ataque reconhecidos")
    target.mkdir(parents=True, exist_ok=True)
    (target / "Samples").mkdir(exist_ok=True)
    files = []
    total = len(strokes)
    for i, stroke in enumerate(strokes, 1):
        filename = f"{stroke.root:03d}-b0-l{stroke.layer:02d}.wav"
        wave_path = target / "Samples" / filename
        if progress:
            progress(i - 1, total, f"Decodificando {note_name(stroke.root)} · camada {stroke.layer} ({i}/{total})")
        cli.decode(source, stroke.index, wave_path)
        files.append({"root": stroke.root, "bank": "attack", "layer": stroke.layer, "filename": filename})
    meta_keys = [asdict(k) for k in keys if any(s["root"] == k.root for s in files)]
    if progress:
        progress(total, total, "Gerando mapeamento e arquivos do Kontakt...")
    return _write_project(target, source.stem, files, meta_keys, str(source))


def import_wavs(source_folder: str | Path, target: str | Path, progress: Progress | None = None) -> Path:
    """Importa WAVs com nomes <root>-b0-l<layer>.wav; útil também para teste."""
    source_folder, target = Path(source_folder).resolve(), Path(target).resolve()
    wavs = sorted(p for p in source_folder.glob("*.wav") if WAV_RE.fullmatch(p.name))
    if not wavs:
        raise ValueError("Nenhum WAV no padrão '060-b0-l00.wav' na pasta escolhida.")
    if target.exists() and any(target.iterdir()):
        raise FileExistsError("Selecione uma pasta de saída vazia")
    target.mkdir(parents=True, exist_ok=True)
    sample_dir = target / "Samples"
    sample_dir.mkdir(exist_ok=True)
    samples = []
    for i, wav in enumerate(wavs, 1):
        root, bank, layer = map(int, WAV_RE.fullmatch(wav.name).groups())
        if bank != 0 or not 0 <= root <= 127:
            continue
        shutil.copy2(wav, sample_dir / wav.name)
        samples.append({"root": root, "bank": "attack", "layer": layer, "filename": wav.name})
        if progress:
            progress(i, len(wavs), f"Importando {wav.name}")
    roots = sorted(set(s["root"] for s in samples))
    if not roots:
        raise ValueError("Nenhuma amostra de ataque no diretório")
    keys = [{"note": i, "root": min(roots, key=lambda r: (abs(i - r), r)), "cents": 0.0}
            for i in range(max(21, min(roots)), min(109, max(roots) + 1))]
    return _write_project(target, source_folder.name, samples, keys, str(source_folder))


def load_project(path: Path) -> dict:
    manifest = Path(path)
    if manifest.is_dir():
        manifest /= "instrument.json"
    doc = json.loads(manifest.read_text(encoding="utf-8"))
    if doc.get("schema") != 1:
        raise ValueError("Formato de projeto não reconhecido")
    doc["folder"] = str(manifest.parent)
    return doc
