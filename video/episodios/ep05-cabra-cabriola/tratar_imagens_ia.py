"""Tira o "brilho de IA" das imagens geradas (imagens/B*) para combinarem com as fotos reais do episódio:
cor lavada e fria (o laranja da luz da porta fica, mais fraco), pretos levantados (foto velha, não escuro),
lente mole com aberração nas bordas, grão grosso, vinheta, poeira. Saída: imagens_tratadas/ (os originais ficam).
Uso: python3 tratar_imagens_ia.py"""
import numpy as np
from pathlib import Path
from PIL import Image, ImageFilter

AQUI = Path(__file__).parent
SAI = AQUI / "imagens_tratadas"; SAI.mkdir(exist_ok=True)
# força do tratamento: as que já são cinzentas/escuras levam menos
FORCA = {"B04": 0.5, "B06": 0.6, "B14": 0.5}


def tratar(arq, f, semente):
    rng = np.random.default_rng(semente)
    im = Image.open(arq).convert("RGB")
    if im.width > 2200:
        im = im.resize((2200, round(im.height * 2200 / im.width)), Image.LANCZOS)
    # lente barata: leve desfoque + aberração cromática (vermelho e azul em escalas diferentes)
    im = im.filter(ImageFilter.GaussianBlur(0.9 * f))
    w, h = im.size
    r, g, b = im.split()
    d = round(w * 0.0022 * f)
    r = r.resize((w + 2 * d, h + 2 * d), Image.BICUBIC).crop((d, d, w + d, h + d))
    b = b.resize((w - 2 * d, h - 2 * d), Image.BICUBIC) if d else b
    if d:
        bb = Image.new("L", (w, h)); bb.paste(b, (d, d)); b = bb
    a = np.asarray(Image.merge("RGB", (r, g, b)), np.float32) / 255
    lum = (a * [0.299, 0.587, 0.114]).sum(2, keepdims=True)
    a = lum + (a - lum) * (1 - 0.5 * f)                       # cor lavada
    sombra = np.clip(1 - lum * 2.2, 0, 1)
    a += sombra * f * np.array([-0.012, 0.012, 0.022])         # sombras esverdeadas/frias
    a = a * (1 - 0.06 * f * np.array([0.3, 0.6, 1.0]))         # altas levemente amareladas (papel velho)
    a = 0.045 * f + a * (1 - 0.075 * f)                        # preto levantado, branco contido
    a = np.clip(a, 0, 1) ** (1 - 0.10 * f)                     # meios-tons um pouco mais abertos: não fica escuro
    yy, xx = np.mgrid[0:h, 0:w]
    rr = np.hypot((xx - w / 2) / (w / 2), (yy - h / 2) / (h / 2))
    a *= (1 - 0.38 * f * np.clip(rr - 0.45, 0, 1) ** 1.6)[..., None]   # vinheta
    # grão grosso (meia resolução) + fino, mais forte nas sombras
    g1 = np.asarray(Image.fromarray(rng.normal(0, 1, (h // 2 + 1, w // 2 + 1)).astype(np.float32)).resize((w, h), Image.BILINEAR))
    g2 = rng.normal(0, 1, (h, w)).astype(np.float32)
    a += ((0.035 * g1 + 0.018 * g2) * f * (1.15 - lum[..., 0]))[..., None]
    # poeira e riscos finos de negativo
    for _ in range(int(14 * f)):
        x, y = rng.integers(0, w), rng.integers(0, h)
        a[max(0, y - 1):y + 2, max(0, x - 1):x + 2] += rng.choice([-0.12, 0.10])
    for _ in range(int(2 * f + 0.5)):
        x, y0, n = rng.integers(0, w), rng.integers(0, h // 2), rng.integers(h // 5, h // 2)
        a[y0:y0 + n, x:x + 1] += 0.05
    Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).save(SAI / (arq.stem + ".jpg"), quality=93)


for k, arq in enumerate(sorted((AQUI / "imagens").glob("B*"))):
    tratar(arq, FORCA.get(arq.stem[:3], 1.0), k)
    print(arq.name)
