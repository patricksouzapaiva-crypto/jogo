"""Ep. 12 (24/11, pedido do usuário): restauração das gravuras mais importantes, para a câmera poder chegar perto.
- Pequenas (Sekien, ~400 px): Real-ESRGAN x4plus ("fiel ao papel": mantém a textura; o traço volta nítido). O modelo
  (~64 MB) fica fora do repo (/dev/shm/modelos). CPU, em blocos de 256 px.
- Grandes (museus, 2000–3400 px): restauração de COR, sem IA: o amarelado do papel volta ao creme (balanço de branco no
  papel), contraste local (CLAHE no L), tinta mais funda, um pouco de saturação e nitidez.
Saída: reais_restauradas/<nome>.jpg (fora do git). No vídeo: a versão antiga entra primeiro e a restaurada aparece por
uma varredura de luz, com o selo RESTAURAÇÃO DIGITAL (montar_roteiro.restauro).
Uso: python3 restaurar.py [nome ...]"""
import sys
from pathlib import Path
import numpy as np, cv2

AQUI = Path(__file__).parent; R = AQUI / "reais"; S = AQUI / "reais_restauradas"; S.mkdir(exist_ok=True)
PEQUENAS = ["ritual_sekien", "hashihime_sekien", "shuten_sekien", "ushioni_sekien", "nureonna_sekien", "sekien_kappa",
            "sekien_satori", "sekien_rokurokubi"]
GRANDES = ["m_hannya_hokusai", "m_raiko_cabeca", "tamamo_xilo", "kyosai_6", "m_ushinokoku", "tsuchigumo_rijks"]


def upscale(img):
    import torch
    from spandrel import ModelLoader
    torch.set_num_threads(2)
    m = ModelLoader().load_from_file("/dev/shm/modelos/x4plus.pth").model.eval()
    x = img.astype(np.float32) / 255; H, W = x.shape[:2]; T, P = 256, 16
    out = np.zeros((H * 4, W * 4, 3), np.float32)
    with torch.no_grad():
        for y in range(0, H, T):
            for xx in range(0, W, T):
                y0, x0 = max(0, y - P), max(0, xx - P); y1, x1 = min(H, y + T + P), min(W, xx + T + P)
                t = torch.from_numpy(x[y0:y1, x0:x1]).permute(2, 0, 1)[None]
                o = m(t)[0].permute(1, 2, 0).clamp(0, 1).numpy()
                oy, ox = (y - y0) * 4, (xx - x0) * 4; hh, ww = min(T, H - y) * 4, min(T, W - xx) * 4
                out[y * 4:y * 4 + hh, xx * 4:xx * 4 + ww] = o[oy:oy + hh, ox:ox + ww]
    return (out * 255).astype(np.uint8)


def cor(img):
    lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB).astype(np.float32)
    L, a, b = cv2.split(lab)
    papel = L >= np.percentile(L, 75)                     # o papel = os 25% mais claros (>=: papel branco puro não fica vazio)
    a -= (a[papel].mean() - 128) * 0.5; b -= (b[papel].mean() - 128 - 6) * 0.45   # tira parte do amarelado (fica um creme quente: é papel antigo)
    L8 = np.clip(L, 0, 255).astype(np.uint8)
    L = cv2.createCLAHE(clipLimit=1.8, tileGridSize=(8, 8)).apply(L8).astype(np.float32)
    L = np.clip((L - np.percentile(L, 1)) / (np.percentile(L, 99.5) - np.percentile(L, 1)) * 255, 0, 255)   # tinta funda, papel limpo
    a = 128 + (a - 128) * 1.15; b = 128 + (b - 128) * 1.15
    out = cv2.cvtColor(np.clip(cv2.merge([L, a, b]), 0, 255).astype(np.uint8), cv2.COLOR_LAB2RGB)
    bl = cv2.GaussianBlur(out, (0, 0), 1.2)
    return cv2.addWeighted(out, 1.35, bl, -0.35, 0)


alvo = set(sys.argv[1:])
for n in PEQUENAS + GRANDES:
    if alvo and n not in alvo: continue
    img = cv2.cvtColor(cv2.imread(str(R / f"{n}.jpg")), cv2.COLOR_BGR2RGB)
    res = cor(upscale(img)) if n in PEQUENAS else cor(img)
    cv2.imwrite(str(S / f"{n}.jpg"), cv2.cvtColor(res, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 92])
    print("ok", n, res.shape[:2], flush=True)
