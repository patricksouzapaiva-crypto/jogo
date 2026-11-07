"""Prepara um pacote de poses (PNG com alfa) para o motor de painel.

- remove pedaços soltos (riscos e restos da prancha), mantendo o corpo principal;
- mede a cabeça de cada pose (topo, centro e largura) para alinhar as trocas de pose.

Uso: python video/painel/ferramentas/preparar_avatar.py <pasta_poses> <pasta_saida> [nome]
"""
import json
import re
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


def limpar(rgba: np.ndarray) -> np.ndarray:
    a = rgba[..., 3]
    n, rotulos, est, _ = cv2.connectedComponentsWithStats((a > 20).astype(np.uint8), 8)
    if n <= 2:
        return rgba
    maior = 1 + int(np.argmax(est[1:, cv2.CC_STAT_AREA]))
    area_maior = est[maior, cv2.CC_STAT_AREA]
    manter = np.zeros(n, bool)
    for i in range(1, n):
        # mantém o corpo e pedaços grandes (mãos separadas), descarta riscos finos e restos pequenos
        w, h, area = est[i, cv2.CC_STAT_WIDTH], est[i, cv2.CC_STAT_HEIGHT], est[i, cv2.CC_STAT_AREA]
        fino = min(w, h) <= 14 or area < 400
        manter[i] = i == maior or (area > 0.03 * area_maior and not fino)
    mascara = manter[rotulos]
    # dilata 2 px para não comer a borda suave do alfa
    mascara = cv2.dilate(mascara.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    out = rgba.copy()
    out[..., 3] = np.where(mascara, a, 0)
    return out


def aparar_bordas(rgba: np.ndarray) -> np.ndarray:
    """Tira faixas da prancha grudadas no recorte: régua no topo e cabeça vizinha embaixo."""
    a = rgba[..., 3] > 20
    cob = a.sum(axis=1)
    w = rgba.shape[1]
    out = rgba.copy()
    # topo: linhas quase cheias seguidas de queda brusca = régua/borda da prancha
    if cob[0] > 0.85 * w:
        for y in range(1, 15):
            if cob[y] < 0.75 * w:
                out[: y + 1, :, 3] = 0
                break
    # base: corpo cortado reto (linha cheia) seguido de um pedaço pequeno abaixo
    cheia = np.nonzero(cob > 0.8 * cob.max())[0]
    if len(cheia):
        ult = cheia.max()
        if ult < len(cob) - 1 and cob[ult + 1:].max(initial=0) < 0.3 * cob.max():
            out[ult + 1:, :, 3] = 0
    return out


def medir(rgba: np.ndarray) -> dict:
    a = rgba[..., 3] > 40
    ys, xs = np.nonzero(a)
    topo = int(ys.min())
    h = rgba.shape[0]
    # faixa da cabeça: do topo até ~30% da altura do recorte
    fim = topo + int(0.30 * (ys.max() - topo))
    faixa = a[topo:fim]
    cols = np.nonzero(faixa.any(axis=0))[0]
    # centro pela massa da faixa (robusto a mechas soltas)
    yy, xx = np.nonzero(faixa)
    return {"topo": topo, "centro_x": float(xx.mean()), "largura_cabeca": int(cols.max() - cols.min()),
            "corta_topo": bool(a[0].any()), "w": int(rgba.shape[1]), "h": int(h)}


def main(origem, destino, nome="avatar"):
    origem, destino = Path(origem), Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    poses = {}
    for f in sorted(origem.glob("*.png")):
        m = re.search(r"(\d+)_(.+)\.png$", f.name)
        chave = m.group(2) if m else f.stem
        rgba = np.array(Image.open(f).convert("RGBA"))
        rgba = limpar(aparar_bordas(rgba))
        Image.fromarray(rgba).save(destino / f"{chave}.png", optimize=True)
        poses[chave] = medir(rgba)
    med = float(np.median([p["largura_cabeca"] for p in poses.values()]))
    json.dump({"nome": nome, "largura_cabeca_mediana": med, "poses": poses},
              open(destino / "poses.json", "w"), ensure_ascii=False, indent=1)
    print(f"{len(poses)} poses -> {destino}")


if __name__ == "__main__":
    main(*sys.argv[1:])
