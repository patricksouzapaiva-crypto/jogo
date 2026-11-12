"""Capas dos 3 Shorts do Ep. 06 "A porta na mata" (1080x1920): uma figura, 2–3 palavras em vermelho. Uso: python3 fazer_capas_shorts.py"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

AQUI = Path(__file__).parent
IMG = AQUI.parent / "imagens"
FONTE = str(AQUI.parents[2] / "painel" / "fontes" / "Anton-400-latin.ttf")
W, H = 1080, 1920


def base(arq, centro, zoom, gama=1.1, sat=1.5):
    im = Image.open(IMG / arq).convert("RGB")
    s = max(W / im.width, H / im.height) * zoom
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    cx, cy = centro[0] * im.width, centro[1] * im.height
    l = int(min(max(0, cx - W / 2), im.width - W)); t = int(min(max(0, cy - H / 2), im.height - H))
    a = np.asarray(im.crop((l, t, l + W, t + H))).astype(np.float32) / 255
    lo, hi = np.percentile(a, [1, 99.7])
    a = np.clip((a - lo) / (hi - lo), 0, 1) ** gama
    lum = a.mean(2, keepdims=True); a = lum + (a - lum) * sat
    yy, xx = np.mgrid[0:H, 0:W]
    v = ((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2
    a *= (1 - 0.5 * np.clip(v / 2, 0, 1))[..., None]
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))


def texto(im, linhas, y, tam, cor=(232, 28, 36)):
    f = ImageFont.truetype(FONTE, tam)
    som = Image.new("RGBA", im.size, (0, 0, 0, 0)); ds = ImageDraw.Draw(som); d = ImageDraw.Draw(im); yy = y
    for ln in linhas:
        x = (W - d.textlength(ln, font=f)) / 2
        ds.text((x, yy), ln, font=f, fill=(0, 0, 0, 255), stroke_width=26, stroke_fill=(0, 0, 0, 255)); yy += int(tam * 1.04)
    im = Image.alpha_composite(im.convert("RGBA"), som.filter(ImageFilter.GaussianBlur(26)))
    d = ImageDraw.Draw(im); yy = y
    for ln in linhas:
        x = (W - d.textlength(ln, font=f)) / 2
        d.text((x, yy), ln, font=f, fill=cor, stroke_width=6, stroke_fill=(0, 0, 0)); yy += int(tam * 1.04)
    return im.convert("RGB")


# 12/11: o texto COMPLETA o título (não repete) e fica na zona segura (y < ~1450): embaixo o app cobre.
texto(base("P09_B.jpg", (0.71, 0.42), 1.0), ["QUEM ERA", "O SEXTO?"], 1040, 200).save(AQUI / "capa_short1_eram_seis.jpg", quality=92)
texto(base("P01_B.jpg", (0.5, 0.45), 1.05), ["ALGUÉM", "BATEU."], 1060, 220).save(AQUI / "capa_short2_alguem_bateu.jpg", quality=92)
texto(base("P14_A.jpg", (0.5, 0.5), 1.15), ["CONTA", "DE NOVO."], 260, 220).save(AQUI / "capa_short3_aponta_a_camera.jpg", quality=92)
print("ok")
