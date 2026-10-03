"""Acoes de trabalho do heroi vistas de FRENTE e de COSTAS, no jeito do Stardew Valley.

O que foi copiado do Stardew (golpe de enxada/picareta/machado):
- poucos quadros e ritmo marcado: levanta e segura (150 ms), dois quadros de golpe bem rapidos
  (40 ms cada), impacto segurado e uma volta rapida (75 ms);
- o corpo quase nao se mexe: so os bracos e a ferramenta; no impacto o corpo desce 1 px;
- de frente a ferramenta sobe por tras da cabeca (aparece por cima do chapeu, os bracos somem atras
  da aba) e desce no meio, na frente dos pes, com a lamina vista de frente;
- de costas e o contrario: a ferramenta sobe por cima das costas (na frente da cabeca, para a camera)
  e desce escondida na frente do heroi; dos bracos so aparecem os cotovelos.

Os bracos sao os do desenho, inteiros (braco de cima com a manga + antebraco com a mao), girando no
ombro e no cotovelo, sem esticar nem amassar. A ferramenta e a da vista de lado, encurtada no
comprimento quando aponta para a camera (k); a enxada ganha a lamina vista de frente.
"""
import json, math, os, sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lado as L
import anim_frente as F
import anim_costas as C
import anim_acoes as A
import ferramentas_desenho as FD

SAIDA = A.SAIDA
MARGEM = (230, 260)          # espaco extra dos lados e em cima (a ferramenta passa por cima da cabeca)
MARGEM_BAIXO = 90            # e embaixo (de frente a ferramenta bate no chao na frente dos pes)
VAO_MAOS = 24                # distancia entre as duas maos no cabo (px do desenho)
CABECA_RIGIDA = {"enxada": 472}   # linha onde comeca a cabeca vista de frente (ela nao encurta com o cabo)


def rot(t):
    return L.rot(math.radians(t))


def ang(v):
    """Angulo de um vetor da tela no mesmo sentido de L.rot (0 = para baixo, + = gira para a direita)."""
    return math.degrees(math.atan2(v[0], v[1]))


def coloca_mat(dst, peca, piv0, piv1, M):
    """Cola 'peca' transformada pela matriz 2x2 M em volta de piv0, com piv0 indo para piv1."""
    m = peca[..., 3] > 0
    if not m.any():
        return
    ys, xs = np.nonzero(m)
    cant = np.array([[xs.min(), ys.min()], [xs.max() + 1, ys.min()], [xs.min(), ys.max() + 1],
                     [xs.max() + 1, ys.max() + 1]], float) - piv0
    novos = cant @ M.T + piv1
    x0, y0 = np.floor(novos.min(0)).astype(int) - 1
    x1, y1 = np.ceil(novos.max(0)).astype(int) + 2
    x0, y0 = max(x0, 0), max(y0, 0)
    x1, y1 = min(x1, dst.shape[1]), min(y1, dst.shape[0])
    if x1 <= x0 or y1 <= y0:
        return
    gy, gx = np.mgrid[y0:y1, x0:x1]
    q = np.stack([gx + 0.5 - piv1[0], gy + 0.5 - piv1[1]], -1) @ np.linalg.inv(M).T + piv0
    sx = np.floor(q[..., 0]).astype(int); sy = np.floor(q[..., 1]).astype(int)
    ok = (sx >= 0) & (sy >= 0) & (sx < peca.shape[1]) & (sy < peca.shape[0])
    src = peca[sy.clip(0, peca.shape[0] - 1), sx.clip(0, peca.shape[1] - 1)]
    ok &= src[..., 3] > 0
    dst[y0:y1, x0:x1][ok] = src[ok]


def enxada_de_frente():
    """Enxada com a lamina vista de frente (para as vistas de frente/costas): o cabo e o anel de latao
    sao os do desenho; a lamina vira um retangulo largo com as cores do proprio ferro (fio claro embaixo)."""
    t = FD.FERRAMENTAS["enxada"]().copy()
    m = t[..., 3] > 0
    H, W = m.shape
    yy, xx = np.mgrid[0:H, 0:W]
    corte = CABECA_RIGIDA["enxada"]          # embaixo do anel de latao
    lam = m & ((yy >= corte) | ((yy >= 430) & (xx < 405)))      # lamina de lado (sai)
    ferro = lam & (xx < 400) & (t[..., 2] >= t[..., 0] - 10)
    cores = t[ferro][:, :3].astype(int)
    luz = cores.sum(1)
    escuro = cores[luz <= np.percentile(luz, 20)].mean(0)
    medio = cores[(luz > np.percentile(luz, 35)) & (luz <= np.percentile(luz, 65))].mean(0)
    claro = cores[luz >= np.percentile(luz, 90)].mean(0)
    t[lam] = 0
    ys, xs = np.nonzero(t[..., 3] > 0)
    cx = xs[(ys > corte - 30) & (ys < corte)].mean()
    alt, larg_cima, larg_baixo = 34, 70, 84
    for j in range(alt):
        y = corte + j
        meia = (larg_cima + (larg_baixo - larg_cima) * j / (alt - 1)) / 2
        x0, x1 = int(round(cx - meia)), int(round(cx + meia))
        cor = escuro if j < 5 else (claro if j >= alt - 8 else medio)
        t[y, x0:x1, :3] = cor; t[y, x0:x1, 3] = 255
        if 5 <= j < alt - 8:
            t[y, x0:x0 + 7, :3] = escuro                         # laterais mais escuras (volume)
            t[y, x1 - 7:x1, :3] = escuro
    return t


class Medidas:
    """O pouco de 'rig_heroi' que a funcao gera() da vista de lado usa (pivo, chao e escala)."""
    ESCALA = 9

    def __init__(self, rig):
        self.QUADRIL = (rig.MEIO, rig.CINTURA)
        self.CHAO = rig.CHAO


def _rig_acao(base):
    class RigAcaoFB(base):
        def __init__(self):
            super().__init__()
            self.off = self.off + np.array(MARGEM)
            self.CW += 2 * MARGEM[0]
            self.CH += MARGEM[1] + MARGEM_BAIXO
            self.R = Medidas(self)
            self.ferr = {}
            yy = np.arange(self.H)[:, None]
            corpo = self.p["corpo"]
            self.cabeca = corpo * (yy < self.PESCOCO)[..., None]
            self.tronco = corpo * (yy >= self.PESCOCO)[..., None]
            self.pecas = {}
            for lado in ("e", "d"):
                b = self.p["braco_e" if lado == "e" else "braco_d"]
                ycot = self.BRACO_PONTOS[lado][1][1]
                sup = b * (yy < ycot)[..., None]
                ant = b * (yy >= ycot - 8)[..., None]          # um pouco por baixo da manga (sem vao no cotovelo)
                self.pecas[lado] = (sup, ant)

        def _ferr(self, nome):
            if nome not in self.ferr:
                self.ferr[nome] = enxada_de_frente() if nome == "enxada" else FD.FERRAMENTAS[nome]()
            return self.ferr[nome]

        # ---------- bracos (ombro + cotovelo, pecas inteiras) ----------
        def braco_ik(self, lado, alvo, desl, cotovelo_fora=True):
            """Gira braco e antebraco para a mao chegar em 'alvo' (canvas). O cotovelo dobra para fora
            do corpo. Devolve camada, posicao da mao e posicao do cotovelo."""
            S0, E0, M0 = (np.array(v, float) for v in self.BRACO_PONTOS[lado])
            S1 = S0 + self.off + desl
            l1, l2 = np.hypot(*(E0 - S0)), np.hypot(*(M0 - E0))
            v = np.array(alvo, float) - S1
            d = float(np.clip(np.hypot(*v), abs(l1 - l2) + 2, l1 + l2 - 0.5))
            base = math.atan2(v[1], v[0])
            a = math.acos(np.clip((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d), -1, 1))
            opcoes = [S1 + l1 * np.array([math.cos(base + s * a), math.sin(base + s * a)]) for s in (1, -1)]
            fora = -1 if lado == "e" else 1
            E1 = max(opcoes, key=lambda e: fora * e[0]) if cotovelo_fora else min(opcoes, key=lambda e: fora * e[0])
            P = S1 + v / max(np.hypot(*v), 1e-6) * d          # alvo (trazido para perto se o braco nao alcanca)
            M1 = E1 + l2 * (P - E1) / max(np.hypot(*(P - E1)), 1e-6)
            a_sup = ang(E1 - S1) - ang(E0 - S0)
            a_ant = ang(M1 - E1) - ang(M0 - E0)
            sup, ant = self.pecas[lado]
            cam = np.zeros((self.CH, self.CW, 4), np.int32)
            L.coloca(cam, ant, E0, E1, a_ant)
            L.coloca(cam, sup, S0, S1, a_sup)
            return cam, M1, E1

        # ---------- ferramenta ----------
        def matriz(self, cabo, k, espelho):
            return rot(cabo) @ np.diag([-1.0 if espelho else 1.0, k])

        def _pontos(self, nome, cabo, k, espelho):
            """Pontos da ferramenta (relativos a pega) ja girados/encurtados, para achar a ponta de baixo."""
            t = self._ferr(nome)
            pega = np.array(FD.pega_de(nome), float)
            ys, xs = np.nonzero(t[..., 3] > 0)
            pts = np.stack([xs + 0.5, ys + 0.5], -1) - pega
            corte = CABECA_RIGIDA.get(nome)
            if corte is None:
                return pts @ self.matriz(cabo, k, espelho).T
            junta = np.array([pts[:, 0][ys < corte].mean() if (ys < corte).any() else 0, corte - pega[1]])
            cabo_pts, cab_pts = pts[ys < corte], pts[ys >= corte] - junta
            j1 = self.matriz(cabo, k, espelho) @ junta
            return np.concatenate([cabo_pts @ self.matriz(cabo, k, espelho).T,
                                   cab_pts @ self.matriz(cabo, 1.0, espelho).T + j1])

        def ferramenta(self, nome, punho, cabo, k, espelho, encostar, folga=0):
            """Camada da ferramenta. Se encostar=True, procura o k (encurtamento) que deixa a ponta de baixo
            na linha do chao da vista (de frente um pouco abaixo dos pes; de costas um pouco acima).
            Ferramentas em CABECA_RIGIDA: so o cabo encurta; a cabeca (vista de frente) fica do mesmo tamanho."""
            t = self._ferr(nome)
            pega = np.array(FD.pega_de(nome), float)
            if encostar:
                chao = self.CHAO + self.off[1] + self.CHAO_BATIDA - folga
                melhor = None
                for kk in np.arange(0.15, 1.001, 0.01):
                    baixo = self._pontos(nome, cabo, kk, espelho)[:, 1].max() + punho[1]
                    err = abs(baixo - chao)
                    if melhor is None or err < melhor[0]:
                        melhor = (err, kk)
                k = melhor[1]
            cam = np.zeros((self.CH, self.CW, 4), np.int32)
            M = self.matriz(cabo, k, espelho)
            corte = CABECA_RIGIDA.get(nome)
            if corte is None:
                coloca_mat(cam, t, pega, punho, M)
            else:
                yy = np.arange(t.shape[0])[:, None, None]
                cabo_img, cab_img = t * (yy < corte), t * (yy >= corte)
                ys, xs = np.nonzero(t[:corte, :, 3] > 0)
                junta = np.array([xs[ys > corte - 40].mean() + 0.5, float(corte)])
                coloca_mat(cam, cab_img, junta, punho + M @ (junta - pega), self.matriz(cabo, 1.0, espelho))
                coloca_mat(cam, cabo_img, pega, punho, M)
            return cam, M

        def quadro_acao(self, nome_ferr, q, ponto_chao=None):
            q = self.pose(q)
            dst = np.zeros((self.CH, self.CW, 4), np.int32)
            bob = q.get("desce", 0)
            desl = np.array((0, bob), float)
            mao_dir = self.MAO_DIREITA
            outra = "d" if mao_dir == "e" else "e"
            # a mao direita vai no ponto pedido; a pega da ferramenta fica nela
            alvo = np.array(q["maos"], float) + self.off + desl
            cam_dir, G, _ = self.braco_ik(mao_dir, alvo, desl)
            ferr, M = self.ferramenta(nome_ferr, G, q["cabo"], q.get("k", 1.0), q.get("espelho", False),
                                      q.get("chao", False), q.get("folga", 0))
            bracos = {mao_dir: cam_dir}
            if q.get("uma_mao"):
                bracos[outra] = self.braco(outra, q.get("livre", 0.0), bob)
            else:                                          # a outra mao um pouco mais para a cabeca da ferramenta
                eixo = M @ np.array([0.0, 1.0]); eixo /= max(1e-6, np.hypot(*eixo))
                bracos[outra] = self.braco_ik(outra, G + eixo * VAO_MAOS, desl)[0]
            self.bico = None
            if nome_ferr == "regador":
                t = self._ferr(nome_ferr)
                ys, xs = np.nonzero(t[..., 3] > 0)
                x_max = xs.max()
                ponta = np.array([x_max - 4, ys[xs >= x_max - 10].mean() + 10], float) - np.array(FD.pega_de(nome_ferr))
                self.bico = G + M @ ponta
            visivel = np.zeros(dst.shape[:2], bool)
            frente = np.zeros(dst.shape[:2], bool)
            ja_colou = [False]

            def cola(cam, eh_ferr=False):
                m = cam[..., 3] > 0
                dst[m] = cam[m]
                visivel[m] = eh_ferr
                if eh_ferr:
                    ja_colou[0] = True; frente[m] = False
                elif ja_colou[0]:
                    frente[m] = True

            def parte(img):
                cam = np.zeros_like(dst)
                cam[self.off[1] + bob:self.off[1] + bob + self.H, self.off[0]:self.off[0] + self.W] = img
                return cam

            pernas = [self.perna(lado, 2, bob, 0) for lado in ("e", "d")]
            cabeca, tronco = parte(self.cabeca), parte(self.tronco)
            ordem_b = [outra, mao_dir]
            alto = bool(q.get("atras"))
            if self.DE_FRENTE and alto:        # la no alto, atras da cabeca: bracos somem atras da aba
                camadas = [(ferr, True)] + [(p, False) for p in pernas] + [(tronco, False)] + \
                          [(bracos[l], False) for l in ordem_b] + [(cabeca, False)]
            elif self.DE_FRENTE:                # na frente do corpo
                camadas = [(p, False) for p in pernas] + [(tronco, False), (cabeca, False), (ferr, True)] + \
                          [(bracos[l], False) for l in ordem_b]
            elif alto:                          # de costas, la no alto: as maos somem atras do chapeu e a
                camadas = [(p, False) for p in pernas] + [(tronco, False)] + \
                          [(bracos[l], False) for l in ordem_b] + [(cabeca, False), (ferr, True)]   # ferramenta cai por cima das costas
            else:                               # de costas, escondida na frente dele: so os cotovelos aparecem
                toco = {}
                for l in ordem_b:
                    if l == outra and q.get("uma_mao"):
                        toco[l] = bracos[l]
                        continue
                    mx = (np.array(q["maos"], float))[0]
                    if l == mao_dir and not (self.TRONCO[0] + 12 <= mx <= self.TRONCO[1] - 12):
                        toco[l] = bracos[l]                     # mao para o lado, fora do corpo: aparece toda
                        continue
                    S1 = np.array(self.BRACO_PONTOS[l][0], float) + self.off + desl
                    dentro = 1 if l == "e" else -1
                    cam, _, _ = self.braco_ik(l, S1 + (dentro * self.TOCO[0], self.TOCO[1]), desl)
                    cam[:, :, 3] *= self._mascara_toco(l, desl)
                    toco[l] = cam
                camadas = [(ferr, True)] + [(bracos[l], False) for l in ordem_b] + [(p, False) for p in pernas] + \
                          [(tronco, False), (cabeca, False)] + [(toco[l], False) for l in ordem_b]
            for cam, eh in camadas:
                cola(cam, eh)
            m = ferr[..., 3] > 0
            ys, xs = np.nonzero(m)
            baixo = ys.max()
            ponto = (int(xs[ys >= baixo - 6].mean()), int(baixo))
            d2 = (xs - G[0]) ** 2 + (ys - G[1]) ** 2
            self.ponta = (float(xs[d2.argmax()]), float(ys[d2.argmax()]))
            self.punho = (float(G[0]), float(G[1]))
            self.visivel = visivel
            self.frente = frente
            return dst, ponto, q["cabo"]

        def _mascara_toco(self, lado, desl):
            """De costas, o braco que vai para a frente aparece so ate um pouco abaixo do cotovelo."""
            m = np.zeros((self.CH, self.CW), np.int32)
            m[:int(self.off[1] + desl[1] + self.TOCO_ATE)] = 1
            return m

        def pose(self, q):
            return q

    return RigAcaoFB


class RigAcaoFrente(_rig_acao(F.RigFrente)):
    DE_FRENTE = True
    MAO_DIREITA = "e"                # de frente a mao direita do heroi fica na esquerda da imagem
    CHAO_BATIDA = +34                # a ferramenta bate no chao na frente dos pes (mais embaixo na tela)
    EFEITO_ATRAS = False
    AGUA_DIR = -1                    # o regador fica na mao direita (esquerda da imagem), bico para fora
    PESCOCO = 222                    # acima disso e cabeca (chapeu, cabelo, rosto)
    # (ombro, cotovelo, meio da mao) de cada braco no desenho de frente
    BRACO_PONTOS = {"e": ((68, 262), (50, 312), (40, 390)), "d": ((232, 262), (250, 312), (264, 390))}


class RigAcaoCostas(_rig_acao(C.RigCostas)):
    DE_FRENTE = False
    MAO_DIREITA = "d"
    CHAO_BATIDA = -16                # bate no chao na frente dele = mais para cima na tela (escondido)
    EFEITO_ATRAS = True
    AGUA_DIR = +1
    PESCOCO = 226
    BRACO_PONTOS = {"e": ((72, 262), (52, 312), (40, 390)), "d": ((225, 262), (245, 312), (262, 390))}
    TOCO = (18, 116)                 # de costas: o braco de cima desce junto do corpo, um pouco para dentro
    TOCO_ATE = 340                   # e aparece so ate aqui (o resto vai para a frente dele, escondido)

    def pose(self, q):
        """Pose de costas = pose de frente espelhada (troca o lado da imagem), com os ajustes de 'costas'."""
        q = dict(q)
        extra = q.pop("costas", {})
        x, y = q["maos"]
        q["maos"] = (2 * self.MEIO - x, y)
        q["cabo"] = -q["cabo"]
        q["espelho"] = not q.get("espelho", False)
        q.update(extra)
        return q


# ---------------- poses (vista de frente; as de costas saem espelhadas + ajustes) ----------------
# maos = onde fica a mao direita (pega da ferramenta), em px do desenho de frente
# cabo = para onde a ferramenta aponta saindo da mao (0 = para baixo, 180 = para cima, + = para a direita da imagem)
# k = quanto sobra do comprimento (1 = deitada na tela; menor = apontando para a camera ou para longe)
# atras = la no alto: de frente fica atras da cabeca; de costas fica por cima das costas
ENXADA = [
    dict(nome="levantar", maos=(150, 150), cabo=180, k=0.9, atras=True, terra=0, dur=0.15,
         costas=dict(maos=(150, 150), cabo=0, k=0.45)),
    dict(nome="golpe_a", maos=(150, 252), cabo=180, k=0.6, terra=0, dur=0.04,
         costas=dict(maos=(150, 200), cabo=180, k=1.0, atras=False)),
    dict(nome="golpe_b", maos=(150, 316), cabo=0, k=0.3, terra=0, dur=0.04,
         costas=dict(maos=(150, 250), cabo=180, k=1.0)),
    dict(nome="impacto", maos=(150, 366), cabo=0, chao=True, desce=9, terra=1, dur=0.10),
    dict(nome="terra", maos=(150, 366), cabo=0, chao=True, desce=9, terra=2, dur=0.10),
    dict(nome="voltar", maos=(150, 352), cabo=0, chao=True, folga=10, terra=3, dur=0.075),
]


ACOES = {"enxada": ("enxada", ENXADA)}


def gera_acao(acao, costas=False):
    ferr_nome, poses = ACOES[acao]
    rig = RigAcaoCostas() if costas else RigAcaoFrente()
    finais, pivot, pal, grandes = A.gera(rig, ferr_nome, poses)
    pontas = list(rig.pontas_jogo)
    info = dict(pivot=[int(v) for v in pivot], tamanho=list(finais[0].shape[1::-1]), cores=len(pal),
                quadros=[dict(nome=q["nome"], duracao_s=q["dur"], ponta_ferramenta=[round(v, 1) for v in pontas[i]])
                         for i, q in enumerate(poses)])
    return finais, pivot, info, grandes


if __name__ == "__main__":
    acao = next((a for a in sys.argv[1:] if not a.startswith("--")), "enxada")
    costas = "--costas" in sys.argv
    pasta = os.path.join(SAIDA, f"{acao}_{'costas' if costas else 'frente'}")
    os.makedirs(pasta, exist_ok=True)
    for f in os.listdir(pasta):
        if f.endswith(".png"):
            os.remove(os.path.join(pasta, f))
    finais, pivot, info, grandes = gera_acao(acao, costas)
    poses = ACOES[acao][1]
    Image.fromarray(finais[0], "RGBA").save(os.path.join(pasta, "parado.png"))
    for i, (f, q) in enumerate(zip(finais[1:], poses)):
        Image.fromarray(f, "RGBA").save(os.path.join(pasta, f"{acao}_{i}_{q['nome']}.png"))
    if "--grande" in sys.argv:
        for i, g in enumerate(grandes):
            Image.fromarray(g.clip(0, 255).astype(np.uint8), "RGBA").save(os.path.join(pasta, f"grande_{i}.png"))
    json.dump(info, open(os.path.join(pasta, "info.json"), "w"), indent=1)
    print(acao, "costas" if costas else "frente", "quadro", info["tamanho"], "pivo", pivot)
