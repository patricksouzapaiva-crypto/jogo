"""Recorta uma prancha de poses de corpo inteiro (PNG com alfa) em arquivos individuais.

Cada mancha (componente conexo) é atribuída à célula da grade onde está seu centro; braços que
invadem a célula vizinha continuam com a pose certa. Mede pés, centro do tronco e topo.

Uso: python recortar_prancha.py prancha.png linhas colunas pasta_saida nome1,nome2,...
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


def recortar(prancha, linhas, colunas, saida, nomes):
    rgba = np.array(Image.open(prancha).convert("RGBA"))
    H, W = rgba.shape[:2]
    a = rgba[..., 3] > 25
    n, rot, est, cen = cv2.connectedComponentsWithStats(a.astype(np.uint8), 8)
    grupos = {}
    for i in range(1, n):
        if est[i, cv2.CC_STAT_AREA] < 30:
            continue
        cx, cy = cen[i]
        cel = int(cy // (H / linhas)) * colunas + int(cx // (W / colunas))
        grupos.setdefault(cel, []).append(i)
    saida = Path(saida); saida.mkdir(parents=True, exist_ok=True)
    meta = json.load(open(saida / "poses.json")) if (saida / "poses.json").exists() else {"poses": {}}
    for cel, comps in sorted(grupos.items()):
        if cel >= len(nomes):
            continue
        mask = np.isin(rot, comps)
        mask = cv2.dilate(mask.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
        ys, xs = np.nonzero(mask)
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        pad = 6
        y0, x0 = max(0, y0 - pad), max(0, x0 - pad)
        y1, x1 = min(H, y1 + pad), min(W, x1 + pad)
        img = rgba[y0:y1, x0:x1].copy()
        img[..., 3] = np.where(mask[y0:y1, x0:x1], img[..., 3], 0)
        Image.fromarray(img).save(saida / f"{nomes[cel]}.png", optimize=True)
        al = img[..., 3] > 40
        yy = np.nonzero(al.any(axis=1))[0]
        topo, pe = int(yy.min()), int(yy.max())
        # centro do tronco: massa da faixa entre 35% e 60% da altura (ignora braços abertos o mais possível)
        faixa = al[topo + int(0.35 * (pe - topo)): topo + int(0.6 * (pe - topo))]
        cols = np.nonzero(faixa)[1]
        meta["poses"][nomes[cel]] = {"w": int(img.shape[1]), "h": int(img.shape[0]), "topo": topo, "pe_y": pe,
                                    "centro_x": float(np.median(cols))}
    # escala de referência POR PRANCHA (pranchas diferentes podem ter tamanhos de desenho diferentes)
    desta = [nomes[c] for c in grupos if c < len(nomes)]
    ref = float(np.median([meta["poses"][k]["pe_y"] - meta["poses"][k]["topo"] for k in desta]))
    for k in desta:
        meta["poses"][k]["altura_ref"] = ref
    alturas = [p["pe_y"] - p["topo"] for p in meta["poses"].values()]
    meta.update({"tipo": "corpo", "altura_mediana": float(np.median(alturas))})
    json.dump(meta, open(saida / "poses.json", "w"), ensure_ascii=False, indent=1)
    print(f"{len(grupos)} poses de {Path(prancha).name}")


if __name__ == "__main__":
    p, l, c, s, nomes = sys.argv[1:6]
    recortar(p, int(l), int(c), s, nomes.split(","))
