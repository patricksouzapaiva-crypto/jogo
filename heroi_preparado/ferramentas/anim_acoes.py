"""Acoes de trabalho do heroi com o mesmo esqueleto do andar (teste: enxada, vista de lado direito).

O braco de perto gira no ombro e dobra no cotovelo; a ferramenta e colada na mao e gira junto.
As pernas usam a mesma perna de 2 partes do andar, numa base firme (um pe na frente, outro atras),
e dobram um pouco no golpe. O corpo inclina 1 px para tras quando levanta a ferramenta e 1 px para
a frente no golpe (sempre em px inteiros do jogo, para o rosto nao tremer).
"""
import json, math, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

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
# Regador: o "cabo" e a inclinacao (0 = pendurado em pe; negativo = bico para baixo).
# agua: 0 sem agua, 1 primeiras gotas, 2/3 regando (gotas em alturas alternadas), 4 ultimas gotas.
_REG = dict(incl=0, desce=0, atras=False, chao=False, terra=0)
REGADOR = [
    dict(nome="segurar", ombro=26, cotovelo=16, cabo=0, agua=0, dur=0.12, **_REG),
    dict(nome="levantar", ombro=40, cotovelo=18, cabo=-12, agua=0, dur=0.10, **_REG),
    dict(nome="inclinar", ombro=48, cotovelo=18, cabo=-32, agua=1, dur=0.10, **_REG),
    dict(nome="regando_a", ombro=50, cotovelo=18, cabo=-40, agua=2, dur=0.12, **_REG),
    dict(nome="regando_b", ombro=50, cotovelo=18, cabo=-40, agua=3, dur=0.12, **_REG),
    dict(nome="regando_a", ombro=50, cotovelo=18, cabo=-40, agua=2, dur=0.12, **_REG),
    dict(nome="regando_b", ombro=50, cotovelo=18, cabo=-40, agua=3, dur=0.12, **_REG),
    dict(nome="voltar", ombro=38, cotovelo=17, cabo=-10, agua=4, dur=0.10, **_REG),
    dict(nome="segurar", ombro=26, cotovelo=16, cabo=0, agua=0, dur=0.12, **_REG),
]
# Machado: mesmo arco da enxada (por cima do ombro), mas o golpe termina na altura do joelho, onde
# bateria no tronco da arvore; saem lascas de madeira em vez de terra.
_MAC = dict(atras=False, chao=False, terra=0)
MACHADO = [
    dict(nome="preparar", ombro=40, cotovelo=15, cabo=62, incl=0, desce=0, lascas=0, dur=0.10, **_MAC),
    dict(nome="levantar", ombro=110, cotovelo=25, cabo=168, incl=0, desce=0, lascas=0, dur=0.09, **_MAC),
    dict(nome="no_alto", ombro=166, cotovelo=24, cabo=232, incl=-9, desce=0, lascas=0, dur=0.15,
         **{**_MAC, "atras": True}),
    dict(nome="golpe", ombro=100, cotovelo=10, cabo=122, incl=0, desce=0, lascas=0, dur=0.05, **_MAC),
    dict(nome="impacto", ombro=64, cotovelo=6, cabo=82, incl=9, desce=9, lascas=1, dur=0.11, **_MAC),
    dict(nome="lascas", ombro=64, cotovelo=6, cabo=82, incl=9, desce=9, lascas=2, dur=0.16, **_MAC),
    dict(nome="voltar", ombro=46, cotovelo=12, cabo=64, incl=0, desce=0, lascas=3, dur=0.11, **_MAC),
]
LASCA = (220, 172, 110); LASCA_CLARA = (246, 214, 160)
# Picareta: arco da enxada ate o chao (onde ficam as pedras); no impacto, faisca e lascas de pedra.
_PIC = dict(atras=False, terra=0, lascas=0)
PICARETA = [
    dict(nome="preparar", ombro=30, cotovelo=15, cabo=42, incl=0, desce=0, chao=True, pedra=0, dur=0.10, **_PIC),
    dict(nome="levantar", ombro=105, cotovelo=25, cabo=165, incl=0, desce=0, chao=False, pedra=0, dur=0.09, **_PIC),
    dict(nome="no_alto", ombro=168, cotovelo=22, cabo=228, incl=-9, desce=0, chao=False, pedra=0, dur=0.16,
         **{**_PIC, "atras": True}),
    dict(nome="golpe", ombro=95, cotovelo=10, cabo=118, incl=0, desce=0, chao=False, pedra=0, dur=0.05, **_PIC),
    dict(nome="impacto", ombro=48, cotovelo=8, cabo=45, incl=9, desce=9, chao=True, pedra=1, dur=0.11, **_PIC),
    dict(nome="pedra", ombro=48, cotovelo=8, cabo=45, incl=9, desce=9, chao=True, pedra=2, dur=0.16, **_PIC),
    dict(nome="voltar", ombro=34, cotovelo=14, cabo=44, incl=0, desce=0, chao=True, folga=30, pedra=3, dur=0.11, **_PIC),
]
# Foice (uma mao): puxa para tras perto do quadril e passa baixo e rapido para a frente, cortando o mato;
# pedacinhos de capim voam.
_FOI = dict(atras=False, terra=0, lascas=0, pedra=0, chao=False)
FOICE = [
    dict(nome="preparar", ombro=10, cotovelo=25, cabo=20, incl=0, desce=0, capim=0, dur=0.10, **_FOI),
    dict(nome="puxar", ombro=-28, cotovelo=30, cabo=-30, incl=-9, desce=9, capim=0, dur=0.14, **_FOI),
    dict(nome="golpe", ombro=4, cotovelo=6, cabo=48, incl=0, desce=18, capim=0, dur=0.05, **_FOI),
    dict(nome="corte", ombro=30, cotovelo=0, cabo=78, incl=9, desce=18, capim=1, dur=0.09, **_FOI),
    dict(nome="seguir", ombro=60, cotovelo=12, cabo=110, incl=9, desce=9, capim=2, dur=0.14, **_FOI),
    dict(nome="voltar", ombro=22, cotovelo=22, cabo=38, incl=0, desce=0, capim=3, dur=0.12, **_FOI),
]
# Pa: crava na terra, faz alavanca, ergue um monte de terra na lamina e joga para a frente.
_PA = dict(atras=False, lascas=0, pedra=0, capim=0)
PA = [
    dict(nome="preparar", ombro=34, cotovelo=18, cabo=26, incl=0, desce=0, chao=True, folga=12, terra=0, dur=0.10, **_PA),
    dict(nome="levantar", ombro=68, cotovelo=22, cabo=62, incl=-9, desce=0, chao=False, terra=0, dur=0.10, **_PA),
    dict(nome="cravar", ombro=36, cotovelo=8, cabo=20, incl=9, desce=9, chao=True, terra=1, dur=0.10, **_PA),
    dict(nome="alavanca", ombro=26, cotovelo=14, cabo=34, incl=0, desce=9, chao=True, folga=10, terra=2, monte=True, dur=0.14, **_PA),
    dict(nome="erguer", ombro=62, cotovelo=22, cabo=70, incl=-9, desce=0, chao=False, terra=0, monte=True, dur=0.12, **_PA),
    dict(nome="jogar", ombro=98, cotovelo=16, cabo=112, incl=9, desce=0, chao=False, terra=0, jogar=2, dur=0.12, **_PA),
    dict(nome="voltar", ombro=46, cotovelo=18, cabo=40, incl=0, desce=0, chao=False, terra=0, jogar=3, dur=0.12, **_PA),
]
# Vara de pescar: so o heroi com a vara (a linha e a boia sao desenhadas pelo jogo, da ponta da vara
# ate a boia; a posicao da ponta em cada quadro vai no info.json).
_VAR = dict(terra=0, lascas=0, pedra=0, capim=0, chao=False, desce=0)
PESCA = [
    dict(nome="segurar", ombro=45, cotovelo=35, cabo=135, incl=0, atras=False, dur=0.14, **_VAR),
    dict(nome="recuar", ombro=150, cotovelo=40, cabo=200, incl=-9, atras=True, dur=0.18, **_VAR),
    dict(nome="lancar", ombro=95, cotovelo=15, cabo=125, incl=0, atras=False, dur=0.06, **_VAR),
    dict(nome="soltar", ombro=68, cotovelo=12, cabo=104, incl=9, atras=False, dur=0.14, **_VAR),
    dict(nome="esperar_a", ombro=55, cotovelo=30, cabo=120, incl=0, atras=False, dur=0.40, **_VAR),
    dict(nome="esperar_b", ombro=55, cotovelo=30, cabo=117, incl=0, atras=False, dur=0.40, **_VAR),
    dict(nome="fisgar", ombro=100, cotovelo=32, cabo=162, incl=-9, atras=False, dur=0.12, **_VAR),
    dict(nome="recolher_a", ombro=82, cotovelo=30, cabo=150, incl=0, atras=False, dur=0.12, **_VAR),
    dict(nome="recolher_b", ombro=80, cotovelo=32, cabo=146, incl=0, atras=False, dur=0.12, **_VAR),
]
CAPIM = (96, 160, 58); CAPIM_CLARO = (164, 214, 96)
PEDRA = (138, 146, 158); PEDRA_CLARA = (196, 202, 210); FAISCA = (255, 246, 190); FAISCA_COR = (255, 196, 64)
AGUA = (112, 186, 236); AGUA_CLARA = (210, 240, 255); AGUA_ESC = (52, 104, 160)
TERRA = (148, 98, 58); TERRA_CLARA = (182, 130, 82)


def rot(t):
    return L.rot(math.radians(t))


class RigAcao(L.Rig):
    def __init__(self, medidas=None):
        super().__init__(medidas)
        self.off = self.off + np.array(MARGEM)
        self.CW += 2 * MARGEM[0]
        self.CH += MARGEM[1]
        self.ferr = {}                 # carrega cada ferramenta so quando for usada

    def _ferr(self, nome):
        if nome not in self.ferr:
            t = FD.FERRAMENTAS[nome]()
            if nome == "enxada_simples":           # so a enxada de teste nao tem contorno no desenho
                L.contorna(t)
            self.ferr[nome] = t
        return self.ferr[nome]

    def mao(self, desl, ombro, cotovelo):
        """Posicao do punho (no canvas) para os angulos do braco."""
        S = np.array(self.R.OMBRO, float); E0 = np.array(self.R.COTOVELO, float); P0 = np.array(PUNHO, float)
        S1 = S + self.off + desl
        E1 = S1 + rot(ombro) @ (E0 - S)
        return E1 + rot(ombro + cotovelo) @ (P0 - E0)

    def ferramenta(self, nome, punho, cabo, encostar, folga=0):
        """Camada da ferramenta. Se encostar=True, ajusta o angulo do cabo ate a lamina ficar 'folga' px
        acima do chao (0 = tocando o chao)."""
        t = self._ferr(nome)
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

    def lascas(self, cam, ponto, fase):
        """Lascas de madeira saltando do ponto do golpe (para tras e para cima)."""
        if fase == 0:
            return
        sobe = {1: 0.35, 2: 1.0, 3: 0.55}[fase]
        for dx, alt, larg, alt_l in ((-70, 80, 26, 14), (-25, 120, 20, 12), (30, 95, 22, 12), (60, 50, 18, 10)):
            x = int(ponto[0] + dx * sobe); y = int(ponto[1] - alt * sobe + (40 * sobe * sobe if fase == 3 else 0))
            pedaco = np.zeros((alt_l + 14, larg + 14, 4), np.int32)
            pedaco[3:-3, 3:-3] = (*LASCA, 255); pedaco[3:9, 3:-6, :3] = LASCA_CLARA
            L.contorna(pedaco, 6)
            y0, x0 = y - pedaco.shape[0] // 2, x - pedaco.shape[1] // 2
            reg = cam[y0:y0 + pedaco.shape[0], x0:x0 + pedaco.shape[1]]
            m = pedaco[:reg.shape[0], :reg.shape[1], 3] > 0
            reg[m] = pedaco[:reg.shape[0], :reg.shape[1]][m]

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
        self.bico = None
        if nome_ferr == "regador":                       # ponta do chuveirinho (de onde sai a agua)
            t = self._ferr(nome_ferr)
            ys, xs = np.nonzero(t[..., 3] > 0)
            x_max = xs.max()
            ponta = np.array([x_max - 4, ys[xs >= x_max - 10].mean() + 10], float) - np.array(FD.pega_de(nome_ferr))
            self.bico = punho + rot(cabo) @ ponta
        visivel = np.zeros(dst.shape[:2], bool)          # onde a ferramenta aparece no quadro final
        frente = np.zeros(dst.shape[:2], bool)           # o que foi desenhado por cima da ferramenta
        ja_colou = [False]

        def cola(cam, eh_ferr=False):
            m = cam[..., 3] > 0
            dst[m] = cam[m]
            visivel[m] = eh_ferr
            if eh_ferr:
                ja_colou[0] = True; frente[m] = False
            elif ja_colou[0]:
                frente[m] = True

        if q["atras"]:
            cola(ferr, True)
        corpo = np.zeros_like(dst)
        corpo[self.off[1] + bob:self.off[1] + bob + self.H, self.off[0] + incl:self.off[0] + incl + self.W] = self.p["corpo"]
        cola(corpo)
        if not q["atras"]:
            cola(ferr, True)
        cola(self.braco(dst, desl, q["ombro"], q["cotovelo"]))
        # (terra e lascas sao desenhadas depois, no tamanho do jogo: veja desenha_particulas)
        # ponto onde a lamina toca o chao (para a terra)
        m = ferr[..., 3] > 0
        ys, xs = np.nonzero(m)
        baixo = ys.max()
        ponto = (int(xs[ys >= baixo - 6].mean()), int(baixo))
        d2 = (xs - punho[0]) ** 2 + (ys - punho[1]) ** 2
        self.ponta = (float(xs[d2.argmax()]), float(ys[d2.argmax()]))
        self.punho = (float(punho[0]), float(punho[1]))
        self.visivel = visivel
        self.frente = frente
        return dst, ponto, cabo


def gera(rig, nome_ferr, poses, extra=16):
    """Quadros grandes -> reduzidos (9x) com a paleta do heroi + cores da ferramenta.
    A borda da ferramenta nao e escurecida (o desenho dela ja tem contorno)."""
    grandes, mascaras, frentes, ponto = [], [], [], None
    for q in poses:                                       # 1a passada: acha o ponto do impacto (terra)
        if q.get("terra") == 1 or q.get("lascas") == 1 or q.get("pedra") == 1 or q.get("capim") == 1:
            ponto = rig.quadro_acao(nome_ferr, q, None)[1]
    bicos, pontas, punhos = [], [], []
    for q in poses:
        f = rig.quadro_acao(nome_ferr, q, ponto)[0]
        grandes.append(f); bicos.append(rig.bico); pontas.append(rig.ponta); punhos.append(rig.punho)
        mk = np.zeros(f.shape, np.int32); mk[rig.visivel] = 255; mascaras.append(mk)
        fr = np.zeros(f.shape, np.int32); fr[rig.frente] = 255; frentes.append(fr)
    RR = rig.R
    piv_src = (RR.QUADRIL[0], RR.CHAO)
    red, pivot = L.reduz_box([rig.parado()] + grandes, rig, piv_src)
    vazio = np.zeros_like(mascaras[0])
    ferr_m = [m[..., 3] >= 128 for m in L.reduz_box([vazio] + mascaras, rig, piv_src)[0]]
    frente_m = [m[..., 3] >= 128 for m in L.reduz_box([vazio] + frentes, rig, piv_src)[0]]
    pal_heroi = np.array(json.load(open(os.path.join(ARTE, "heroi.json")))["paleta"])
    pal_ferr = FD.paleta_de(nome_ferr)
    if pal_ferr is None:                                  # ferramenta sem paleta propria (enxada de teste)
        pal = paleta_com_ferramenta(red, pal_heroi, extra)
        return L.aplica_paleta(red, pal, ferr_m), pivot, pal, grandes
    finais = L.aplica_paleta(red, pal_heroi, ferr_m)
    ninho = [[0, 1, 0], [1, 1, 1], [0, 1, 0]]
    for f, r, fm, fr in zip(finais, red, ferr_m, frente_m):
        fm = fm & (r[..., 3] == 255)
        if not fm.any():
            continue
        # cores da propria ferramenta (nitidas, sem misturar com as do heroi)
        cor = r[fm][:, :3].astype(int)
        f[fm, :3] = pal_ferr[((cor[:, None, :] - pal_ferr[None]) ** 2).sum(-1).argmin(1)]
        # contorno firme de 1 px em volta (menos onde o braco/mao esta por cima)
        anel = ndi.binary_dilation(fm, structure=ninho) & ~fm & ~fr
        f[anel, :3] = FD.CONTORNO_JOGO; f[anel, 3] = 255
    # agua, terra e lascas (desenhadas direto no tamanho do jogo, pixel a pixel, para ficarem nitidas)
    px_src = RR.QUADRIL[0] + rig.off[0]; chao_src = RR.CHAO + rig.off[1] + 1
    # vistas de frente/costas: a ferramenta bate no chao na frente (abaixo) ou atras (acima) dos pes, e
    # de costas os efeitos ficam atras do heroi (so pintam onde o quadro esta vazio)
    chao_ef = pivot[1] - 1 + round(getattr(rig, "CHAO_BATIDA", 0) / RR.ESCALA)
    atras = getattr(rig, "EFEITO_ATRAS", False)
    ct = getattr(rig, "DE_FRENTE", False)
    fora = 0
    if ponto is not None:
        gx = pivot[0] + (ponto[0] - px_src) / RR.ESCALA
        gy = pivot[1] + (ponto[1] - chao_src) / RR.ESCALA
        if hasattr(rig, "DE_FRENTE"):
            fora = (1 if gx > pivot[0] else -1) if abs(gx - pivot[0]) > 3 else 2
        for f, q in zip(finais[1:], poses):
            if q.get("terra"):
                desenha_particulas(f, gx, min(gy, chao_ef), "terra", q["terra"], atras, ct, fora)
            if q.get("lascas"):
                desenha_particulas(f, gx, gy, "lascas", q["lascas"], atras, ct, fora)
            if q.get("pedra"):
                desenha_particulas(f, gx, min(gy, chao_ef), "pedra", q["pedra"], atras, ct, fora)
            if q.get("capim"):
                desenha_particulas(f, gx, min(gy, chao_ef), "capim", q["capim"], atras, ct, fora)
    rig.pontas_jogo = [(float(pivot[0] + (pt[0] - px_src) / RR.ESCALA), float(pivot[1] + (pt[1] - chao_src) / RR.ESCALA))
                       for pt in pontas]
    for f, q, pt, pu in zip(finais[1:], poses, pontas, punhos):   # pa: monte de terra na lamina e terra jogada
        tx = pivot[0] + (pt[0] - px_src) / RR.ESCALA
        ty = pivot[1] + (pt[1] - chao_src) / RR.ESCALA
        if q.get("monte"):
            # em cima da lamina: 4 px para tras da ponta (na direcao da mao) e 2 px acima
            d = np.array(pt) - np.array(pu); d /= max(1e-6, np.hypot(*d))
            desenha_monte(f, tx - 4 * d[0], ty - 4 * d[1] - 2, atras and not q.get("atras"))
        if q.get("jogar"):
            desenha_particulas(f, tx + 2, ty - 2, "terra", q["jogar"], atras and not q.get("atras"), ct)
    for f, q, b in zip(finais[1:], poses, bicos):
        if q.get("agua") and b is not None:
            bx = pivot[0] + (b[0] - px_src) / RR.ESCALA
            by = pivot[1] + (b[1] - chao_src) / RR.ESCALA
            desenha_agua(f, bx, by, chao_ef, q["agua"], getattr(rig, "AGUA_DIR", 1), atras)
    return finais, pivot, np.concatenate([pal_heroi, pal_ferr, [FD.CONTORNO_JOGO]]), grandes


def desenha_particulas(f, x0, y0, tipo, fase, so_vazio=False, contorno_total=False, fora=0):
    """Torroes de terra (enxada) ou lascas de madeira (machado) com contorno de 1 px, no tamanho do jogo.
    fase 1 = acabaram de sair, 2 = no alto, 3 = caindo."""
    H, W = f.shape[:2]
    if tipo == "terra":
        cores = (TERRA_CLARA, TERRA); forma = [(0, 0), (1, 0), (0, 1), (1, 1)]
        trajetos = [(-6, -4), (1, -7), (6, -3)]
    elif tipo == "capim":
        cores = (CAPIM_CLARO, CAPIM); forma = [(0, 0), (0, 1)]
        trajetos = [(2, -6), (6, -9), (9, -4), (-2, -8), (12, -7)]
    elif tipo == "pedra":
        cores = (PEDRA_CLARA, PEDRA); forma = [(0, 0), (1, 0), (0, 1), (1, 1)]
        trajetos = [(-7, -6), (-1, -10), (5, -8), (8, -3)]
        if fase == 1:                                 # faisca no ponto do golpe
            for (dx, dy), cor in (((0, -1), FAISCA), ((-1, -1), FAISCA_COR), ((1, -1), FAISCA_COR),
                                  ((0, -2), FAISCA_COR), ((0, 0), FAISCA_COR), ((-2, -3), FAISCA), ((2, -3), FAISCA)):
                x, y = int(round(x0 + dx)), int(round(y0 + dy))
                if 0 <= x < W and 0 <= y < H and not (so_vazio and f[y, x, 3]):
                    f[y, x, :3] = cor; f[y, x, 3] = 255
    else:
        cores = (LASCA_CLARA, LASCA); forma = [(0, 0), (1, 0)]
        trajetos = [(-9, -7), (-3, -11), (4, -9), (9, -4)]
    if fora:                                          # frente/costas: tudo voa para fora do corpo e mais alto
        trajetos = {"terra": [(-9, -5), (-3, -11), (-13, -10)],
                    "capim": [(-3, -7), (-8, -12), (-12, -5), (-1, -12), (-15, -9)],
                    "pedra": [(-9, -6), (-3, -12), (-14, -10), (-6, -2)],
                    "lascas": [(-10, -7), (-4, -13), (-14, -11), (-7, -2)]}[tipo]
        if fora == 2:                                 # golpe no meio: metade para cada lado
            trajetos = [((1 if i % 2 else -1) * abs(dx), dy) for i, (dx, dy) in enumerate(trajetos)]
        else:
            trajetos = [(fora * abs(dx), dy) for dx, dy in trajetos]
            x0 += 2 * fora
    andou = {1: 0.35, 2: 1.0, 3: 0.75}[fase]
    cai = {1: 0, 2: 0, 3: 3}[fase]
    for i, (dx, dy) in enumerate(trajetos):
        if fase == 1 and i % 2:
            continue
        cx = int(round(x0 + dx * andou)); cy = int(round(y0 + dy * andou + cai))
        pts = [(cx + a, cy + b) for a, b in forma]
        anel = {(x + ax, y + ay) for x, y in pts for ax, ay in ((1, 0), (-1, 0), (0, 1), (0, -1))} - set(pts)
        livre = [(x, y) for x, y in pts if 0 <= x < W and 0 <= y < H and not (so_vazio and f[y, x, 3])]
        for x, y in anel:              # contorno_total: na frente do heroi (contorno por cima dele tambem)
            if 0 <= x < W and 0 <= y < H and (f[y, x, 3] == 0 or contorno_total):
                f[y, x, :3] = FD.CONTORNO_JOGO; f[y, x, 3] = 255
        for x, y in livre:
            f[y, x, :3] = cores[0] if (y == cy) else cores[1]; f[y, x, 3] = 255


def desenha_monte(f, x0, y0, so_vazio=False):
    """Montinho de terra em cima da lamina da pa (5x3 px com contorno)."""
    H, W = f.shape[:2]
    cx, cy = int(round(x0)), int(round(y0)) - 2
    forma = [(-1, 0), (0, 0), (1, 0), (2, 0), (-2, 1), (-1, 1), (0, 1), (1, 1), (2, 1), (3, 1), (0, -1), (1, -1)]
    pts = [(cx + a, cy + b) for a, b in forma]
    anel = {(x + ax, y + ay) for x, y in pts for ax, ay in ((1, 0), (-1, 0), (0, 1), (0, -1))} - set(pts)
    livre = [(x, y) for x, y in pts if 0 <= x < W and 0 <= y < H and not (so_vazio and f[y, x, 3])]
    for x, y in anel:
        if 0 <= x < W and 0 <= y < H and f[y, x, 3] == 0:
            f[y, x, :3] = FD.CONTORNO_JOGO; f[y, x, 3] = 255
    for x, y in livre:
        f[y, x, :3] = TERRA_CLARA if y <= cy else TERRA; f[y, x, 3] = 255


def desenha_agua(f, bx, by, chao_y, fase, dirx=1, so_vazio=False):
    """Gotas caindo do chuveirinho ate o chao (duas colunas, alturas alternadas) e respingo no chao.
    dirx = para que lado da imagem a agua cai (+1 direita, -1 esquerda); so_vazio = fica atras do heroi."""
    H, W = f.shape[:2]

    def px(x, y, cor):
        x = bx + (x - bx) * dirx
        x, y = int(round(x)), int(round(y))
        if 0 <= x < W and 0 <= y < H and not (so_vazio and f[y, x, 3]):
            f[y, x, :3] = cor; f[y, x, 3] = 255

    def gota(x, y):
        px(x, y, AGUA_CLARA); px(x, y + 1, AGUA)

    queda = chao_y - by
    if queda <= 2:
        return
    fracoes = {1: [(0, 0.08), (1, 0.22)], 2: [(0, 0.12), (1, 0.30), (0, 0.48), (1, 0.66), (0, 0.84)],
               3: [(1, 0.04), (0, 0.21), (1, 0.39), (0, 0.57), (1, 0.75), (0, 0.93)], 4: [(0, 0.62)]}[fase]
    for coluna, fr in fracoes:
        x = bx - 1 + 2 * coluna + 2.0 * fr           # cai um pouco para a frente
        y = by + 1 + fr * (queda - 2)
        if y < chao_y - 1:
            gota(x, y)
    if fase in (2, 3, 4):                             # respingo no chao
        x0 = bx + 2.0
        for dx in (-1, 0, 1, 2):
            px(x0 + dx, chao_y, AGUA)
        px(x0 + (-2 if fase == 2 else 3), chao_y - 1, AGUA_CLARA)
        if fase != 4:
            px(x0 + (3 if fase == 2 else -2), chao_y - 2, AGUA_CLARA)
        px(x0, chao_y - 1, AGUA_ESC)


def paleta_com_ferramenta(reduzidos, pal_heroi, extra=8):
    """Paleta do heroi (32 cores, a mesma do andar) + algumas cores so para a ferramenta e a terra."""
    todos = np.concatenate([r[r[..., 3] == 255][:, :3] for r in reduzidos]).astype(int)
    d = ((todos[:, None, :] - pal_heroi[None]) ** 2).sum(-1).min(1)
    longe = todos[d > 900]
    if len(longe) < extra:
        return pal_heroi
    novas = L.paleta([np.concatenate([longe, np.full((len(longe), 1), 255)], 1).reshape(-1, 1, 4).astype(np.uint8)], extra)
    return np.concatenate([pal_heroi, novas])


ACOES = {"enxada": ("enxada", ENXADA), "regador": ("regador", REGADOR), "machado": ("machado", MACHADO),
         "picareta": ("picareta", PICARETA), "foice": ("foice", FOICE),
         "pa": ("pa", PA), "vara": ("vara", PESCA)}


def gera_acao(acao, esquerda=False):
    """Gera uma acao (lado direito, ou esquerdo com o desenho da esquerda: as contas sao feitas numa
    copia virada e cada quadro e desvirado no fim, como no andar). Devolve quadros, pivo e info."""
    ferr_nome, poses = ACOES[acao]
    if esquerda:
        import rig_heroi_esq as RE
        rig = RigAcao(RE)
    else:
        rig = RigAcao()
    finais, pivot, pal, grandes = gera(rig, ferr_nome, poses)
    pontas = list(rig.pontas_jogo)
    if esquerda:
        larg = finais[0].shape[1]
        finais = [np.ascontiguousarray(f[:, ::-1]) for f in finais]
        pivot = (larg - 1 - pivot[0], pivot[1])
        pontas = [(larg - 1 - x, y) for x, y in pontas]
    info = dict(pivot=[int(v) for v in pivot], tamanho=list(finais[0].shape[1::-1]), cores=len(pal),
                quadros=[dict(nome=q["nome"], duracao_s=q["dur"], ponta_ferramenta=[round(v, 1) for v in pontas[i]])
                         for i, q in enumerate(poses)])
    return finais, pivot, info, grandes


if __name__ == "__main__":
    acao = next((a for a in sys.argv[1:] if not a.startswith("--")), "enxada")
    esq = "--esq" in sys.argv
    pasta = os.path.join(SAIDA, f"{acao}_{'esq' if esq else 'lado'}"); os.makedirs(pasta, exist_ok=True)
    finais, pivot, info, grandes = gera_acao(acao, esq)
    poses = ACOES[acao][1]
    Image.fromarray(finais[0], "RGBA").save(os.path.join(pasta, "parado.png"))
    for i, (f, q) in enumerate(zip(finais[1:], poses)):
        Image.fromarray(f, "RGBA").save(os.path.join(pasta, f"{acao}_{i}_{q['nome']}.png"))
    json.dump(info, open(os.path.join(pasta, "info.json"), "w"), indent=1)
    print(acao, "esq" if esq else "dir", "quadro", info["tamanho"], "pivo", pivot)
