"""Esqueleto do heroi - vista de lado (direita).

Separa da pose parada: corpo (cabeca+tronco+cintura), braco de perto (manga + punho/mao)
e a perna de perto (calca + bota). A perna de longe e o braco de longe sao copias mais escuras
(no desenho original eles estao escondidos atras do corpo).
Cada perna e montada com duas partes (coxa e canela) por cinematica inversa: o pe e colocado
onde deve pisar e o joelho dobra para a frente. A bota gira sozinha (calcanhar no contato,
ponta do pe no impulso). Tudo e feito na resolucao do desenho original e so depois reduzido.
"""
import json, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

AQUI = os.path.dirname(os.path.abspath(__file__))
FONTE = os.path.join(AQUI, "..", "fonte", "lado_dir.png")
SAIDA = os.path.join(AQUI, "..", "revisao", "lado")

ESCALA = 9            # o desenho foi feito ~9x maior que o tamanho do jogo (64 px de altura)
CHAO = 583            # linha da sola (coordenadas do desenho original)
PAD_X, PAD_TOP = 120, 40

# --- pontos do esqueleto (coordenadas do desenho original) ---
QUADRIL = (147, 362)
JOELHO = (147, 437)
TORNOZELO = (147, 512)
OMBRO = (108, 252)
COTOVELO = (104, 286)

ESCURO = 150          # soma RGB abaixo disso = contorno
COSTAS_X = 80         # borda das costas na altura do ombro (y=250)
COSTAS_INCLINA = 0.03 # a borda das costas desce quase reta


def carrega():
    a = np.array(Image.open(FONTE).convert("RGBA")).astype(np.int32)
    # restos de magenta na borda viram contorno
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mag = (a[..., 3] > 0) & (r > 120) & (b > g + 20) & (g < 0.45 * r)
    a[mag, :3] = (26, 6, 6)
    return a


def escuro(a):
    return (a[..., :3].sum(2) < ESCURO) & (a[..., 3] > 0)


def caixa(shape, x0, x1, y0, y1):
    m = np.zeros(shape, bool); m[y0:y1, x0:x1] = True; return m


def separa(a):
    H, W = a.shape[:2]
    al = a[..., 3] > 0
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    esc = escuro(a)
    yy, xx = np.mgrid[0:H, 0:W]

    # ---------- braco de perto ----------
    pele = (r > 200) & (g > 110) & (b < 160) & (g > b + 25)
    mao = al & caixa(al.shape, 50, 141, 312, 427) & (pele | esc)
    punho = al & caixa(al.shape, 62, 140, 278, 322) & (((r > 120) & (g > 150) & (b > 170)) | esc)
    manga = al & (yy >= 252) & (yy < 290) & (xx >= 60) & (xx <= 134 + (yy - 262).clip(0) // 6)
    braco = mao | punho | manga
    perto = ndi.binary_dilation(braco, iterations=10)
    braco |= perto & esc & caixa(al.shape, 54, 143, 250, 428)
    braco = ndi.binary_fill_holes(braco) & al
    # mao: so o componente ligado ao punho
    lab, n = ndi.label(braco)
    if n > 1:
        tam = ndi.sum(np.ones_like(lab), lab, index=range(1, n + 1))
        braco = lab == (1 + int(np.argmax(tam)))
    antebraco = braco & (yy >= COTOVELO[1] - 6)
    braco_sup = braco & ~antebraco

    # ---------- perna de perto ----------
    sep = {}
    for y in range(420, 513):
        x = 126
        while x > 92 and not esc[y, x]:
            x -= 1
        x2 = x
        while x2 > 90 and esc[y, x2 - 1]:
            x2 -= 1
        sep[y] = x2
    ys = sorted(sep); v = ndi.median_filter(np.array([sep[y] for y in ys]), size=9)
    sep = dict(zip(ys, v))
    perna = np.zeros_like(al)
    for y in range(352, H):
        if y < 420:
            x0 = sep[420]
        elif y <= 512:
            x0 = sep[y] if y < 496 else max(sep[y], 105)   # perto da bota a linha encosta na bota de tras: corta a lasca
        else:
            x0 = 110
        perna[y, x0:] = al[y, x0:]
    # parte da perna escondida atras da mao: copia a coluna de baixo (calca e reta)
    escondida = perna & braco
    perna_rgba = a.copy()
    perna_rgba[~perna] = 0
    for y in range(352, 436):
        for x in range(sep[420] - 4, 146):
            if braco[y, x]:
                perna_rgba[y, x] = a[442, x] if perna[442, x] else 0
    # completa por cima (fica escondido sob a cintura) para a coxa poder girar sem abrir buraco
    for y in range(300, 366):
        perna_rgba[y] = perna_rgba[368]
    perna_m = perna_rgba[..., 3] > 0

    # ---------- corpo ----------
    corpo_rgba = a.copy()
    tira = braco | (yy >= 362)
    corpo_rgba[tira] = 0
    # tronco atras do braco: preenche com a camisa
    camisa = (82, 146, 206); camisa_esc = (63, 110, 159); contorno = (20, 8, 10)
    # as costas sao retas: o buraco so e preenchido ate a linha das costas (sem o formato do punho
    # e da mao, que criava uma "corcunda" quando o braco ia para a frente)
    linha_costas = np.ceil(COSTAS_X - (yy - 250) * COSTAS_INCLINA).astype(int)
    buraco_tronco = braco & (yy < 338) & (yy >= 240) & (xx >= linha_costas)
    corpo_rgba[buraco_tronco, :3] = camisa
    corpo_rgba[buraco_tronco, 3] = 255
    # cintura atras da mao: repete a faixa da cintura que aparece na frente
    for y in range(336, 362):
        for x in range(linha_costas[y, 0], 140):
            if braco[y, x] or corpo_rgba[y, x, 3] == 0:
                corpo_rgba[y, x] = a[y, 140 + (x - 72) % 24]
    # sombra da camisa nas costas e contorno nas bordas novas
    m = corpo_rgba[..., 3] > 0
    borda = m & ~ndi.binary_erosion(m, iterations=7)
    novo = (buraco_tronco | caixa(al.shape, 72, 140, 336, 362)) & borda
    corpo_rgba[novo, :3] = contorno
    costas = buraco_tronco & ~novo & (xx < linha_costas + 16)
    corpo_rgba[costas, :3] = camisa_esc

    braco_rgba = a.copy(); braco_rgba[~braco] = 0
    sup_rgba = a.copy(); sup_rgba[~braco_sup] = 0
    ant_rgba = a.copy(); ant_rgba[~antebraco] = 0
    return dict(corpo=corpo_rgba, braco=braco_rgba, braco_sup=sup_rgba, antebraco=ant_rgba,
                perna=perna_rgba, mascara_braco=braco, mascara_perna=perna_m, sep=sep)


if __name__ == "__main__":
    os.makedirs(SAIDA, exist_ok=True)
    a = carrega()
    p = separa(a)
    H, W = a.shape[:2]
    # prancha de conferencia das mascaras
    vis = np.zeros((H, W, 4), np.int32)
    vis[..., :3] = 60; vis[..., 3] = 255
    al = a[..., 3] > 0
    vis[al, :3] = (a[al, :3] * 0.35 + 40).astype(int)
    vis[p["mascara_perna"] & (np.mgrid[0:H, 0:W][0] >= 352), :3] = (230, 140, 40)
    vis[p["mascara_braco"], :3] = (60, 200, 255)
    Image.fromarray(vis.astype(np.uint8)).resize((W * 2, H * 2), Image.NEAREST).save(os.path.join(SAIDA, "mascaras.png"))
    for k in ("corpo", "perna", "braco_sup", "antebraco"):
        im = p[k].astype(np.uint8)
        bg = Image.new("RGBA", (W, H), (60, 60, 70, 255)); bg.alpha_composite(Image.fromarray(im))
        bg.resize((W * 2, H * 2), Image.NEAREST).save(os.path.join(SAIDA, f"parte_{k}.png"))
    print("ok", {k: int((p[k][..., 3] > 0).sum()) for k in ("corpo", "perna", "braco_sup", "antebraco")})
