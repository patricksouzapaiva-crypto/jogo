"""Capas do Ep. 08 (13/11) — pedido do usuário: "bem feita, nada a ver com a história da Dani; ligada ao tema das
lendas japonesas e ao título" ("Por que o terror japonês é o mais pesado do mundo").
Usa só gravuras reais em domínio público (créditos em imagens_reais/CREDITOS.txt). A frase COMPLETA o título, não
repete. Canto inferior direito livre (é onde o YouTube põe a duração).
Uso: python3 gerar_capas.py  → capa_A_esqueleto.jpg, capa_B_olhar.jpg, capa_C_poco.jpg (1280×720)"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

AQUI = Path(__file__).parent
R = AQUI.parent / "imagens_reais"
F = Path(__file__).resolve().parents[3] / "painel" / "fontes"
ANTON, PINCEL = str(F / "Anton-400-latin.ttf"), str(F / "YujiSyuku-400.ttf")
W, H = 1280, 720
VERMELHO = (205, 22, 28)


def cobrir(img, cx, cy, zoom):
    """Recorta 16:9 centrado em (cx, cy) (frações) com zoom (1 = maior recorte possível)."""
    iw, ih = img.size
    cw = min(iw, ih * W / H) / zoom; ch = cw * H / W
    x0 = min(max(0, cx * iw - cw / 2), iw - cw); y0 = min(max(0, cy * ih - ch / 2), ih - ch)
    return img.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, H), Image.LANCZOS)


def a_direita(img, caixa, x_dest=430):
    """Recorta a caixa (frações x0,y0,x1,y1), escala para 720 de altura e encosta à direita; o lado esquerdo vira
    preto (o degradê de escurecer() funde a borda). Para gravuras em pé (rosto grande, texto do lado)."""
    iw, ih = img.size; x0, y0, x1, y1 = caixa
    r = img.crop((int(x0 * iw), int(y0 * ih), int(x1 * iw), int(y1 * ih)))
    r = r.resize((int(r.width * H / r.height), H), Image.LANCZOS)
    x = W - r.width                                      # sempre encostada na borda direita
    m = np.ones((H, r.width), np.float32); f = min(220, r.width // 3)
    m[:, :f] = np.linspace(0, 1, f)[None, :] ** 1.5        # borda esquerda some no preto (sem emenda reta)
    tela = Image.new("RGB", (W, H), (8, 6, 6))
    tela.paste(r, (x, 0), Image.fromarray((m * 255).astype(np.uint8)))
    return tela


def tratar(img, sat=0.75, luz=0.9, contraste=1.25):
    img = ImageEnhance.Color(img).enhance(sat)
    img = ImageEnhance.Contrast(img).enhance(contraste)
    return ImageEnhance.Brightness(img).enhance(luz)


def escurecer(img, lado="esq", forca=0.92, ate=0.62):
    """Degradê preto de um lado (onde vai o texto) + vinheta leve."""
    a = np.asarray(img).astype(np.float32)
    x = np.linspace(0, 1, W)[None, :, None]
    g = np.clip(1 - x / ate, 0, 1) if lado == "esq" else np.clip((x - (1 - ate)) / ate, 0, 1)
    a *= 1 - forca * g ** 1.3
    yy, xx = np.mgrid[0:H, 0:W]
    v = 1 - 0.35 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / 2
    a *= v[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def grao(img, q=7):
    rng = np.random.default_rng(8)
    a = np.asarray(img).astype(np.float32) + rng.normal(0, q, (H, W, 1))
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def kanji(base, txt, x, y, tam, cor=VERMELHO, brilho=True):
    f = ImageFont.truetype(PINCEL, tam)
    cam = Image.new("RGBA", base.size, (0, 0, 0, 0)); d = ImageDraw.Draw(cam)
    d.text((x, y), txt, font=f, fill=cor + (255,))
    if brilho:
        g = cam.filter(ImageFilter.GaussianBlur(tam / 9))
        base.alpha_composite(Image.eval(g, lambda v: int(v * 0.85)))
    base.alpha_composite(cam)


def texto(base, linhas, x, y, cores, tam, contorno=6):
    """Linhas em Anton, cada uma com sua cor; sombra + contorno escuros para ler em qualquer fundo."""
    d = ImageDraw.Draw(base)
    for k, (l, c) in enumerate(zip(linhas, cores)):
        f = ImageFont.truetype(ANTON, tam[k] if isinstance(tam, list) else tam)
        sombra = Image.new("RGBA", base.size, (0, 0, 0, 0))
        ImageDraw.Draw(sombra).text((x + 6, y + 8), l, font=f, fill=(0, 0, 0, 200))
        base.alpha_composite(sombra.filter(ImageFilter.GaussianBlur(8)))
        d.text((x, y), l, font=f, fill=c, stroke_width=contorno, stroke_fill=(10, 6, 6))
        y += int(f.size * 1.08)
    return y


def selo(base, x, y):
    """Faixinha 'LENDAS REAIS DO JAPÃO' (contexto rápido: é documentário)."""
    f = ImageFont.truetype(ANTON, 30); d = ImageDraw.Draw(base)
    t = "LENDAS REAIS DO JAPÃO"; w = d.textlength(t, font=f)
    d.rectangle((x, y, x + w + 28, y + 46), fill=VERMELHO)
    d.text((x + 14, y + 4), t, font=f, fill=(255, 245, 235))


def salvar(img, nome):
    img.convert("RGB").save(AQUI / nome, quality=93); print("ok", nome)


# A — O esqueleto gigante (Kuniyoshi, c. 1844): a imagem mais forte das lendas; texto à esquerda.
a = Image.open(R / "R04_esqueleto_kuniyoshi.jpg").convert("RGB")
a = cobrir(a, 0.415, 0.353, 1.795)
a = escurecer(tratar(a, sat=0.7, luz=0.95, contraste=1.3), "esq", 0.93, 0.6)
a = grao(a).convert("RGBA")
kanji(a, "呪", 40, 20, 300)
y = texto(a, ["NÃO TEM REZA", "QUE DESFAZ."], 48, 365, [(255, 250, 240), VERMELHO], [118, 118])
selo(a, 52, 640)
salvar(a, "capa_A_esqueleto.jpg")

# B — O olhar da lanterna (Hokusai, Oiwa, c. 1831): os olhos encaram quem vê a capa; texto à esquerda.
b = Image.open(R / "R01_oiwa_lanterna_hokusai.jpg").convert("RGB")
b = a_direita(b, (0.06, 0.22, 0.965, 0.80), 420)
b = escurecer(tratar(b, sat=0.65, luz=0.92, contraste=1.35), "esq", 0.95, 0.55)
b = grao(b).convert("RGBA")
texto(b, ["VOCÊ SÓ", "PRECISA", "OLHAR."], 48, 70, [(255, 250, 240), (255, 250, 240), VERMELHO], [120, 120, 170])
selo(b, 52, 640)
salvar(b, "capa_B_olhar.jpg")

# C — O poço (Hokusai, Okiku, c. 1831): a mãe de todos os fantasmas de poço (Sadako); texto à esquerda.
c = Image.open(R / "R03_okiku_poco_hokusai.jpg").convert("RGB")
c = a_direita(c, (0.25, 0.12, 0.965, 0.62), 380)
c = escurecer(tratar(c, sat=0.6, luz=0.9, contraste=1.3), "esq", 0.93, 0.58)
c = grao(c).convert("RGBA")
kanji(c, "怨", 40, 20, 280)
texto(c, ["NÃO TEM REZA", "QUE DESFAZ."], 48, 365, [(255, 250, 240), VERMELHO], [118, 118])
selo(c, 52, 640)
salvar(c, "capa_C_poco.jpg")

# ---- 13/11 (2ª rodada, "mais sinistras") ----
# D — Kasane com a foice (pintura do séc. XIX): o fantasma mais repulsivo das lendas; corpo inteiro à direita.
d = Image.open(R / "R20_kasane_kinugawa.jpg").convert("RGB")
d = a_direita(d, (0.0, 0.08, 1.0, 0.72))
d = escurecer(tratar(d, sat=0.85, luz=0.95, contraste=1.35), "esq", 0.95, 0.5)
d = grao(d).convert("RGBA")
kanji(d, "怨", 40, 20, 280)
texto(d, ["NÃO TEM REZA", "QUE DESFAZ."], 48, 365, [(255, 250, 240), VERMELHO], [118, 118])
selo(d, 52, 640)
salvar(d, "capa_D_kasane.jpg")

# E — Kasane, só o rosto (olhos vermelhos) bem grande: o olhar que dá nome à frase.
e = Image.open(R / "R20_kasane_kinugawa.jpg").convert("RGB")
e = a_direita(e, (0.18, 0.12, 0.78, 0.42))
e = escurecer(tratar(e, sat=0.9, luz=0.95, contraste=1.4), "esq", 0.95, 0.5)
e = grao(e).convert("RGBA")
texto(e, ["VOCÊ SÓ", "PRECISA", "OLHAR."], 48, 70, [(255, 250, 240), (255, 250, 240), VERMELHO], [120, 120, 170])
selo(e, 52, 640)
salvar(e, "capa_E_kasane_rosto.jpg")

# F — Máscara Hannya (Nō, séc. XVIII, Met Museum): o demônio do ciúme, encarando de frente.
f = Image.open(R / "R21_hannya_mascara_met.jpg").convert("RGB")
f = a_direita(f, (0.08, 0.06, 0.92, 0.94))
f = escurecer(tratar(f, sat=0.95, luz=0.9, contraste=1.35), "esq", 0.95, 0.5)
f = grao(f).convert("RGBA")
kanji(f, "鬼", 40, 20, 280)
texto(f, ["NÃO TEM REZA", "QUE DESFAZ."], 48, 365, [(255, 250, 240), VERMELHO], [118, 118])
selo(f, 52, 640)
salvar(f, "capa_F_hannya.jpg")
