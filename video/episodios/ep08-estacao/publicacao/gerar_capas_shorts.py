"""Capas dos 3 Shorts do Ep. 08 (1080×1920) — 13/11. Regra da casa: texto na zona segura (longe do topo, da base
e da coluna de botões à direita) e a frase COMPLETA o título do Short, não repete.
Uso: python3 gerar_capas_shorts.py"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

AQUI = Path(__file__).parent
EP = AQUI.parent
F = Path(__file__).resolve().parents[3] / "painel" / "fontes"
ANTON, PINCEL = str(F / "Anton-400-latin.ttf"), str(F / "YujiSyuku-400.ttf")
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
    w = d.textlength(txt, font=f); d.text(((W - w) / 2 - 30, y), txt, font=f, fill=VERMELHO + (255,))
    img.alpha_composite(cam.filter(ImageFilter.GaussianBlur(tam / 10))); img.alpha_composite(cam)


def salvar(img, nome):
    img.convert("RGB").save(AQUI / nome, quality=92); print("ok", nome)


# 1 — a placa de Kisaragi (a imagem do próprio Short)
a = base(cobrir(Image.open(EP / "imagens" / "D03_placa_kisaragi.jpg").convert("RGB"), 0.8, 0.45, 1.0), sat=0.7, luz=0.9)
kanji(a, "きさらぎ", 1020, 150)
texto(a, ["NÃO ESTÁ", "NO MAPA."], [(255, 250, 240), VERMELHO], 1190, 170)
salvar(a, "capa_short1_kisaragi.jpg")

# 2 — Okiku saindo do poço (Hokusai): de onde a Sadako veio
b = base(cobrir(Image.open(EP / "imagens_reais" / "R03_okiku_poco_hokusai.jpg").convert("RGB"), 0.6, 0.42, 1.25), sat=0.7, luz=0.9)
kanji(b, "井戸", 1020, 150)
texto(b, ["ELA VEIO", "DO POÇO."], [(255, 250, 240), VERMELHO], 1190, 170)
salvar(b, "capa_short2_sadako.jpg")

# 3 — a mulher da boca rasgada no livro de 1801 (Ehon Sayoshigure)
c = base(cobrir(Image.open(EP / "imagens_reais" / "R19_kuchisake_ehon_sayoshigure.jpg").convert("RGB"), 0.45, 0.4, 1.0), sat=0.6, luz=0.8, contraste=1.4)
kanji(c, "口裂け女", 1020, 140)
texto(c, ["EU SOU", "BONITA?"], [(255, 250, 240), VERMELHO], 1190, 180)
salvar(c, "capa_short3_eu_sou_bonita.jpg")
