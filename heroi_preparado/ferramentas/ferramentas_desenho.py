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


FERRAMENTAS = {"enxada": enxada}


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
# Ferramentas desenhadas no ChatGPT (fonte/ferramentas/tools_source.png, 6 celulas de 512x512 com
# fundo magenta). Cada uma e recortada, tem o fundo tirado, e girada para a mesma posicao da enxada
# (pega em PEGA, cabo descendo, cabeca embaixo, lado de corte virado para -x) e reduzida para a escala
# do desenho do heroi (9x o tamanho do jogo). A pegada e calculada pelo proprio desenho: os pontos de
# pegada do METADATA.json ficavam fora do cabo no machado, na picareta e na vara.
# ---------------------------------------------------------------------------------------------
import os as _os
import math as _math

FONTE_CHATGPT = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "fonte", "ferramentas", "tools_source.png")
# celula (x, y), comprimento no jogo (px, da ponta do cabo ate a ponta mais longe), onde a mao segura
# (fracao do comprimento a partir da ponta do cabo, ou ponto fixo na celula), para onde fica a cabeca
CHATGPT = {
    "pa":       dict(celula=(0, 0), alvo=34, pega_frac=0.10, cabeca="metal"),
    "foice":    dict(celula=(512, 0), alvo=17, pega=(368, 352), cabeca="metal"),
    "regador":  dict(celula=(1024, 0), alvo=21, pega=(298, 150), cabeca="pendurado"),
    "machado":  dict(celula=(0, 512), alvo=30, pega_frac=0.14, cabeca="metal"),
    "picareta": dict(celula=(512, 512), alvo=31, pega_frac=0.14, cabeca="metal"),
    "vara":     dict(celula=(1024, 512), alvo=44, pega_frac=0.20, cabeca="ponta", sem_linha=True),
}
_FONTE_CACHE = {}


def _celula(cx, cy):
    from PIL import Image as _I
    import fundo_magenta as _fm
    if "img" not in _FONTE_CACHE:
        _FONTE_CACHE["img"] = np.array(_I.open(FONTE_CHATGPT).convert("RGB")).astype(np.int32)
    a = _FONTE_CACHE["img"][cy:cy + 512, cx:cx + 512]
    out, fg, puro, _ = _fm.remove_fundo(a.astype(np.uint8))
    rgba = np.zeros((512, 512, 4), np.int32)
    rgba[..., :3] = out; rgba[..., 3] = np.where(fg, 255, 0)
    return rgba


def _maior_pedaco(m):
    from scipy import ndimage as _ndi
    lab, n = _ndi.label(m)
    if n <= 1:
        return m
    tam = _ndi.sum(np.ones_like(lab), lab, index=range(1, n + 1))
    return lab == (1 + int(np.argmax(tam)))


def chatgpt(nome):
    """Ferramenta do ChatGPT pronta para o esqueleto (mesma convencao da enxada)."""
    from PIL import Image as _I
    cfg = CHATGPT[nome]
    t = _celula(*cfg["celula"])
    r, g, b, al = t[..., 0], t[..., 1], t[..., 2], t[..., 3] > 0
    if cfg.get("sem_linha"):                       # tira a linha e o anzol desenhados (a linha sera um efeito)
        amarelo = al & (r > 170) & (g > 150) & (b < 170) & (np.abs(r - g) < 70)
        al = _maior_pedaco(al & ~amarelo)
        t[~al] = 0
    else:
        al = _maior_pedaco(al); t[~al] = 0
    ys, xs = np.nonzero(al)
    pts = np.stack([xs, ys], -1).astype(float)
    madeira = al & (r > 170) & (g > 55) & (g < 200) & (b < 60)
    metal = al & (np.abs(r - g) < 28) & (np.abs(g - b) < 34) & (r > 105)
    # eixo do cabo (madeira) e ponta do cabo (o lado oposto a cabeca)
    wy, wx = np.nonzero(madeira if madeira.sum() > 200 else al)   # o regador nao tem madeira
    centro = np.array([wx.mean(), wy.mean()])
    _, _, vt = np.linalg.svd(np.stack([wx, wy], -1) - centro, full_matrices=False)
    eixo = vt[0]
    if cfg["cabeca"] == "metal":
        my, mx = np.nonzero(metal); cab = np.array([mx.mean(), my.mean()])
    elif cfg["cabeca"] == "pendurado":
        cab = pts.mean(0)
    else:
        cab = None
    proj = (pts - centro) @ eixo
    if cab is not None and (cab - centro) @ eixo < 0:
        eixo = -eixo; proj = -proj
    if cab is None:                                # vara: a ponta e o lado mais comprido
        if proj.max() < -proj.min():
            eixo = -eixo; proj = -proj
    comprimento = proj.max() - proj.min()
    if "pega" in cfg:
        pega = np.array(cfg["pega"], float)
    else:
        pega = centro + eixo * (proj.min() + cfg["pega_frac"] * comprimento)
    # direcao pega -> cabeca no padrao do esqueleto (0 = para baixo, 90 = +x)
    alvo_dir = (cab if cab is not None else centro + eixo * proj.max()) - pega
    if cfg["cabeca"] == "pendurado":
        graus = 0.0                                 # o regador fica de pe, pendurado pela alca
        comprimento = xs.max() - xs.min()           # para o regador o "comprimento" e a largura
    else:
        graus = _math.degrees(_math.atan2(alvo_dir[0], alvo_dir[1]))
    esc = cfg["alvo"] * 9 / comprimento
    # reduz para a escala do heroi (media em blocos, alpha so 0/255) e gira deixando a cabeca para baixo
    im = _I.fromarray(t.clip(0, 255).astype(np.uint8), "RGBA")
    W2, H2 = max(1, round(512 * esc)), max(1, round(512 * esc))
    red = np.array(im.convert("RGBa").resize((W2, H2), _I.BOX).convert("RGBA")).astype(np.int32)
    red[..., 3] = np.where(red[..., 3] >= 128, 255, 0)
    pega_r = pega * esc
    lado = int(cfg["alvo"] * 9 * 2.4) + 40
    out = np.zeros((lado, lado, 4), np.int32)
    centro_out = np.array([lado / 2, lado * 0.25])
    import anim_lado as _L
    _L.coloca(out, red, pega_r, centro_out, -graus)
    # lado de corte para -x (como a enxada); o regador fica com o bico para +x (frente do heroi)
    m = out[..., 3] > 0
    yy, xx = np.nonzero(m)
    met = m & (np.abs(out[..., 0] - out[..., 1]) < 28) & (np.abs(out[..., 1] - out[..., 2]) < 34) & (out[..., 0] > 105)
    if cfg["cabeca"] == "pendurado":
        bico_esq = (xx < centro_out[0]).sum() > (xx > centro_out[0]).sum()
        espelha = bico_esq
    elif met.any():
        espelha = np.nonzero(met)[1].mean() > centro_out[0]
    else:
        espelha = False
    if espelha:
        out = out[:, ::-1].copy()
        centro_out = np.array([lado - centro_out[0], centro_out[1]])
    _CHATGPT_PEGA[nome] = tuple(centro_out)
    return out


_CHATGPT_PEGA = {}


def pega_de(nome):
    return _CHATGPT_PEGA.get(nome, PEGA)


for _n in CHATGPT:
    FERRAMENTAS[_n] = (lambda n: (lambda: chatgpt(n)))(_n)
