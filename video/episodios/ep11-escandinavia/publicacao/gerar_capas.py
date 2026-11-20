"""Capas do Ep. 11 (20/11) no estilo aprovado no Ep. 10: visão noturna de câmera de trilha, texto enorme (2 palavras por
linha, a de baixo em vermelho), SEM círculo e SEM seta, pretos esmagados, falhas de câmera e a bandeira da Suécia.
A criatura é sempre a mesma (o desenho de chifres largos do clímax). Nenhum rosto humano.
Uso: python3 gerar_capas.py → capa_*.jpg (1280×720)"""
from pathlib import Path
import math
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont

AQUI = Path(__file__).parent
R = AQUI.parent / "imagens" / "cenas"
F = Path(__file__).resolve().parents[3] / "painel" / "fontes"
ANTON, MONO = str(F / "Anton-400-latin.ttf"), "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
W, H = 1280, 720
VERM = (230, 20, 28)
BRANCO = (255, 248, 236)
rng = np.random.default_rng(11)
COM_CIRCULO = False
COM_SETA = False


def abrir(cod, cx, cy, zoom):
    img = Image.open(next((R / cod.rsplit("_", 1)[0]).glob(cod + ".*"))).convert("RGB"); iw, ih = img.size
    cw = min(iw, ih * W / H) / zoom; ch = cw * H / W
    x0 = min(max(0, cx * iw - cw / 2), iw - cw); y0 = min(max(0, cy * ih - ch / 2), ih - ch)
    return img.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, H), Image.LANCZOS), (x0, y0, cw / W)


def para_tela(px, py, geo):            # coordenada (fração da imagem original) → pixel da capa
    x0, y0, k = geo
    return (px - x0) / k, (py - y0) / k


def curva(a, preto=0.05, gama=1.08):    # pretos esmagados + contraste em S
    a = np.clip((a / 255 - preto) / (1 - preto), 0, 1) ** gama
    return a * 255


def grade(img, modo):
    a = np.asarray(img).astype(np.float32)
    lum = a.mean(2, keepdims=True)
    if modo == "ir":       # visão noturna: verde-acinzentado, brilhos quase brancos
        a = lum * np.array([0.80, 1.0, 0.84]) * 1.3
    elif modo == "sangue":  # folclore: frio nas sombras, vermelho saturado onde já é vermelho
        r = a[..., 0:1]; red = np.clip((r - a[..., 1:2] * 1.1) / 60, 0, 1)
        a = a * (1 - red) * np.array([0.72, 0.86, 1.0]) + a * red * np.array([1.6, 0.55, 0.5])
    elif modo == "quente":
        a = a * np.array([1.12, 0.92, 0.8])
    a = curva(a)
    yy, xx = np.mgrid[0:H, 0:W]
    v = 1 - 0.55 * np.clip((((xx - W * 0.55) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2) - 0.25, 0, 1)
    return Image.fromarray(np.clip(a * v[..., None], 0, 255).astype(np.uint8))


def escuro_lado(img, lado, forca=0.92, ate=0.55):
    a = np.asarray(img).astype(np.float32); x = np.linspace(0, 1, W)[None, :, None]
    g = np.clip(1 - x / ate, 0, 1) if lado == "esq" else np.clip((x - (1 - ate)) / ate, 0, 1)
    return Image.fromarray(np.clip(a * (1 - forca * g ** 1.4), 0, 255).astype(np.uint8))


def falha_cctv(img):
    a = np.asarray(img).astype(np.float32)
    a[::3] *= 0.82                                                   # linhas de varredura
    a += rng.normal(0, 9, (H, W, 1))                                 # ruído do sensor
    out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    r, g, b = out.split()                                            # aberração cromática nas bordas
    out = Image.merge("RGB", (ImageChops.offset(r, 3, 0), g, ImageChops.offset(b, -3, 0)))
    y = int(H * 0.72); faixa = out.crop((0, y, W, y + 14))           # faixa de interferência deslocada
    out.paste(ImageChops.offset(faixa, 22, 0), (0, y))
    return out


def brilho_vermelho(img, cx, cy, r, forca=0.9):
    a = np.asarray(img).astype(np.float32); yy, xx = np.mgrid[0:H, 0:W]
    g = np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * r * r)))[..., None]
    a = a + g * forca * np.array([255, 20, 25]) * 0.9
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def circulo_seta(base, cx, cy, r, de):
    if not (COM_CIRCULO or COM_SETA):
        return
    cam = Image.new("RGBA", base.size, (0, 0, 0, 0)); d = ImageDraw.Draw(cam)
    if not COM_CIRCULO:
        r = min(r, 34)   # sem círculo, a seta chega quase encostando no alvo
    if COM_CIRCULO:   # 16/11: o usuário pediu para tirar o círculo — fica só a seta apontando
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=VERM + (255,), width=10)
    # seta: do ponto "de" até a borda do círculo
    ang = math.atan2(cy - de[1], cx - de[0]); px, py = cx - math.cos(ang) * (r + 14), cy - math.sin(ang) * (r + 14)
    d.line((de[0], de[1], px, py), fill=VERM + (255,), width=14)
    ca = 34
    for s in (+1, -1):
        d.line((px, py, px - math.cos(ang + s * 0.5) * ca * 1.6, py - math.sin(ang + s * 0.5) * ca * 1.6), fill=VERM + (255,), width=14)
    glow = cam.filter(ImageFilter.GaussianBlur(10))
    base.alpha_composite(glow); base.alpha_composite(cam)


def texto(base, linhas, x, y, cores, tam, ang=0.0):
    cam = Image.new("RGBA", base.size, (0, 0, 0, 0)); d = ImageDraw.Draw(cam)
    yy = y
    for l, c, t in zip(linhas, cores, tam):
        f = ImageFont.truetype(ANTON, t)
        d.text((x, yy), l, font=f, fill=c + (255,), stroke_width=7, stroke_fill=(8, 4, 4, 255)); yy += int(t * 1.02)
    if ang:
        cam = cam.rotate(ang, resample=Image.BICUBIC, center=(x, y))
    a = np.asarray(cam).astype(np.float32)
    verm = (a[..., 0] > 150) & (a[..., 1] < 90)                      # brilho só nas letras vermelhas
    gl = np.zeros_like(a); gl[verm] = [255, 30, 30, 255]
    gl = Image.fromarray(gl.astype(np.uint8)).filter(ImageFilter.GaussianBlur(18))
    sombra = Image.new("RGBA", base.size, (0, 0, 0, 0)); sombra.paste((0, 0, 0, 230), mask=cam.split()[3])
    base.alpha_composite(ImageChops.offset(sombra.filter(ImageFilter.GaussianBlur(10)), 8, 10))
    base.alpha_composite(gl); base.alpha_composite(gl); base.alpha_composite(cam)


def hud(base, cam, hora):
    f = ImageFont.truetype(MONO, 26); d = ImageDraw.Draw(base)
    d.text((34, 26), cam, font=f, fill=(225, 245, 228)); d.ellipse((36, 70, 56, 90), fill=(255, 30, 30))
    d.text((66, 64), "REC  " + hora, font=f, fill=(225, 245, 228))


def selo(base, x, y, t="FOLCLORE REAL DA ESCANDINÁVIA"):
    f = ImageFont.truetype(ANTON, 30); d = ImageDraw.Draw(base); w = d.textlength(t, font=f)
    d.rectangle((x, y, x + w + 28, y + 46), fill=VERM); d.text((x + 14, y + 4), t, font=f, fill=BRANCO)


def bandeira(base, x=1150, y=24, w=104):   # Suécia: azul com a cruz nórdica amarela
    h = int(w * 5 / 8); d = ImageDraw.Draw(base)
    d.rectangle((x - 3, y - 3, x + w + 3, y + h + 3), fill=(10, 8, 8)); d.rectangle((x, y, x + w, y + h), fill=(0, 92, 160))
    t = h // 5; cx = x + int(w * 5 / 16)
    d.rectangle((cx, y, cx + t, y + h), fill=(254, 204, 0)); d.rectangle((x, y + (h - t) // 2, x + w, y + (h + t) // 2), fill=(254, 204, 0))


def salvar(img, nome):
    img.convert("RGB").save(AQUI / nome, quality=92); print("ok", nome)




def capa(cod, cx, cy, zoom, linhas, cores, tam, txy, cam, hora, nome, lado_escuro="esq", luz=1.0, forca=0.75, ate=0.42):
    img, geo = abrir(cod, cx, cy, zoom)
    img = ImageEnhance.Brightness(img).enhance(luz)
    im = falha_cctv(grade(escuro_lado(img, lado_escuro, forca, ate), "ir")).convert("RGBA")
    texto(im, linhas, txy[0], txy[1], cores, tam, ang=3)
    hud(im, cam, hora); bandeira(im)
    salvar(im, nome)


# A — a criatura no feixe da lanterna (a mesma do clímax). "NÃO SIGA / O CANTO"
capa("G02c_01", 0.62, 0.5, 1.25, ["NÃO SIGA", "O CANTO"], [BRANCO, VERM], [140, 160], (36, 150),
     "CAM 02 - TRILHA NORTE", "02:41:07", "capa_A_canto.jpg")
# B — a mesma criatura de corpo inteiro, parada entre os troncos. "NÃO ENTRE / NA MATA"
capa("C3_03_01", 0.62, 0.45, 1.15, ["NÃO ENTRE", "NA MATA"], [BRANCO, VERM], [140, 160], (36, 150),
     "CAM 01 - CLAREIRA", "02:53:44", "capa_B_mata.jpg", lado_escuro="dir")
# C — os moradores em linha na borda da clareira, olhando a floresta. "ELES ESTÃO / ESPERANDO"
capa("H10_02", 0.62, 0.45, 1.3, ["ELES ESTÃO", "ESPERANDO"], [BRANCO, VERM], [130, 150], (36, 150),
     "CAM 01 - CLAREIRA", "02:31:12", "capa_C_esperando.jpg", luz=1.3)
# D — o altar de chifres e sangue na neve. "VOCÊ É / O TRIBUTO"
capa("G02b_02", 0.55, 0.5, 1.2, ["VOCÊ É", "O TRIBUTO"], [BRANCO, VERM], [140, 160], (36, 150),
     "CAM 03 - ALTAR", "03:02:55", "capa_D_tributo.jpg", luz=1.15)
