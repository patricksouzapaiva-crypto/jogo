"""Importa poses individuais em alta resolução (uma pose por arquivo, meio corpo) para um avatar.

- aceita PNG com fundo transparente ou com fundo liso (cinza/branco/verde): recorta o fundo a partir das bordas;
- remove sujeira solta, apara a área vazia e mede a cabeça (topo, centro e largura) para alinhar as trocas;
- o grupo vem do prefixo do nome: c_ = conversa, e_ = enfase, s_ = sombrio.

Uso: python importar_poses_hd.py <pasta_ou_zip_com_pngs> <pasta_saida_avatar>
"""
import json
import sys
import tempfile
import zipfile
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

GRUPOS = {"c": "conversa", "e": "enfase", "s": "sombrio"}


def remover_fundo(rgba: np.ndarray) -> np.ndarray:
    a = rgba[..., 3]
    if (a < 250).mean() > 0.05:  # já tem transparência de verdade
        return rgba
    rgb = rgba[..., :3].astype(np.int16)
    h, w = a.shape
    borda = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
    cor = np.median(borda, axis=0)
    dist = np.abs(rgb - cor).sum(axis=2)
    parecido = (dist < 38).astype(np.uint8)
    # só o fundo conectado às bordas (não apaga partes da roupa com cor parecida)
    n, rot = cv2.connectedComponents(parecido, 4)
    fundo_ids = set(np.unique(np.concatenate([rot[0], rot[-1], rot[:, 0], rot[:, -1]]))) - {0}
    fundo = np.isin(rot, list(fundo_ids))
    alfa = np.where(fundo, 0, 255).astype(np.uint8)
    alfa = cv2.GaussianBlur(alfa, (0, 0), 1.0)  # borda suave
    out = rgba.copy()
    out[..., 3] = alfa
    return out


def limpar(rgba):
    a = rgba[..., 3] > 30
    n, rot, est, _ = cv2.connectedComponentsWithStats(a.astype(np.uint8), 8)
    if n > 2:
        maior = 1 + int(np.argmax(est[1:, cv2.CC_STAT_AREA]))
        manter = np.zeros(n, bool)
        for i in range(1, n):
            manter[i] = i == maior or est[i, cv2.CC_STAT_AREA] > 0.02 * est[maior, cv2.CC_STAT_AREA]
        rgba = rgba.copy()
        rgba[..., 3] = np.where(manter[rot], rgba[..., 3], 0)
    ys, xs = np.nonzero(rgba[..., 3] > 30)
    m = 12
    y0, y1 = max(0, ys.min() - m), min(rgba.shape[0], ys.max() + m)
    x0, x1 = max(0, xs.min() - m), min(rgba.shape[1], xs.max() + m)
    return rgba[y0:y1, x0:x1]


def medir(rgba):
    al = rgba[..., 3] > 60
    ys = np.nonzero(al.any(axis=1))[0]
    topo, base = int(ys.min()), int(ys.max())
    alt = base - topo
    larg, centros = [], []
    for y in range(topo + int(0.04 * alt), topo + int(0.20 * alt)):  # faixa da cabeça, acima dos ombros
        cols = np.nonzero(al[y])[0]
        if len(cols):
            larg.append(cols.max() - cols.min())
            centros.append((cols.max() + cols.min()) / 2)
    return {"w": int(rgba.shape[1]), "h": int(rgba.shape[0]), "topo": topo,
            "centro_x": float(np.median(centros)), "largura_cabeca": float(np.median(larg))}


def main(origem, destino):
    origem, destino = Path(origem), Path(destino)
    if origem.suffix.lower() == ".zip":
        tmp = Path(tempfile.mkdtemp())
        zipfile.ZipFile(origem).extractall(tmp)
        origem = tmp
    destino.mkdir(parents=True, exist_ok=True)
    arq = destino / "poses.json"
    meta = json.load(open(arq)) if arq.exists() else {"tipo": "busto", "poses": {}}
    for f in sorted(origem.rglob("*")):
        if f.suffix.lower() not in (".png", ".webp", ".jpg", ".jpeg"):
            continue
        nome = f.stem.lower().replace(" ", "_").replace("-", "_")
        rgba = np.array(Image.open(f).convert("RGBA"))
        rgba = limpar(remover_fundo(rgba))
        Image.fromarray(rgba).save(destino / f"{nome}.png", optimize=True)
        m = medir(rgba)
        m["grupo"] = GRUPOS.get(nome.split("_")[0], "conversa")
        meta["poses"][nome] = m
        print(f"{nome:28s} {m['w']}x{m['h']}  cabeça {m['largura_cabeca']:.0f}px  ({m['grupo']})")
    meta["tipo"] = "busto"
    meta["largura_cabeca_mediana"] = float(np.median([p["largura_cabeca"] for p in meta["poses"].values()]))
    json.dump(meta, open(arq, "w"), ensure_ascii=False, indent=1)
    print(f"{len(meta['poses'])} poses em {destino}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
