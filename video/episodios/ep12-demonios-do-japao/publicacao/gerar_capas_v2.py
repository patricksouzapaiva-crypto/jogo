"""Capas v2 do Ep. 12 (25/11), em 1920×1080 (alta qualidade).
Pedido do usuário: "crie as capas… quero com alta qualidade, pesquise vídeos virais do tema pra aprender, uma das capas
quero uma das ilustrações reais melhoradas, a mais sinistra".
O que as capas que viralizaram no tema (folclore japonês, 2026) têm em comum (vidIQ outliers):
  - UM rosto de criatura grande, ocupando metade ou mais da capa, olhando para a câmera;
  - fundo escuro, alto contraste, brilho vermelho;
  - 2 a 4 palavras, enormes (ex.: "JAPÃO É BIZARRO", 13× o normal do canal);
  - ukiyo-e colorido funciona (Beauties & Beasts: 200 mil views por vídeo).
Mantém a identidade da capa do Ep. 08: kanji vermelho de pincel + texto branco/vermelho + selo "LENDAS REAIS DO JAPÃO".
A: a Warai Hannya de Hokusai (1831), RESTAURADA (Real-ESRGAN ×4 + cor) — a ilustração real mais sinistra do episódio.
Uso: python3 gerar_capas_v2.py  (a restauração da Hokusai fica em fontes_capas/, ignorada no git)"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

AQUI = Path(__file__).parent; EP = AQUI.parent
F = EP.parents[1] / "painel" / "fontes"
ANTON, PINCEL = str(F / "Anton-400-latin.ttf"), str(F / "YujiSyuku-400.ttf")
W, H = 1920, 1080
VERM, BRANCO = (232, 18, 26), (252, 248, 240)


def cobrir(img, w, h, cx, cy, zoom=1.0):
    iw, ih = img.size; esc = max(w / iw, h / ih) * zoom
    img = img.resize((int(iw * esc), int(ih * esc)), Image.LANCZOS)
    x0 = int(min(max(0, cx * img.width - w / 2), img.width - w)); y0 = int(min(max(0, cy * img.height - h / 2), img.height - h))
    return img.crop((x0, y0, x0 + w, y0 + h))


def montar(img, de=0.30, ate=0.55, contraste=1.15, cor=1.1, brilho=1.0):
    img = ImageEnhance.Contrast(ImageEnhance.Color(ImageEnhance.Brightness(img).enhance(brilho)).enhance(cor)).enhance(contraste)
    a = np.asarray(img).astype(np.float32)
    x = np.linspace(0, 1, W)[None, :, None]; g = 1 - np.clip((x - de) / (ate - de), 0, 1)
    a = a * (1 - 0.97 * g ** 1.3)                                     # o lado do texto vai ao preto
    yy, xx = np.mgrid[0:H, 0:W]
    v = 1 - 0.45 * np.clip(((xx - W * 0.7) / (W * 0.55)) ** 2 + ((yy - H * 0.5) / (H * 0.75)) ** 2 - 0.35, 0, 1)
    a = a * v[..., None]                                              # vinheta: o rosto acende no meio
    a = np.clip((a / 255 - 0.03) / 0.97, 0, 1) ** 1.05 * 255          # pretos esmagados
    return Image.fromarray(a.astype(np.uint8)).convert("RGBA")


def brilho_vermelho(base, cx, cy, r, forca=0.35):
    a = np.asarray(base).astype(np.float32); yy, xx = np.mgrid[0:H, 0:W]
    g = np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * r * r)))[..., None]
    a[..., :3] = a[..., :3] + g * forca * np.array([255, 10, 20])
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def kanji(base, k, x, y, tam):
    cam = Image.new("RGBA", base.size, (0, 0, 0, 0)); d = ImageDraw.Draw(cam)
    d.text((x, y), k, font=ImageFont.truetype(PINCEL, tam), fill=VERM + (255,))
    base.alpha_composite(cam.filter(ImageFilter.GaussianBlur(30))); base.alpha_composite(cam)


def texto(base, linhas, x, y, cores, tam, passo=1.12):
    cam = Image.new("RGBA", base.size, (0, 0, 0, 0)); d = ImageDraw.Draw(cam); yy = y
    for l, c, t in zip(linhas, cores, tam):
        d.text((x, yy), l, font=ImageFont.truetype(ANTON, t), fill=c + (255,), stroke_width=8, stroke_fill=(5, 2, 2, 255))
        yy += int(t * passo)
    a = np.asarray(cam).astype(np.float32)
    gl = np.zeros_like(a); verm = (a[..., 0] > 150) & (a[..., 1] < 90); gl[verm] = [255, 20, 20, 255]
    gl = Image.fromarray(gl.astype(np.uint8)).filter(ImageFilter.GaussianBlur(24))
    sombra = Image.new("RGBA", base.size, (0, 0, 0, 0)); sombra.paste((0, 0, 0, 235), mask=cam.split()[3])
    base.alpha_composite(sombra.filter(ImageFilter.GaussianBlur(14)).transform(base.size, Image.AFFINE, (1, 0, -10, 0, 1, -12)))
    base.alpha_composite(gl); base.alpha_composite(cam)
    return yy


def selo(base, x, y, t="LENDAS REAIS DO JAPÃO", tam=44):
    f = ImageFont.truetype(ANTON, tam); d = ImageDraw.Draw(base); w = d.textlength(t, font=f)
    d.rectangle((x, y, x + w + 36, y + tam * 1.45), fill=VERM); d.text((x + 18, y + tam * 0.12), t, font=f, fill=BRANCO)


def capa(img, k, linhas, cores, tam, nome, glow=None, **kw):
    base = montar(img, **kw)
    if glow: base = brilho_vermelho(base, *glow).convert("RGBA")
    kanji(base, k, 70, 40, 300)
    fim = texto(base, linhas, 72, 420, cores, tam)
    selo(base, 80, fim + 26)
    rgb = base.convert("RGB")
    rgb.save(AQUI / f"{nome}.jpg", quality=92, optimize=True, subsampling=0)
    print("ok", nome, round((AQUI / f"{nome}.jpg").stat().st_size / 1e6, 2), "MB")


def rosto(arq, fx, fy, fh, alvo_h=640, cx=1380, cy=545):
    """27/11 (usuário: "centralizando melhor o rosto dos monstros pra ficar bem focado"): o ROSTO (centro fx, fy e
    altura fh, em fração da imagem) vai para o centro do lado direito (cx, cy), sempre com alvo_h px de altura. Onde a
    imagem não cobre, fica preto; as bordas dela se esfumam (nada de corte reto)."""
    img = Image.open(arq).convert("RGB"); iw, ih = img.size
    esc = alvo_h / (fh * ih); img = img.resize((max(1, int(iw * esc)), max(1, int(ih * esc))), Image.LANCZOS)
    x0, y0 = int(cx - fx * img.width), int(cy - fy * img.height)
    tela = Image.new("RGB", (W, H)); cob = Image.new("L", (W, H), 0)
    tela.paste(img, (x0, y0)); cob.paste(255, (x0, y0, x0 + img.width, y0 + img.height))
    cob = cob.filter(ImageFilter.GaussianBlur(40))
    x = np.linspace(0, 1, W); rampa = np.clip((x - 0.30) / 0.22, 0, 1) ** 1.4          # o lado do texto vai ao preto
    al = np.asarray(cob).astype(np.float32) / 255 * rampa[None, :]
    return Image.fromarray((np.asarray(tela).astype(np.float32) * al[..., None]).astype(np.uint8))


I = EP / "imagens"; R = EP / "reais"
# A — a Warai Hannya de Hokusai, RESTAURADA (a mais sinistra): o rosto rindo no centro, a cabeça da criança acima
capa(rosto(AQUI / "fontes_capas" / "hannya_hokusai_rest.jpg", 0.56, 0.52, 0.48, alvo_h=700), "鬼", ["ELES QUEREM", "OUTRA COISA."],
     [BRANCO, VERM], [150, 170], "capa_A_hokusai", de=0.30, ate=0.50, contraste=1.12, cor=1.15)
# B — a máscara Hannya: o rosto inteiro (sem cortar a boca), os chifres saindo pelo alto
capa(rosto(R / "hannya_preto.jpg", 0.52, 0.55, 0.60, alvo_h=860, cy=575), "鬼", ["NINGUÉM NASCE", "DEMÔNIO."], [BRANCO, VERM],
     [140, 190], "capa_B_hannya", glow=(1380, 575, 480, 0.20), de=0.30, ate=0.50)
# C — a pessoa do ritual de costas: a cabeça e a coroa de velas no centro
capa(rosto(I / "H12_coroa_velas_costas.jpg", 0.53, 0.38, 0.55, alvo_h=640, cy=500), "呪", ["NÃO SEJA", "VISTO."], [BRANCO, VERM],
     [190, 230], "capa_C_ritual", de=0.30, ate=0.50, brilho=1.08)
# D — o ushi-oni: o rosto (olhos e boca vermelha) no centro, os chifres e as patas em volta
capa(rosto(R / "ushioni_rolo.jpg", 0.555, 0.80, 0.30, alvo_h=620, cy=680), "牛鬼", ["ESSE NÃO", "TEM REGRA."], [BRANCO, VERM],
     [170, 190], "capa_D_ushioni", de=0.30, ate=0.50, contraste=1.2)
