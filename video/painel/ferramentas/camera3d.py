"""Câmera 3D numa imagem parada (Ep. 09): estima a profundidade (Depth Anything V2 Small, CPU) e faz a câmera
andar DE VERDADE dentro da foto — o que está perto mexe mais que o fundo (paralaxe), em vez do zoom chapado.
Também faz o foco de lente: o plano escolhido fica nítido e o resto desfoca conforme a distância dele.

Uso (biblioteca):  gerar(img, saida, dur=9, mov="entrar", foco=(x,y), forca=1.0, desfoque=0.0)
  mov: "entrar" (dolly para dentro, rumo ao foco), "sair" (afasta), "lado" (desliza para a direita), "lado_esq".
  foco: ponto (frações) para onde a câmera anda e cuja profundidade fica nítida.
  desfoque: 0 = tudo nítido; 1 = lente bem aberta (fundo/primeiro plano bem borrados).
Uso (linha):  python3 camera3d.py img.jpg saida.mp4 [dur] [mov] [fx] [fy] [forca] [desfoque]
Cache da profundidade em painel/.cache_profundidade (npy)."""
import hashlib, subprocess, sys
from pathlib import Path
import cv2
import numpy as np

AQUI = Path(__file__).resolve().parents[1]
CACHE = AQUI / ".cache_profundidade"; CACHE.mkdir(exist_ok=True)
W, H, FPS = 1920, 1080, 30
_modelo = None


def profundidade(img_path):
    """Mapa 0..1 (1 = perto), do tamanho da imagem."""
    global _modelo
    chave = hashlib.md5(Path(img_path).read_bytes()).hexdigest()[:16]
    arq = CACHE / f"{chave}.npy"
    if arq.exists():
        return np.load(arq)
    if _modelo is None:
        from transformers import pipeline
        _modelo = pipeline("depth-estimation", model="depth-anything/Depth-Anything-V2-Small-hf", device=-1)
    from PIL import Image
    im = Image.open(img_path).convert("RGB")
    d = np.asarray(_modelo(im)["predicted_depth"].squeeze().float().numpy(), np.float32)
    d = cv2.resize(d, im.size, interpolation=cv2.INTER_CUBIC)
    lo, hi = np.percentile(d, 2), np.percentile(d, 98)
    d = np.clip((d - lo) / max(1e-6, hi - lo), 0, 1)
    np.save(arq, d)
    return d


def _ease(t):
    return t * t * (3 - 2 * t)                      # começa e termina devagar (sem tranco)


def gerar(img_path, saida, dur=9.0, mov="entrar", foco=(0.5, 0.5), forca=1.0, desfoque=0.0):
    src = cv2.imread(str(img_path))
    d = profundidade(img_path)
    # trabalha com a imagem cobrindo 1920×1080 com margem de 8% (a câmera nunca mostra a borda)
    M = 1.08
    s = max(W * M / src.shape[1], H * M / src.shape[0])
    src = cv2.resize(src, (round(src.shape[1] * s), round(src.shape[0] * s)), interpolation=cv2.INTER_LANCZOS4)
    d = cv2.resize(d, (src.shape[1], src.shape[0]), interpolation=cv2.INTER_LINEAR)
    # profundidade "engordada" nas bordas dos objetos de perto: evita rasgar o contorno quando eles se mexem
    d = cv2.GaussianBlur(cv2.dilate(d, np.ones((15, 15), np.uint8)), (0, 0), 6)
    sh, sw = src.shape[:2]
    fx, fy = foco[0] * sw, foco[1] * sh
    if desfoque > 0:                                # foco de lente: nítido na profundidade do ponto de foco
        df = float(d[int(min(sh - 1, fy)), int(min(sw - 1, fx))])
        borr = cv2.GaussianBlur(src, (0, 0), 2.2 + 5 * desfoque)
        meio = cv2.GaussianBlur(src, (0, 0), 1.2 + 2 * desfoque)
        dist = np.clip(np.abs(d - df) * 2.6 * desfoque, 0, 1)[..., None]
        w2 = np.clip(dist * 2 - 1, 0, 1); w1 = np.clip(dist * 2, 0, 1) - w2
        src = (src * (1 - w1 - w2) + meio * w1 + borr * w2).astype(np.uint8)
    # grade de saída em coordenadas da imagem grande (centrada no foco, limitada às bordas)
    cx = min(max(fx, W / 2), sw - W / 2); cy = min(max(fy, H / 2), sh - H / 2)
    xs, ys = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
    n = int(round(dur * FPS))
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                             "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "16", "-preset", "medium",
                             "-pix_fmt", "yuv420p", str(saida)], stdin=subprocess.PIPE)
    amp = 0.07 * forca
    for k in range(n):
        t = _ease(k / max(1, n - 1))
        if mov == "sair":
            t = 1 - t
        px, py = xs - W / 2 + cx, ys - H / 2 + cy                     # pixel de saída → imagem grande
        dl = cv2.remap(d, px, py, cv2.INTER_LINEAR)
        if mov in ("entrar", "sair"):
            esc = 1 + amp * t * (0.35 + 0.65 * dl) * 2.0                # perto cresce mais que o fundo
            mx = (px - fx) / esc + fx; my = (py - fy) / esc + fy
        else:
            sentido = 1 if mov == "lado" else -1
            desl = sentido * (t - 0.5) * W * amp * 0.9
            esc = 1 + amp * 0.4
            mx = (px - cx) / esc + cx + desl * (0.25 + 0.75 * dl); my = (py - cy) / esc + cy
        quadro = cv2.remap(src, mx.astype(np.float32), my.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        proc.stdin.write(quadro.tobytes())
    proc.stdin.close(); proc.wait()
    return saida


if __name__ == "__main__":
    a = sys.argv[1:]
    gerar(a[0], a[1], float(a[2]) if len(a) > 2 else 9.0, a[3] if len(a) > 3 else "entrar",
          (float(a[4]), float(a[5])) if len(a) > 5 else (0.5, 0.5), float(a[6]) if len(a) > 6 else 1.0,
          float(a[7]) if len(a) > 7 else 0.0)
