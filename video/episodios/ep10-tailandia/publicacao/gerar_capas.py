"""Capas do Ep. 10 (16/11) — as 3 versões do pacote (YOUTUBE.md) para o teste A/B, com as imagens do episódio.
A: o corredor da câmera de segurança (G03), "NUNCA ABRA / A PORTA"; B: a Krasue atrás do vidro (C2_03), "O TERROR /
DE ISAN"; C: o Mateus na cama (H18) com o círculo vermelho no teto, "ELES ENTRAM / EM VOCÊ".
Nenhum rosto. Bandeira da Tailândia no ALTO à direita (embaixo à direita o YouTube põe a duração).
Uso: python3 gerar_capas.py → capa_A_porta.jpg, capa_B_isan.jpg, capa_C_entram.jpg (1280×720)"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

AQUI = Path(__file__).parent
R = AQUI.parent / "imagens" / "recebidas"
F = Path(__file__).resolve().parents[3] / "painel" / "fontes"
ANTON, MONO = str(F / "Anton-400-latin.ttf"), "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
W, H = 1280, 720
VERMELHO = (214, 24, 30)
BRANCO = (255, 250, 240)


def abrir(cod, cx=0.5, cy=0.5, zoom=1.0):
    img = Image.open(R / f"{cod}.jpg").convert("RGB"); iw, ih = img.size
    cw = min(iw, ih * W / H) / zoom; ch = cw * H / W
    x0 = min(max(0, cx * iw - cw / 2), iw - cw); y0 = min(max(0, cy * ih - ch / 2), ih - ch)
    return img.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, H), Image.LANCZOS)


def tratar(img, sat=0.8, luz=1.0, contraste=1.25):
    img = ImageEnhance.Color(img).enhance(sat); img = ImageEnhance.Contrast(img).enhance(contraste)
    return ImageEnhance.Brightness(img).enhance(luz)


def escurecer(img, forca=0.9, ate=0.6):
    a = np.asarray(img).astype(np.float32)
    g = np.clip(1 - np.linspace(0, 1, W)[None, :, None] / ate, 0, 1)
    a *= 1 - forca * g ** 1.3
    yy, xx = np.mgrid[0:H, 0:W]
    a *= (1 - 0.35 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / 2)[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def grao(img, q=7):
    a = np.asarray(img).astype(np.float32) + np.random.default_rng(10).normal(0, q, (H, W, 1))
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def texto(base, linhas, x, y, cores, tam, contorno=6):
    d = ImageDraw.Draw(base)
    for l, c, t in zip(linhas, cores, tam):
        f = ImageFont.truetype(ANTON, t)
        s = Image.new("RGBA", base.size, (0, 0, 0, 0)); ImageDraw.Draw(s).text((x + 6, y + 8), l, font=f, fill=(0, 0, 0, 210))
        base.alpha_composite(s.filter(ImageFilter.GaussianBlur(8)))
        d.text((x, y), l, font=f, fill=c, stroke_width=contorno, stroke_fill=(10, 6, 6)); y += int(t * 1.06)


def selo(base, x, y, t="LENDAS REAIS DA TAILÂNDIA"):
    f = ImageFont.truetype(ANTON, 30); d = ImageDraw.Draw(base); w = d.textlength(t, font=f)
    d.rectangle((x, y, x + w + 28, y + 46), fill=VERMELHO); d.text((x + 14, y + 4), t, font=f, fill=BRANCO)


def bandeira(base, x=1146, y=26, w=108):
    h = int(w * 2 / 3); d = ImageDraw.Draw(base)
    d.rectangle((x - 3, y - 3, x + w + 3, y + h + 3), fill=(15, 12, 12))
    for k, cor in enumerate([(165, 25, 49), (244, 245, 248), (45, 42, 74), (45, 42, 74), (244, 245, 248), (165, 25, 49)]):
        d.rectangle((x, y + k * h // 6, x + w, y + (k + 1) * h // 6), fill=cor)


def cctv(base, cam="CAM 01 - CORREDOR", hora="02:40:18"):
    f = ImageFont.truetype(MONO, 28); d = ImageDraw.Draw(base)
    d.text((40, 30), cam, font=f, fill=(235, 240, 235)); d.ellipse((40, 76, 60, 96), fill=(255, 40, 40))
    d.text((70, 70), "REC  18-09-2025  " + hora, font=f, fill=(235, 240, 235))


def circulo(base, cx, cy, r):
    c = Image.new("RGBA", base.size, (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=VERMELHO + (255,), width=9)
    base.alpha_composite(c.filter(ImageFilter.GaussianBlur(5))); base.alpha_composite(c)


def salvar(img, nome):
    img.convert("RGB").save(AQUI / nome, quality=92); print("ok", nome)


a = abrir("G03_variacao_2", 0.3, 0.5, 1.3)
a = grao(escurecer(tratar(a, 0.5, 1.15, 1.35), 0.9, 0.55)).convert("RGBA")
texto(a, ["NUNCA ABRA", "A PORTA"], 46, 210, [BRANCO, VERMELHO], [130, 150])
selo(a, 50, 600); bandeira(a); cctv(a)
salvar(a, "capa_A_porta.jpg")

b = abrir("C2_03_variacao_2", 0.62, 0.45, 1.1)
b = grao(escurecer(tratar(b, 1.0, 1.05, 1.3), 0.92, 0.55)).convert("RGBA")
texto(b, ["O TERROR", "DE ISAN"], 46, 200, [BRANCO, VERMELHO], [140, 160])
selo(b, 50, 600); bandeira(b)
salvar(b, "capa_B_isan.jpg")

c = abrir("H18_variacao_4", 0.35, 0.5, 1.15)
c = grao(escurecer(tratar(c, 0.5, 1.15, 1.35), 0.9, 0.5)).convert("RGBA")
circulo(c, 1100, 230, 95)
texto(c, ["ELES ENTRAM", "EM VOCÊ"], 46, 210, [BRANCO, VERMELHO], [128, 150])
selo(c, 50, 600); bandeira(c); cctv(c, "CAM 04 - QUARTO", "06:12:01")
salvar(c, "capa_C_entram.jpg")
