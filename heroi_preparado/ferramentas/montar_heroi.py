"""Monta o pacote final do heroi para o Godot.

1. Gera os quadros das 4 direcoes com os esqueletos aprovados (lado, lado_esq, frente, costas).
2. Parado respirando: 2 quadros por direcao. O primeiro e o desenho original (parado); no segundo
   cabeca, tronco e bracos descem 1 px (9 px do desenho) e as pernas ficam paradas.
3. Uma paleta so (32 cores) para as 4 direcoes: as cores ficam exatamente iguais quando ele vira.
4. Junta tudo numa folha (atlas) com celulas do mesmo tamanho e o pivo (meio dos pes) no mesmo
   ponto de todas as celulas, mais o JSON com animacoes, duracoes e velocidade.

Uso: python3 montar_heroi.py
Saidas: revisao/<direcao>/ (quadros soltos), JogoFazenda/arte/preparado/heroi/ (atlas + JSON).
"""
import json, os, sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lado as L
import rig_heroi as R
import rig_heroi_esq as RE
import anim_frente as F
import anim_costas as C

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.join(AQUI, "..")
REV = os.path.join(RAIZ, "revisao")
GODOT_ARTE = os.path.join(RAIZ, "JogoFazenda", "arte", "preparado", "heroi")

RESPIRA = 9                       # 1 px do jogo
DUR_PARADO = [0.8, 0.7]           # inspira (mais longo) / expira, em segundos
DUR_ANDAR = L.DURACAO_MS / 1000
VELOCIDADE = 47                   # px do jogo por segundo: com 75 ms por quadro os pes nao escorregam
CORES = 32
ORDEM = ["down", "left", "right", "up"]
PASTA = {"right": "lado", "left": "lado_esq", "down": "frente", "up": "costas"}


def respira(rig, cintura, mascara_braco, d):
    """Cabeca + tronco + bracos descem d px; da cintura para baixo (pernas) fica parado."""
    a = rig.a
    H, W = a.shape[:2]
    yy = np.mgrid[0:H, 0:W][0]
    dst = np.zeros((rig.CH, rig.CW, 4), np.int32)
    ox, oy = rig.off
    baixo = a.copy(); baixo[yy < cintura] = 0
    cima = a.copy(); cima[~((yy < cintura) | mascara_braco)] = 0
    for camada, dy in ((baixo, 0), (cima, d)):
        reg = dst[oy + dy:oy + dy + H, ox:ox + W]
        m = camada[..., 3] > 0
        reg[m] = camada[m]
    return dst


def direcoes():
    """Para cada direcao: quadros grandes [parado, respira, andar 0..7], pivo e se precisa desvirar."""
    saida = {}
    for nome, rig, pivo, cintura, mascara, virar in (
            ("right", L.Rig(), (R.QUADRIL[0], R.CHAO), R.QUADRIL[1], "mascara_braco", False),
            ("left", L.Rig(RE), (RE.QUADRIL[0], RE.CHAO), RE.QUADRIL[1], "mascara_braco", True),
            ("down", F.RigFrente(), None, None, "m_bracos", False),
            ("up", C.RigCostas(), None, None, "m_bracos", False)):
        if pivo is None:
            pivo, cintura = (rig.MEIO, rig.CHAO), rig.CINTURA
        andar = []
        for k in range(8):
            q = rig.quadro(k)
            andar.append(q[0] if isinstance(q, tuple) else q)
        grandes = [rig.parado(), respira(rig, cintura, rig.p[mascara], RESPIRA)] + andar
        red, pv = L.reduz_box(grandes, rig, pivo)
        if virar:
            red = [np.ascontiguousarray(r[:, ::-1]) for r in red]
            pv = (red[0].shape[1] - 1 - pv[0], pv[1])
        saida[nome] = dict(red=red, pivot=pv)
        print(f"{nome}: quadro {red[0].shape[1]}x{red[0].shape[0]} pivo {pv}")
    return saida


def caixa_util(quadros, pv):
    """Extensao do desenho em volta do pivo: (esq, dir, cima, baixo)."""
    e = d = c = b = 0
    for q in quadros:
        ys, xs = np.nonzero(q[..., 3] > 0)
        e = max(e, pv[0] - xs.min()); d = max(d, xs.max() + 1 - pv[0])
        c = max(c, pv[1] - ys.min()); b = max(b, ys.max() + 1 - pv[1])
    return e, d, c, b


def parecido(a, b):
    ma, mb = a[..., 3] > 0, b[..., 3] > 0
    return (ma & mb).sum() / max(1, (ma | mb).sum())


if __name__ == "__main__":
    dados = direcoes()
    # ---- paleta unica ----
    todos = [r for d in dados.values() for r in d["red"]]
    pal = L.paleta(todos, CORES)
    for nome, d in dados.items():
        d["final"] = L.aplica_paleta(d["red"], pal)
    # ---- quadros soltos (revisao) ----
    for nome, d in dados.items():
        pasta = os.path.join(REV, PASTA[nome]); os.makedirs(pasta, exist_ok=True)
        f = d["final"]
        Image.fromarray(f[0], "RGBA").save(os.path.join(pasta, "parado.png"))
        Image.fromarray(f[1], "RGBA").save(os.path.join(pasta, "respirar_1.png"))
        for k in range(8):
            Image.fromarray(f[2 + k], "RGBA").save(os.path.join(pasta, f"andar_{k}.png"))
        info = json.load(open(os.path.join(pasta, "info.json"))) if os.path.exists(os.path.join(pasta, "info.json")) else {}
        info.update(pivot=list(d["pivot"]), tamanho=list(f[0].shape[1::-1]), duracao_ms=L.DURACAO_MS, paleta="unica (4 direcoes)")
        json.dump(info, open(os.path.join(pasta, "info.json"), "w"))
    # ---- celula comum ----
    ext = [caixa_util(d["final"], d["pivot"]) for d in dados.values()]
    esq = max(e[0] for e in ext); dir_ = max(e[1] for e in ext); cima = max(e[2] for e in ext)
    meia = max(esq, dir_)
    cw = max(48, 2 * meia + (2 * meia) % 2)
    ch = max(72, cima + 3)
    piv = (cw // 2, ch - 3)                      # pivo da celula: meio embaixo (3 px de folga embaixo)
    linhas = [("walk", n) for n in ORDEM] + [("idle", n) for n in ORDEM]
    atlas = np.zeros((ch * len(linhas), cw * 8, 4), np.uint8)
    anim = {}
    for li, (tipo, n) in enumerate(linhas):
        d = dados[n]
        quadros = d["final"][2:] if tipo == "walk" else d["final"][:2]
        for i, q in enumerate(quadros):
            ys, xs = np.nonzero(q[..., 3] > 0)                 # cola so a parte desenhada
            y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
            x = i * cw + piv[0] - d["pivot"][0] + x0; y = li * ch + piv[1] - d["pivot"][1] + y0
            assert i * cw <= x and x + (x1 - x0) <= (i + 1) * cw and li * ch <= y and y + (y1 - y0) <= (li + 1) * ch
            parte = q[y0:y1, x0:x1]
            reg = atlas[y:y + parte.shape[0], x:x + parte.shape[1]]
            m = parte[..., 3] > 0
            reg[m] = parte[m]
        if tipo == "walk":
            semelhanca = [parecido(d["final"][0], q) for q in quadros]
            inicio = (int(np.argmax(semelhanca)) + 1) % 8
            anim[f"walk_{n}"] = dict(linha=li, quadros=8, duracoes=[DUR_ANDAR] * 8, loop=True, inicio=inicio)
        else:
            anim[f"idle_{n}"] = dict(linha=li, quadros=2, duracoes=DUR_PARADO, loop=True)
    os.makedirs(GODOT_ARTE, exist_ok=True)
    Image.fromarray(atlas, "RGBA").save(os.path.join(GODOT_ARTE, "heroi_atlas.png"))
    json.dump(dict(nome="heroi", versao="v1", atlas="heroi_atlas.png", celula=[cw, ch], pivot=list(piv),
                   altura_px=int(cima), velocidade_andar_px_s=VELOCIDADE, duracao_quadro_andar_s=DUR_ANDAR,
                   ordem_linhas=[f"{t}_{n}" for t, n in linhas], animacoes=anim,
                   paleta=[[int(c) for c in cor] for cor in pal],
                   observacao="pivot = ponto do chao entre os pes; use offset = -pivot com centered = false"),
              open(os.path.join(GODOT_ARTE, "heroi.json"), "w"), indent=1)
    print(f"atlas {atlas.shape[1]}x{atlas.shape[0]}  celula {cw}x{ch}  pivo {piv}  altura {cima} px  cores {len(pal)}")
    print("inicio do andar (quadro depois do mais parecido com o parado):", {k: v.get("inicio") for k, v in anim.items() if "inicio" in v})
