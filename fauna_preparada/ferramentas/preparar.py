"""Etapa 2: escala constante por especie, alinhamento, canvas e pivot unicos, paleta fixa.

- Uma escala por FOLHA, calculada para que o animal parado de lado tenha a mesma altura final
  na caminhada e nas acoes (as duas folhas vieram em escalas diferentes).
- Nenhuma pose e redimensionada sozinha: cada pose e posicionada (em px da folha) num canvas
  comum, com o pivot no mesmo lugar, e o canvas inteiro e reduzido de uma vez (media por area,
  alpha pre-multiplicado). Depois: alpha binario (sem semi-transparencia) e paleta fixa da
  especie (sem dithering), para as cores nao "piscarem" entre quadros. Sem bilinear, sem blur.
- Alinhamento: pes no chao (linha de base) e corpo parado na horizontal.
    caminhada: desloca cada quadro para casar o TRONCO com o 1o quadro da direcao;
    acoes: desloca cada quadro para casar as PATAS com o 1o quadro de respirar/piscar.
"""
import numpy as np, json, os, sys
from PIL import Image
from scipy import ndimage as ndi

SEG, OUT, CFG, META = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
cfg = json.load(open(CFG)); seg = json.load(open(os.path.join(SEG, "segmentacao.json")))
meta = {os.path.basename(m["file"]): m for m in json.load(open(META))["files"]}
os.makedirs(OUT, exist_ok=True)

def carrega(fn):
    return np.asarray(Image.open(os.path.join(SEG, fn)).convert("RGBA"))

def base_y(al):           # linha mais baixa com pixel opaco (contato com o chao)
    return np.where(al.any(1))[0].max()

def faixa(al, y0f, y1f):  # mascara so de uma faixa vertical (fracoes da altura da pose)
    ys = np.where(al.any(1))[0]; t, b = ys.min(), ys.max(); h = b - t + 1
    m = np.zeros_like(al); a0, a1 = int(t + h * y0f), int(t + h * y1f)
    m[a0:a1] = al[a0:a1]; return m

def melhor_dx(ref, mov, ref_base, mov_base, busca=24):
    """desloca 'mov' na horizontal para maximizar a sobreposicao com 'ref' (pes ja na mesma base)"""
    H = max(ref.shape[0], mov.shape[0]) + 4
    W = max(ref.shape[1], mov.shape[1]) + 2 * busca + 4
    R = np.zeros((H, W), bool); M = np.zeros((H, W), bool)
    oy_r = H - 2 - ref_base; oy_m = H - 2 - mov_base
    ox = busca + 2
    R[oy_r:oy_r + ref.shape[0], ox:ox + ref.shape[1]] = ref
    best, bdx = -1, 0
    for dx in range(-busca, busca + 1):
        M[:] = False
        M[oy_m:oy_m + mov.shape[0], ox + dx:ox + dx + mov.shape[1]] = mov
        inter = (R & M).sum(); uni = (R | M).sum()
        s = inter / max(uni, 1)
        if s > best: best, bdx = s, dx
    return bdx, best

relatorio = {}
for esp in ["penala", "ovelha", "pato", "gruntho", "vaca"]:
    alvo = cfg[esp]["altura_lado_px"]
    fw, fa = f"{esp}_walk.png", f"{esp}_actions.png"
    ow, oa = meta[fw]["row_order"], meta[fa]["row_order"]
    pw = {(p["linha"], p["coluna"]): p for p in seg[fw]["poses"]}
    pa = {(p["linha"], p["coluna"]): p for p in seg[fa]["poses"]}
    r_lado_w = ow.index("right"); r_idle = oa.index("idle_blink")
    # se a caminhada lateral foi gerada pelo esqueleto (a partir das acoes), a escala da folha de
    # caminhada vem da altura lateral ORIGINAL guardada pelo rig_patas.py
    h_lado_w = seg[fw].get("h_lado_original") or np.median([pw[(r_lado_w, c)]["h"] for c in range(8)])
    rigados = sorted({ow[p["linha"]] for p in seg[fw]["poses"] if p.get("gerado_por_rig")})
    h_idle_a = np.median([pa[(r_idle, c)]["h"] for c in range(6)])
    fator = {"walk": alvo / h_lado_w, "actions": alvo / h_idle_a}
    # ---- ancoras (px da folha): x do corpo e y da base, por pose ----
    poses = []   # (tipo, nome_anim, quadro, arr, ax, by)
    for tipo, ordem, P, ncol in [("walk", ow, pw, 8), ("actions", oa, pa, 6)]:
        for ri, nome in enumerate(ordem):
            arrs = [carrega(P[(ri, c)]["arquivo"]) for c in range(ncol)]
            als = [a[..., 3] > 127 for a in arrs]
            bys = [base_y(al) for al in als]
            if tipo == "walk":
                ref_m = faixa(als[0], 0.0, 0.62)          # tronco + cabeca
                movs = [faixa(al, 0.0, 0.62) for al in als]
            else:
                ref_m = None
            dxs, scores = [], []
            rig_linha = tipo == "walk" and all(P[(ri, c)].get("gerado_por_rig") for c in range(ncol))
            if rig_linha:
                # quadros do esqueleto: mesmo recorte e corpo identico -> sem realinhar (preserva o
                # gingado e evita o corpo "afundar" quando o pe mais baixo levanta)
                bys = [max(bys)] * ncol
            for c in range(ncol):
                if rig_linha:
                    dxs.append(0); scores.append(1.0); continue
                if tipo == "walk":
                    dx, sc = melhor_dx(ref_m, movs[c], bys[0], bys[c])
                else:
                    if c == 0 and nome == "idle_blink":
                        dx, sc = 0, 1.0
                    else:
                        # patas (faixa de baixo) contra o 1o quadro de respirar/piscar
                        ref_arr = carrega(pa[(r_idle, 0)]["arquivo"]); ref_al = ref_arr[..., 3] > 127
                        dx, sc = melhor_dx(faixa(ref_al, 0.72, 1.0), faixa(als[c], 0.72, 1.0), base_y(ref_al), bys[c])
                dxs.append(dx); scores.append(round(float(sc), 3))
            # x de referencia do quadro 0 da linha: centro do tronco (faixa 30%-70%)
            m0 = faixa(als[0], 0.30, 0.70); xs0 = np.where(m0.any(0))[0]
            ax0 = (xs0.min() + xs0.max()) / 2
            if tipo == "actions":
                ref_al = carrega(pa[(r_idle, 0)]["arquivo"])[..., 3] > 127
                mr = faixa(ref_al, 0.30, 0.70); xr = np.where(mr.any(0))[0]
                ax0 = (xr.min() + xr.max()) / 2
            for c in range(ncol):
                esc = P[(ri, c)].get("escala_da_folha", tipo)
                poses.append(dict(tipo=tipo, escala=esc, anim=nome, q=c, arr=arrs[c], ax=ax0 - dxs[c], by=bys[c], score=scores[c]))
    # ---- encaixe andar -> parado: desloca TODAS as acoes para a silhueta do respirar casar com a
    #      caminhada para a direita (evita o "pulo" quando o animal para e vira acao) ----
    def mascara_final(p):
        f = fator[p["escala"]]; al = p["arr"][..., 3] > 127
        h, w = al.shape; img = Image.fromarray((al * 255).astype(np.uint8))
        m = np.asarray(img.resize((max(1, round(w * f)), max(1, round(h * f))), Image.BOX)) > 127
        return m, p["ax"] * f, p["by"] * f
    def no_canvas(m, ax, by, cw=200, ch=200, cx=100, cy=180):
        c = np.zeros((ch, cw), bool); ox, oy = int(round(cx - ax)), int(round(cy - by))
        c[oy:oy + m.shape[0], ox:ox + m.shape[1]] = m; return c
    walk_dir = [p for p in poses if p["tipo"] == "walk" and p["anim"] == "right"]
    idle0 = [p for p in poses if p["tipo"] == "actions" and p["anim"] == "idle_blink" and p["q"] == 0][0]
    mi = no_canvas(*mascara_final(idle0))
    melhor = (0.0, 0)
    for pw_ in walk_dir:
        mw = no_canvas(*mascara_final(pw_))
        for dx in range(-8, 9):
            s_ = (np.roll(mw, dx, 1) & mi).sum() / (np.roll(mw, dx, 1) | mi).sum()
            if s_ > melhor[0]: melhor = (s_, dx)
    encaixe_px = -melhor[1]                   # px finais para deslocar as acoes
    for p in poses:
        if p["tipo"] == "actions": p["ax"] -= encaixe_px / fator["actions"]
    # ---- canvas comum (px finais) ----
    ext = []
    for p in poses:
        f = fator[p["escala"]]; h, w = p["arr"].shape[:2]
        ext.append(((0 - p["ax"]) * f, (w - p["ax"]) * f, (0 - p["by"]) * f, (h - p["by"]) * f))
    L = int(np.floor(min(e[0] for e in ext))) - 1; Rr = int(np.ceil(max(e[1] for e in ext))) + 1
    T = int(np.floor(min(e[2] for e in ext))) - 1; Bm = 2
    W, H = Rr - L, Bm - T
    W += W % 2; px, py = -L, -T          # pivot dentro do canvas (pes no chao)
    # ---- reduz cada pose: posiciona no canvas da folha com o pivot fixo e reduz o canvas inteiro ----
    finais = []
    for p in poses:
        f = fator[p["escala"]]
        Ws, Hs = int(round(W / f)), int(round(H / f))
        src = Image.new("RGBA", (Ws, Hs), (0, 0, 0, 0))
        ox = int(round(px / f - p["ax"])); oy = int(round(py / f - p["by"] - 1))
        src.alpha_composite(Image.fromarray(p["arr"], "RGBA"), (ox, oy))
        red = src.convert("RGBa").resize((W, H), Image.BOX).convert("RGBA")
        a = np.asarray(red).copy()
        a[..., 3] = np.where(a[..., 3] >= 128, 255, 0)
        finais.append(a)
    # ---- paleta fixa da especie ----
    todos = np.concatenate([a[a[..., 3] == 255][:, :3] for a in finais])
    amostra = Image.fromarray(todos.reshape(-1, 1, 3).astype(np.uint8), "RGB")
    pal_img = amostra.quantize(colors=cfg[esp]["cores"], method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pal = np.array(pal_img.getpalette()[:3 * cfg[esp]["cores"]]).reshape(-1, 3)
    def mapeia(rgb):
        d = ((rgb[:, None, :].astype(int) - pal[None]) ** 2).sum(-1); return pal[d.argmin(1)]
    out_esp = os.path.join(OUT, esp); os.makedirs(out_esp, exist_ok=True)
    quadros = []
    for p, a in zip(poses, finais):
        al = a[..., 3] == 255
        rgb = a[..., :3].astype(float)
        if cfg["contorno"]["aplicar"]:
            borda = al & ndi.binary_dilation(~al, structure=[[0, 1, 0], [1, 1, 1], [0, 1, 0]])
            rgb[borda] *= cfg["contorno"]["escurecer"]
        out = np.zeros_like(a)
        out[al, :3] = mapeia(rgb[al].round().clip(0, 255).astype(np.uint8))
        out[al, 3] = 255
        nome = f"{esp}_{p['tipo']}_{p['anim']}_{p['q']}.png"
        Image.fromarray(out, "RGBA").save(os.path.join(out_esp, nome))
        quadros.append(dict(arquivo=nome, tipo=p["tipo"], anim=p["anim"], quadro=p["q"], ajuste_score=p["score"]))
    relatorio[esp] = dict(canvas=[W, H], pivot=[px, py], fator_reducao=dict(walk=round(fator["walk"], 4), actions=round(fator["actions"], 4)),
                          diferenca_escala_entre_folhas=round(fator["walk"] / fator["actions"], 3),
                          encaixe_acoes_px=int(encaixe_px), encaixe_iou=round(float(melhor[0]), 3),
                          caminhada_gerada_por_esqueleto=rigados,
                          altura_lado_px=alvo, cores=len(pal), quadros=quadros)
    print(f"{esp}: encaixe acoes {encaixe_px:+d} px (IoU {melhor[0]:.2f}) | canvas {W}x{H} pivot ({px},{py}) fator walk {fator['walk']:.4f} actions {fator['actions']:.4f} (walk/actions {fator['walk']/fator['actions']:.3f})")
json.dump(relatorio, open(os.path.join(OUT, "preparo.json"), "w"), indent=1, ensure_ascii=False)
