"""Desenho das ferramentas de trabalho no tamanho do desenho do heroi (9x maior que o jogo).

Cada ferramenta e desenhada "em pe": o ponto onde a mao segura fica em PEGA, o cabo desce
(para baixo da imagem) e a cabeca da ferramenta fica na ponta de baixo. Para usar, gira-se a
imagem em volta da PEGA (anim_lado.coloca), do mesmo jeito que o braco.
As cores seguem o estilo do jogo: madeira quente, metal azulado claro e contorno escuro colorido
(o contorno e refeito com espessura uniforme por anim_lado.contorna).
"""
import numpy as np
from PIL import Image, ImageDraw

LARG, ALT = 220, 380
PEGA = (110, 40)                     # onde a mao segura (perto da ponta de tras do cabo)

MADEIRA = (156, 98, 52); MADEIRA_CLARA = (196, 134, 72); MADEIRA_ESC = (112, 66, 34)
METAL = (150, 164, 176); METAL_CLARO = (214, 224, 230); METAL_ESC = (92, 100, 116)
LATA = (96, 150, 190); LATA_CLARA = (150, 196, 224); LATA_ESC = (60, 102, 140)


def _cabo(d, x, y0, y1, larg=34):
    d.rectangle((x - larg // 2, y0, x + larg // 2, y1), fill=MADEIRA)
    d.rectangle((x - larg // 2 + 7, y0, x - larg // 2 + 15, y1), fill=MADEIRA_CLARA)   # luz (o contorno come 7 px de cada lado)
    d.rectangle((x + larg // 2 - 14, y0, x + larg // 2 - 7, y1), fill=MADEIRA_ESC)


def enxada():
    """Cabo comprido e lamina de metal perpendicular na ponta (virada para -x)."""
    im = Image.new("RGBA", (LARG, ALT), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = PEGA[0]
    _cabo(d, x, PEGA[1] - 30, 300)
    # bocal de metal que prende a lamina
    d.rectangle((x - 24, 284, x + 24, 322), fill=METAL_ESC)
    d.rectangle((x - 17, 291, x - 6, 315), fill=METAL)
    # lamina: sai para a esquerda (-x) e termina num fio reto
    d.polygon([(x - 16, 292), (x - 104, 296), (x - 112, 352), (x - 16, 334)], fill=METAL)
    d.polygon([(x - 16, 292), (x - 104, 296), (x - 103, 310), (x - 16, 306)], fill=METAL_CLARO)
    d.polygon([(x - 112, 340), (x - 112, 352), (x - 16, 334), (x - 16, 324)], fill=METAL_ESC)
    return np.array(im).astype(np.int32)


FERRAMENTAS = {"enxada": enxada}


if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import anim_lado as L
    t = enxada()
    L.contorna(t)
    im = Image.fromarray(t.clip(0, 255).astype(np.uint8))
    bg = Image.new("RGBA", im.size, (96, 140, 70, 255)); bg.alpha_composite(im)
    bg.save(sys.argv[1] if len(sys.argv) > 1 else "enxada.png")
