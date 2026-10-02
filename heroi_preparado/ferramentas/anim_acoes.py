"""Acoes de trabalho do heroi com o mesmo esqueleto do andar (teste: enxada, vista de lado direito).

O braco de perto gira no ombro e dobra no cotovelo; a ferramenta e colada na mao e gira junto.
As pernas usam a mesma perna de 2 partes do andar, numa base firme (um pe na frente, outro atras),
e dobram um pouco no golpe. O corpo inclina 1 px para tras quando levanta a ferramenta e 1 px para
a frente no golpe (sempre em px inteiros do jogo, para o rosto nao tremer).
"""
import json, math, os, sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lado as L
import rig_heroi as R
import ferramentas_desenho as FD

AQUI = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(AQUI, "..", "revisao", "acoes")
ARTE = os.path.join(AQUI, "..", "JogoFazenda", "arte", "preparado", "heroi")

PUNHO = (100, 386)            # onde o cabo passa dentro da mao (no desenho do braco)
MARGEM = (230, 260)           # espaco extra no canvas (a ferramenta passa por cima da cabeca e longe do corpo)
BASE = dict(perto=(+30, 0, 0), longe=(-30, 0, 0))   # pes firmes: perna de perto na frente, a outra atras

# Quadros da enxada: ombro (graus, 0 = braco caido, 90 = para a frente, 180 = para cima),
# dobra do cotovelo, angulo do cabo (mesma regra: para onde o cabo aponta saindo da mao),
# inclinacao do corpo (px do desenho, + = para a frente), descida (px, + = para baixo),
# ferramenta atras do corpo?, encostar a lamina no chao?, terra voando (0 = nao), duracao (s)
ENXADA = [
    dict(nome="preparar", ombro=30, cotovelo=15, cabo=42, incl=0, desce=0, atras=False, chao=True, terra=0, dur=0.10),
    dict(nome="levantar", ombro=105, cotovelo=25, cabo=165, incl=0, desce=0, atras=False, chao=False, terra=0, dur=0.09),
    dict(nome="no_alto", ombro=168, cotovelo=22, cabo=228, incl=-9, desce=0, atras=True, chao=False, terra=0, dur=0.15),
    dict(nome="golpe", ombro=95, cotovelo=10, cabo=118, incl=0, desce=0, atras=False, chao=False, terra=0, dur=0.05),
    dict(nome="impacto", ombro=48, cotovelo=8, cabo=45, incl=9, desce=9, atras=False, chao=True, terra=1, dur=0.11),
    dict(nome="terra", ombro=48, cotovelo=8, cabo=45, incl=9, desce=9, atras=False, chao=True, terra=2, dur=0.16),
    dict(nome="voltar", ombro=34, cotovelo=14, cabo=44, incl=0, desce=0, atras=False, chao=True, folga=30, terra=3, dur=0.11),
]
TERRA = (148, 98, 58); TERRA_CLARA = (182, 130, 82)


def rot(t):
    return L.rot(math.radians(t))


class RigAcao(L.Rig):
    def __init__(self, medidas=None):
        super().__init__(medidas)
        self.off = self.off + np.array(MARGEM)
        self.CW += 2 * MARGEM[0]
        self.CH += MARGEM[1]
        self.ferr = {}
        for nome, f in FD.FERRAMENTAS.items():
            t = f(); L.contorna(t); self.ferr[nome] = t

    def mao(self, desl, ombro, cotovelo):
        """Posicao do punho (no canvas) para os angulos do braco."""
        S = np.array(self.R.OMBRO, float); E0 = np.array(self.R.COTOVELO, float); P0 = np.array(PUNHO, float)
        S1 = S + self.off + desl
        E1 = S1 + rot(ombro) @ (E0 - S)
        return E1 + rot(ombro + cotovelo) @ (P0 - E0)

    def ferramenta(self, nome, punho, cabo, encostar, folga=0):
        """Camada da ferramenta. Se encostar=True, ajusta o angulo do cabo ate a lamina ficar 'folga' px
        acima do chao (0 = tocando o chao)."""
        t = self.ferr[nome]
        chao = self.R.CHAO + self.off[1] - folga
        if encostar:
            ys, xs = np.nonzero(t[..., 3] > 0)
            pts = np.stack([xs + 0.5, ys + 0.5], -1) - np.array(FD.pega_de(nome))
            melhor = None
            for c in np.arange(cabo - 25, cabo + 25.01, 0.5):
                baixo = (pts @ rot(c).T)[:, 1].max() + punho[1]
                err = abs(baixo - chao)
                if melhor is None or err < melhor[0]:
                    melhor = (err, c)
            cabo = melhor[1]
        cam = np.zeros((self.CH, self.CW, 4), np.int32)
        L.coloca(cam, t, np.array(FD.pega_de(nome), float), punho, cabo)
        return cam, cabo

    def terra(self, cam, ponto, fase):
        """Torroes de terra pulando perto da lamina."""
        if fase == 0:
            return
        sobe = {1: 0.4, 2: 1.0, 3: 0.6}[fase]
        for dx, alt, tam in ((-40, 70, 22), (10, 95, 18), (45, 60, 16)):
            x = int(ponto[0] + dx * (0.6 + 0.4 * sobe)); y = int(ponto[1] - alt * sobe)
            pedra = np.zeros((tam + 14, tam + 14, 4), np.int32)
            pedra[3:-3, 3:-3] = (*TERRA, 255); pedra[3:10, 3:-6, :3] = TERRA_CLARA
            L.contorna(pedra, 6)
            reg = cam[y - tam // 2:y - tam // 2 + pedra.shape[0], x - tam // 2:x - tam // 2 + pedra.shape[1]]
            m = pedra[..., 3] > 0
            reg[m[:reg.shape[0], :reg.shape[1]]] = pedra[:reg.shape[0], :reg.shape[1]][m[:reg.shape[0], :reg.shape[1]]]

    def quadro_acao(self, nome_ferr, q, ponto_chao=None):
        dst = np.zeros((self.CH, self.CW, 4), np.int32)
        bob, incl = q["desce"], q["incl"]
        H = np.array(self.R.QUADRIL, float) + self.off + (incl, bob)
        # pernas: pes plantados (a perna absorve a inclinacao e a descida)
        for chave, esc in (("longe", L.LONGE_ESCURECE), ("perto", None)):
            dx, ang, lift = BASE[chave]
            Hk = H + (L.LONGE_DESLOCA if chave == "longe" else (0, 0))
            cam, _ = self.perna(dst, Hk, (dx - incl, ang, lift), esc)
            L.cola(dst, L.recorta_quadril(cam, self, bob))
        desl = np.array((incl, bob), float)
        punho = self.mao(desl, q["ombro"], q["cotovelo"])
        ferr, cabo = self.ferramenta(nome_ferr, punho, q["cabo"], q["chao"], q.get("folga", 0))
        if q["atras"]:
            L.cola(dst, ferr)
        corpo = np.zeros_like(dst)
        corpo[self.off[1] + bob:self.off[1] + bob + self.H, self.off[0] + incl:self.off[0] + incl + self.W] = self.p["corpo"]
        L.cola(dst, corpo)
        if not q["atras"]:
            L.cola(dst, ferr)
        L.cola(dst, self.braco(dst, desl, q["ombro"], q["cotovelo"]))
        if q["terra"] and ponto_chao is not None:
            self.terra(dst, ponto_chao, q["terra"])
        # ponto onde a lamina toca o chao (para a terra)
        m = ferr[..., 3] > 0
        ys, xs = np.nonzero(m)
        baixo = ys.max()
        ponto = (int(xs[ys >= baixo - 6].mean()), int(baixo))
        return dst, ponto, cabo


def paleta_com_ferramenta(reduzidos, pal_heroi, extra=8):
    """Paleta do heroi (32 cores, a mesma do andar) + algumas cores so para a ferramenta e a terra."""
    todos = np.concatenate([r[r[..., 3] == 255][:, :3] for r in reduzidos]).astype(int)
    d = ((todos[:, None, :] - pal_heroi[None]) ** 2).sum(-1).min(1)
    longe = todos[d > 900]
    if len(longe) < extra:
        return pal_heroi
    novas = L.paleta([np.concatenate([longe, np.full((len(longe), 1), 255)], 1).reshape(-1, 1, 4).astype(np.uint8)], extra)
    return np.concatenate([pal_heroi, novas])


if __name__ == "__main__":
    pasta = os.path.join(SAIDA, "enxada_lado"); os.makedirs(pasta, exist_ok=True)
    rig = RigAcao()
    grandes, ponto = [], None
    for q in ENXADA:
        f, p, cabo = rig.quadro_acao("enxada", q, ponto)
        if q["nome"] == "impacto":
            ponto = p
        grandes.append((f, q))
    # refaz os quadros com terra (precisam do ponto do impacto)
    grandes = [(rig.quadro_acao("enxada", q, ponto)[0], q) for q in ENXADA]
    red, pivot = L.reduz_box([rig.parado()] + [g[0] for g in grandes], rig, (R.QUADRIL[0], R.CHAO))
    pal_heroi = np.array(json.load(open(os.path.join(ARTE, "heroi.json")))["paleta"])
    pal = paleta_com_ferramenta(red, pal_heroi)
    finais = L.aplica_paleta(red, pal)
    Image.fromarray(finais[0], "RGBA").save(os.path.join(pasta, "parado.png"))
    for i, (f, q) in enumerate(zip(finais[1:], ENXADA)):
        Image.fromarray(f, "RGBA").save(os.path.join(pasta, f"enxada_{i}_{q['nome']}.png"))
    if "--grande" in sys.argv:
        for i, (g, q) in enumerate(grandes):
            Image.fromarray(g.clip(0, 255).astype(np.uint8), "RGBA").save(os.path.join(pasta, f"grande_{i}.png"))
    json.dump(dict(pivot=list(pivot), tamanho=list(finais[0].shape[1::-1]), cores=len(pal),
                   quadros=[dict(nome=q["nome"], duracao_s=q["dur"]) for q in ENXADA]),
              open(os.path.join(pasta, "info.json"), "w"), indent=1)
    print("quadro", finais[0].shape[1::-1], "pivo", pivot, "cores", len(pal))
