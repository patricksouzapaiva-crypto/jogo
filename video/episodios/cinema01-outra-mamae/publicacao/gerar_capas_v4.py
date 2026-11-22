"""Capas do O QUE É A CRIATURA? #1 — Outra Mamãe — v4 (23/11).
Pedido do usuário (23/11): "use cenas do filme nas capas como eles fazem" — quadros REAIS do filme (publicacao/quadros,
fora do git), limpos do grão. Pedido do usuário: "melhores ainda, com mais edição, como nos
canais de exemplo" (Refúgio Cult, Derrotando Filmes, Ed Nerd, Thayla Moitinho): cor forte e saturada, o monstro
recortado com brilho em volta, letra Montserrat Black enorme com degradê amarelo→laranja, contorno grosso, sombra 3D,
o nome OUTRA MAMÃE numa tarja vermelha e UMA seta (a capa que mais estourou no nicho usa). Uso: python3 gerar_capas_v4.py"""
from pathlib import Path
import numpy as np
import cv2
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont
from rembg import remove

AQUI = Path(__file__).parent
EP = AQUI.parent
F = Path(__file__).resolve().parents[3] / "painel" / "fontes"
MONT = str(F / "Montserrat-900-latin.ttf")
MONT_I = str(F / "Montserrat-900-italic-latin.ttf")
W, H = 1280, 720
BRANCO, PRETO, VERM = (255, 255, 255), (0, 0, 0), (225, 20, 30)
OURO = ((255, 238, 70), (255, 140, 0))
SANGUE = ((255, 80, 60), (175, 0, 10))
CACHE = AQUI / "quadros"; CACHE.mkdir(exist_ok=True)


def base(arq, cx=0.5, cy=0.5, zoom=1.0, espelhar=False, limpar=0, luz=1.0):
    if arq.startswith("q_"):   # quadro do filme: clareia e tira o grão antes de recortar
        a = cv2.imread(str(CACHE / arq)).astype(np.float32) * luz
        a = np.clip(a, 0, 255).astype(np.uint8)
        if limpar:
            a = cv2.fastNlMeansDenoisingColored(a, None, limpar, limpar, 7, 21)
        im = Image.fromarray(cv2.cvtColor(a, cv2.COLOR_BGR2RGB))
    else:
        im = Image.open(EP / "imagens" / arq).convert("RGB")
    if espelhar:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    iw, ih = im.size; ch = ih / zoom; cw = ch * W / H
    if cw > iw:
        cw = iw; ch = cw * H / W
    x0 = min(max(0, cx * iw - cw / 2), iw - cw); y0 = min(max(0, cy * ih - ch / 2), ih - ch)
    return im.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, H), Image.LANCZOS)


def grade(im, sat=1.35, contraste=1.25, brilho=1.15, tinta=(1.0, 1.0, 1.0), gama=0.9):
    a = np.asarray(im).astype(np.float32) / 255
    a = np.clip(a * brilho, 0, 1) ** gama
    lum = a.mean(2, keepdims=True)
    a = lum + (a - lum) * sat
    a = np.clip(0.5 + (a - 0.5) * contraste, 0, 1) * np.array(tinta)
    # nitidez (os canais grandes passam tudo no "clarity")
    b = cv2.GaussianBlur(a, (0, 0), 2.2)
    a = np.clip(a * 1.5 - b * 0.5, 0, 1)
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))


def vinheta(im, forca=0.55, cx=0.5, cy=0.5):
    yy, xx = np.mgrid[0:H, 0:W]
    v = 1 - forca * np.clip(((xx - W * cx) / (W * 0.75)) ** 2 + ((yy - H * cy) / (H * 0.75)) ** 2 - 0.1, 0, 1)
    a = np.asarray(im).astype(np.float32) * v[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def lado_escuro(im, lado="esq", ate=0.5, forca=0.85):
    x = np.linspace(0, 1, W)[None, :, None]
    g = np.clip(1 - x / ate, 0, 1) if lado == "esq" else np.clip((x - (1 - ate)) / ate, 0, 1)
    a = np.asarray(im).astype(np.float32) * (1 - forca * g ** 1.5)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def recorte(im, nome):
    """máscara do sujeito (rembg), guardada"""
    arq = CACHE / f"mask_{nome}.png"
    if not arq.exists():
        remove(im.convert("RGB")).getchannel("A").save(arq)
    return Image.open(arq).convert("L")


def brilho_em_volta(im, mask, cor=(255, 30, 30), raio=18, forca=1.0):
    """contorno brilhante em volta do sujeito (o "glow" das capas de terror)"""
    m = mask.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(raio))
    m = m.point(lambda v: min(255, int(v * 1.6 * forca)))
    camada = Image.new("RGB", im.size, cor)
    out = im.convert("RGB").copy()
    out = Image.composite(Image.blend(out, camada, 0.85), out, ImageChops.subtract(m, mask))
    # o sujeito um pouco mais claro e nítido que o fundo
    claro = grade(im, sat=1.1, contraste=1.1, brilho=1.12, gama=0.95)
    return Image.composite(claro, out, mask.filter(ImageFilter.GaussianBlur(1.5)))


def letreiro(img, linhas, x, y, alinhar="esq", contorno=12, entre=1.0, brilho=(255, 150, 0), sombra3d=(8, 10)):
    """linhas = [(texto, fonte, tam, cor | (c1, c2))]: degradê vertical, contorno preto, sombra dura 3D e brilho colorido"""
    mt = Image.new("L", img.size, 0); mc = Image.new("L", img.size, 0)
    cor = Image.new("RGB", img.size, (0, 0, 0)); yy = y
    for t, fonte, tam, c in linhas:
        f = ImageFont.truetype(fonte, tam); d = ImageDraw.Draw(mt); w = d.textlength(t, font=f)
        xx = x - w if alinhar == "dir" else (x - w / 2 if alinhar == "centro" else x)
        m = Image.new("L", img.size, 0); ImageDraw.Draw(m).text((xx, yy), t, font=f, fill=255)
        ImageDraw.Draw(mc).text((xx, yy), t, font=f, fill=255, stroke_width=contorno, stroke_fill=255)
        bb = m.getbbox() or (0, 0, 1, 1)
        c1, c2 = (c, c) if isinstance(c[0], int) else c
        g = np.zeros((H, W, 3), np.float32)
        y0, y1 = bb[1], bb[3]
        k = np.clip((np.arange(H) - y0) / max(1, y1 - y0), 0, 1)[:, None]
        g[:] = (np.array(c1) * (1 - k) + np.array(c2) * k)[:, None, :]
        cor.paste(Image.fromarray(g.astype(np.uint8)), mask=m)
        mt.paste(255, mask=m)
        yy += int(tam * entre)
    out = img.convert("RGBA")
    if brilho:
        gl = Image.new("RGBA", img.size, brilho + (0,)); gl.putalpha(mc.filter(ImageFilter.GaussianBlur(26)).point(lambda v: int(v * 0.7)))
        out.alpha_composite(gl)
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0)); sh.paste((0, 0, 0, 255), mask=mc)
    out.alpha_composite(ImageChops.offset(sh, *sombra3d))
    out.alpha_composite(sh)
    ct = cor.convert("RGBA"); ct.putalpha(mt)
    out.alpha_composite(ct)
    return out


def tarja(img, texto, x, y, tam=46, fundo=VERM, cor=BRANCO, giro=-3):
    f = ImageFont.truetype(MONT, tam); w = int(f.getlength(texto)) + 44; h = int(tam * 1.45)
    t = Image.new("RGBA", (w + 20, h + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(t)
    d.rectangle([10, 10, 10 + w, 10 + h], fill=fundo + (255,), outline=PRETO + (255,), width=5)
    d.text((10 + 22, 10 + (h - tam) / 2 - tam * 0.08), texto, font=f, fill=cor)
    t = t.rotate(giro, expand=True, resample=Image.BICUBIC)
    img.alpha_composite(t, (int(x), int(y)))


def seta(img, p0, p1, cor=VERM, larg=26, curva=0.25):
    """seta curva grossa, vermelha com contorno preto (como na capa que mais estourou)"""
    (x0, y0), (x1, y1) = p0, p1
    mx, my = (x0 + x1) / 2 - (y1 - y0) * curva, (y0 + y1) / 2 + (x1 - x0) * curva
    ts = np.linspace(0, 0.86, 40)
    pts = [((1 - t) ** 2 * x0 + 2 * (1 - t) * t * mx + t * t * x1, (1 - t) ** 2 * y0 + 2 * (1 - t) * t * my + t * t * y1) for t in ts]
    ex, ey = pts[-1]; dx, dy = x1 - ex, y1 - ey; n = max(1e-6, (dx * dx + dy * dy) ** 0.5); ux, uy = dx / n, dy / n
    cab = [(x1, y1), (ex - uy * larg * 1.5, ey + ux * larg * 1.5), (ex + uy * larg * 1.5, ey - ux * larg * 1.5)]
    camada = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(camada)
    for cc, w_ in ((PRETO, larg + 14), (cor, larg)):
        d.line(pts, fill=cc + (255,), width=w_, joint="curve")
        if cc == PRETO:
            d.polygon([(x1 + ux * 9, y1 + uy * 9), (cab[1][0] - ux * 7 - uy * 7, cab[1][1] - uy * 7 + ux * 7),
                       (cab[2][0] - ux * 7 + uy * 7, cab[2][1] - uy * 7 - ux * 7)], fill=PRETO + (255,))
        else:
            d.polygon(cab, fill=cor + (255,))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0)); sh.paste((0, 0, 0, 150), mask=camada.getchannel("A"))
    img.alpha_composite(ImageChops.offset(sh.filter(ImageFilter.GaussianBlur(6)), 5, 8))
    img.alpha_composite(camada)


def salvar(img, nome):
    img.convert("RGB").save(AQUI / nome, quality=95); print("ok", nome)


# A — a cena-ícone (a mesma que 3 dos canais grandes usaram): a mãe dobrada debaixo da mesa, sorrindo; "O QUE ELA É?"
im = base("q_704.9.png", 0.74, 0.5, 1.0, limpar=3, luz=1.1)
im = grade(im, sat=1.35, contraste=1.2, brilho=1.12, tinta=(1.05, 0.98, 0.92))
mk = recorte(im, "f_mesa")
im = brilho_em_volta(im, mk, (255, 40, 20), 12, 0.55)
im = vinheta(lado_escuro(im, "esq", 0.5, 0.85), 0.4, 0.7)
c = letreiro(im, [("O QUE", MONT, 150, BRANCO), ("ELA É?", MONT, 170, OURO)], 46, 205, entre=1.0)
tarja(c, "OUTRA MAMÃE", 40, 70, 50)
seta(c, (470, 665), (745, 480), larg=24, curva=0.18)
salvar(c, "capa_A_mesa.jpg")

# B — a criatura de perto, clara e limpa, com brilho vermelho; "ELA NÃO É SUA MÃE" (23/11, usuário: "não é um demônio" entregava o veredito)
im = base("q_4898.5.png", 0.0, 0.5, 1.0, espelhar=True, limpar=5, luz=2.2)
im = grade(im, sat=1.25, contraste=1.2, brilho=1.45, tinta=(1.1, 0.97, 0.9), gama=0.8)
mk = recorte(im, "f_criatura")
im = vinheta(lado_escuro(im, "dir", 0.48, 0.88), 0.35, 0.3)
c = letreiro(im, [("ELA NÃO É", MONT, 112, BRANCO), ("SUA MÃE", MONT, 150, SANGUE)], W - 40, 220,
             alinhar="dir", entre=1.02, brilho=(230, 20, 40))
tarja(c, "OUTRA MAMÃE", W - 500, 70, 50, giro=3)
salvar(c, "capa_B_sua_mae.jpg")

# C — antes × depois: a mãe sorrindo | a coisa com o mesmo sorriso, corte inclinado; "FINAL EXPLICADO"
e = grade(base("q_609.png", 0.0, 0.40, 1.15, limpar=3, luz=1.2), sat=1.3, contraste=1.15, brilho=1.15, tinta=(1.06, 1.0, 0.94))
d = grade(base("q_4898.5.png", 0.0, 0.5, 1.05, limpar=5, luz=2.2), sat=1.05, contraste=1.3, brilho=1.1, tinta=(0.88, 1.02, 0.98))
ea = np.roll(np.asarray(e), -W // 4 - 110, axis=1); da = np.roll(np.asarray(d)[:, ::-1], W // 4 - 30, axis=1)
yy, xx = np.mgrid[0:H, 0:W]
corte = (xx > W / 2 + (yy - H / 2) * 0.18)[..., None]
a = np.where(corte, da, ea).astype(np.float32)
a *= (1 - 0.8 * np.clip((yy - H * 0.52) / (H * 0.48), 0, 1) ** 1.3)[..., None]
im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
dd = ImageDraw.Draw(im)
for k in range(H):
    cx_ = W / 2 + (k - H / 2) * 0.18
    dd.line([(cx_ - 5, k), (cx_ + 5, k)], fill=(255, 255, 255, 255))
c = letreiro(im.convert("RGB"), [("FINAL", MONT, 120, BRANCO), ("EXPLICADO", MONT, 120, OURO)], W / 2, 455, alinhar="centro", entre=1.0)
tarja(c, "OUTRA MAMÃE", 40, 40, 46, giro=-3)
salvar(c, "capa_C_final.jpg")
