"""Motor de edição: imagens paradas + narração -> MP4 com movimento de câmera suave,
transições, tratamento de cor, granulação, legendas sincronizadas e mixagem com ducking.

Uso:
    python video/motor/editor.py roteiro.json saida.mp4 [--rascunho]

O roteiro (JSON) descreve formato, áudio e cenas. Veja video/GUIA_DO_EDITOR.md.
"""
from __future__ import annotations

import json
import math
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np

FORMATOS = {"9:16": (1080, 1920), "16:9": (1920, 1080), "1:1": (1080, 1080), "4:5": (1080, 1350)}


# ---------------------------------------------------------------- curvas de movimento
def suave(x: float) -> float:
    """ease-in-out cúbico: nada de movimento linear (parece robótico)."""
    x = min(max(x, 0.0), 1.0)
    return 4 * x * x * x if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def senoide(x: float) -> float:
    """ease-in-out senoidal: mais macio, bom para movimentos longos e lentos."""
    x = min(max(x, 0.0), 1.0)
    return -(math.cos(math.pi * x) - 1) / 2


CURVAS = {"suave": suave, "senoide": senoide, "linear": lambda x: min(max(x, 0.0), 1.0)}

# movimentos prontos: (zoom inicial, zoom final, centro inicial (x,y), centro final) em fração da imagem
MOVIMENTOS = {
    "aproximar": (1.00, 1.12, (0.5, 0.5), (0.5, 0.5)),
    "afastar": (1.14, 1.00, (0.5, 0.5), (0.5, 0.5)),
    "esquerda": (1.10, 1.10, (0.56, 0.5), (0.44, 0.5)),
    "direita": (1.10, 1.10, (0.44, 0.5), (0.56, 0.5)),
    "subir": (1.10, 1.10, (0.5, 0.56), (0.5, 0.44)),
    "descer": (1.10, 1.10, (0.5, 0.44), (0.5, 0.56)),
    "parado": (1.04, 1.05, (0.5, 0.5), (0.5, 0.5)),  # "respiração": nunca 100% congelado
}


@dataclass
class Cena:
    imagem: str
    duracao: float
    movimento: str = "aproximar"
    zoom: tuple[float, float] | None = None
    centro: tuple[tuple[float, float], tuple[float, float]] | None = None
    curva: str = "senoide"
    transicao: str = "fundir"  # transição de ENTRADA desta cena: fundir | preto | corte | luz
    duracao_transicao: float = 0.8
    texto: str | None = None  # texto de tela (título/data), opcional


@dataclass
class Roteiro:
    formato: str = "9:16"
    fps: int = 30
    cenas: list[Cena] = field(default_factory=list)
    voz: str | None = None
    alinhamento: str | None = None  # JSON de alinhamento do ElevenLabs
    inicio_voz: float = 0.6
    musica: str | None = None
    volume_musica_db: float = -20.0
    legendas: bool = True
    palavras_por_legenda: int = 3
    grade: dict = field(default_factory=dict)
    fonte: str = "Inter"
    loudness: float = -14.0
    cor_destaque: str = "#E63946"  # coral da marca


# ---------------------------------------------------------------- imagem
class Camera:
    """Renderiza uma cena com subpixel (warpAffine + Lanczos): sem o tremido do zoompan."""

    def __init__(self, caminho: str, W: int, H: int):
        img = cv2.imread(caminho, cv2.IMREAD_COLOR)
        if img is None:
            raise FileNotFoundError(caminho)
        h, w = img.shape[:2]
        # recorta para a proporção do quadro (cobre sem barras)
        alvo = W / H
        if w / h > alvo:
            nw = int(h * alvo)
            img = img[:, (w - nw) // 2:(w - nw) // 2 + nw]
        else:
            nh = int(w / alvo)
            img = img[(h - nh) // 2:(h - nh) // 2 + nh]
        # trabalha numa fonte >= 1.5x o quadro para ter margem de zoom com nitidez
        escala = max(1.5 * W / img.shape[1], 1.0)
        if escala > 1.0:
            img = cv2.resize(img, None, fx=escala, fy=escala, interpolation=cv2.INTER_LANCZOS4)
        self.img = img.astype(np.float32)
        self.W, self.H = W, H

    def quadro(self, zoom: float, cx: float, cy: float) -> np.ndarray:
        h, w = self.img.shape[:2]
        # tamanho da janela na fonte para este zoom (zoom 1 = a imagem inteira)
        jw = w / zoom
        # mantém a janela dentro da imagem
        jh = jw * self.H / self.W
        x0 = min(max(cx * w - jw / 2, 0), w - jw)
        y0 = min(max(cy * h - jh / 2, 0), h - jh)
        s = self.W / jw
        M = np.array([[s, 0, -x0 * s], [0, s, -y0 * s]], dtype=np.float64)
        return cv2.warpAffine(self.img, M, (self.W, self.H), flags=cv2.INTER_LANCZOS4,
                              borderMode=cv2.BORDER_REFLECT)


def parametros(c: Cena):
    z0, z1, p0, p1 = MOVIMENTOS[c.movimento]
    if c.zoom:
        z0, z1 = c.zoom
    if c.centro:
        p0, p1 = c.centro
    return z0, z1, p0, p1


# ---------------------------------------------------------------- tratamento
class Tratamento:
    """Cor + vinheta + granulação, igual em todas as cenas (dá unidade de 'filme')."""

    def __init__(self, W, H, g: dict, semente=7):
        self.contraste = g.get("contraste", 1.06)
        self.saturacao = g.get("saturacao", 0.92)
        self.quente = g.get("quente", 0.04)  # >0 puxa para âmbar, <0 para azul
        self.granulacao = g.get("granulacao", 0.03)
        vin = g.get("vinheta", 0.28)
        y, x = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2) / math.sqrt(2)
        self.vinheta = (1 - vin * np.clip(r, 0, 1) ** 2.2)[..., None]
        rng = np.random.default_rng(semente)
        # banco de granulação: 8 texturas em meia resolução, sorteadas por quadro
        self.graos = [cv2.resize(rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32), (W, H))[..., None]
                      for _ in range(8)]

    def aplicar(self, f: np.ndarray, i: int) -> np.ndarray:
        f = f / 255.0
        # contraste em S suave em torno do meio-tom
        f = 0.5 + (f - 0.5) * self.contraste
        cinza = f.mean(axis=2, keepdims=True)
        f = cinza + (f - cinza) * self.saturacao
        if self.quente:
            f = f * np.array([1 - self.quente, 1.0, 1 + self.quente], dtype=np.float32)  # BGR
        f = f * self.vinheta
        if self.granulacao:
            lum = f.mean(axis=2, keepdims=True)
            f = f + self.graos[i % 8] * self.granulacao * (0.4 + 0.6 * (1 - lum))  # mais grão nas sombras
        return np.clip(f * 255, 0, 255)


# ---------------------------------------------------------------- legendas
def palavras_do_alinhamento(caminho: str, deslocamento: float):
    a = json.load(open(caminho))
    chars, ini, fim = a["characters"], a["character_start_times_seconds"], a["character_end_times_seconds"]
    palavras, atual, t0 = [], "", None
    for ch, s, e in zip(chars, ini, fim):
        if ch.isspace():
            if atual:
                palavras.append((atual, t0 + deslocamento, ultimo + deslocamento))
            atual, t0 = "", None
            continue
        if t0 is None:
            t0 = s
        atual += ch
        ultimo = e
    if atual:
        palavras.append((atual, t0 + deslocamento, ultimo + deslocamento))
    return palavras


def blocos_de_legenda(palavras, n=3, pausa=0.35):
    """Agrupa até n palavras; quebra em pontuação ou pausa; nunca deixa um bloco < 0,35 s."""
    blocos, atual = [], []
    for i, p in enumerate(palavras):
        atual.append(p)
        prox = palavras[i + 1] if i + 1 < len(palavras) else None
        quebra = (len(atual) >= n or p[0][-1] in ".,;:!?—" or prox is None or prox[1] - p[2] > pausa)
        if quebra:
            blocos.append([" ".join(w for w, _, _ in atual), atual[0][1], atual[-1][2], atual])
            atual = []
    for i, b in enumerate(blocos):  # cada bloco fica até o próximo começar (sem piscar)
        prox = blocos[i + 1][1] if i + 1 < len(blocos) else b[2] + 0.4
        b[2] = max(min(prox, b[2] + 0.5), b[1] + 0.35)
    return blocos


def ass_tempo(t):
    h, r = divmod(max(t, 0), 3600)
    m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def gerar_ass(blocos, W, H, fonte, caminho, cor_destaque="#E63946"):
    r_, g_, b_ = cor_destaque[1:3], cor_destaque[3:5], cor_destaque[5:7]
    destaque = f"&H00{b_}{g_}{r_}&"
    tam = int(W * 0.068)
    margem = int(H * 0.22) if H > W else int(H * 0.09)
    cab = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Leg,{fonte},{tam},&H00EBF3F7,&H00EBF3F7,&H00101010,&H64000000,-1,0,0,0,100,100,0,0,1,{max(3, tam // 14)},2,2,80,80,{margem},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    linhas = []
    for texto, t0, t1, pals in blocos:
        # um evento por palavra: a palavra que está sendo falada fica na cor de destaque
        marcos = [p[1] for p in pals] + [t1]
        for j in range(len(pals)):
            a, b = (t0 if j == 0 else marcos[j]), marcos[j + 1]
            if b - a < 0.01:
                continue
            txt = " ".join((f"{{\\c{destaque}}}{w}{{\\c&H00EBF3F7&}}" if k == j else w)
                           for k, (w, _, _) in enumerate(pals))
            fade = "{\\fad(80,0)}" if j == 0 else ""
            linhas.append(f"Dialogue: 0,{ass_tempo(a)},{ass_tempo(b)},Leg,,0,0,0,,{fade}{txt}")
    Path(caminho).write_text(cab + "\n".join(linhas) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- áudio
def duracao_audio(caminho):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", caminho],
                         capture_output=True, text=True).stdout
    return float(out.strip())


def mixar(r: Roteiro, total: float, saida: str):
    """Voz na frente; música abaixa sozinha quando a voz fala (sidechain); loudnorm em 2 passadas."""
    ent, filtros, rotulos = [], [], []
    if r.voz:
        ent += ["-i", r.voz]
        atraso = int(r.inicio_voz * 1000)
        filtros.append(f"[0:a]aresample=48000,highpass=f=80,acompressor=threshold=-20dB:ratio=3:attack=5:release=120,"
                       f"adelay={atraso}|{atraso},apad,atrim=0:{total:.3f},asplit=2[voz][chave]")
    if r.musica:
        idx = len(ent) // 2
        ent += ["-stream_loop", "-1", "-i", r.musica]
        filtros.append(f"[{idx}:a]aresample=48000,volume={r.volume_musica_db}dB,atrim=0:{total:.3f},"
                       f"afade=t=in:d=1.5,afade=t=out:st={max(total - 2.5, 0):.3f}:d=2.5[mus]")
    if r.voz and r.musica:
        filtros.append("[mus][chave]sidechaincompress=threshold=0.03:ratio=6:attack=40:release=600[musd]")
        filtros.append("[voz][musd]amix=inputs=2:normalize=0[mix]")
    elif r.voz:
        filtros.append("[voz]anull[mix]")
        filtros.append("[chave]anullsink")
    elif r.musica:
        filtros.append("[mus]anull[mix]")
    else:
        return None
    grafo = ";".join(filtros)
    bruto = saida + ".bruto.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", *ent, "-filter_complex", grafo, "-map", "[mix]", "-t", f"{total:.3f}",
                    bruto], check=True)
    # passada 1: medir
    med = subprocess.run(["ffmpeg", "-v", "info", "-i", bruto, "-af",
                          f"loudnorm=I={r.loudness}:TP=-1.0:LRA=11:print_format=json", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    m = json.loads(med[med.rfind("{"):med.rfind("}") + 1])
    # passada 2: aplicar linear
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", bruto, "-af",
                    f"loudnorm=I={r.loudness}:TP=-1.0:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
                    f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:"
                    f"linear=true,aresample=48000", "-c:a", "pcm_s16le", saida], check=True)
    os.remove(bruto)
    return saida


# ---------------------------------------------------------------- montagem
def carregar(caminho: str) -> Roteiro:
    d = json.load(open(caminho))
    base = Path(caminho).parent
    cenas = []
    for c in d.pop("cenas"):
        c["imagem"] = str((base / c["imagem"]).resolve())
        for k in ("zoom",):
            if k in c:
                c[k] = tuple(c[k])
        if "centro" in c:
            c["centro"] = tuple(tuple(p) for p in c["centro"])
        cenas.append(Cena(**c))
    for k in ("voz", "alinhamento", "musica"):
        if d.get(k):
            d[k] = str((base / d[k]).resolve())
    return Roteiro(cenas=cenas, **d)


def renderizar(r: Roteiro, saida: str, rascunho: bool = False):
    W, H = FORMATOS[r.formato]
    if rascunho:  # prévia rápida em meia resolução
        W, H = W // 2, H // 2
    fps = r.fps
    # linha do tempo: cada cena começa sobreposta à anterior durante a transição de entrada
    inicios, t = [], 0.0
    for i, c in enumerate(r.cenas):
        if i > 0 and c.transicao in ("fundir", "luz"):
            t -= c.duracao_transicao
        inicios.append(t)
        t += c.duracao
    total = t
    if r.voz:
        total = max(total, r.inicio_voz + duracao_audio(r.voz) + 0.8)
        # estica a última cena para cobrir a voz
        r.cenas[-1].duracao += total - t
    n = int(round(total * fps))
    trat = Tratamento(W, H, r.grade)
    tmp = tempfile.mkdtemp(prefix="edicao_")
    video = os.path.join(tmp, "video.mp4")
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                           "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "16",
                           "-pix_fmt", "yuv420p", "-tune", "film", video], stdin=subprocess.PIPE)
    cams: dict[int, Camera] = {}

    def quadro_da_cena(i, tl):
        c = r.cenas[i]
        if i not in cams:
            cams[i] = Camera(c.imagem, W, H)
            for k in [k for k in cams if k < i - 1]:
                del cams[k]
        z0, z1, p0, p1 = parametros(c)
        e = CURVAS[c.curva](tl / c.duracao)
        z = z0 + (z1 - z0) * e
        return cams[i].quadro(z, p0[0] + (p1[0] - p0[0]) * e, p0[1] + (p1[1] - p0[1]) * e)

    for k in range(n):
        tg = k / fps
        ativas = [i for i, s in enumerate(inicios) if s <= tg < s + r.cenas[i].duracao]
        if not ativas:
            ativas = [len(r.cenas) - 1]
        i = ativas[-1]
        c = r.cenas[i]
        tl = tg - inicios[i]
        f = quadro_da_cena(i, tl)
        if c.transicao in ("fundir", "luz") and i > 0 and tl < c.duracao_transicao and (i - 1) in [
                j for j, s in enumerate(inicios) if s <= tg < s + r.cenas[j].duracao]:
            a = suave(tl / c.duracao_transicao)
            ant = quadro_da_cena(i - 1, tg - inicios[i - 1])
            if c.transicao == "luz":  # flash de luz quente no meio da fusão
                brilho = math.sin(math.pi * a) * 90
                f = ant * (1 - a) + f * a + brilho
            else:
                f = ant * (1 - a) + f * a
        elif c.transicao == "preto":
            d = c.duracao_transicao / 2
            if i > 0 and tl < d:
                f = f * suave(tl / d)
        # saída da última cena e entrada da primeira: fade do/para preto
        if tg < 0.5:
            f = f * suave(tg / 0.5)
        if tg > total - 1.0:
            f = f * suave((total - tg) / 1.0)
        # a cena seguinte com 'preto' escurece o fim desta
        if i + 1 < len(r.cenas) and r.cenas[i + 1].transicao == "preto":
            d = r.cenas[i + 1].duracao_transicao / 2
            rest = inicios[i + 1] - tg
            if 0 <= rest < d:
                f = f * suave(rest / d)
        out = trat.aplicar(f, k).astype(np.uint8)
        ff.stdin.write(out.tobytes())
        if k % (fps * 5) == 0:
            print(f"  quadro {k}/{n}", file=sys.stderr)
    ff.stdin.close()
    ff.wait()

    audio = mixar(r, total, os.path.join(tmp, "audio.wav"))
    vf = []
    if r.legendas and r.alinhamento:
        ass = os.path.join(tmp, "leg.ass")
        gerar_ass(blocos_de_legenda(palavras_do_alinhamento(r.alinhamento, r.inicio_voz), r.palavras_por_legenda),
                  W, H, r.fonte, ass, r.cor_destaque)
        vf = ["-vf", f"ass={ass}"]
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", video]
    if audio:
        cmd += ["-i", audio]
    cmd += vf + ["-c:v", "libx264", "-preset", "veryfast" if rascunho else "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(fps)]
    if audio:
        cmd += ["-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest"]
    cmd += ["-movflags", "+faststart", saida]
    subprocess.run(cmd, check=True)
    print(f"ok: {saida} ({total:.1f}s, {W}x{H}@{fps})")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    renderizar(carregar(args[0]), args[1], rascunho="--rascunho" in sys.argv)
