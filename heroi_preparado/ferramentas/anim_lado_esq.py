"""Andar do heroi para a ESQUERDA, a partir do desenho do lado esquerdo (fonte/lado_esq.png).

Usa a mesma tecnica e o mesmo ciclo aprovados do lado direito (anim_lado.py): mesmas posicoes dos
pes, mesmo sobe e desce, mesmo balanco dos bracos, mesma velocidade. As contas sao feitas numa copia
virada do desenho da esquerda (veja rig_heroi_esq.py) e cada quadro e desvirado no fim, entao todos
os pixels sao do desenho da esquerda e ele anda olhando para a esquerda.
"""
import json, os, sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lado as L
import rig_heroi_esq as RE


def gera():
    rig = L.Rig(RE)
    grandes, estic = [], []
    for k in range(8):
        f, e = rig.quadro(k); grandes.append(f); estic.append(round(e, 1))
    finais, pivot = L.reduz([rig.parado()] + grandes, rig, pivo=(RE.QUADRIL[0], RE.CHAO))
    # desvira: volta a olhar para a esquerda
    finais = [np.ascontiguousarray(f[:, ::-1]) for f in finais]
    grandes = [np.ascontiguousarray(f[:, ::-1]) for f in grandes]
    largura = finais[0].shape[1]
    pivot = (int(largura - 1 - pivot[0]), int(pivot[1]))
    return finais, grandes, pivot, estic


if __name__ == "__main__":
    os.makedirs(RE.SAIDA, exist_ok=True)
    finais, grandes, pivot, estic = gera()
    print("esticamento (px do desenho):", estic)
    for i, f in enumerate(finais):
        Image.fromarray(f, "RGBA").save(os.path.join(RE.SAIDA, ("parado" if i == 0 else f"andar_{i-1}") + ".png"))
    if "--grande" in sys.argv:
        for k, f in enumerate(grandes):
            Image.fromarray(f.clip(0, 255).astype(np.uint8), "RGBA").save(os.path.join(RE.SAIDA, f"grande_{k}.png"))
    json.dump(dict(pivot=pivot, tamanho=list(finais[0].shape[1::-1]), duracao_ms=L.DURACAO_MS, direcao="lado_esq"),
              open(os.path.join(RE.SAIDA, "info.json"), "w"))
    print("quadro final", finais[0].shape[1::-1], "pivot", pivot)
