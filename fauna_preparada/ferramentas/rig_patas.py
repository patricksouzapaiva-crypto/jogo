"""Esqueleto de patas (v3): gera a CAMINHADA de quadrupedes a partir de UMA pose limpa por direcao.

O corpo, a cabeca e a textura sao exatamente os da pose-base em todos os quadros (nada cintila,
nada muda de tamanho). So as patas, abaixo da linha do joelho, se movem:
  - de lado: sequencia de quadrupede  traseira-esq -> dianteira-esq -> traseira-dir -> dianteira-dir
    (1/4 de ciclo entre cada uma). Cada pata fica 60% do ciclo apoiada (indo para tras) e 40% no ar
    (indo para frente, com o casco levantado);
  - de frente/costas: as duas patas visiveis levantam alternadamente.
O sobe e desce do corpo (1 px) e acrescentado depois, na resolucao do jogo (melhorar_andar.py).
As regioes das patas foram marcadas a mao em cada pose (coordenadas da folha original).
"""
import numpy as np, json, os, sys, shutil
from PIL import Image

# papel: TE/TD = traseira esquerda/direita, DE/DD = dianteira esquerda/direita (lado do animal)
# perto=True: desenhada na frente do corpo; False: atras (pata do outro lado)
RIG = {
    # de lado: cada par (traseiro/dianteiro) e separado em duas patas pelo contorno escuro, usando um
    # ponto-semente dentro de cada pata (perto = lado de ca, desenhada na frente do corpo)
    # pernas: (papel, sementes [(x, y), ...], perto, meia-largura da janela, primeira linha da pata)
    ("gruntho", "right"): dict(base=("actions", 0, 0), vista="lado", passo=14, levanta=10, pares=[
        dict(x=(8, 92), y=98, pernas=[("TE", [(30, 112), (30, 124)], True, 20, 106), ("TD", [(68, 112), (70, 120)], False, 18, 108)]),
        dict(x=(100, 170), y=98, pernas=[("DE", [(120, 110), (121, 125)], True, 22, 108), ("DD", [(150, 108), (152, 117)], False, 18, 104)])]),
    ("vaca", "right"): dict(base=("actions", 0, 0), vista="lado", passo=14, levanta=10, pares=[
        dict(x=(4, 104), y=100, excluir=(52, 102, 0, 121), pernas=[("TE", [(35, 110), (30, 138)], True, 28, 104), ("TD", [(75, 126), (86, 126)], False, 22, 119)]),
        dict(x=(112, 196), y=100, pernas=[("DE", [(140, 118), (135, 141)], True, 28, 108), ("DD", [(166, 118), (172, 138)], False, 20, 110)])]),
    # de frente/costas: as duas patas visiveis ja sao separadas por um vao
    ("vaca", "down"): dict(base=("walk", 0, 4), vista="frente", levanta=16, patas=[
        dict(papel="DD", x=(24, 77), y=200, perto=True), dict(papel="DE", x=(78, 132), y=200, perto=True)]),
    ("vaca", "up"): dict(base=("walk", 3, 6), vista="costas", levanta=16, patas=[
        dict(papel="TE", x=(12, 69), y=196, perto=True), dict(papel="TD", x=(80, 140), y=196, perto=True)]),
    ("gruntho", "down"): dict(base=("walk", 0, 3), vista="frente", levanta=14, patas=[
        dict(papel="DD", x=(18, 66), y=176, perto=True), dict(papel="DE", x=(78, 128), y=176, perto=True)]),
    ("gruntho", "up"): dict(base=("walk", 3, 0), vista="costas", levanta=14, espelhar_pata_esq_para_dir=172, patas=[
        dict(papel="TE", x=(20, 78), y=172, perto=True), dict(papel="TD", x=(80, 140), y=172, perto=True)]),
}
JUNCAO = 7          # faixa (px da folha) abaixo do joelho preenchida com a pose original (sem frestas)
ESCURO = 140        # soma R+G+B abaixo disso = contorno


# esquerda = espelho da direita (as acoes so existem viradas para a direita; assim andar e parar usam o mesmo desenho)
ESPELHO = {("gruntho", "left"): ("gruntho", "right"), ("vaca", "left"): ("vaca", "right")}
FASE = {"TE": 0.0, "DE": 0.25, "TD": 0.5, "DD": 0.75}
FASE_2 = {"TE": 0.0, "DD": 0.0, "TD": 0.5, "DE": 0.5}   # frente/costas: duas patas alternando
MARGEM = 14


def mascara_pata(rgba, p):
    al = rgba[..., 3] > 127
    m = np.zeros_like(al)
    x0, x1 = p["x"]
    m[p["y"] + 1:, x0:x1 + 1] = al[p["y"] + 1:, x0:x1 + 1]
    if p.get("sem_rosa"):
        c = rgba[..., :3].astype(int)
        rosa = (c[..., 0] > 170) & (c[..., 0] - c[..., 1] > 35) & (c[..., 0] - c[..., 2] > 25) & (c[..., 1] > 90)
        m &= ~rosa
    return m


def separar_par(rgba, par):
    """regiao do par abaixo do joelho -> uma mascara por pata, cortando pelo contorno escuro"""
    from scipy import ndimage as ndi
    al = rgba[..., 3] > 127
    reg = np.zeros_like(al)
    x0, x1 = par["x"]; y0 = par["y"]
    reg[y0 + 1:, x0:x1 + 1] = al[y0 + 1:, x0:x1 + 1]
    c = rgba[..., :3].astype(int)
    if par.get("excluir"):            # area fixa (ex.: ubere da vaca) que fica no corpo
        ex0, ex1, ey0, ey1 = par["excluir"]
        reg[ey0:ey1 + 1, ex0:ex1 + 1] = False
    # caminho mais barato a partir das sementes: atravessar contorno escuro ou troca forte de cor custa caro
    import heapq
    lum = c.sum(-1)
    Hh, Ww = reg.shape
    custo = np.full((Hh, Ww), np.inf); dono = np.full((Hh, Ww), -1)
    fila = []
    for k, perna in enumerate(par["pernas"]):
        for (sx, sy) in perna[1]:
            if 0 <= sy < Hh and 0 <= sx < Ww and reg[sy, sx]:
                custo[sy, sx] = 0; dono[sy, sx] = k; heapq.heappush(fila, (0.0, sy, sx, k))
    viz = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
    while fila:
        cst, y, x, k = heapq.heappop(fila)
        if cst > custo[y, x]: continue
        for dy, dx in viz:
            yy, xx = y + dy, x + dx
            if 0 <= yy < Hh and 0 <= xx < Ww and reg[yy, xx]:
                dc = np.abs(c[yy, xx] - c[y, x]).sum()
                passo = (1.41 if dy and dx else 1.0) + dc / 40.0 + (6.0 if lum[yy, xx] < ESCURO else 0.0)
                nc = cst + passo
                if nc < custo[yy, xx]:
                    custo[yy, xx] = nc; dono[yy, xx] = k; heapq.heappush(fila, (nc, yy, xx, k))
    out = []
    Yg, Xg = np.mgrid[0:Hh, 0:Ww]
    for k, perna in enumerate(par["pernas"]):
        papel, sementes_k, perto, jx, ymin = perna
        sx = int(round(np.mean([p[0] for p in sementes_k])))
        m = (dono == k) & reg & (np.abs(Xg - sx) <= jx) & (Yg >= ymin)
        m = ndi.binary_fill_holes(m) & reg          # sem furos dentro da pata
        out.append(dict(papel=papel, y=ymin - 1, perto=perto, x=(sx - jx, sx + jx), m=m))
    return out


def completar_pata_de_longe(rgba, pernas, largura=12):
    """a parte da pata de longe escondida atras da pata de perto nao existe no desenho; ela e
    completada refletindo a textura da propria pata de longe para dentro da area da pata de perto
    (so aparece quando a pata de perto se afasta)."""
    for longe in [q for q in pernas if not q["perto"]]:
        for perto in [q for q in pernas if q["perto"]]:
            camada = longe["camada"]; m = camada[..., 3] > 0; mp = perto["m"]
            novo = camada.copy()
            for y in np.where(m.any(1))[0]:
                xs = np.where(m[y])[0]
                xl, xr = xs.min(), xs.max()
                # lado encostado na pata de perto
                if xl > 0 and mp[y, max(0, xl - 2):xl].any():
                    for d in range(1, largura + 1):
                        xd, xsrc = xl - d, min(xr, xl + d)
                        if xd < 0 or not mp[y, xd]: break
                        novo[y, xd] = camada[y, xsrc]
                if xr < m.shape[1] - 1 and mp[y, xr + 1:xr + 3].any():
                    for d in range(1, largura + 1):
                        xd, xsrc = xr + d, max(xl, xr - d)
                        if xd >= m.shape[1] or not mp[y, xd]: break
                        novo[y, xd] = camada[y, xsrc]
            longe["camada"] = novo


def mover_pata(rgba, m, py, dx_casco, encolhe):
    """cisalha a pata em torno do joelho (linha py): o casco anda dx_casco na horizontal e sobe
    'encolhe' px (a pata encurta). Mapeamento inverso, sem buracos."""
    H, W = m.shape
    yy, xx = np.where(m)
    L = max(1.0, float(yy.max() - py))
    s = (L - encolhe) / L
    Yd, Xd = np.mgrid[0:H, 0:W]
    ys = py + (Yd - py) / s
    t = np.clip((ys - py) / L, 0, 1)
    xs = Xd - dx_casco * t
    yi = np.round(ys).astype(int); xi = np.round(xs).astype(int)
    ok = (yi > py) & (yi < H) & (xi >= 0) & (xi < W)
    yi = np.clip(yi, 0, H - 1); xi = np.clip(xi, 0, W - 1)
    sel = ok & m[yi, xi]
    out = np.zeros_like(rgba)
    out[sel] = rgba[yi[sel], xi[sel]]
    return out


def ciclo(rgba, spec, n=8):
    H0, W0 = rgba.shape[:2]
    base = np.zeros((H0 + MARGEM, W0 + 2 * MARGEM, 4), np.uint8)
    base[MARGEM:, MARGEM:MARGEM + W0] = rgba    # margem em cima/lados para o movimento
    if spec.get("espelhar_pata_esq_para_dir"):
        # pose-base com as duas patas no chao: a pata direita (desenhada sempre levantada) recebe o
        # espelho da esquerda abaixo da linha indicada
        y0 = spec["espelhar_pata_esq_para_dir"] + MARGEM
        al = base[..., 3] > 127
        cols = np.where(al.any(0))[0]; cx = (cols.min() + cols.max()) // 2
        for x in range(cx + 1, base.shape[1]):
            xm = 2 * cx - x
            if 0 <= xm < base.shape[1]:
                base[y0:, x] = base[y0:, xm]
    patas = []
    for par in spec.get("pares", []):
        q = dict(par); q["x"] = (par["x"][0] + MARGEM, par["x"][1] + MARGEM); q["y"] = par["y"] + MARGEM
        q["pernas"] = [(pp, [(sx + MARGEM, sy + MARGEM) for sx, sy in sem], pt, jx, ym + MARGEM) for pp, sem, pt, jx, ym in par["pernas"]]
        if par.get("excluir"):
            e0, e1, f0, f1 = par["excluir"]; q["excluir"] = (e0 + MARGEM, e1 + MARGEM, f0 + MARGEM, f1 + MARGEM)
        patas += separar_par(base, q)
    for p in spec.get("patas", []):
        q = dict(p); q["x"] = (p["x"][0] + MARGEM, p["x"][1] + MARGEM); q["y"] = p["y"] + MARGEM
        q["m"] = mascara_pata(base, q); patas.append(q)
    corpo = base.copy()
    for q in patas: corpo[q["m"]] = 0
    for q in patas:
        q["camada"] = np.zeros_like(base); q["camada"][q["m"]] = base[q["m"]]
    completar_pata_de_longe(base, patas)
    lateral = spec["vista"] == "lado"
    quadros = []
    for f in range(n):
        tt = f / n
        tras, frente = [], []
        for q in patas:
            ph = (tt - (FASE if lateral else FASE_2)[q["papel"]]) % 1.0
            if ph < 0.6:
                s = ph / 0.6; pos = 1 - 2 * s; lift = 0.0
            else:
                s = (ph - 0.6) / 0.4; pos = -1 + 2 * s; lift = np.sin(np.pi * s)
            dx = pos * spec.get("passo", 0) if lateral else 0.0
            camada = mover_pata(q["camada"], q["camada"][..., 3] > 0, q["y"], dx, spec["levanta"] * lift)
            (frente if q["perto"] else tras).append(camada)
        img = np.zeros_like(base)
        for c in tras + [corpo] + frente:
            a = c[..., 3] > 0; img[a] = c[a]
        # frestas na juncao joelho/barriga: completa com a pose original (parte de cima da pata e fixa)
        for q in patas:
            y0, x0, x1 = q["y"], q["x"][0], q["x"][1]
            faixa = np.zeros(img.shape[:2], bool); faixa[y0 + 1:y0 + 1 + JUNCAO, x0:x1 + 1] = True
            op = img[..., 3] > 0
            esq = np.zeros_like(op); dir_ = np.zeros_like(op)
            for k in range(1, 4):
                esq[:, k:] |= op[:, :-k]; dir_[:, :-k] |= op[:, k:]
            buraco = faixa & ~op & (base[..., 3] > 127) & esq & dir_
            img[buraco] = base[buraco]
        quadros.append(img)
    return quadros


def aplicar(seg_in, seg_out, meta_path):
    if os.path.exists(seg_out): shutil.rmtree(seg_out)
    shutil.copytree(seg_in, seg_out)
    seg = json.load(open(os.path.join(seg_in, "segmentacao.json")))
    meta = {os.path.basename(m["file"]): m for m in json.load(open(meta_path))["files"]}
    gerados = {}
    for (esp, dn), spec in RIG.items():
        folha, ri, ci = spec["base"]
        rgba = np.asarray(Image.open(os.path.join(seg_in, f"{esp}_{folha}_r{ri}_c{ci}.png"))).copy()
        gerados[(esp, dn)] = (ciclo(rgba, spec), folha, spec)
    for (esp, dn), (esp_src, dn_src) in ESPELHO.items():
        q, folha, spec = gerados[(esp_src, dn_src)]
        gerados[(esp, dn)] = ([np.ascontiguousarray(x[:, ::-1]) for x in q], folha, spec)
    for (esp, dn), (quadros, folha, spec) in gerados.items():
        fw = f"{esp}_walk.png"
        linha = meta[fw]["row_order"].index(dn)
        ent = seg[fw]
        if "h_lado_original" not in ent:
            r_dir = meta[fw]["row_order"].index("right")
            ent["h_lado_original"] = float(np.median([p["h"] for p in ent["poses"] if p["linha"] == r_dir]))
        for c, img in enumerate(quadros):
            al = img[..., 3] > 0
            ys, xs = np.where(al)
            crop = img[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
            fn = f"{esp}_walk_r{linha}_c{c}.png"
            Image.fromarray(crop, "RGBA").save(os.path.join(seg_out, fn))
            for p in ent["poses"]:
                if p["linha"] == linha and p["coluna"] == c:
                    p.update(w=int(crop.shape[1]), h=int(crop.shape[0]), area=int(al.sum()),
                             escala_da_folha=folha, gerado_por_rig=True)
        print(f"{esp:8s} {dn:5s} gerado por esqueleto a partir de {folha} {spec['base'][1:]}"
              + (" (espelhado)" if (esp, dn) in ESPELHO else ""))
    json.dump(seg, open(os.path.join(seg_out, "segmentacao.json"), "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    aplicar(sys.argv[1], sys.argv[2], sys.argv[3])
