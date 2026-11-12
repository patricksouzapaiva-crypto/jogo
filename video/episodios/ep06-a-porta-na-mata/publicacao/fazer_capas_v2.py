"""Capas do Ep. 06 — versão 2 (12/11), pelas regras novas de CTR: um ponto focal (a porta azul + o bombeiro), fundo
escurecido para a porta saltar, texto grande de 2 palavras que COMPLETA o título ("Éramos cinco. As lanternas eram
seis.") sem repetir. Variante principal: uma silhueta escura e desfocada na neblina, do outro lado da porta (o sexto) —
sem rosto. Uso: python3 fazer_capas_v2.py"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from fazer_capas import IMG, FONTE, texto

AQUI = Path(__file__).parent
W, H = 1280, 720


def recorte(arq, cx, cy, zoom):
    im = Image.open(IMG / arq).convert("RGB")
    s = max(W / im.width, H / im.height) * zoom
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    l = int(min(max(0, cx * im.width - W / 2), im.width - W)); t = int(min(max(0, cy * im.height - H / 2), im.height - H))
    return np.asarray(im.crop((l, t, l + W, t + H))).astype(np.float32) / 255


def grade(a, foco):
    """Neblina vira noite fria: escurece, contraste em S, azul da porta saturado, resto dessaturado, vinheta no foco."""
    lum = a.mean(2, keepdims=True)
    azul = np.clip((a[..., 2] - a[..., 0]) * 4, 0, 1)[..., None]           # máscara da tinta azul
    a = lum + (a - lum) * (0.55 + 1.6 * azul)
    a = np.clip((a - 0.10) / 0.85, 0, 1)
    a = a ** 1.55                                                           # escurece a neblina clara
    a = a * np.array([0.92, 0.98, 1.08])                                    # frio
    yy, xx = np.mgrid[0:H, 0:W]
    v = ((xx - foco[0] * W) / (0.62 * W)) ** 2 + ((yy - foco[1] * H) / (0.75 * H)) ** 2
    a *= (1 - 0.72 * np.clip(v, 0, 1) ** 1.2)[..., None]
    return np.clip(a, 0, 1)


def silhueta(a, x, y, alt, forca=0.55):
    """Vulto humano parado (cabeça, ombros, corpo), muito desfocado, como se estivesse dentro da neblina."""
    m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m)
    hc = alt * 0.13; om = alt * 0.26
    d.ellipse([x - hc * 0.42, y, x + hc * 0.42, y + hc], fill=255)                                   # cabeça
    d.polygon([(x - om / 2, y + hc * 1.25), (x + om / 2, y + hc * 1.25), (x + om * 0.42, y + alt * 0.62),
               (x + om * 0.3, y + alt), (x - om * 0.3, y + alt), (x - om * 0.42, y + alt * 0.62)], fill=255)  # corpo
    d.rectangle([x - hc * 0.2, y + hc * 0.9, x + hc * 0.2, y + hc * 1.3], fill=255)                     # pescoço
    m = np.asarray(m.filter(ImageFilter.GaussianBlur(alt * 0.035))).astype(np.float32)[..., None] / 255
    return a * (1 - forca * m) + np.array([0.02, 0.025, 0.03]) * forca * m


def salvar(a, linhas, nome, x=48, y=None, tam=190, alinhar="esq"):
    im = Image.fromarray((a * 255).astype(np.uint8))
    y = y if y is not None else (H - int(tam * 1.02) * len(linhas)) // 2
    texto(im, linhas, x, y, tam, alinhar=alinhar).save(AQUI / nome, quality=93)


porta = recorte("P05_A.jpg", 0.0, 0.48, 1.18)
# recorte encostado na esquerda: a porta fica em x≈545–1030 e o bombeiro no vão (x≈640–800); o texto vai na mata escura
# à esquerda (até x≈520) e o vulto fica entre as árvores à direita da porta, olhando
base = grade(porta, (0.62, 0.5))
salvar(silhueta(base.copy(), 1100, 200, 250, 0.7), ["QUEM", "VOLTOU?"], "capa_v2_A_quem_voltou.jpg", x=34, tam=165)
salvar(base.copy(), ["CONTA", "DE NOVO."], "capa_v2_B_conta_de_novo.jpg", x=34, tam=150)
so = grade(recorte("P01_B.jpg", 0.5, 0.45, 1.25), (0.5, 0.5))
salvar(so, ["ALGUÉM", "BATEU."], "capa_v2_C_alguem_bateu.jpg", x=W - 40, tam=190, alinhar="dir")
print("ok")
