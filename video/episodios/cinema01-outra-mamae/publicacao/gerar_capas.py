"""Capas do O QUE É A CRIATURA? #1 — Outra Mamãe — v2 (22/11, usuário: "não gostei, pesquise como os canais fazem").
Pesquisa (as mais vistas de 'final explicado' no BR — Sessão Nerd, PeeWee — e 'Horror History' do CZsWorld, o formato
mais parecido com o nosso, + estudo do vidIQ com 500 vídeos que explodiram):
  - imagem CLARA e saturada, rosto grande com emoção forte (medo / sorriso perturbador), nunca uma capa escura;
  - a criatura RECORTADA e com brilho em volta, sobre um fundo escurecido;
  - 3 a 5 palavras em letra condensada amarela/branca com contorno preto; o rótulo vermelho "FINAL EXPLICADO";
  - círculo vermelho + seta no detalhe que dá curiosidade; no Horror History, a linha do tempo (ano da lenda → ano do filme).
Quadros REAIS do filme (nenhum rosto de IA); os recortes saem do rembg (quadros/recorte_*.png, fora do git).
Uso: python3 gerar_capas.py → capa_*.jpg (1280×720)"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageChops

AQUI = Path(__file__).parent
Q = AQUI / "quadros"
F = Path(__file__).resolve().parents[3] / "painel" / "fontes"
ANTON = str(F / "Anton-400-latin.ttf")
W, H = 1280, 720
AMARELO, BRANCO, VERM, PRETO = (255, 214, 0), (255, 255, 255), (226, 18, 28), (0, 0, 0)


def vivo(im, cor=1.35, contraste=1.15, brilho=1.08):
    im = ImageEnhance.Color(im).enhance(cor); im = ImageEnhance.Contrast(im).enhance(contraste)
    return ImageEnhance.Brightness(im).enhance(brilho)


def recorte(nome, altura, cor=1.35, contraste=1.15, brilho=1.08, tinge=None):
    r = Image.open(Q / f"recorte_{nome}.png").convert("RGBA"); r = r.crop(r.getbbox())
    rgb = vivo(r.convert("RGB"), cor, contraste, brilho)
    if tinge:   # a criatura sai esverdeada do quadro escuro: puxa para a pele pálida e fria
        a = np.asarray(rgb).astype(np.float32); lum = a.mean(2, keepdims=True)
        a = lum * np.array(tinge); rgb = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    rgb.putalpha(r.split()[3])
    k = altura / rgb.height
    return rgb.resize((int(rgb.width * k), int(rgb.height * k)), Image.LANCZOS)


def colar(base, fig, x, y, borda=None, brilho=None):
    """cola o recorte com contorno (borda=(cor, px)) e brilho atrás (brilho=(cor, raio)), como no Horror History"""
    m = fig.split()[3]
    if brilho:
        g = Image.new("RGBA", base.size, (0, 0, 0, 0)); cam = Image.new("RGBA", fig.size, brilho[0] + (255,)); cam.putalpha(m)
        g.alpha_composite(cam, (x, y)); g = g.filter(ImageFilter.GaussianBlur(brilho[1]))
        base.alpha_composite(g); base.alpha_composite(g)
    if borda:
        mm = m.filter(ImageFilter.MaxFilter(borda[1] * 2 + 1)); cam = Image.new("RGBA", fig.size, borda[0] + (255,)); cam.putalpha(mm)
        base.alpha_composite(cam, (x, y))
    base.alpha_composite(fig, (x, y))


def fundo(arq, luz=0.35, blur=18, cor=1.0):
    im = Image.open(Q / arq).convert("RGB"); iw, ih = im.size; cw = ih * W / H
    if cw > iw:
        ch = iw * H / W; im = im.crop((0, (ih - ch) / 2, iw, (ih + ch) / 2))
    else:
        im = im.crop(((iw - cw) / 2, 0, (iw + cw) / 2, ih))
    im = ImageEnhance.Color(im.resize((W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(blur))).enhance(cor)
    a = np.asarray(im).astype(np.float32) * luz
    yy, xx = np.mgrid[0:H, 0:W]
    v = 1 - 0.55 * np.clip(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2 - 0.2, 0, 1)
    return Image.fromarray(np.clip(a * v[..., None], 0, 255).astype(np.uint8)).convert("RGBA")


def texto(base, t, x, y, tam, cor, contorno=10, ang=0, centro=False):
    f = ImageFont.truetype(ANTON, tam); d0 = ImageDraw.Draw(base)
    w = d0.textlength(t, font=f)
    cam = Image.new("RGBA", base.size, (0, 0, 0, 0)); d = ImageDraw.Draw(cam)
    x0 = x - w / 2 if centro else x
    d.text((x0, y), t, font=f, fill=cor + (255,), stroke_width=contorno, stroke_fill=PRETO + (255,))
    if ang:
        cam = cam.rotate(ang, resample=Image.BICUBIC, center=(x0 + w / 2, y + tam / 2))
    sombra = Image.new("RGBA", base.size, (0, 0, 0, 0)); sombra.paste((0, 0, 0, 200), mask=cam.split()[3])
    base.alpha_composite(ImageChops.offset(sombra.filter(ImageFilter.GaussianBlur(6)), 6, 8)); base.alpha_composite(cam)
    return w


def rotulo(base, t, x, y, tam=54, ang=-3):
    """o selo vermelho 'FINAL EXPLICADO' (caixa vermelha, letra branca, levemente torto)"""
    f = ImageFont.truetype(ANTON, tam); w = int(ImageDraw.Draw(base).textlength(t, font=f))
    cam = Image.new("RGBA", (w + 44, int(tam * 1.5)), (0, 0, 0, 0)); d = ImageDraw.Draw(cam)
    d.rectangle([0, 0, cam.width - 1, cam.height - 1], fill=VERM + (255,), outline=BRANCO + (255,), width=4)
    d.text((22, int(tam * 0.1)), t, font=f, fill=BRANCO + (255,))
    cam = cam.rotate(ang, expand=True, resample=Image.BICUBIC)
    base.alpha_composite(cam, (x, y))


def circulo(base, cx, cy, r, larg=12):
    g = Image.new("RGBA", base.size, (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=VERM + (255,), width=larg)
    gl = g.filter(ImageFilter.GaussianBlur(10)); base.alpha_composite(gl); base.alpha_composite(g)


def seta(base, x0, y0, x1, y1, larg=16, cor=VERM):
    d = ImageDraw.Draw(base); v = np.array([x1 - x0, y1 - y0], float); n = v / np.linalg.norm(v); p = np.array([-n[1], n[0]])
    ponta = np.array([x1, y1]); base_p = ponta - n * 46
    d.line([(x0, y0), tuple(base_p)], fill=PRETO + (255,), width=larg + 10)
    d.polygon([tuple(ponta + n * 6), tuple(base_p + p * 38), tuple(base_p - p * 38)], fill=PRETO + (255,))
    d.line([(x0, y0), tuple(base_p)], fill=cor + (255,), width=larg)
    d.polygon([tuple(ponta), tuple(base_p + p * 30), tuple(base_p - p * 30)], fill=cor + (255,))


def salvar(img, nome):
    img.convert("RGB").save(AQUI / nome, quality=93); print("ok", nome)


CRIATURA_COR = (0.98, 0.95, 0.9)   # pele pálida, sem o verde do quadro escuro

# 1 — estilo Sessão Nerd: a menina com medo (grande, à esquerda) + a criatura no círculo vermelho; "FINAL EXPLICADO"
b = fundo("q_840.png", luz=0.45, cor=1.2)
colar(b, recorte("bela", 720), -330, 0, borda=(BRANCO, 5))
cr = recorte("criatura", 420, cor=1.1, contraste=1.25, brilho=1.15, tinge=CRIATURA_COR)
cx, cy, r = 1020, 330, 200
disco = Image.new("L", b.size, 0); ImageDraw.Draw(disco).ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
cam = Image.new("RGBA", b.size, (0, 0, 0, 0)); cam.alpha_composite(cr, (cx - cr.width // 2 + 20, cy - cr.height // 2 + 30))
fundo_c = Image.new("RGBA", b.size, (25, 6, 8, 255)); fundo_c.alpha_composite(cam)
b.paste(fundo_c, (0, 0), disco)
circulo(b, cx, cy, r, 14)
seta(b, 600, 600, cx - r * 0.78, cy + r * 0.62)
rotulo(b, "FINAL EXPLICADO", 760, 575, 58)
texto(b, "O QUE ELA É?", 985, -4, 122, AMARELO, centro=True)
salvar(b, "capa_A_final_explicado.jpg")

# 2 — estilo Horror History: a criatura recortada com brilho vermelho + a linha do tempo (1895 → 2026)
b = fundo("q_3027.png", luz=0.32, blur=24, cor=1.3)
cr = recorte("criatura", 700, cor=1.1, contraste=1.3, brilho=1.2, tinge=CRIATURA_COR)
colar(b, cr, W // 2 - cr.width // 2 + 120, 30, borda=(PRETO, 4), brilho=(VERM, 38))
y = 560; d = ImageDraw.Draw(b)
for x0, x1 in ((70, 330), (950, 1210)):
    d.rectangle([x0, y - 6, x1, y + 6], fill=(240, 120, 30, 255))
d.rectangle([70, y - 26, 80, y + 26], fill=(240, 120, 30, 255)); d.rectangle([1200, y - 26, 1210, y + 26], fill=(240, 120, 30, 255))
texto(b, "1895", 60, y - 120, 92, BRANCO, 8)
texto(b, "2026", 1050, y - 120, 92, BRANCO, 8)
rotulo(b, "O QUE É A CRIATURA?", 36, 26, 50, ang=-2)
salvar(b, "capa_B_linha_do_tempo.jpg")

# 3 — as duas caras: a mãe perfeita (clara, à esquerda) e a criatura (à direita) no círculo + "NÃO É A MÃE DELA"
b = fundo("q_609.png", luz=0.3, blur=22)
m = recorte("mae", 760, cor=1.2, contraste=1.12, brilho=1.12)
colar(b, m, -90, 0, borda=(BRANCO, 5))
cr = recorte("criatura", 450, cor=1.1, contraste=1.3, brilho=1.2, tinge=CRIATURA_COR)
colar(b, cr, 760, 10, borda=(PRETO, 4), brilho=(VERM, 34))
circulo(b, 985, 215, 165, 13)
texto(b, "NÃO É A", 985, 440, 110, BRANCO, centro=True)
texto(b, "MÃE DELA", 985, 560, 124, AMARELO, centro=True)
salvar(b, "capa_C_nao_e_a_mae.jpg")
