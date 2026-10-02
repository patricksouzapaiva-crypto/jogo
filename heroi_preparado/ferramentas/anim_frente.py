"""Andar do heroi de FRENTE (vindo para a camera), com o mesmo esqueleto do lado.

Da pose de frente separa: corpo (cabeca + tronco + cintura), os dois bracos e as duas pernas
(calca + bota). Visto de frente as pernas nao giram: a perna que da o passo dobra o joelho para a
camera e por isso fica mais curta (a coxa encurta mais que a canela), o pe sobe e depois pisa um
pouco mais para baixo na tela. A bota e colada sempre na barra da calca (nunca abre vao).
Os bracos balancam ao contrario das pernas: o que vai para a frente desce um pouco e fica na frente
de tudo; o que vai para tras sobe e entra um pouco atras do quadril.
"""
import json, math, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig_heroi as R
import anim_lado as L

AQUI = os.path.dirname(os.path.abspath(__file__))
FONTE = os.path.join(AQUI, "..", "fonte", "frente.png")
SAIDA = os.path.join(AQUI, "..", "revisao", "frente")

CHAO = 583            # linha da sola
MEIO = 150            # meio entre as pernas (pivo x)
CINTURA = 362         # fim da faixa da cintura (as pernas comecam embaixo dela)
JOELHO_Y = 437
BARRA_Y = 512         # barra da calca / topo da bota
OMBRO_Y = 255         # o braco comeca a se mexer abaixo do ombro
PUNHO_Y = 292         # do punho para baixo o braco se mexe inteiro

# ciclo de 8 quadros (mesmo ritmo do lado). A perna da esquerda da imagem (perna direita do heroi,
# a mesma que fica "de perto" na vista de lado) usa o quadro k; a outra usa k+4.
# (profundidade: + = pe mais para baixo na tela / mais perto da camera; altura do pe)  em px do desenho
PE = [
    (+13, 0),    # 0 contato na frente
    (+7, 0),     # 1 recebe o peso
    (0, 0),      # 2 passagem (apoio embaixo do corpo)
    (-7, 0),     # 3 impulso
    (-13, 0),    # 4 pe de tras, so a ponta no chao
    (-9, 18),    # 5 pe sai do chao, joelho dobra para a camera
    (0, 27),     # 6 passagem no ar (pe mais alto)
    (+9, 12),    # 7 perna vai para a frente
]
BOTA_ALTURA = [1.0, 1.0, 1.0, 1.0, 0.94, 0.88, 0.92, 1.0]   # bota "inclinada" (ponta para baixo) parece mais baixa
SOBE_DESCE = L.SOBE_DESCE                                 # 1, 2, 1, 0 px do jogo
COXA_PARTE = 0.7                                          # quanto do encurtamento fica na coxa
BRACO_DESCE = 12                                          # px do desenho que a mao desce/sobe no balanco
BRACO_LADO = 4                                            # px que a mao vai para fora (frente) / para dentro (tras)
DURACAO_MS = L.DURACAO_MS
PAD_X, PAD_TOP = 60, 40


def carrega():
    a = np.array(Image.open(FONTE).convert("RGBA")).astype(np.int32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mag = (a[..., 3] > 0) & (r > 120) & (b > g + 20) & (g < 0.45 * r)
    a[mag, :3] = (26, 6, 6)
    return a


def separa(a):
    H, W = a.shape[:2]
    al = a[..., 3] > 0
    yy, xx = np.mgrid[0:H, 0:W]
    # bracos: tudo que fica fora do tronco/calca, do ombro para baixo
    esq = al & (yy >= 238) & (yy < 432) & (((yy < 330) & (xx < 86)) | ((yy >= 330) & (xx < 80)))
    dir_ = al & (yy >= 238) & (yy < 432) & (((yy < 330) & (xx > 219)) | ((yy >= 330) & (xx > 225)))
    # fica so o pedaco ligado (tira lascas)
    def maior(m):
        lab, n = ndi.label(m)
        if n <= 1:
            return m
        tam = ndi.sum(np.ones_like(lab), lab, index=range(1, n + 1))
        return lab == (1 + int(np.argmax(tam)))
    esq, dir_ = maior(esq), maior(dir_)
    bracos = esq | dir_
    # corpo: acima do fim da cintura, sem os bracos (a manga perto do tronco fica no corpo tambem)
    corpo = a.copy()
    tronco = (xx >= 84) & (xx <= 221)
    corpo[(yy >= CINTURA) | (bracos & ~tronco)] = 0
    # pernas: da cintura para baixo, sem os bracos
    pernas = al & (yy >= CINTURA - 4) & ~bracos & (xx >= 30) & (xx <= 270)
    perna_e = a.copy(); perna_e[~(pernas & (xx < MEIO))] = 0
    perna_d = a.copy(); perna_d[~(pernas & (xx >= MEIO))] = 0
    for p in (perna_e, perna_d):
        # completa para cima (fica escondido embaixo da cintura) para a perna poder encurtar sem buraco
        for y in range(300, CINTURA + 4):
            p[y] = p[CINTURA + 8]
    braco_e = a.copy(); braco_e[~esq] = 0
    braco_d = a.copy(); braco_d[~dir_] = 0
    return dict(corpo=corpo, braco_e=braco_e, braco_d=braco_d, perna_e=perna_e, perna_d=perna_d,
                m_bracos=bracos, m_pernas=pernas)


class RigFrente:
    def __init__(self):
        self.a = carrega()
        self.p = separa(self.a)
        self.H, self.W = self.a.shape[:2]
        self.CW, self.CH = self.W + 2 * PAD_X, self.H + PAD_TOP + 20
        self.off = np.array([PAD_X, PAD_TOP])

    def perna(self, lado, k, bob):
        """Calca + bota de um lado, ja na posicao do quadro k (no espaco do canvas)."""
        tmpl = self.p["perna_e" if lado == "e" else "perna_d"]
        prof, alt = PE[k % 8]
        topo_bota = BARRA_Y + prof - alt              # onde a barra da calca encosta na bota
        quadril = CINTURA + bob
        comp = topo_bota - quadril
        if comp > BARRA_Y - CINTURA:                  # nunca estica a perna
            comp = BARRA_Y - CINTURA
            topo_bota = quadril + comp
        encurta = (BARRA_Y - CINTURA) - comp
        coxa = (JOELHO_Y - CINTURA) - COXA_PARTE * encurta
        canela = (BARRA_Y - JOELHO_Y) - (1 - COXA_PARTE) * encurta
        cam = np.zeros((self.CH, self.CW, 4), np.int32)
        ox, oy = self.off
        # linha de destino -> linha do desenho
        sb = BOTA_ALTURA[k % 8]
        alt_bota = CHAO + 1 - BARRA_Y
        y_fim = int(math.ceil(topo_bota + alt_bota * sb))
        for yd in range(300 + bob, y_fim):
            if yd < quadril:
                ys = yd - bob
            elif yd < quadril + coxa:
                ys = CINTURA + (yd - quadril) * (JOELHO_Y - CINTURA) / coxa
            elif yd < topo_bota:
                ys = JOELHO_Y + (yd - quadril - coxa) * (BARRA_Y - JOELHO_Y) / canela
            else:
                ys = BARRA_Y + (yd - topo_bota) / sb
            ys = int(math.floor(ys + 0.5))
            if 0 <= ys < self.H:
                linha = tmpl[ys]
                m = linha[:, 3] > 0
                cam[oy + yd, ox:ox + self.W][m] = linha[m]
        return cam

    def braco(self, lado, a_balanco, bob):
        """Braco deformado: abaixo do ombro vai descendo/subindo ate o punho; do punho para baixo
        anda inteiro. a_balanco: +1 = todo para a frente (desce, vai para fora), -1 = para tras."""
        tmpl = self.p["braco_e" if lado == "e" else "braco_d"]
        dy_max = a_balanco * BRACO_DESCE
        fora = -1 if lado == "e" else 1
        dx_max = fora * a_balanco * BRACO_LADO
        cam = np.zeros((self.CH, self.CW, 4), np.int32)
        ox, oy = self.off
        ys, xs = np.nonzero(tmpl[..., 3] > 0)
        cores = tmpl[ys, xs]
        for sub in (1 / 6, 0.5, 5 / 6):
            yf = ys + sub
            t = np.clip((yf - OMBRO_Y) / (PUNHO_Y - OMBRO_Y), 0, 1)
            t = t * t * (3 - 2 * t)
            Y = np.floor(yf + bob + dy_max * t).astype(int) + oy
            X = np.floor(xs + 0.5 + dx_max * t).astype(int) + ox
            ok = (Y >= 0) & (Y < self.CH) & (X >= 0) & (X < self.CW)
            cam[Y[ok], X[ok]] = cores[ok]
        return cam

    def quadro(self, k):
        bob = SOBE_DESCE[k % 8]
        dst = np.zeros((self.CH, self.CW, 4), np.int32)
        # balanco dos bracos: o braco da esquerda da imagem vai para tras quando a perna da esquerda vai para a frente
        a_e = -math.cos(2 * math.pi * (k - 0.5) / 8)
        a_d = -a_e
        bracos = {"e": self.braco("e", a_e, bob), "d": self.braco("d", a_d, bob)}
        atras = [l for l, a in (("e", a_e), ("d", a_d)) if a < 0]
        frente = [l for l, a in (("e", a_e), ("d", a_d)) if a >= 0]
        for l in atras:
            L.cola(dst, bracos[l])
        # pernas: a que esta mais perto da camera (pe mais para baixo) por cima
        pe_e, pe_d = PE[k % 8][0], PE[(k + 4) % 8][0]
        ordem = [("e", k), ("d", k + 4)] if pe_e <= pe_d else [("d", k + 4), ("e", k)]
        for lado, kk in ordem:
            L.cola(dst, self.perna(lado, kk, bob))
        corpo = np.zeros_like(dst)
        corpo[self.off[1] + bob:self.off[1] + bob + self.H, self.off[0]:self.off[0] + self.W] = self.p["corpo"]
        L.cola(dst, corpo)
        for l in frente:
            L.cola(dst, bracos[l])
        return dst

    def parado(self):
        dst = np.zeros((self.CH, self.CW, 4), np.int32)
        dst[self.off[1]:self.off[1] + self.H, self.off[0]:self.off[0] + self.W] = self.a
        return dst


if __name__ == "__main__":
    os.makedirs(SAIDA, exist_ok=True)
    rig = RigFrente()
    grandes = [rig.quadro(k) for k in range(8)]
    finais, pivot = L.reduz([rig.parado()] + grandes, rig, pivo=(MEIO, CHAO))
    for i, f in enumerate(finais):
        Image.fromarray(f, "RGBA").save(os.path.join(SAIDA, ("parado" if i == 0 else f"andar_{i-1}") + ".png"))
    if "--grande" in sys.argv:
        for k, f in enumerate(grandes):
            Image.fromarray(f.clip(0, 255).astype(np.uint8), "RGBA").save(os.path.join(SAIDA, f"grande_{k}.png"))
    json.dump(dict(pivot=pivot, tamanho=list(finais[0].shape[1::-1]), duracao_ms=DURACAO_MS, direcao="frente"),
              open(os.path.join(SAIDA, "info.json"), "w"))
    print("quadro final", finais[0].shape[1::-1], "pivot", pivot)
