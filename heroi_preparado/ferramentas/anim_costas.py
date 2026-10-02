"""Andar do heroi de COSTAS (indo embora da camera), com o mesmo esqueleto da frente.

Herda tudo da vista de frente (anim_frente.RigFrente) e troca so o que muda de costas:
- o pe que da o passo vai um pouco para CIMA na tela (indo embora) e o de tras fica mais embaixo;
- a perna da direita da imagem e a perna direita do heroi (a mesma "de perto" da vista de lado);
- quando o pe sai do chao aparece a sola da bota (faixa mais escura embaixo);
- perna dobrada: a coxa fica um pouco mais escura e a canela pega um pouco mais de luz
  (o contrario da frente, porque agora vemos a parte de tras da perna);
- os bracos usam o mesmo balanco da frente: o que vai para tras vem para a camera (desce, abre um
  pouco e fica na frente de tudo); o que vai para a frente sobe e entra atras do corpo.
"""
import json, os, sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_frente as F
import anim_lado as L

AQUI = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(AQUI, "..", "revisao", "costas")


class RigCostas(F.RigFrente):
    FONTE = os.path.join(AQUI, "..", "fonte", "costas.png")
    CHAO = 583
    MEIO = 148
    CINTURA = 360
    JOELHO_Y = 437
    BARRA_Y = 513
    # (profundidade: + = pe mais para baixo na tela / mais perto da camera; altura do pe)
    PE = [
        (-12, 0),    # 0 contato: o pe da frente pisa mais para cima (mais longe)
        (-6, 0),     # 1 recebe o peso
        (0, 0),      # 2 passagem
        (+6, 2),     # 3 impulso: calcanhar comeca a subir
        (+12, 6),    # 4 so a ponta do pe no chao (pe de tras, mais perto da camera)
        (+8, 18),    # 5 pe sai do chao (aparece a sola)
        (0, 24),     # 6 passagem no ar
        (-8, 12),    # 7 perna vai para a frente
    ]
    BALANCO_LADO = [0, 0, +9, +9, 0, 0, -9, -9]   # peso para o lado da perna de apoio (agora a da direita da imagem)
    FASE = {"e": 4, "d": 0}
    JOELHO_LUZ = -0.08
    CANELA_SOMBRA = -0.05
    SOLA = 0.5
    BRACO_ESQ = dict(y0=238, y1=432, corte=336, x_cima=91, x_baixo=76)
    BRACO_DIR = dict(y0=238, y1=432, corte=336, x_cima=204, x_baixo=221)
    TRONCO = (91, 204)
    PERNAS_X = (25, 270)


if __name__ == "__main__":
    os.makedirs(SAIDA, exist_ok=True)
    rig = RigCostas()
    grandes = [rig.quadro(k) for k in range(8)]
    finais, pivot = L.reduz([rig.parado()] + grandes, rig, pivo=(rig.MEIO, rig.CHAO))
    for i, f in enumerate(finais):
        Image.fromarray(f, "RGBA").save(os.path.join(SAIDA, ("parado" if i == 0 else f"andar_{i-1}") + ".png"))
    if "--grande" in sys.argv:
        for k, f in enumerate(grandes):
            Image.fromarray(f.clip(0, 255).astype(np.uint8), "RGBA").save(os.path.join(SAIDA, f"grande_{k}.png"))
    json.dump(dict(pivot=pivot, tamanho=list(finais[0].shape[1::-1]), duracao_ms=F.DURACAO_MS, direcao="costas"),
              open(os.path.join(SAIDA, "info.json"), "w"))
    print("quadro final", finais[0].shape[1::-1], "pivot", pivot)
