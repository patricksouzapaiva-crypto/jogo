"""Gera o andar do heroi na vista de lado (direita) com o esqueleto do rig_heroi.py."""
import json, math, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig_heroi as R

# ------------------------------------------------------------------ ciclo de 8 quadros
# perna de perto; a perna de longe usa o quadro k+4.
# (pe_x em relacao ao quadril, angulo da bota em graus (+ = ponta para cima), altura do pe)
PE = [
    (+66, +14, 0),    # 0 contato: calcanhar toca o chao na frente
    (+34, 0, 0),      # 1 recebe o peso (corpo no ponto mais baixo)
    (+2, 0, 0),       # 2 passagem: perna de apoio embaixo do corpo
    (-30, -6, 0),     # 3 impulso: calcanhar comeca a subir
    (-62, -18, 0),    # 4 contato da outra perna: so a ponta do pe no chao
    (-58, -34, 24),   # 5 pe sai do chao, joelho dobra
    (-4, -14, 40),    # 6 passagem no ar
    (+48, +4, 22),    # 7 perna estica para a frente
]
SOBE_DESCE = [9, 18, 9, 0, 9, 18, 9, 0]      # px do desenho (9 = 1 px no jogo), + = desce
BRACO_AMPL = 20                               # graus do ombro
DURACAO_MS = 75
LONGE_ESCURECE = 0.72
LONGE_ESCURECE_BRACO = 0.62
LONGE_DESLOCA = (-3, -6)                      # perna/braco de longe um pouco atras e acima


def rot(t):
    c, s = math.cos(t), math.sin(t)
    return np.array([[c, s], [-s, c]])


def coloca(dst, peca, piv0, piv1, graus):
    """Gira 'peca' (RGBA no espaco do desenho) em volta de piv0 e cola com piv0 em piv1 (espaco do canvas)."""
    m = peca[..., 3] > 0
    if not m.any():
        return
    ys, xs = np.nonzero(m)
    Rm = rot(math.radians(graus))
    cant = np.array([[xs.min(), ys.min()], [xs.max(), ys.min()], [xs.min(), ys.max()], [xs.max(), ys.max()]], float) - piv0
    novos = cant @ Rm.T + piv1
    x0, y0 = np.floor(novos.min(0)).astype(int) - 1
    x1, y1 = np.ceil(novos.max(0)).astype(int) + 2
    x0, y0 = max(x0, 0), max(y0, 0)
    x1, y1 = min(x1, dst.shape[1]), min(y1, dst.shape[0])
    gy, gx = np.mgrid[y0:y1, x0:x1]
    q = np.stack([gx + 0.5 - piv1[0], gy + 0.5 - piv1[1]], -1) @ np.linalg.inv(Rm).T + piv0
    sx = np.floor(q[..., 0]).astype(int); sy = np.floor(q[..., 1]).astype(int)
    ok = (sx >= 0) & (sy >= 0) & (sx < peca.shape[1]) & (sy < peca.shape[0])
    sx = sx.clip(0, peca.shape[1] - 1); sy = sy.clip(0, peca.shape[0] - 1)
    src = peca[sy, sx]
    ok &= src[..., 3] > 0
    reg = dst[y0:y1, x0:x1]
    reg[ok] = src[ok]


def coloca_canela(dst, peca, K0, K1, canela_graus, bota_graus, y_tornozelo, faixa=30):
    """Cola a canela girada em volta do joelho, mas a barra da calca (ultimos 'faixa' px) vai virando
    ate ficar no angulo da bota: assim a barra sempre encosta no cano da bota, sem abrir vao."""
    ys, xs = np.nonzero(peca[..., 3] > 0)
    cores = peca[ys, xs]
    tc = math.radians(canela_graus)
    for oy in (1 / 6, 0.5, 5 / 6):
        for ox in (1 / 6, 0.5, 5 / 6):
            u = xs + ox - K0[0]
            v = ys + oy - K0[1]
            t = np.clip((ys + oy - (y_tornozelo - faixa)) / faixa, 0, 1)
            t = t * t * (3 - 2 * t)
            th = np.radians(canela_graus + (bota_graus - canela_graus) * t)
            X = K1[0] + v * math.sin(tc) + u * np.cos(th)
            Y = K1[1] + v * math.cos(tc) - u * np.sin(th)
            X = np.floor(X).astype(int); Y = np.floor(Y).astype(int)
            ok = (X >= 0) & (Y >= 0) & (X < dst.shape[1]) & (Y < dst.shape[0])
            dst[Y[ok], X[ok]] = cores[ok]


def ik(H, A, l1, l2):
    d = np.subtract(A, H).astype(float)
    dist = math.hypot(*d)
    esticou = 0.0
    if dist > (l1 + l2) * 0.999:
        esticou = dist - (l1 + l2) * 0.999
        d *= (l1 + l2) * 0.999 / dist; dist = (l1 + l2) * 0.999
        A = np.add(H, d)
    g = math.atan2(d[0], d[1])
    b = math.acos(max(-1, min(1, (l1 * l1 + dist * dist - l2 * l2) / (2 * l1 * dist))))
    tc = g + b
    K = np.add(H, (l1 * math.sin(tc), l1 * math.cos(tc)))
    ts = math.atan2(A[0] - K[0], A[1] - K[1])
    return K, tc, ts, np.asarray(A, float), esticou


CONTORNO = 7


def sem_contorno(rgba, larg):
    """Troca o contorno externo (irregular no desenho) pela cor de dentro; o contorno e refeito
    depois de montar a perna, com espessura uniforme e sem linhas no meio das juntas."""
    m = rgba[..., 3] > 0
    faixa = m & ~ndi.binary_erosion(m, iterations=larg + 2)
    esc = rgba[..., :3].sum(2) < R.ESCURO
    ruim = faixa & esc
    bom = m & ~ruim
    _, (iy, ix) = ndi.distance_transform_edt(~bom, return_indices=True)
    o = rgba.copy()
    o[ruim] = rgba[iy[ruim], ix[ruim]]
    return o


def contorna(rgba, larg=CONTORNO):
    m = rgba[..., 3] > 0
    borda = m & ~ndi.binary_erosion(m, iterations=larg)
    claro = rgba[..., :3].sum(2) >= R.ESCURO
    rgba[borda & claro, :3] = (22, 8, 6)


class Rig:
    def __init__(self, medidas=None):
        # medidas = modulo com as medidas do desenho (padrao: rig_heroi, lado direito)
        self.R = medidas or R
        self.a = self.R.carrega()
        p = self.R.separa(self.a)
        self.p = p
        H, W = self.a.shape[:2]
        yy, xx = np.mgrid[0:H, 0:W]
        perna = p["perna"].copy()
        m = ndi.binary_opening(perna[..., 3] > 0, iterations=3)      # tira lascas finas (restos da outra bota)
        m = ndi.binary_fill_holes(m)
        perna[~m] = 0
        perna = sem_contorno(perna, CONTORNO)
        jx, jy = self.R.JOELHO
        tampa = (xx - jx) ** 2 + (yy - jy) ** 2 <= 37 ** 2
        self.coxa = perna.copy(); self.coxa[~((yy <= jy) | tampa)] = 0
        self.canela = perna.copy(); self.canela[~(((yy >= jy) | tampa) & (yy < self.R.TORNOZELO[1] + 4))] = 0
        self.bota = perna.copy(); self.bota[yy < self.R.TORNOZELO[1]] = 0
        self.l1 = self.R.JOELHO[1] - self.R.QUADRIL[1]
        self.l2 = self.R.TORNOZELO[1] - self.R.JOELHO[1]
        by, bx = np.nonzero(self.bota[..., 3] > 0)
        self.bota_pts = np.stack([bx + 0.5, by + 0.5], -1) - np.array(self.R.TORNOZELO)
        self.W, self.H = W, H
        self.CW, self.CH = W + 2 * self.R.PAD_X, H + self.R.PAD_TOP + 20
        self.off = np.array([self.R.PAD_X, self.R.PAD_TOP])

    def escurece(self, rgba, f):
        o = rgba.copy()
        o[..., :3] = (o[..., :3] * f).astype(np.int32)
        return o

    def bota_altura(self, graus):
        Rm = rot(math.radians(graus))
        return (self.bota_pts @ Rm.T)[:, 1].max()

    def perna(self, dst, H, pe, escurecer=None):
        dx, ang, lift = pe
        A = np.array([H[0] + dx, self.R.CHAO + self.off[1] - self.bota_altura(ang) - lift])
        K, tc, ts, A, est = ik(H, A, self.l1, self.l2)
        camada = np.zeros_like(dst)
        coloca(camada, self.bota, np.array(self.R.TORNOZELO, float), A, ang)
        coloca_canela(camada, self.canela, np.array(self.R.JOELHO, float), K, math.degrees(ts), ang, self.R.TORNOZELO[1])
        coloca(camada, self.coxa, np.array(self.R.QUADRIL, float), H, math.degrees(tc))
        contorna(camada)
        if escurecer:
            claro = camada[..., :3].sum(2) >= self.R.ESCURO
            camada[claro, :3] = (camada[claro, :3] * escurecer).astype(np.int32)
        return camada, est

    def braco(self, dst, desl, tu, tf, escurecer=None):
        S = np.array(self.R.OMBRO, float); E0 = np.array(self.R.COTOVELO, float)
        S1 = S + self.off + desl
        E1 = S1 + rot(math.radians(tu)) @ (E0 - S)
        camada = np.zeros_like(dst)
        sup, ant = self.p["braco_sup"], self.p["antebraco"]
        coloca(camada, sup, S, S1, tu)
        coloca(camada, ant, E0, E1, tu + tf)
        if escurecer:
            claro = camada[..., :3].sum(2) >= self.R.ESCURO
            camada[claro, :3] = (camada[claro, :3] * escurecer).astype(np.int32)
        return camada

    def quadro(self, k):
        dst = np.zeros((self.CH, self.CW, 4), np.int32)
        bob = SOBE_DESCE[k % 8]
        H = np.array(self.R.QUADRIL, float) + self.off + (0, bob)
        tu = lambda kk: -BRACO_AMPL * math.cos(2 * math.pi * (kk - 0.5) / 8)
        tf = lambda t: 8 + 24 * max(0.0, t / BRACO_AMPL)
        # braco de longe (atras de tudo)
        # (so aparece quando vai para a frente; quando vai para tras fica escondido pelo tronco)
        t_l = tu(k + 4)
        if t_l > 4:
            cam = self.braco(dst, np.array((3, bob)), t_l, tf(t_l), LONGE_ESCURECE_BRACO)
            cam[:, :self.off[0] + 150] = 0
            cola(dst, cam)
        # perna de longe
        cam, e1 = self.perna(dst, H + LONGE_DESLOCA, PE[(k + 4) % 8], LONGE_ESCURECE)
        cola(dst, recorta_quadril(cam, self, bob))
        # perna de perto
        cam, e2 = self.perna(dst, H, PE[k % 8])
        cola(dst, recorta_quadril(cam, self, bob))
        # corpo
        cam = np.zeros_like(dst)
        cam[self.off[1] + bob:self.off[1] + bob + self.H, self.off[0]:self.off[0] + self.W] = self.p["corpo"]
        cola(dst, cam)
        # braco de perto
        t_p = tu(k)
        cola(dst, self.braco(dst, np.array((0, bob)), t_p, tf(t_p)))
        return dst, max(e1, e2)

    def parado(self):
        dst = np.zeros((self.CH, self.CW, 4), np.int32)
        dst[self.off[1]:self.off[1] + self.H, self.off[0]:self.off[0] + self.W] = self.a
        return dst


def cola(dst, cam):
    m = cam[..., 3] > 0
    dst[m] = cam[m]


def recorta_quadril(cam, rig, bob):
    """Acima da cintura a perna so pode aparecer dentro da largura do tronco (o resto fica escondido)."""
    y_cint = rig.off[1] + 336 + bob
    x0, x1 = rig.off[0] + 76, rig.off[0] + 194
    cam[:y_cint, :x0] = 0
    cam[:y_cint, x1:] = 0
    cam[:rig.off[1] + 300 + bob] = 0
    return cam


def reduz(frames, rig, cores=32, pivo=None):
    """Reduz 9x com a grade alinhada ao pivot (quadril / chao), paleta fixa e contorno escuro.
    pivo = (x do meio dos pes, linha da sola) no desenho original; padrao = vista de lado."""
    e = R.ESCALA
    pivo_x, chao_y = pivo if pivo else (R.QUADRIL[0], R.CHAO)
    px = pivo_x + rig.off[0]
    chao = chao_y + rig.off[1] + 1
    x0 = px - 4 - e * ((px - 4) // e)
    y0 = chao - e * (chao // e)
    Wf = (rig.CW - x0) // e; Hf = (rig.CH - y0) // e
    red = []
    for f in frames:
        im = Image.fromarray(f.clip(0, 255).astype(np.uint8), "RGBA").crop((x0, y0, x0 + Wf * e, y0 + Hf * e))
        r = np.asarray(im.convert("RGBa").resize((Wf, Hf), Image.BOX).convert("RGBA")).copy()
        r[..., 3] = np.where(r[..., 3] >= 128, 255, 0)
        red.append(r)
    todos = np.concatenate([r[r[..., 3] == 255][:, :3] for r in red])
    amostra = Image.fromarray(todos.reshape(-1, 1, 3).astype(np.uint8), "RGB")
    pal = np.array(amostra.quantize(colors=cores, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).getpalette()[:3 * cores]).reshape(-1, 3)
    out = []
    for r in red:
        al = r[..., 3] == 255
        rgb = r[..., :3].astype(float)
        borda = al & ndi.binary_dilation(~al, structure=[[0, 1, 0], [1, 1, 1], [0, 1, 0]])
        rgb[borda] *= 0.45
        o = np.zeros_like(r)
        d = ((rgb[al][:, None, :] - pal[None]) ** 2).sum(-1)
        o[al, :3] = pal[d.argmin(1)]; o[al, 3] = 255
        out.append(o)
    pivot = (int((px - x0) // e), int((chao - y0) // e))
    return out, pivot


if __name__ == "__main__":
    os.makedirs(R.SAIDA, exist_ok=True)
    rig = Rig()
    grandes, estic = [], []
    for k in range(8):
        f, e = rig.quadro(k); grandes.append(f); estic.append(round(e, 1))
    print("esticamento (px do desenho):", estic)
    finais, pivot = reduz([rig.parado()] + grandes, rig)
    for i, f in enumerate(finais):
        Image.fromarray(f, "RGBA").save(os.path.join(R.SAIDA, ("parado" if i == 0 else f"andar_{i-1}") + ".png"))
    if "--grande" in sys.argv:   # previa na resolucao do desenho (para conferir juntas)
        for k, f in enumerate(grandes):
            Image.fromarray(f.clip(0, 255).astype(np.uint8), "RGBA").save(os.path.join(R.SAIDA, f"grande_{k}.png"))
    json.dump(dict(pivot=pivot, tamanho=list(finais[0].shape[1::-1]), duracao_ms=DURACAO_MS), open(os.path.join(R.SAIDA, "info.json"), "w"))
    print("quadro final", finais[0].shape[1::-1], "pivot", pivot)
