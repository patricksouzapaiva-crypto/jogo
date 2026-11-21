"""Tira o fundo verde das camadas da identidade (brutas/*.png → camadas/*.png com alfa).
Chave por distância de cor ao verde + suavização da borda + despill (o verde que respinga na borda vira neutro).
Corta a sobra transparente. Uso: python3 recortar.py"""
from pathlib import Path
import numpy as np, cv2
AQUI = Path(__file__).parent
for f in sorted((AQUI / "brutas").glob("ID*.png")):
    im = cv2.imread(str(f), cv2.IMREAD_COLOR).astype(np.float32) / 255
    b, g, r = im[..., 0], im[..., 1], im[..., 2]
    verde = g - np.maximum(r, b)                    # quanto o pixel é "mais verde" que o resto
    if np.mean(verde > 0.35) < 0.08:                # fundo sem verde (cenários): copia como está
        cv2.imwrite(str(AQUI / "camadas" / f.name), (im * 255).astype(np.uint8)); continue
    a = np.clip(1 - (verde - 0.12) / 0.28, 0, 1)    # 0 = verde puro, 1 = objeto
    a = cv2.GaussianBlur(a, (0, 0), 0.8)
    m = (a > 0.02).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)   # tira ilhas pequenas de sujeira
    keep = np.zeros_like(m)
    for k in range(1, n):
        if st[k, cv2.CC_STAT_AREA] > 400: keep[lab == k] = 1
    a *= keep
    g2 = np.minimum(g, np.maximum(r, b) * 1.02)     # despill
    out = np.dstack([b, g2, r, a])
    ys, xs = np.where(a > 0.02); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    cv2.imwrite(str(AQUI / "camadas" / f.name), (out[y0:y1, x0:x1] * 255).astype(np.uint8))
    print("ok", f.name, (x1 - x0, y1 - y0))
