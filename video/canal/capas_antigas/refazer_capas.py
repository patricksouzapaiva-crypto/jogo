"""Capas novas para vídeos antigos do canal (padrão do guia: UMA figura, 2–3 palavras em vermelho, texto diferente
do título). Parte da capa atual: recorta a área sem o texto antigo, amplia e trata. Uso: python3 refazer_capas.py"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

AQUI = Path(__file__).parent
FONTE = str(AQUI.parents[1] / "painel" / "fontes" / "Anton-400-latin.ttf")
W, H = 1280, 720


def base(arq, caixa, gama=0.85, sat=1.25, ganho=1.0):
    """caixa = (x0, y0, x1, y1) em fração da capa atual, na proporção 16:9."""
    im = Image.open(AQUI / arq).convert("RGB")
    x0, y0, x1, y1 = caixa
    im = im.crop((int(x0 * im.width), int(y0 * im.height), int(x1 * im.width), int(y1 * im.height))).resize((W, H), Image.LANCZOS)
    im = im.filter(ImageFilter.UnsharpMask(radius=2.2, percent=90, threshold=2))
    a = np.asarray(im).astype(np.float32) / 255
    lo, hi = np.percentile(a, [0.5, 99.8])
    a = np.clip((a - lo) / (hi - lo), 0, 1) ** gama * ganho
    lum = a.mean(2, keepdims=True); a = lum + (a - lum) * sat
    yy, xx = np.mgrid[0:H, 0:W]
    v = ((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2
    a *= (1 - 0.5 * np.clip(v / 2, 0, 1))[..., None]
    a += np.random.default_rng(1).normal(0, 0.012, a.shape[:2])[..., None]     # grão leve disfarça a ampliação
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))


def texto(im, linhas, x, y, tam, cor=(232, 28, 36), alinhar="esq"):
    f = ImageFont.truetype(FONTE, tam); d = ImageDraw.Draw(im)
    som = Image.new("RGBA", im.size, (0, 0, 0, 0)); ds = ImageDraw.Draw(som); yy = y
    for ln in linhas:
        w = d.textlength(ln, font=f); xx = x if alinhar == "esq" else x - w
        ds.text((xx, yy), ln, font=f, fill=(0, 0, 0, 255), stroke_width=22, stroke_fill=(0, 0, 0, 255)); yy += int(tam * 1.02)
    im = Image.alpha_composite(im.convert("RGBA"), som.filter(ImageFilter.GaussianBlur(22)))
    d = ImageDraw.Draw(im); yy = y
    for ln in linhas:
        w = d.textlength(ln, font=f); xx = x if alinhar == "esq" else x - w
        d.text((xx, yy), ln, font=f, fill=cor, stroke_width=5, stroke_fill=(0, 0, 0)); yy += int(tam * 1.02)
    return im.convert("RGB")


# caixas (x0, y0, x1, y1): largura e altura na mesma fração = 16:9
# As batidas não vinham de fora — o corredor pelo olho mágico (o texto antigo ficava embaixo)
a = base("MaR2Ezx1Mno.jpg", (0.14, 0.0, 0.86, 0.72), gama=0.8)
a = texto(a, ["VÊM DE", "DENTRO."], 40, 365, 150)
a.save(AQUI / "capa_batidas.jpg", quality=92)

# A sereia de verdade vive no abismo — a figura pequena vira o centro (o título antigo ficava embaixo)
b = base("y2i10N0kpCo.jpg", (0.24, 0.12, 0.76, 0.64), gama=0.62, sat=1.4, ganho=1.15)
b = texto(b, ["NÃO É", "LENDA."], 40, 365, 150)
b.save(AQUI / "capa_sereia.jpg", quality=92)

# As pegadas paravam na minha tenda — as barracas no escuro (o título antigo ficava em cima)
c = base("t_yQhWbVtBY.jpg", (0.31, 0.51, 0.80, 1.0), gama=0.72, sat=1.3, ganho=1.1)
c = texto(c, ["NÃO ERAM", "MINHAS."], 40, 385, 140)
c.save(AQUI / "capa_pegadas.jpg", quality=92)

W2 = Image.new("RGB", (1280, 1080))
for i, (v, n) in enumerate((("MaR2Ezx1Mno", "capa_batidas"), ("y2i10N0kpCo", "capa_sereia"), ("t_yQhWbVtBY", "capa_pegadas"))):
    W2.paste(Image.open(AQUI / f"{v}.jpg").convert("RGB").resize((640, 360)), (0, i * 360))
    W2.paste(Image.open(AQUI / f"{n}.jpg").resize((640, 360)), (640, i * 360))
W2.save(AQUI / "antes_depois.jpg", quality=90)
print("ok")
