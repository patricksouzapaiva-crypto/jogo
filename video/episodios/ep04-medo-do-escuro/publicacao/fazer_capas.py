"""Capas do Ep. 04 (1280x720) no padrão novo (métricas do Ep. 03): UMA figura, alto contraste, 2–3 palavras
em vermelho, texto diferente do título. Uso: python3 fazer_capas.py"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

AQUI = Path(__file__).parent
IMG = AQUI.parent / "imagens"
FONTE = str(AQUI.parents[2] / "painel" / "fontes" / "Anton-400-latin.ttf")
W, H = 1280, 720


def base(arq, centro, zoom, ganho=1.0, gama=0.8):
    im = Image.open(IMG / arq).convert("RGB")
    s = max(W / im.width, H / im.height) * zoom
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    cx, cy = centro[0] * im.width, centro[1] * im.height
    l = int(min(max(0, cx - W / 2), im.width - W)); t = int(min(max(0, cy - H / 2), im.height - H))
    a = np.asarray(im.crop((l, t, l + W, t + H))).astype(np.float32) / 255
    lo, hi = np.percentile(a, [1, 99.7])
    a = np.clip((a - lo) / (hi - lo), 0, 1) ** gama * ganho          # alto contraste
    yy, xx = np.mgrid[0:H, 0:W]
    v = ((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2
    a *= (1 - 0.55 * np.clip(v / 2, 0, 1))[..., None]              # vinheta: o olho vai pra figura
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))


def texto(im, linhas, x, y, tam, cor=(232, 28, 36), alinhar="esq"):
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FONTE, tam)
    brilho = Image.new("RGBA", im.size, (0, 0, 0, 0)); db = ImageDraw.Draw(brilho)
    yy = y
    for ln in linhas:
        w = d.textlength(ln, font=f)
        xx = x if alinhar == "esq" else x - w
        db.text((xx, yy), ln, font=f, fill=cor + (255,))
        yy += int(tam * 1.02)
    glow = brilho.filter(ImageFilter.GaussianBlur(18))
    im = Image.alpha_composite(im.convert("RGBA"), glow)
    im = Image.alpha_composite(im, glow)
    # contorno preto fino + texto
    d = ImageDraw.Draw(im); yy = y
    for ln in linhas:
        w = d.textlength(ln, font=f); xx = x if alinhar == "esq" else x - w
        d.text((xx, yy), ln, font=f, fill=cor, stroke_width=4, stroke_fill=(0, 0, 0))
        yy += int(tam * 1.02)
    return im.convert("RGB")


def circulo(im, x0, y0, x1, y1, cor=(232, 28, 36)):
    """Elipse vermelha em volta da figura INTEIRA (caixa x0,y0-x1,y1), traço grosso e liso."""
    camada = Image.new("RGBA", (W * 2, H * 2), (0, 0, 0, 0))
    ImageDraw.Draw(camada).ellipse([x0 * 2, y0 * 2, x1 * 2, y1 * 2], outline=cor + (255,), width=12)
    camada = camada.resize((W, H), Image.LANCZOS)
    return Image.alpha_composite(im.convert("RGBA"), camada).convert("RGB")


ELIPSE_B = (745, 95, 950, 650)


# A — a criatura, a dois passos da cama
a = base("A10_dois_passos_clara.png", (0.44, 0.42), 1.55, ganho=0.95, gama=1.6)
a = texto(a, ["NÃO", "PISCA."], 1220, 70, 190, alinhar="dir")
a.save(AQUI / "capa_A_nao_pisca.jpg", quality=92)

# B — o canto do quarto (a forma quase invisível) com o círculo vermelho
b = base("A01_quarto_escuro.png", (0.66, 0.5), 1.2, ganho=1.12, gama=0.95)
import os
if os.environ.get("SEM_CIRCULO"):
    b.save(AQUI / "_b_sem_circulo.png")
else:
    b = circulo(b, *ELIPSE_B)
b = texto(b, ["20", "MINUTOS"], 40, 30, 165)
b.save(AQUI / "capa_B_20_minutos.jpg", quality=92)

# C — o seu Aurélio, de olhos abertos para o canto, luz verde do monitor
c = base("A07_aurelio.png", (0.58, 0.48), 1.45, ganho=1.15, gama=0.7)
c = texto(c, ["ELE NÃO", "DORME."], 60, 70, 165)
c.save(AQUI / "capa_C_ele_nao_dorme.jpg", quality=92)
print("ok")
