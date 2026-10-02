"""Etapa 1: fundo magenta -> alpha real, separa cada pose e atribui linha/coluna.
Nao redimensiona nada. Saida: poses RGBA na resolucao original + segmentacao.json

Remocao do fundo:
 1. "magenta puro" (r>200, b>200, g<90, r~b) e fundo em qualquer lugar (inclusive entre patas);
 2. pixels de borda (ate 3 px do fundo) passam por um teste de MISTURA: se o pixel fica na reta
    entre a cor do fundo e a cor do animal ao lado, ele e franja (vira transparente se tem mais
    fundo que animal, ou recebe a cor do animal se tem mais animal). Cores proprias do desenho
    (pena rosa/ameixa, contorno escuro) nao ficam nessa reta e sao mantidas como estao.
"""
import numpy as np, json, os, sys
from PIL import Image
from scipy import ndimage as ndi

SRC, OUT = sys.argv[1], sys.argv[2]
META = json.load(open(sys.argv[3]))
os.makedirs(OUT, exist_ok=True)
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

def agrupa(vals, k):
    idx = np.argsort(vals); v = np.asarray(vals)[idx]
    if k == 1: return [list(idx)]
    cuts = sorted(np.argsort(np.diff(v))[-(k - 1):])
    grupos, ini = [], 0
    for c in cuts:
        grupos.append(list(idx[ini:c + 1])); ini = c + 1
    grupos.append(list(idx[ini:]))
    return grupos

relatorio = {}
for item in META["files"]:
    nome = os.path.basename(item["file"]); esp = item["species"]; tipo = item["kind"]
    R, C = item["rows"], item["frames_per_row"]
    a0 = np.asarray(Image.open(os.path.join(SRC, nome)).convert("RGB")).astype(np.int16)
    a, fg, puro, st = remove_fundo(a0)
    lab, n = ndi.label(fg, structure=np.ones((3, 3)))
    tam = ndi.sum(fg, lab, range(1, n + 1))
    objs = ndi.find_objects(lab)
    grandes = [i for i in range(n) if tam[i] > 1500]
    pequenos = [i for i in range(n) if 4 <= tam[i] <= 1500]
    cent = {i: ((objs[i][1].start + objs[i][1].stop) / 2, (objs[i][0].start + objs[i][0].stop) / 2) for i in range(n)}
    anexos, descartes = {}, []
    for p in pequenos:
        sl = objs[p]; melhor, dmin = None, 1e9
        for gi in grandes:
            gs = objs[gi]
            dx = max(gs[1].start - sl[1].stop, sl[1].start - gs[1].stop, 0)
            dy = max(gs[0].start - sl[0].stop, sl[0].start - gs[0].stop, 0)
            dd = (dx * dx + dy * dy) ** .5
            if dd < dmin: dmin, melhor = dd, gi
        if dmin <= 12: anexos.setdefault(melhor, []).append(p)
        else: descartes.append((p, int(tam[p]), round(dmin, 1)))
    linhas = agrupa([cent[i][1] for i in grandes], R)
    grade, avisos = {}, []
    for ri, grp in enumerate(sorted(linhas, key=lambda g: np.mean([cent[grandes[j]][1] for j in g]))):
        comps = sorted([grandes[j] for j in grp], key=lambda i: cent[i][0])
        if len(comps) != C: avisos.append(f"linha {ri}: {len(comps)} pecas em vez de {C}")
        for ci, comp in enumerate(comps): grade[(ri, ci)] = comp
    poses = []
    for (ri, ci), comp in sorted(grade.items()):
        ids = [comp] + anexos.get(comp, [])
        m = np.isin(lab, [i + 1 for i in ids])
        ys, xs = np.where(m)
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        rgba = np.zeros((y1 - y0, x1 - x0, 4), np.uint8)
        rgba[..., :3] = a[y0:y1, x0:x1].clip(0, 255)
        rgba[..., 3] = (m[y0:y1, x0:x1] * 255).astype(np.uint8)
        fn = f"{esp}_{tipo}_r{ri}_c{ci}.png"
        Image.fromarray(rgba, "RGBA").save(os.path.join(OUT, fn))
        poses.append(dict(arquivo=fn, linha=ri, coluna=ci, x=int(x0), y=int(y0), w=int(x1 - x0), h=int(y1 - y0),
                          area=int(m.sum()), pedacos_anexados=len(ids) - 1,
                          toca_borda_da_folha=bool(y0 == 0 or x0 == 0 or y1 == a.shape[0] or x1 == a.shape[1])))
    relatorio[nome] = dict(especie=esp, tipo=tipo, linhas=R, colunas=C, poses_encontradas=len(poses),
                           pixels_fundo_puro=int(puro.sum()), **st,
                           pedacos_descartados=descartes, avisos=avisos, poses=poses)
    print(f"{nome}: {len(poses)}/{R*C} poses | franja removida {st['franja_removida']} recolorida {st['franja_recolorida']} roxo {st['roxo_de_borda_neutralizado']} | anexos {sum(len(v) for v in anexos.values())} descartes {len(descartes)} {avisos}")
json.dump(relatorio, open(os.path.join(OUT, "segmentacao.json"), "w"), indent=1, ensure_ascii=False)
