"""Capas dos 3 Shorts do Ep. 09 (1080×1920) — 15/11, no molde do Ep. 08 (hangul a pincel: Nanum Brush). Regra da casa: texto na zona segura (longe do topo, da base
e da coluna de botões à direita) e a frase COMPLETA o título do Short, não repete.
Uso: python3 gerar_capas_shorts.py"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

AQUI = Path(__file__).parent
EP = AQUI.parent
F = Path(__file__).resolve().parents[3] / "painel" / "fontes"
ANTON, PINCEL = str(F / "Anton-400-latin.ttf"), str(F / "NanumBrushScript-Regular.ttf")
W, H = 1080, 1920
VERMELHO = (205, 22, 28)


def cobrir(img, cx, cy, zoom=1.0):
    iw, ih = img.size
    cw = min(iw, ih * W / H) / zoom; ch = cw * H / W
    if ch > ih: ch = ih; cw = ch * W / H
    x0 = min(max(0, cx * iw - cw / 2), iw - cw); y0 = min(max(0, cy * ih - ch / 2), ih - ch)
    return img.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, H), Image.LANCZOS)


def base(img, sat=0.8, luz=0.85, contraste=1.3):
    img = ImageEnhance.Brightness(ImageEnhance.Contrast(ImageEnhance.Color(img).enhance(sat)).enhance(contraste)).enhance(luz)
    a = np.asarray(img).astype(np.float32)
    y = np.linspace(0, 1, H)[:, None, None]
    a *= 1 - 0.75 * np.clip((y - 0.45) / 0.35, 0, 1) ** 1.2      # escurece de 45% para baixo (onde vai o texto)
    a *= 1 - 0.5 * np.clip((0.12 - y) / 0.12, 0, 1)               # e um pouco o topo
    a += np.random.default_rng(3).normal(0, 6, (H, W, 1))
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")


def texto(img, linhas, cores, y, tam):
    d = ImageDraw.Draw(img)
    for l, c in zip(linhas, cores):
        f = ImageFont.truetype(ANTON, tam)
        while d.textlength(l, font=f) > W * 0.78:                 # cabe longe da coluna de botões
            tam -= 4; f = ImageFont.truetype(ANTON, tam)
        w = d.textlength(l, font=f); x = (W - w) / 2 - 30
        sombra = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(sombra).text((x + 6, y + 8), l, font=f, fill=(0, 0, 0, 220))
        img.alpha_composite(sombra.filter(ImageFilter.GaussianBlur(9)))
        d.text((x, y), l, font=f, fill=c, stroke_width=7, stroke_fill=(10, 6, 6))
        y += int(tam * 1.1)


def kanji(img, txt, y, tam):
    f = ImageFont.truetype(PINCEL, tam); cam = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(cam)
    w = d.textlength(txt, font=f)
    d.text(((W - w) / 2 - 30, y), txt, font=f, fill=VERMELHO + (255,), stroke_width=max(2, tam // 40), stroke_fill=VERMELHO + (255,))
    img.alpha_composite(cam.filter(ImageFilter.GaussianBlur(tam / 10))); img.alpha_composite(cam)


def salvar(img, nome):
    img.convert("RGB").save(AQUI / nome, quality=92); print("ok", nome)


# 1 — o Rafa no elevador do hospital: "esse prédio não tem dez andares"
a = base(cobrir(Image.open(EP / "imagens_v4" / "escolhidas" / "H04.jpg").convert("RGB"), 0.66, 0.5, 1.0), sat=0.7, luz=0.95)
kanji(a, "오빠", 900, 290)
texto(a, ["ELE TÁ", "SUBINDO."], [(255, 250, 240), VERMELHO], 1190, 180)
salvar(a, "capa_short1_elevador_rafa.jpg")

# 2 — o Jangsan-beom (sem o carimbo de data da foto: o corte vertical fica na metade esquerda)
b = base(cobrir(Image.open(EP / "imagens_v3" / "M07_A.jpg").convert("RGB"), 0.46, 0.38, 1.25), sat=0.7, luz=1.0)
kanji(b, "장산범", 900, 270)
texto(b, ["ELE IMITA", "A SUA MÃE."], [(255, 250, 240), VERMELHO], 1190, 170)
salvar(b, "capa_short2_jangsan_beom.jpg")

# 3 — o botão do quinto andar aceso
c = base(cobrir(Image.open(EP / "imagens_v4" / "extras" / "H05_B.jpg").convert("RGB"), 0.43, 0.45, 1.0), sat=0.8, luz=1.0)
kanji(c, "오층", 900, 290)
texto(c, ["NÃO OLHE", "PRA ELA."], [(255, 250, 240), VERMELHO], 1190, 180)
salvar(c, "capa_short3_jogo_do_elevador.jpg")
