"""Capas v2 do Ep. 10 (16/11) — usuário: "muito fracas, mais chamativas e sinistras".
O que mudou da v1: (1) cada capa tem UM detalhe que dá medo, marcado com círculo + seta vermelhos (a mão na fresta, o
prato de carne crua, o brilho vermelho da Krasue, o selo rasgado); (2) cor dirigida — visão noturna verde nas da câmera,
vermelho-sangue nas do folclore — com pretos esmagados e vinheta pesada; (3) texto maior, 2 palavras por linha, com
brilho vermelho e contorno; (4) falhas de câmera (linhas de varredura, aberração cromática, faixa de interferência).
Nenhum rosto. Canto inferior direito livre (duração do YouTube). Uso: python3 gerar_capas_v2.py → capa_D…G.jpg"""
from pathlib import Path
import math
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont

AQUI = Path(__file__).parent
R = AQUI.parent / "imagens" / "recebidas"
F = Path(__file__).resolve().parents[3] / "painel" / "fontes"
ANTON, MONO = str(F / "Anton-400-latin.ttf"), "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
W, H = 1280, 720
VERM = (230, 20, 28)
BRANCO = (255, 248, 236)
rng = np.random.default_rng(10)
COM_CIRCULO = False


def abrir(cod, cx, cy, zoom):
    img = Image.open(R / f"{cod}.jpg").convert("RGB"); iw, ih = img.size
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


def selo(base, x, y, t="LENDAS REAIS DA TAILÂNDIA"):
    f = ImageFont.truetype(ANTON, 30); d = ImageDraw.Draw(base); w = d.textlength(t, font=f)
    d.rectangle((x, y, x + w + 28, y + 46), fill=VERM); d.text((x + 14, y + 4), t, font=f, fill=BRANCO)


def bandeira(base, x=1150, y=24, w=104):
    h = int(w * 2 / 3); d = ImageDraw.Draw(base)
    d.rectangle((x - 3, y - 3, x + w + 3, y + h + 3), fill=(10, 8, 8))
    for k, cor in enumerate([(165, 25, 49), (244, 245, 248), (45, 42, 74), (45, 42, 74), (244, 245, 248), (165, 25, 49)]):
        d.rectangle((x, y + k * h // 6, x + w, y + (k + 1) * h // 6), fill=cor)


def salvar(img, nome):
    img.convert("RGB").save(AQUI / nome, quality=92); print("ok", nome)


# D — a MÃO na fresta da porta (CCTV). "ELA ESTÁ / LÁ DENTRO"
img, geo = abrir("H12_variacao_1", 0.47, 0.5, 1.45)
im = falha_cctv(grade(escuro_lado(img, "esq", 0.75, 0.42), "ir")).convert("RGBA")
hx, hy = para_tela(0.576 * 1672, 0.55 * 941, geo)
circulo_seta(im, hx, hy, 66, (hx + 230, hy + 170))
texto(im, ["ELA ESTÁ", "LÁ DENTRO"], 36, 150, [BRANCO, VERM], [132, 150], ang=3)
hud(im, "CAM 02 - PORTA", "02:40:31"); bandeira(im)
salvar(im, "capa_D_dentro.jpg")

# E — o PRATO de carne crua no colo (CCTV). "O QUE ELE / ESTÁ COMENDO?"
img, geo = abrir("H18_variacao_4", 0.36, 0.5, 1.3)
im = falha_cctv(grade(escuro_lado(img, "esq", 0.88, 0.62), "ir"))
px, py = para_tela(0.44 * 1672, 0.485 * 941, geo)
im = brilho_vermelho(im, px, py, 30, 0.4).convert("RGBA")
circulo_seta(im, px, py, 66, (px - 210, py + 230))
texto(im, ["O QUE ELE", "ESTÁ", "COMENDO?"], 36, 120, [BRANCO, BRANCO, VERM], [112, 112, 124], ang=2)
hud(im, "CAM 04 - QUARTO", "06:12:01"); bandeira(im)
salvar(im, "capa_E_comendo.jpg")

# F — a Krasue atrás do vidro: o vermelho que pulsa no peito. "A CABEÇA / SAI À NOITE"
img, geo = abrir("C2_03_variacao_2", 0.62, 0.45, 1.12)
im = grade(escuro_lado(img, "esq", 0.9, 0.5), "sangue")
im = ImageEnhance.Brightness(im).enhance(1.35).convert("RGBA")
texto(im, ["A CABEÇA", "SAI À NOITE"], 40, 120, [BRANCO, VERM], [140, 138], ang=2)
selo(im, 44, 600); bandeira(im)
salvar(im, "capa_F_cabeca.jpg")

# G — o selo Pha Yant RASGADO na porta. "NUNCA QUEBRE / O SELO"
img, geo = abrir("G04a_variacao_2", 0.42, 0.45, 1.05)
im = grade(escuro_lado(img, "dir", 0.92, 0.45), "sangue").convert("RGBA")
texto(im, ["NUNCA", "QUEBRE", "O SELO"], 690, 70, [BRANCO, BRANCO, VERM], [130, 130, 170], ang=2)
selo(im, 700, 620); bandeira(im)
salvar(im, "capa_G_selo.jpg")

# ---- 16/11 (usuário: "gostei da D, quero outras nesse estilo: ela sentada no canto no escuro e ela parada em frente
# à porta, na câmera") ----
def capa_cctv(cod, cx, cy, zoom, alvo, r, de, linhas, cores, tam, txy, cam, hora, nome, lado_escuro="esq", luz=1.0):
    img, geo = abrir(cod, cx, cy, zoom)
    img = ImageEnhance.Brightness(img).enhance(luz)
    im = falha_cctv(grade(escuro_lado(img, lado_escuro, 0.75, 0.42), "ir")).convert("RGBA")
    ax, ay = para_tela(alvo[0] * 1672, alvo[1] * 941, geo)
    circulo_seta(im, ax, ay, r, (ax + de[0], ay + de[1]))
    texto(im, linhas, txy[0], txy[1], cores, tam, ang=3)
    hud(im, cam, hora); bandeira(im)
    salvar(im, nome)


# H — sentada no canto escuro do quarto (C4_02)
capa_cctv("C4_02_variacao_1", 0.42, 0.5, 1.35, (0.665, 0.47), 88, (230, 190), ["NÃO OLHE", "PRO CANTO"], [BRANCO, VERM],
          [132, 150], (36, 150), "CAM 03 - QUARTO", "03:02:11", "capa_H_canto.jpg")
capa_cctv("C4_02_variacao_2", 0.5, 0.42, 1.35, (0.76, 0.27), 76, (250, 190), ["ELA VIU", "VOCÊ ENTRAR"], [BRANCO, VERM],
          [132, 140], (36, 150), "CAM 03 - QUARTO", "03:41:56", "capa_H2_canto.jpg", luz=1.2)
# I — parada de costas diante da porta, no corredor (G03)
capa_cctv("G03_variacao_2", 0.38, 0.5, 1.35, (0.47, 0.37), 80, (230, 230), ["NÃO ABRA", "A PORTA"], [BRANCO, VERM],
          [140, 160], (36, 150), "CAM 01 - CORREDOR", "03:17:40", "capa_I_porta.jpg")
capa_cctv("G03_variacao_1", 0.5, 0.45, 1.35, (0.575, 0.36), 80, (220, 230), ["ELA ESTÁ", "ESPERANDO"], [BRANCO, VERM],
          [132, 150], (36, 150), "CAM 01 - CORREDOR", "02:40:18", "capa_I2_espera.jpg", luz=1.4)
