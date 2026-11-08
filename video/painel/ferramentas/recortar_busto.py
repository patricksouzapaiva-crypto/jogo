"""Recorta pranchas de poses da cintura para cima (PNG com alfa) e mede a cabeça de cada pose.

Uso: python recortar_busto.py prancha.png linhas colunas pasta_saida grupo nome1,nome2,...
grupo: conversa | enfase | sombrio (o motor usa 'conversa' para as trocas automáticas)
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


def recortar(prancha, linhas, colunas, saida, grupo, nomes):
    rgba = np.array(Image.open(prancha).convert("RGBA"))
    H, W = rgba.shape[:2]
    a = rgba[..., 3] > 25
    n, rot, est, cen = cv2.connectedComponentsWithStats(a.astype(np.uint8), 8)
    grupos = {}
    for i in range(1, n):
        if est[i, cv2.CC_STAT_AREA] < 40:
            continue
        cx, cy = cen[i]
        cel = int(cy // (H / linhas)) * colunas + int(cx // (W / colunas))
        grupos.setdefault(cel, []).append(i)
    saida = Path(saida); saida.mkdir(parents=True, exist_ok=True)
    arq = saida / "poses.json"
    meta = json.load(open(arq)) if arq.exists() else {"tipo": "busto", "poses": {}}
    for cel, comps in sorted(grupos.items()):
        if cel >= len(nomes):
            continue
        mask = np.isin(rot, comps)
        mask = cv2.dilate(mask.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
        ys, xs = np.nonzero(mask)
        y0, y1, x0, x1 = max(0, ys.min() - 6), min(H, ys.max() + 7), max(0, xs.min() - 6), min(W, xs.max() + 7)
        img = rgba[y0:y1, x0:x1].copy()
        img[..., 3] = np.where(mask[y0:y1, x0:x1], img[..., 3], 0)
        Image.fromarray(img).save(saida / f"{nomes[cel]}.png", optimize=True)
        al = img[..., 3] > 40
        topo = int(np.nonzero(al.any(axis=1))[0].min())
        # largura da cabeça: faixa logo abaixo do topo do cabelo (antes dos ombros), mediana por linha
        larg, centros = [], []
        for y in range(topo + 12, min(al.shape[0], topo + 75)):
            cols = np.nonzero(al[y])[0]
            if len(cols):
                larg.append(cols.max() - cols.min()); centros.append((cols.max() + cols.min()) / 2)
        meta["poses"][nomes[cel]] = {"w": int(img.shape[1]), "h": int(img.shape[0]), "topo": topo,
                                    "centro_x": float(np.median(centros)), "largura_cabeca": float(np.median(larg)),
                                    "grupo": grupo}
    meta["tipo"] = "busto"
    meta["largura_cabeca_mediana"] = float(np.median([p["largura_cabeca"] for p in meta["poses"].values()]))
    json.dump(meta, open(arq, "w"), ensure_ascii=False, indent=1)
    print(f"{len(grupos)} poses ({grupo}) de {Path(prancha).name}")


if __name__ == "__main__":
    p, l, c, s, g, nomes = sys.argv[1:7]
    recortar(p, int(l), int(c), s, g, nomes.split(","))
