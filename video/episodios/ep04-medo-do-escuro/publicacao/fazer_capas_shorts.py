"""Capas dos 3 Shorts do Ep. 04 (1080x1920): UMA figura, alto contraste, 2–3 palavras em vermelho.
Texto na faixa segura do vertical (longe do rodapé e da coluna de botões). Uso: python3 fazer_capas_shorts.py"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

AQUI = Path(__file__).parent
EP = AQUI.parent
FONTE = str(AQUI.parents[2] / "painel" / "fontes" / "Anton-400-latin.ttf")
W, H = 1080, 1920


def base(arq, centro, zoom, ganho=1.0, gama=0.8):
    im = Image.open(EP / arq).convert("RGB")
    s = max(W / im.width, H / im.height) * zoom
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    cx, cy = centro[0] * im.width, centro[1] * im.height
    l = int(min(max(0, cx - W / 2), im.width - W)); t = int(min(max(0, cy - H / 2), im.height - H))
    a = np.asarray(im.crop((l, t, l + W, t + H))).astype(np.float32) / 255
    lo, hi = np.percentile(a, [1, 99.7])
    a = np.clip((a - lo) / (hi - lo), 0, 1) ** gama * ganho
    yy, xx = np.mgrid[0:H, 0:W]
    v = ((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2
    a *= (1 - 0.55 * np.clip(v / 2, 0, 1))[..., None]
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))


def texto(im, linhas, y, tam, cor=(232, 28, 36)):
    """Linhas centralizadas, com brilho vermelho e contorno preto."""
    f = ImageFont.truetype(FONTE, tam)
    d = ImageDraw.Draw(im)
    pos, yy = [], y
    for ln in linhas:
        pos.append(((W - d.textlength(ln, font=f)) / 2, yy, ln)); yy += int(tam * 1.04)
    brilho = Image.new("RGBA", im.size, (0, 0, 0, 0)); db = ImageDraw.Draw(brilho)
    for x, yy, ln in pos:
        db.text((x, yy), ln, font=f, fill=cor + (255,))
    glow = brilho.filter(ImageFilter.GaussianBlur(20))
    im = Image.alpha_composite(Image.alpha_composite(im.convert("RGBA"), glow), glow)
    d = ImageDraw.Draw(im)
    for x, yy, ln in pos:
        d.text((x, yy), ln, font=f, fill=cor, stroke_width=5, stroke_fill=(0, 0, 0))
    return im.convert("RGB")


# 3 — a criatura a dois passos da cama
c3 = base("imagens/A10_dois_passos_clara.png", (0.44, 0.5), 1.0, ganho=0.95, gama=1.5)
texto(c3, ["NÃO", "PISCA."], 1050, 250).save(AQUI / "capa_short3_nao_pisca.jpg", quality=92)

# 1 — o caderno do seu Aurélio
c1 = base("imagens_reais/caderno_3.jpg", (0.55, 0.55), 1.15, ganho=0.8, gama=1.3)
texto(c1, ["40 CM.", "ELA SORRIU."], 720, 200).save(AQUI / "capa_short1_o_caderno.jpg", quality=92)

# 2 — o seu Aurélio olhando para o canto
c2 = base("imagens/A07_aurelio.png", (0.58, 0.5), 1.0, ganho=1.15, gama=0.7)
texto(c2, ["VOCÊ APAGOU", "A LUZ."], 1120, 190).save(AQUI / "capa_short2_voce_apagou_a_luz.jpg", quality=92)
print("ok")
