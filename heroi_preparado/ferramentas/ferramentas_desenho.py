"""Desenho das ferramentas de trabalho no tamanho do desenho do heroi (9x maior que o jogo).

Cada ferramenta e desenhada "em pe": o ponto onde a mao segura fica em PEGA, o cabo desce
(para baixo da imagem) e a cabeca da ferramenta fica na ponta de baixo. Para usar, gira-se a
imagem em volta da PEGA (anim_lado.coloca), do mesmo jeito que o braco.
As cores seguem o estilo do jogo: madeira quente, metal azulado claro e contorno escuro colorido
(o contorno e refeito com espessura uniforme por anim_lado.contorna).
"""
import numpy as np
from PIL import Image, ImageDraw

LARG, ALT = 220, 380
PEGA = (110, 40)                     # onde a mao segura (perto da ponta de tras do cabo)

MADEIRA = (156, 98, 52); MADEIRA_CLARA = (196, 134, 72); MADEIRA_ESC = (112, 66, 34)
METAL = (150, 164, 176); METAL_CLARO = (214, 224, 230); METAL_ESC = (92, 100, 116)
LATA = (96, 150, 190); LATA_CLARA = (150, 196, 224); LATA_ESC = (60, 102, 140)


def _cabo(d, x, y0, y1, larg=34):
    d.rectangle((x - larg // 2, y0, x + larg // 2, y1), fill=MADEIRA)
    d.rectangle((x - larg // 2 + 7, y0, x - larg // 2 + 15, y1), fill=MADEIRA_CLARA)   # luz (o contorno come 7 px de cada lado)
    d.rectangle((x + larg // 2 - 14, y0, x + larg // 2 - 7, y1), fill=MADEIRA_ESC)


def enxada():
    """Cabo comprido e lamina de metal perpendicular na ponta (virada para -x)."""
    im = Image.new("RGBA", (LARG, ALT), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = PEGA[0]
    _cabo(d, x, PEGA[1] - 30, 300)
    # bocal de metal que prende a lamina
    d.rectangle((x - 24, 284, x + 24, 322), fill=METAL_ESC)
    d.rectangle((x - 17, 291, x - 6, 315), fill=METAL)
    # lamina: sai para a esquerda (-x) e termina num fio reto
    d.polygon([(x - 16, 292), (x - 104, 296), (x - 112, 352), (x - 16, 334)], fill=METAL)
    d.polygon([(x - 16, 292), (x - 104, 296), (x - 103, 310), (x - 16, 306)], fill=METAL_CLARO)
    d.polygon([(x - 112, 340), (x - 112, 352), (x - 16, 334), (x - 16, 324)], fill=METAL_ESC)
    return np.array(im).astype(np.int32)


FERRAMENTAS = {"enxada_simples": enxada}      # primeira enxada (teste); as do jogo sao as artesanais abaixo


if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import anim_lado as L
    t = enxada()
    L.contorna(t)
    im = Image.fromarray(t.clip(0, 255).astype(np.uint8))
    bg = Image.new("RGBA", im.size, (96, 140, 70, 255)); bg.alpha_composite(im)
    bg.save(sys.argv[1] if len(sys.argv) > 1 else "enxada.png")


# ---------------------------------------------------------------------------------------------
# Ferramentas desenhadas no ChatGPT. Cada uma tem o fundo magenta tirado, e girada para a mesma
# posicao da enxada de teste (pega em cima, cabo descendo, cabeca embaixo, lado de corte para -x) e
# reduzida para a escala do desenho do heroi (9x o tamanho do jogo). A pegada e calculada pelo
# proprio desenho (eixo do cabo + fracao do comprimento a partir da ponta do cabo).
#
# ARTESANAIS (fonte/ferramentas_artesanais/0*.png, 1 por imagem): as 7 aprovadas, usadas no jogo.
# V1 (fonte/ferramentas/tools_source.png, 6 celulas): primeiro pacote, mantido so como referencia.
# ---------------------------------------------------------------------------------------------
import os as _os
import math as _math

_FONTE = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "fonte")
# alvo = comprimento no jogo (px, da ponta do cabo ate a ponta mais longe; no regador, a largura)
ARTESANAIS = {
    "enxada":   dict(arquivo="01_enxada.png", alvo=38, pega_frac=0.16, cabeca="metal"),
    "machado":  dict(arquivo="02_machado.png", alvo=34, pega_frac=0.15, cabeca="metal"),
    "picareta": dict(arquivo="03_picareta.png", alvo=35, pega_frac=0.15, cabeca="metal"),
    "pa":       dict(arquivo="04_pa.png", alvo=38, pega_frac=0.08, cabeca="metal"),
    "foice":    dict(arquivo="05_foice_mao.png", alvo=19, pega_frac=0.30, cabeca="metal"),
    "regador":  dict(arquivo="06_regador_cobre.png", alvo=24, cabeca="pendurado"),
    "vara":     dict(arquivo="07_vara_pescar.png", alvo=48, pega_frac=0.17, cabeca="ponta"),
}
V1 = {
    "pa_v1":       dict(celula=(0, 0), alvo=34, pega_frac=0.10, cabeca="metal"),
    "foice_v1":    dict(celula=(512, 0), alvo=17, pega=(368, 352), cabeca="metal"),
    "regador_v1":  dict(celula=(1024, 0), alvo=21, pega=(298, 150), cabeca="pendurado", bico_esquerda=True),
    "machado_v1":  dict(celula=(0, 512), alvo=30, pega_frac=0.14, cabeca="metal"),
    "picareta_v1": dict(celula=(512, 512), alvo=31, pega_frac=0.14, cabeca="metal"),
    "vara_v1":     dict(celula=(1024, 512), alvo=44, pega_frac=0.20, cabeca="ponta", sem_linha=True),
}
_CACHE = {}
_PEGA = {}


def _sem_fundo(rgb):
    import fundo_magenta as _fm
    out, fg, puro, _ = _fm.remove_fundo(rgb.astype(np.uint8))
    rgba = np.zeros(rgb.shape[:2] + (4,), np.int32)
    rgba[..., :3] = out; rgba[..., 3] = np.where(fg, 255, 0)
    return rgba


def original(nome):
    """Imagem da ferramenta sem o fundo (antes de girar e reduzir)."""
    from PIL import Image as _I
    if nome in ARTESANAIS:
        cam = _os.path.join(_FONTE, "ferramentas_artesanais", ARTESANAIS[nome]["arquivo"])
        return _sem_fundo(np.array(_I.open(cam).convert("RGB")).astype(np.int32))
    cx, cy = V1[nome]["celula"]
    if "v1" not in _CACHE:
        _CACHE["v1"] = np.array(_I.open(_os.path.join(_FONTE, "ferramentas", "tools_source.png")).convert("RGB")).astype(np.int32)
    return _sem_fundo(_CACHE["v1"][cy:cy + 512, cx:cx + 512])


def _maior_pedaco(m):
    from scipy import ndimage as _ndi
    lab, n = _ndi.label(m)
    if n <= 1:
        return m
    tam = _ndi.sum(np.ones_like(lab), lab, index=range(1, n + 1))
    return lab == (1 + int(np.argmax(tam)))


def _eh_metal(t):
    r, g, b = t[..., 0], t[..., 1], t[..., 2]
    return (t[..., 3] > 0) & (np.abs(r - g) < 30) & (b >= r - 12) & (np.abs(g - b) < 45) & (r > 70)


CONTORNO_JOGO = (36, 20, 14)          # contorno de 1 px em volta da ferramenta, no tamanho do jogo
_PALETA = {}


def _tira_contorno(t, larg=16, limite=200):
    """Troca o contorno escuro do desenho pela cor de dentro (o contorno e refeito no tamanho do
    jogo, com 1 pixel firme). Detalhes escuros de dentro (couro, sombras) ficam."""
    from scipy import ndimage as _ndi
    m = t[..., 3] > 0
    faixa = m & ~_ndi.binary_erosion(m, iterations=larg)
    ruim = faixa & (t[..., :3].sum(2) < limite)
    bom = m & ~ruim
    if not bom.any():
        return t
    _, (iy, ix) = _ndi.distance_transform_edt(~bom, return_indices=True)
    o = t.copy()
    o[ruim] = t[iy[ruim], ix[ruim]]
    return o


def _paleta_propria(t, cores=12):
    """Cores da propria ferramenta (sem contorno), para ela nao se misturar com as cores do heroi."""
    from PIL import Image as _I
    px = t[t[..., 3] > 0][:, :3]
    if len(px) > 200000:
        px = px[np.random.default_rng(1).choice(len(px), 200000, replace=False)]
    amostra = _I.fromarray(px.reshape(-1, 1, 3).astype(np.uint8), "RGB")
    q = amostra.quantize(colors=cores, method=_I.Quantize.MEDIANCUT, dither=_I.Dither.NONE)
    return np.array(q.getpalette()[:3 * cores]).reshape(-1, 3)


def paleta_de(nome):
    return _PALETA.get(nome)


def prepara(nome):
    """Ferramenta pronta para o esqueleto: (imagem RGBA, ponto da pega)."""
    from PIL import Image as _I
    import anim_lado as _L
    cfg = ARTESANAIS.get(nome) or V1[nome]
    t = original(nome)
    r, g, b = t[..., 0], t[..., 1], t[..., 2]
    al = t[..., 3] > 0
    if cfg.get("sem_linha"):                       # tira a linha e o anzol desenhados (a linha sera um efeito)
        al &= ~((r > 170) & (g > 150) & (b < 170) & (np.abs(r - g) < 70))
    al = _maior_pedaco(al); t[~al] = 0
    if nome in ARTESANAIS:
        t = _tira_contorno(t)
        _PALETA[nome] = _paleta_propria(t)
    ys, xs = np.nonzero(al)
    pts = np.stack([xs, ys], -1).astype(float)
    madeira = al & (r > 140) & (g > 55) & (b < 120) & (r - b > 70) & (r > g)
    wy, wx = np.nonzero(madeira if madeira.sum() > 500 else al)
    centro = np.array([wx.mean(), wy.mean()])
    _, _, vt = np.linalg.svd(np.stack([wx, wy], -1) - centro, full_matrices=False)
    eixo = vt[0]
    proj = (pts - centro) @ eixo
    comprimento = proj.max() - proj.min()
    if cfg["cabeca"] == "metal":
        # a cabeca e a ponta que tem mais metal perto dela
        met = _eh_metal(t)[ys, xs]
        perto_max = met & (proj > proj.max() - 0.3 * comprimento)
        perto_min = met & (proj < proj.min() + 0.3 * comprimento)
        if perto_min.sum() > perto_max.sum():
            eixo = -eixo; proj = -proj
    elif cfg["cabeca"] == "ponta":                  # vara: a ponta e o lado mais fino (menos pixels)
        fim_max = (proj > proj.max() - 0.2 * comprimento).sum()
        fim_min = (proj < proj.min() + 0.2 * comprimento).sum()
        if fim_max > fim_min:
            eixo = -eixo; proj = -proj
    if cfg["cabeca"] == "pendurado":
        # regador: pega no meio da alca de cima; fica de pe; "comprimento" = largura
        topo = ys.min()
        faixa = (ys < topo + 0.035 * (ys.max() - topo))
        pega = np.array([xs[faixa].mean(), topo + 0.02 * (ys.max() - topo)]) if "pega" not in cfg else np.array(cfg["pega"], float)
        graus = 0.0
        comprimento = xs.max() - xs.min()
    else:
        pega = np.array(cfg["pega"], float) if "pega" in cfg else centro + eixo * (proj.min() + cfg["pega_frac"] * comprimento)
        alvo_dir = eixo
        graus = _math.degrees(_math.atan2(alvo_dir[0], alvo_dir[1]))
    esc = cfg["alvo"] * 9 / comprimento
    im = _I.fromarray(t.clip(0, 255).astype(np.uint8), "RGBA")
    W2, H2 = max(1, round(t.shape[1] * esc)), max(1, round(t.shape[0] * esc))
    red = np.array(im.convert("RGBa").resize((W2, H2), _I.BOX).convert("RGBA")).astype(np.int32)
    red[..., 3] = np.where(red[..., 3] >= 128, 255, 0)
    pega_r = pega * np.array([W2 / t.shape[1], H2 / t.shape[0]])
    lado = int(cfg["alvo"] * 9 * 2.4) + 40
    out = np.zeros((lado, lado, 4), np.int32)
    centro_out = np.array([lado / 2, lado * 0.25])
    _L.coloca(out, red, pega_r, centro_out, -graus)
    # lado de corte para -x (como a enxada de teste); o regador fica com o bico para +x
    m = out[..., 3] > 0
    if cfg["cabeca"] == "pendurado":
        espelha = bool(cfg.get("bico_esquerda", False))
    else:
        met = _eh_metal(out)
        espelha = bool(met.any() and np.nonzero(met)[1].mean() > centro_out[0] + 2)
    if espelha:
        out = out[:, ::-1].copy()
        centro_out = np.array([lado - centro_out[0], centro_out[1]])
    _PEGA[nome] = tuple(centro_out)
    return out, tuple(centro_out)


def pega_de(nome):
    return _PEGA.get(nome, PEGA)


def _carregador(n):
    def f():
        img, _ = prepara(n)
        return img
    return f


for _n in list(ARTESANAIS) + list(V1):
    FERRAMENTAS[_n] = _carregador(_n)
