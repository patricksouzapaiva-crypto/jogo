"""Capas do O QUE É A CRIATURA? #1 — Outra Mamãe (22/11). Estilo do canal (Ep. 10/11): texto enorme em Anton, a linha
de baixo em vermelho com brilho, pretos esmagados, vinheta. Quadros REAIS do filme (nenhum rosto de IA), como nos
canais de análise de cinema. Uso: python3 gerar_capas.py → capa_*.jpg (1280×720)
Os quadros saem do filme (fora do git): quadros/q_609.png (a Outra Mamãe sorrindo, 10:09) e q_4903.png (a criatura, 1:21:43)."""
from pathlib import Path
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

AQUI = Path(__file__).parent
Q = AQUI / "quadros"
F = Path(__file__).resolve().parents[3] / "painel" / "fontes"
ANTON = str(F / "Anton-400-latin.ttf")
W, H = 1280, 720
VERM = (230, 20, 28)
BRANCO = (255, 248, 236)


def recorte(arq, cx, cy, zoom, luz=1.0, gama=1.0):
    """recorte 16:9 centrado em (cx, cy) (frações do quadro), com zoom; luz/gama para abrir quadros muito escuros."""
    img = Image.open(Q / arq).convert("RGB"); iw, ih = img.size
    ch = ih / zoom; cw = ch * W / H
    if cw > iw:
        cw = iw; ch = cw * H / W
    x0 = min(max(0, cx * iw - cw / 2), iw - cw); y0 = min(max(0, cy * ih - ch / 2), ih - ch)
    img = img.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, H), Image.LANCZOS)
    a = np.asarray(img).astype(np.float32) / 255
    if luz == "auto":   # quadro escuro: o 99,5º percentil vira quase branco (abre a criatura sem estourar)
        luz = 0.9 / max(1e-3, np.percentile(a, 99.5))
    a = np.clip(a * luz, 0, 1) ** gama
    return a * 255


def grade(a, frio=0.25, preto=0.06, sat=0.8, vx=0.5):
    lum = a.mean(2, keepdims=True)
    a = lum + (a - lum) * sat                                         # menos cor: o rosto fica "de cera"
    a = a * (1 - frio) + a * np.array([0.82, 0.95, 1.12]) * frio      # sombras frias
    a = np.clip((a / 255 - preto) / (1 - preto), 0, 1) ** 1.1 * 255   # pretos esmagados
    yy, xx = np.mgrid[0:H, 0:W]
    v = 1 - 0.6 * np.clip((((xx - W * vx) / (W * 0.6)) ** 2 + ((yy - H / 2) / (H * 0.6)) ** 2) - 0.2, 0, 1)
    return a * v[..., None]


def escuro_lado(a, lado, forca=0.9, ate=0.5):
    x = np.linspace(0, 1, W)[None, :, None]
    g = np.clip(1 - x / ate, 0, 1) if lado == "esq" else np.clip((x - (1 - ate)) / ate, 0, 1)
    return a * (1 - forca * g ** 1.4)


def texto(base, linhas, x, y, cores, tam, ang=0.0):
    cam = Image.new("RGBA", base.size, (0, 0, 0, 0)); d = ImageDraw.Draw(cam)
    yy = y
    for l, c, t in zip(linhas, cores, tam):
        f = ImageFont.truetype(ANTON, t)
        d.text((x, yy), l, font=f, fill=c + (255,), stroke_width=7, stroke_fill=(8, 4, 4, 255)); yy += int(t * 1.02)
    if ang:
        cam = cam.rotate(ang, resample=Image.BICUBIC, center=(x, y))
    a = np.asarray(cam).astype(np.float32)
    verm = (a[..., 0] > 150) & (a[..., 1] < 90)
    gl = np.zeros_like(a); gl[verm] = [255, 30, 30, 255]
    gl = Image.fromarray(gl.astype(np.uint8)).filter(ImageFilter.GaussianBlur(18))
    sombra = Image.new("RGBA", base.size, (0, 0, 0, 0)); sombra.paste((0, 0, 0, 230), mask=cam.split()[3])
    base.alpha_composite(ImageChops.offset(sombra.filter(ImageFilter.GaussianBlur(10)), 8, 10))
    base.alpha_composite(gl); base.alpha_composite(gl); base.alpha_composite(cam)


def carimbo(base, txt, cx, cy, tam=86, ang=12):
    """o carimbo vermelho do formato (o mesmo do veredito), torto e com falhas de tinta"""
    f = ImageFont.truetype(ANTON, tam); tw = int(f.getlength(txt)) + 70; th = int(tam * 1.45)
    c = Image.new("RGBA", (tw, th), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    d.rectangle([6, 6, tw - 6, th - 6], outline=VERM + (240,), width=10)
    d.text((35, int(tam * 0.12)), txt, font=f, fill=VERM + (240,))
    a = np.array(c); rng = np.random.default_rng(5)
    a[..., 3] = np.where(rng.random(a.shape[:2]) < 0.12, a[..., 3] // 3, a[..., 3])
    c = Image.fromarray(a).rotate(ang, expand=True, resample=Image.BICUBIC)
    base.alpha_composite(c, (int(cx - c.width / 2), int(cy - c.height / 2)))


def tela(a):
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")


def salvar(img, nome):
    img.convert("RGB").save(AQUI / nome, quality=92); print("ok", nome)


# A — o sorriso perfeito demais: a Outra Mamãe à direita, o texto à esquerda
a = escuro_lado(grade(recorte("q_609.png", 0.0, 0.42, 1.25), vx=0.72), "esq", 0.95, 0.5)
b = tela(a)
texto(b, ["ELA NÃO É", "SUA MÃE"], 46, 160, [BRANCO, VERM], [150, 170])
salvar(b, "capa_A_sorriso.jpg")

# B — as duas caras: a mãe (esq.) e a criatura (dir.), cortadas no meio; a pergunta do vídeo embaixo
m = grade(recorte("q_609.png", 0.5, 0.4, 1.25), vx=0.5)
c = grade(recorte("q_4903.png", 0.64, 0.45, 1.2, luz="auto", gama=0.8), frio=0.4, sat=0.6, preto=0.02, vx=0.5)
a = np.concatenate([m[:, W // 4 + 40:W // 4 + 40 + W // 2], c[:, W // 4:W // 4 + W // 2]], axis=1)
x = np.arange(W)[None, :]; borda = W * 0.5 + 14 * np.sin(np.arange(H) / 23.0)[:, None]
a[np.abs(x - borda) < 3] = [230, 20, 28]
a = a * np.clip(1 - np.clip((np.arange(H)[:, None, None] - H * 0.55) / (H * 0.45), 0, 1) * 0.75, 0, 1)
b = tela(a)
f = ImageFont.truetype(ANTON, 150); w = ImageDraw.Draw(b).textlength("O QUE ELA É?", font=f)
texto(b, ["O QUE ELA É?"], int(W / 2 - w / 2), 520, [BRANCO], [150])
texto(b, ["?"], int(W / 2 + w / 2 - ImageDraw.Draw(b).textlength("?", font=f)), 520, [VERM], [150])
salvar(b, "capa_B_duas_caras.jpg")

# C — a criatura e o carimbo do veredito (sem dizer qual: a curiosidade fica para o vídeo)
a = recorte("q_4903.png", 0.6, 0.45, 1.1, luz="auto", gama=0.8)
a = escuro_lado(grade(a, frio=0.4, sat=0.65, preto=0.02, vx=0.66), "esq", 0.95, 0.5)
b = tela(a)
texto(b, ["NÃO É", "DEMÔNIO"], 46, 90, [BRANCO, VERM], [150, 170])
carimbo(b, "É PIOR", 290, 560, tam=120, ang=9)
salvar(b, "capa_C_veredito.jpg")
