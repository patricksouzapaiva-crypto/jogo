"""Tira o fundo magenta de uma imagem (mesma tecnica usada na fauna: a franja misturada com o
magenta vira transparente ou recebe a cor de dentro, e o roxo que sobra na borda e neutralizado).
Copiado de fauna_preparada/ferramentas/segmentar.py para esta pasta funcionar sozinha."""
import numpy as np
from scipy import ndimage as ndi

FAIXA = 3          # largura da borda analisada (px da folha)
RESIDUO_MAX = 45   # distancia maxima da reta fundo-animal para ser considerado mistura

def remove_fundo(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    puro = (r > 200) & (b > 200) & (g < 90) & (np.abs(r - b) < 40)
    fg = ~puro
    faixa = fg & ~ndi.binary_erosion(fg, iterations=FAIXA)
    P = a.astype(float)
    _, (by, bx) = ndi.distance_transform_edt(fg, return_indices=True)
    B = P[by, bx]                                   # cor do fundo mais proxima
    melhor_res = np.full(a.shape[:2], 1e9); melhor_F = np.zeros_like(P); melhor_a = np.zeros(a.shape[:2])
    melhor_dist = np.zeros(a.shape[:2])
    cands = []
    for k in range(1, FAIXA + 2):                   # cor do animal a 1, 2, 3, 4 px para dentro
        inter = ndi.binary_erosion(fg, iterations=k)
        _, (iy, ix) = ndi.distance_transform_edt(~inter, return_indices=True)
        F = P[iy, ix]; d = F - B; n2 = (d * d).sum(-1) + 1e-6
        al = np.clip(((P - B) * d).sum(-1) / n2, 0, 1)
        res = np.linalg.norm(P - (B + al[..., None] * d), axis=-1)
        cands.append((res, F, al, np.sqrt(n2)))
    best = np.min([c[0] for c in cands], axis=0)
    # entre as cores que explicam bem o pixel (ate +10 do melhor), usa a mais "pura" (mais longe do fundo)
    for res, F, al, dist in cands:
        ok = (res <= best + 10) & (dist > melhor_dist)
        melhor_res[ok] = res[ok]; melhor_F[ok] = F[ok]; melhor_a[ok] = al[ok]; melhor_dist[ok] = dist[ok]
    mistura = faixa & (melhor_res < RESIDUO_MAX)
    transparente = puro | (mistura & (melhor_a < 0.5))
    recolorir = mistura & (melhor_a >= 0.5)
    out = a.copy()
    out[recolorir] = melhor_F[recolorir].round().astype(a.dtype)
    # roxo neutro que sobrou na borda (r~b, verde baixo): nenhum animal tem essa cor no desenho
    # (o ameixa da Penala e avermelhado, r-b ~ +58). Troca pelo vizinho opaco mais escuro.
    fg2 = ~transparente
    anel = fg2 & ~ndi.binary_erosion(fg2, iterations=2)
    o = out.astype(int)
    roxo = anel & (np.abs(o[..., 0] - o[..., 2]) < 35) & (np.minimum(o[..., 0], o[..., 2]) - o[..., 1] > 45)
    lum = o.sum(-1) + np.where(fg2 & ~roxo, 0, 10000)
    ys, xs = np.where(roxo)
    H, W = lum.shape
    for y, x in zip(ys, xs):
        y0, y1, x0, x1 = max(0, y - 2), min(H, y + 3), max(0, x - 2), min(W, x + 3)
        jan = lum[y0:y1, x0:x1]; k = np.unravel_index(np.argmin(jan), jan.shape)
        if jan[k] < 10000: out[y, x] = out[y0 + k[0], x0 + k[1]]
    stats = dict(franja_removida=int((mistura & (melhor_a < 0.5)).sum()), franja_recolorida=int(recolorir.sum()),
                 roxo_de_borda_neutralizado=int(roxo.sum()))
    return out, fg2, puro, stats
