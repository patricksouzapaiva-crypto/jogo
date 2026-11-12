"""Capas do Ep. 06 "A porta na mata" (1280x720): UMA figura, alto contraste, 2–3 palavras em vermelho, texto diferente do título
("Se achar uma porta no meio da mata, não abra"). Usa as imagens originais (mais cor que as corrigidas: miniatura precisa saltar no feed).
Uso: python3 fazer_capas.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ep04-medo-do-escuro" / "publicacao"))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

AQUI = Path(__file__).parent
IMG = AQUI.parent / "imagens"
FONTE = str(AQUI.parents[2] / "painel" / "fontes" / "Anton-400-latin.ttf")
W, H = 1280, 720


def base(arq, centro, zoom, ganho=1.0, gama=0.8, sat=1.15):
    im = Image.open(IMG / arq).convert("RGB")
    s = max(W / im.width, H / im.height) * zoom
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    cx, cy = centro[0] * im.width, centro[1] * im.height
    l = int(min(max(0, cx - W / 2), im.width - W)); t = int(min(max(0, cy - H / 2), im.height - H))
    a = np.asarray(im.crop((l, t, l + W, t + H))).astype(np.float32) / 255
    lo, hi = np.percentile(a, [1, 99.7])
    a = np.clip((a - lo) / (hi - lo), 0, 1) ** gama * ganho
    lum = a.mean(2, keepdims=True); a = lum + (a - lum) * sat
    yy, xx = np.mgrid[0:H, 0:W]
    v = ((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2
    a *= (1 - 0.55 * np.clip(v / 2, 0, 1))[..., None]
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))


def texto(im, linhas, x, y, tam, cor=(232, 28, 36), alinhar="esq"):
    d = ImageDraw.Draw(im); f = ImageFont.truetype(FONTE, tam)
    brilho = Image.new("RGBA", im.size, (0, 0, 0, 0)); db = ImageDraw.Draw(brilho); yy = y
    for ln in linhas:
        w = d.textlength(ln, font=f); xx = x if alinhar == "esq" else x - w
        db.text((xx, yy), ln, font=f, fill=(0, 0, 0, 255), stroke_width=22, stroke_fill=(0, 0, 0, 255)); yy += int(tam * 1.02)
    im = Image.alpha_composite(im.convert("RGBA"), brilho.filter(ImageFilter.GaussianBlur(22)))   # sombra: lê em qualquer fundo
    d = ImageDraw.Draw(im); yy = y
    for ln in linhas:
        w = d.textlength(ln, font=f); xx = x if alinhar == "esq" else x - w
        d.text((xx, yy), ln, font=f, fill=cor, stroke_width=5, stroke_fill=(0, 0, 0)); yy += int(tam * 1.02)
    return im.convert("RGB")


# A — as seis lanternas em volta do fogo (o gancho)
a = base("P09_B.jpg", (0.66, 0.45), 1.3, ganho=1.1, gama=1.0, sat=1.2)
a = texto(a, ["ERAM", "SEIS."], 40, 360, 160)
a.save(AQUI / "capa_A_eram_seis.jpg", quality=92)

# B — a porta azul sozinha na neblina
b = base("P01_B.jpg", (0.5, 0.45), 1.25, ganho=1.0, gama=1.0, sat=1.5)
b = texto(b, ["ALGUÉM", "BATEU."], 1240, 280, 165, alinhar="dir")
b.save(AQUI / "capa_B_alguem_bateu.jpg", quality=92)

# C — o bombeiro de costas atravessando a porta
c = base("P05_A.jpg", (0.5, 0.45), 1.2, ganho=1.0, gama=1.0, sat=1.5)
c = texto(c, ["CONTA", "DE NOVO."], 40, 300, 160)
c.save(AQUI / "capa_C_conta_de_novo.jpg", quality=92)
print("ok")
