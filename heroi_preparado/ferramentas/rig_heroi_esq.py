"""Esqueleto do heroi - vista de lado ESQUERDO (desenho proprio, nao e o lado direito espelhado).

Todos os pixels vem de fonte/lado_esq.png (com a luz e os detalhes desse desenho).
Para reaproveitar exatamente a matematica aprovada do lado direito (rig_heroi.py / anim_lado.py),
o desenho da esquerda e virado so DENTRO das contas: as medidas abaixo foram feitas nessa copia
virada (olhando para a direita) e, no fim, anim_lado_esq.py desvira cada quadro. O resultado olha
para a esquerda, com o joelho dobrando para a esquerda e a ponta da bota para a esquerda.

Medidas refeitas no desenho da esquerda (copia virada):
- perna de perto: x ~116..186 (meio 150), separacao das pernas em x ~106..120, bota de perto a
  partir de x 112, bota de longe ate x ~104; sola em y 583
- braco que aparece: manga y 230..282, punho x 72..134 / y 282..317, mao x 64..135 / y 312..422
- costas: borda em x ~80 no ombro; cintura y 338..362
"""
import os
import numpy as np
from PIL import Image, ImageOps

import rig_heroi as base

AQUI = os.path.dirname(os.path.abspath(__file__))
FONTE = os.path.join(AQUI, "..", "fonte", "lado_esq.png")
SAIDA = os.path.join(AQUI, "..", "revisao", "lado_esq")

ESCALA = base.ESCALA
CHAO = 583
PAD_X, PAD_TOP = base.PAD_X, base.PAD_TOP
ESCURO = base.ESCURO

# --- pontos do esqueleto (na copia virada do desenho da esquerda) ---
QUADRIL = (150, 362)
JOELHO = (150, 437)
TORNOZELO = (150, 512)
OMBRO = (108, 252)
COTOVELO = (104, 286)

COSTAS_X = 80
COSTAS_INCLINA = 0.03
COSTAS_RECUO = base.COSTAS_RECUO
MAO_CAIXA = (50, 141, 312, 425)
PUNHO_CAIXA = (62, 140, 278, 322)
CONTORNO_BRACO_CAIXA = (54, 143, 250, 426)
CAMISA = (82, 147, 207)          # cores medidas na manga do desenho da esquerda
CAMISA_ESC = (64, 111, 160)


def carrega():
    a = np.array(ImageOps.mirror(Image.open(FONTE).convert("RGBA"))).astype(np.int32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mag = (a[..., 3] > 0) & (r > 120) & (b > g + 20) & (g < 0.45 * r)
    a[mag, :3] = (26, 6, 6)
    return a


def separa(a):
    import sys
    return base.separa(a, sys.modules[__name__])
