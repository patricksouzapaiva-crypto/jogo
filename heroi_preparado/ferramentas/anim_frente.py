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
    (+12, 0),    # 0 contato na frente
    (+6, 0),     # 1 recebe o peso
    (0, 0),      # 2 passagem (apoio embaixo do corpo)
    (-6, 2),     # 3 impulso: o calcanhar comeca a subir
    (-12, 6),    # 4 so a ponta do pe no chao
    (-8, 18),    # 5 pe sai do chao, joelho vem para a camera
    (0, 24),     # 6 passagem no ar (pe mais alto)
    (+8, 12),    # 7 perna desce para a frente
]
ALTURA_MAX = 24
BOTA_ALTURA = [1.0, 1.0, 1.0, 0.98, 0.94, 0.88, 0.9, 0.97]  # bota "inclinada" (ponta para baixo) parece mais baixa
# Corpo mais calmo que no lado: no maximo 1 px para baixo e 1 px para o lado da perna de apoio, e o
# balanco para o lado vem 1 quadro depois da descida. Assim a cabeca faz um caminho redondo
# (desce, vai para o lado, sobe, volta ao centro) de 1 px por quadro, como numa caminhada de verdade,
# em vez de quicar so para cima e para baixo.
# Sempre em px inteiros do jogo (9 px do desenho) para o rosto nao "tremer" na reducao.
SOBE_DESCE = [0, 9, 9, 0, 0, 9, 9, 0]
BALANCO_LADO = [0, 0, -9, -9, 0, 0, +9, +9]
COXA_PARTE = 0.7                                          # quanto do encurtamento fica na coxa
PE_PARA_DENTRO = 5                                        # o pe no ar vem um pouco para o meio
JOELHO_LUZ = 0.07                                         # perna dobrada: coxa pega mais luz...
CANELA_SOMBRA = 0.16                                      # ...e a canela fica mais escura
# bracos: como na primeira versao (aprovada): a mao desce/sobe 12 px do desenho e abre 4 px para fora
# quando vai para a frente (entra 4 px quando vai para tras). Os bracos acompanham o corpo (descida e
# balanco para o lado) para nao descolar do ombro.
BRACO_DESCE = 12
BRACO_LADO = 4
DURACAO_MS = L.DURACAO_MS
PAD_X, PAD_TOP = 60, 40


class RigFrente:
    # configuracoes da vista (a vista de costas herda esta classe e troca so o que muda)
    FONTE, CHAO, MEIO, CINTURA, JOELHO_Y, BARRA_Y, OMBRO_Y, PUNHO_Y = FONTE, CHAO, MEIO, CINTURA, JOELHO_Y, BARRA_Y, OMBRO_Y, PUNHO_Y
    PE, ALTURA_MAX, BOTA_ALTURA = PE, ALTURA_MAX, BOTA_ALTURA
    SOBE_DESCE, BALANCO_LADO = SOBE_DESCE, BALANCO_LADO
    COXA_PARTE, PE_PARA_DENTRO, JOELHO_LUZ, CANELA_SOMBRA = COXA_PARTE, PE_PARA_DENTRO, JOELHO_LUZ, CANELA_SOMBRA
    BRACO_DESCE, BRACO_LADO = BRACO_DESCE, BRACO_LADO
    BRACO_ESQ = dict(y0=238, y1=432, corte=330, x_cima=86, x_baixo=80)
    BRACO_DIR = dict(y0=238, y1=432, corte=330, x_cima=219, x_baixo=225)
    TRONCO = (84, 221)
    PERNAS_X = (30, 270)
    FASE = {"e": 0, "d": 4}      # perna da esquerda da imagem usa o quadro k, a da direita k+4
    SOLA = 0.0                   # de frente nao aparece a sola da bota
    SOLA_COR = (74, 48, 40)      # cor da sola (marrom acinzentado escuro)

    def carrega(self):
        a = np.array(Image.open(self.FONTE).convert("RGBA")).astype(np.int32)
        r, g, b = a[..., 0], a[..., 1], a[..., 2]
        mag = (a[..., 3] > 0) & (r > 120) & (b > g + 20) & (g < 0.45 * r)
        a[mag, :3] = (26, 6, 6)
        return a


    def separa(self, a):
        H, W = a.shape[:2]
        al = a[..., 3] > 0
        yy, xx = np.mgrid[0:H, 0:W]
        # bracos: tudo que fica fora do tronco/calca, do ombro para baixo
        be, bd = self.BRACO_ESQ, self.BRACO_DIR
        esq = al & (yy >= be["y0"]) & (yy < be["y1"]) & (((yy < be["corte"]) & (xx < be["x_cima"])) | ((yy >= be["corte"]) & (xx < be["x_baixo"])))
        dir_ = al & (yy >= bd["y0"]) & (yy < bd["y1"]) & (((yy < bd["corte"]) & (xx > bd["x_cima"])) | ((yy >= bd["corte"]) & (xx > bd["x_baixo"])))
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
        tronco = (xx >= self.TRONCO[0]) & (xx <= self.TRONCO[1])
        corpo[(yy >= self.CINTURA) | (bracos & ~tronco)] = 0
        # pernas: da cintura para baixo, sem os bracos
        pernas = al & (yy >= self.CINTURA - 4) & ~bracos & (xx >= self.PERNAS_X[0]) & (xx <= self.PERNAS_X[1])
        perna_e = a.copy(); perna_e[~(pernas & (xx < self.MEIO))] = 0
        perna_d = a.copy(); perna_d[~(pernas & (xx >= self.MEIO))] = 0
        for p in (perna_e, perna_d):
            # completa para cima (fica escondido embaixo da cintura) para a perna poder encurtar sem buraco
            for y in range(300, self.CINTURA + 4):
                p[y] = p[self.CINTURA + 8]
        braco_e = a.copy(); braco_e[~esq] = 0
        braco_d = a.copy(); braco_d[~dir_] = 0
        return dict(corpo=corpo, braco_e=braco_e, braco_d=braco_d, perna_e=perna_e, perna_d=perna_d,
                    m_bracos=bracos, m_pernas=pernas)

    def __init__(self):
        self.a = self.carrega()
        self.p = self.separa(self.a)
        self.H, self.W = self.a.shape[:2]
        self.CW, self.CH = self.W + 2 * PAD_X, self.H + PAD_TOP + 20
        self.off = np.array([PAD_X, PAD_TOP])

    def perna(self, lado, k, bob, balanco=0):
        """Calca + bota de um lado, ja na posicao do quadro k (no espaco do canvas).
        O quadril acompanha o corpo (balanco); o pe fica na sua faixa (o pe no ar vem um pouco para o meio)."""
        tmpl = self.p["perna_e" if lado == "e" else "perna_d"]
        prof, alt = self.PE[k % 8]
        topo_bota = self.BARRA_Y + prof - alt              # onde a barra da calca encosta na bota
        quadril = self.CINTURA + bob
        comp = topo_bota - quadril
        if comp > self.BARRA_Y - self.CINTURA:                  # nunca estica a perna
            comp = self.BARRA_Y - self.CINTURA
            topo_bota = quadril + comp
        encurta = (self.BARRA_Y - self.CINTURA) - comp
        coxa = (self.JOELHO_Y - self.CINTURA) - self.COXA_PARTE * encurta
        canela = (self.BARRA_Y - self.JOELHO_Y) - (1 - self.COXA_PARTE) * encurta
        dobra = alt / self.ALTURA_MAX                      # 0 = perna esticada, 1 = joelho mais dobrado
        pe_dx = (1 if lado == "e" else -1) * self.PE_PARA_DENTRO * dobra
        cam = np.zeros((self.CH, self.CW, 4), np.int32)
        ox, oy = self.off
        sb = self.BOTA_ALTURA[k % 8]
        alt_bota = self.CHAO + 1 - self.BARRA_Y
        y_fim = int(math.ceil(topo_bota + alt_bota * sb))
        for yd in range(300 + bob, y_fim):
            if yd < quadril:
                ys = yd - bob; dx = balanco; luz = 1.0
            elif yd < topo_bota:
                t = (yd - quadril) / (topo_bota - quadril)
                dx = balanco * (1 - t) + pe_dx * t
                if yd < quadril + coxa:
                    ys = self.CINTURA + (yd - quadril) * (self.JOELHO_Y - self.CINTURA) / coxa
                    luz = 1 + self.JOELHO_LUZ * dobra * min(1, (yd - quadril) / max(coxa, 1) * 1.5)
                else:
                    ys = self.JOELHO_Y + (yd - quadril - coxa) * (self.BARRA_Y - self.JOELHO_Y) / canela
                    luz = 1 - self.CANELA_SOMBRA * dobra
            else:
                ys = self.BARRA_Y + (yd - topo_bota) / sb; dx = pe_dx; luz = 1.0
                if self.SOLA and dobra > 0 and yd >= y_fim - alt_bota * sb * self.SOLA * dobra:
                    luz = -1            # pe saindo do chao: aparece a sola (mais escura e mais "cinza")
            ys = int(math.floor(ys + 0.5))
            if 0 <= ys < self.H:
                linha = tmpl[ys].copy()
                m = linha[:, 3] > 0
                if luz == -1:
                    claro = m & (linha[:, :3].sum(1) >= R.ESCURO)
                    linha[claro, :3] = (linha[claro, :3] * 0.35 + np.array(self.SOLA_COR) * 0.65).astype(np.int32)
                elif luz != 1.0:
                    claro = m & (linha[:, :3].sum(1) >= R.ESCURO)
                    linha[claro, :3] = (linha[claro, :3] * luz).clip(0, 255).astype(np.int32)
                d = int(round(dx))
                x0 = ox + d
                cam[oy + yd, x0:x0 + self.W][m] = linha[m]
        return cam

    def braco(self, lado, a_balanco, bob, balanco=0):
        """Braco deformado: abaixo do ombro vai descendo/subindo ate o punho; do punho para baixo
        anda inteiro. a_balanco: +1 = todo para a frente (desce, vai para fora), -1 = para tras."""
        tmpl = self.p["braco_e" if lado == "e" else "braco_d"]
        dy_max = a_balanco * self.BRACO_DESCE
        fora = -1 if lado == "e" else 1
        dx_max = fora * a_balanco * self.BRACO_LADO
        cam = np.zeros((self.CH, self.CW, 4), np.int32)
        ox, oy = self.off
        ys, xs = np.nonzero(tmpl[..., 3] > 0)
        cores = tmpl[ys, xs]
        for sub in (1 / 6, 0.5, 5 / 6):
            yf = ys + sub
            t = np.clip((yf - self.OMBRO_Y) / (self.PUNHO_Y - self.OMBRO_Y), 0, 1)
            t = t * t * (3 - 2 * t)
            Y = np.floor(yf + bob + dy_max * t).astype(int) + oy
            X = np.floor(xs + 0.5 + balanco + dx_max * t).astype(int) + ox
            ok = (Y >= 0) & (Y < self.CH) & (X >= 0) & (X < self.CW)
            cam[Y[ok], X[ok]] = cores[ok]
        return cam

    def quadro(self, k):
        bob = self.SOBE_DESCE[k % 8]
        dst = np.zeros((self.CH, self.CW, 4), np.int32)
        # balanco dos bracos: o braco da esquerda da imagem vai para tras quando a perna da esquerda vai para a frente
        a_e = -math.cos(2 * math.pi * (k - 0.5) / 8)
        a_d = -a_e
        bal = self.BALANCO_LADO[k % 8]
        bracos = {"e": self.braco("e", a_e, bob, bal), "d": self.braco("d", a_d, bob, bal)}
        atras = [l for l, a in (("e", a_e), ("d", a_d)) if a < 0]
        frente = [l for l, a in (("e", a_e), ("d", a_d)) if a >= 0]
        for l in atras:
            L.cola(dst, bracos[l])
        # pernas: a que esta mais perto da camera (pe mais para baixo) por cima
        ke, kd = k + self.FASE["e"], k + self.FASE["d"]
        pe_e, pe_d = self.PE[ke % 8][0], self.PE[kd % 8][0]
        ordem = [("e", ke), ("d", kd)] if pe_e <= pe_d else [("d", kd), ("e", ke)]
        for lado, kk in ordem:
            L.cola(dst, self.perna(lado, kk, bob, bal))
        corpo = np.zeros_like(dst)
        corpo[self.off[1] + bob:self.off[1] + bob + self.H, self.off[0] + bal:self.off[0] + bal + self.W] = self.p["corpo"]
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
