"""Capas do Ep. 12 (25/11) no estilo da capa do Ep. 08 (a que o usuário mandou como referência): fundo preto à esquerda
com o KANJI vermelho de pincel, o texto enorme (branco em cima, vermelho embaixo) e o selo "LENDAS REAIS DO JAPÃO";
a imagem do episódio à direita, fundindo no preto. Nenhum rosto humano.
Uso: python3 gerar_capas.py → capa_*.jpg (1280×720)   e   capa_short*.jpg (1080×1920)"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

AQUI = Path(__file__).parent; EP = AQUI.parent
F = EP.parents[1] / "painel" / "fontes"
ANTON, PINCEL = str(F / "Anton-400-latin.ttf"), str(F / "YujiSyuku-400.ttf")
VERM, BRANCO = (226, 22, 30), (250, 246, 238)


def abrir(arq, W, H, cx, cy, zoom):
    img = Image.open(arq).convert("RGB"); iw, ih = img.size
    if iw / ih > W / H:
        ch = ih / zoom; cw = ch * W / H
    else:
        cw = iw / zoom; ch = cw * H / W
    x0 = min(max(0, cx * iw - cw / 2), iw - cw); y0 = min(max(0, cy * ih - ch / 2), ih - ch)
    return img.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, H), Image.LANCZOS)


def fundir_preto(img, de=0.30, ate=0.62, vertical=False):
    """Escurece o lado do texto (esquerda; no Short, a metade de baixo) até o preto."""
    a = np.asarray(img).astype(np.float32); H, W = a.shape[:2]
    if vertical:
        t = np.linspace(0, 1, H)[:, None, None]; g = np.clip((t - de) / (ate - de), 0, 1)
    else:
        t = np.linspace(0, 1, W)[None, :, None]; g = 1 - np.clip((t - de) / (ate - de), 0, 1)
    a = a * (1 - 0.96 * g ** 1.2)
    a = np.clip((a / 255 - 0.04) / 0.96, 0, 1) ** 1.08 * 255          # pretos esmagados
    return Image.fromarray(a.astype(np.uint8))


def kanji(base, k, x, y, tam):
    cam = Image.new("RGBA", base.size, (0, 0, 0, 0)); d = ImageDraw.Draw(cam)
    d.text((x, y), k, font=ImageFont.truetype(PINCEL, tam), fill=VERM + (255,))
    gl = cam.filter(ImageFilter.GaussianBlur(22))
    base.alpha_composite(gl); base.alpha_composite(cam)


def texto(base, linhas, x, y, cores, tam):
    cam = Image.new("RGBA", base.size, (0, 0, 0, 0)); d = ImageDraw.Draw(cam); yy = y
    for l, c, t in zip(linhas, cores, tam):
        d.text((x, yy), l, font=ImageFont.truetype(ANTON, t), fill=c + (255,), stroke_width=5, stroke_fill=(6, 3, 3, 255))
        yy += int(t * 1.16)
    sombra = Image.new("RGBA", base.size, (0, 0, 0, 0)); sombra.paste((0, 0, 0, 220), mask=cam.split()[3])
    base.alpha_composite(sombra.filter(ImageFilter.GaussianBlur(9)).transform(base.size, Image.AFFINE, (1, 0, -6, 0, 1, -8)))
    base.alpha_composite(cam)
    return yy


def selo(base, x, y, t="LENDAS REAIS DO JAPÃO", tam=30):
    f = ImageFont.truetype(ANTON, tam); d = ImageDraw.Draw(base); w = d.textlength(t, font=f)
    d.rectangle((x, y, x + w + 24, y + tam * 1.45), fill=VERM); d.text((x + 12, y + tam * 0.12), t, font=f, fill=BRANCO)


def capa(arq, cx, cy, zoom, k, linhas, cores, tam, nome, luz=1.0):
    W, H = 1280, 720
    img = ImageEnhance.Brightness(abrir(arq, W, H, cx, cy, zoom)).enhance(luz)
    im = fundir_preto(img).convert("RGBA")
    kanji(im, k, 44, 18, 230)
    fim = texto(im, linhas, 44, 300, cores, tam)
    selo(im, 50, fim + 22)
    im.convert("RGB").save(AQUI / nome, quality=93); print("ok", nome)


def capa_short(arq, cx, cy, zoom, k, linhas, cores, tam, nome, luz=1.0):
    W, H = 1080, 1920
    img = ImageEnhance.Brightness(abrir(arq, W, H, cx, cy, zoom)).enhance(luz)
    im = fundir_preto(img, 0.42, 0.66, vertical=True).convert("RGBA")
    kanji(im, k, 70, 1010, 200)
    fim = texto(im, linhas, 70, 1250, cores, tam)       # zona segura: longe da base e dos botões da direita
    selo(im, 76, fim + 26, tam=36)
    im.convert("RGB").save(AQUI / nome, quality=93); print("ok", nome)


I = EP / "imagens"; R = EP / "reais"
# A — a pessoa do ritual de costas, a coroa de velas (a história). 呪 = maldição
capa(I / "H12_coroa_velas_costas.jpg", 0.62, 0.35, 1.05, "呪", ["NÃO SEJA", "VISTO."], [BRANCO, VERM], [150, 160], "capa_A_visto.jpg")
# B — o boneco de palha pregado (o caso real de Matsudo). 釘 = prego
capa(I / "G02_boneco_prego_tronco.jpg", 0.40, 0.45, 1.1, "釘", ["O PREGO", "É PRA VOCÊ."], [BRANCO, VERM], [140, 140], "capa_B_prego.jpg")
# C — a máscara Hannya (a mulher que virou demônio). 鬼 = oni
capa(R / "hannya_preto.jpg", 0.5, 0.45, 1.0, "鬼", ["ELES NÃO QUEREM", "SUA ALMA."], [BRANCO, VERM], [104, 150], "capa_C_alma.jpg")
# D — a lanterna no rosto de quem pregava. 見 = ver
capa(I / "H11_lanterna_feixe.jpg", 0.6, 0.4, 1.1, "見", ["VOCÊ VIU.", "AGORA É VOCÊ."], [BRANCO, VERM], [140, 120], "capa_D_viu.jpg")

# Shorts
capa_short(I / "G03_camera_santuario.jpg", 0.65, 0.5, 1.0, "釘", ["ELE PREGOU", "ÀS 2 DA", "MANHÃ."], [BRANCO, BRANCO, VERM], [150, 150, 170], "capa_short1_matsudo.jpg")
capa_short(I / "N08_mulher_mar_bebe.jpg", 0.3, 0.5, 1.0, "牛鬼", ["NÃO SEGURE", "O BEBÊ."], [BRANCO, VERM], [150, 170], "capa_short2_praia.jpg")
capa_short(R / "pedra_rachada.jpg", 0.5, 0.5, 1.0, "殺生石", ["A PEDRA", "QUE MATA", "RACHOU."], [BRANCO, BRANCO, VERM], [150, 150, 170], "capa_short3_pedra.jpg")
