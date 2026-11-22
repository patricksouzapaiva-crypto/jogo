"""Capas do O QUE É A CRIATURA? #1 — Outra Mamãe — v3 (22/11).
v1: escuras demais. v2 (padrão do nicho: recorte, círculo, seta, selos): "poluída / amadora".
v3: UMA imagem forte por capa, nítida e com cor de cinema; 2–4 palavras bem compostas; nada de círculo, seta ou vários
selos. O que fica da pesquisa: rosto grande e claro, contraste alto, letra condensada amarela/branca com contorno.
Quadros REAIS do filme (nenhum rosto de IA). Uso: python3 gerar_capas.py → capa_*.jpg (1280×720)"""
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

AQUI = Path(__file__).parent
Q = AQUI / "quadros"
F = Path(__file__).resolve().parents[3] / "painel" / "fontes"
ANTON = str(F / "Anton-400-latin.ttf")
W, H = 1280, 720
AMARELO, BRANCO, VERM = (255, 212, 0), (255, 255, 255), (230, 24, 32)


def quadro(arq, cx, cy, zoom, limpar=0, luz=1.0):
    """recorte 16:9 do quadro, limpo do grão (limpar = força do denoise) e com nitidez"""
    im = cv2.imread(str(Q / arq)).astype(np.float32)
    if luz == "auto":   # quadro escuro: o 99,5º percentil vira quase branco
        luz = 235 / max(1.0, np.percentile(im, 99.5))
    if luz != 1.0:
        im = np.clip(im * luz, 0, 255)
    im = im.astype(np.uint8)
    if limpar:
        im = cv2.fastNlMeansDenoisingColored(im, None, limpar, limpar, 7, 21)
    ih, iw = im.shape[:2]; ch = ih / zoom; cw = ch * W / H
    if cw > iw:
        cw = iw; ch = cw * H / W
    x0 = int(min(max(0, cx * iw - cw / 2), iw - cw)); y0 = int(min(max(0, cy * ih - ch / 2), ih - ch))
    im = cv2.resize(im[y0:y0 + int(ch), x0:x0 + int(cw)], (W, H), interpolation=cv2.INTER_LANCZOS4)
    borr = cv2.GaussianBlur(im, (0, 0), 2.0)
    im = cv2.addWeighted(im, 1.6, borr, -0.6, 0)          # nitidez (unsharp)
    return cv2.cvtColor(im, cv2.COLOR_BGR2RGB).astype(np.float32)


def cor_cinema(a, sombras=(0.85, 1.0, 1.12), luzes=(1.08, 1.0, 0.92), sat=1.15, contraste=1.18, brilho=1.0, vx=0.5, vy=0.5):
    """teal & orange leve, contraste em S, vinheta suave"""
    a = a / 255 * brilho
    lum = a.mean(2, keepdims=True)
    a = lum + (a - lum) * sat
    a = a * (np.array(sombras) * (1 - lum) + np.array(luzes) * lum)
    a = np.clip(0.5 + (a - 0.5) * contraste, 0, 1)
    yy, xx = np.mgrid[0:H, 0:W]
    v = 1 - 0.5 * np.clip(((xx - W * vx) / (W * 0.7)) ** 2 + ((yy - H * vy) / (H * 0.7)) ** 2 - 0.15, 0, 1)
    return np.clip(a * v[..., None], 0, 1) * 255


def lado_escuro(a, lado="esq", ate=0.45, forca=0.85):
    x = np.linspace(0, 1, W)[None, :, None]
    g = np.clip(1 - x / ate, 0, 1) if lado == "esq" else np.clip((x - (1 - ate)) / ate, 0, 1)
    return a * (1 - forca * g ** 1.6)


def tela(a):
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")


def texto(base, linhas, x, y, tam, cores, alinhar="esq", contorno=9, entre=0.98):
    """bloco de linhas em Anton, contorno preto grosso e sombra macia (sem brilho, sem rotação)"""
    cam = Image.new("RGBA", base.size, (0, 0, 0, 0)); d = ImageDraw.Draw(cam); yy = y
    for l, c, t in zip(linhas, cores, tam):
        f = ImageFont.truetype(ANTON, t); w = d.textlength(l, font=f)
        xx = x - w if alinhar == "dir" else (x - w / 2 if alinhar == "centro" else x)
        d.text((xx, yy), l, font=f, fill=c + (255,), stroke_width=contorno, stroke_fill=(0, 0, 0, 255)); yy += int(t * entre)
    sombra = Image.new("RGBA", base.size, (0, 0, 0, 0)); sombra.paste((0, 0, 0, 170), mask=cam.split()[3])
    base.alpha_composite(ImageChops.offset(sombra.filter(ImageFilter.GaussianBlur(14)), 4, 10))
    base.alpha_composite(cam)


def salvar(img, nome):
    img.convert("RGB").save(AQUI / nome, quality=94); print("ok", nome)


# A — o sorriso perfeito demais. Só o rosto e duas linhas.
a = quadro("q_609.png", 0.0, 0.40, 1.22, limpar=3, luz=1.25)
a = lado_escuro(cor_cinema(a, brilho=1.15, vx=0.72, contraste=1.12), "esq", 0.42, 0.85)
b = tela(a)
texto(b, ["ELA NÃO É", "SUA MÃE"], 60, 175, [148, 168], [BRANCO, AMARELO])
salvar(b, "capa_A_sorriso.jpg")

# B — a criatura de perto, iluminada e limpa do grão, fria; a pergunta do vídeo
a = quadro("q_4903.png", 0.62, 0.42, 1.05, limpar=10, luz="auto")
a = cor_cinema(a, sombras=(0.85, 0.95, 1.12), luzes=(1.02, 1.0, 0.98), sat=0.7, contraste=1.25, brilho=1.15, vx=0.4)
a = lado_escuro(a, "dir", 0.42, 0.85)
b = tela(a)
texto(b, ["O QUE", "ELA É?"], W - 60, 175, [150, 170], [BRANCO, AMARELO], alinhar="dir")
salvar(b, "capa_B_criatura.jpg")

# C — a menina no túnel vermelho: a imagem mais forte do filme; só "FINAL EXPLICADO"
a = quadro("q_3027.png", 0.40, 0.5, 1.0, limpar=4, luz=1.6)
a = cor_cinema(a, sombras=(1.0, 0.92, 0.95), luzes=(1.04, 1.0, 0.97), sat=1.05, contraste=1.12, brilho=1.1, vx=0.66)
a = lado_escuro(a, "esq", 0.42, 0.85)
b = tela(a)
texto(b, ["FINAL", "EXPLICADO"], 60, 175, [160, 160], [BRANCO, AMARELO])
salvar(b, "capa_C_tunel.jpg")
