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


def gerar(img_path, saida, dur=9.0, mov="entrar", foco=(0.5, 0.5), forca=1.0, desfoque=0.0, camadas=True):
    """16/11: o padrão agora é a câmera em CAMADAS (gerar_camadas); camadas=False = a de uma camada (Ep. 09)."""
    if camadas:
        return gerar_camadas(img_path, saida, dur, mov, foco, forca, desfoque)
    return gerar_uma(img_path, saida, dur, mov, foco, forca, desfoque)


def gerar_uma(img_path, saida, dur=9.0, mov="entrar", foco=(0.5, 0.5), forca=1.0, desfoque=0.0):
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


def _deformar(img, dmap, px, py, fx, fy, cx, cy, mov, t, amp, peso_perto):
    """Grade de leitura (mx, my) para o quadro t: o que é 'perto' (dmap→1) anda mais."""
    dl = cv2.remap(dmap, px, py, cv2.INTER_LINEAR)
    if mov in ("entrar", "sair"):
        esc = 1 + amp * t * (0.35 + peso_perto * dl) * 2.0
        mx = (px - fx) / esc + fx; my = (py - fy) / esc + fy
    else:
        sentido = 1 if mov == "lado" else -1
        desl = sentido * (t - 0.5) * W * amp * 0.9
        esc = 1 + amp * 0.4
        mx = (px - cx) / esc + cx + desl * (0.25 + peso_perto * dl); my = (py - cy) / esc + cy
    return mx.astype(np.float32), my.astype(np.float32)


def gerar_camadas(img_path, saida, dur=9.0, mov="entrar", foco=(0.5, 0.5), forca=1.0, desfoque=0.0):
    """16/11 (pesquisa do motor — 3D Photo Inpainting / DepthFlow): câmera 3D em DUAS CAMADAS. O primeiro plano (o que
    está perto, pela profundidade) é recortado com borda suave; o fundo que ele escondia é RECONSTRUÍDO (inpainting) e
    as duas camadas andam em velocidades diferentes. Assim o objeto da frente desliza sobre um fundo de verdade, em vez
    de a imagem 'esticar' no contorno — e o movimento pode ser maior."""
    src = cv2.imread(str(img_path)); d = profundidade(img_path)
    M = 1.10
    s = max(W * M / src.shape[1], H * M / src.shape[0])
    src = cv2.resize(src, (round(src.shape[1] * s), round(src.shape[0] * s)), interpolation=cv2.INTER_LANCZOS4)
    d = cv2.resize(d, (src.shape[1], src.shape[0]), interpolation=cv2.INTER_LINEAR)
    sh, sw = src.shape[:2]
    # o primeiro plano: profundidade acima do limiar de Otsu (no mínimo o percentil 55) — e só se for uma parte razoável
    d8 = (d * 255).astype(np.uint8)
    lim, _ = cv2.threshold(cv2.GaussianBlur(d8, (0, 0), 3), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    lim = max(lim, np.percentile(d8, 55))
    mask = (d8 > lim).astype(np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))
    # só o OBJETO PRINCIPAL: o maior pedaço perto do ponto de foco (folhas e vasos soltos ficam no fundo)
    n_c, rot, est, cent = cv2.connectedComponentsWithStats(mask, 8)
    if n_c > 1:
        fxp, fyp = foco[0] * sw, foco[1] * sh
        nota = [(est[i, cv2.CC_STAT_AREA] / (1 + (np.hypot(cent[i][0] - fxp, cent[i][1] - fyp) / (0.12 * sw)) ** 2), i) for i in range(1, n_c)]
        mask = (rot == max(nota)[1]).astype(np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
    frac = mask.mean()
    if not 0.04 < frac < 0.6:                          # sem um primeiro plano claro: volta para a câmera de uma camada
        return gerar_uma(img_path, saida, dur, mov, foco, forca, desfoque)
    alfa = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), max(2, sw / 900))
    # fundo reconstruído: tira o primeiro plano (com folga) e preenche em resolução menor (rápido), depois cola só ali
    folga = cv2.dilate(mask, np.ones((int(sw * 0.035) | 1, int(sw * 0.035) | 1), np.uint8))
    k = 4
    peq = cv2.resize(src, (sw // k, sh // k), interpolation=cv2.INTER_AREA)
    mpeq = cv2.resize(folga * 255, (sw // k, sh // k), interpolation=cv2.INTER_NEAREST)
    preenchido = cv2.inpaint(peq, mpeq, 9, cv2.INPAINT_TELEA)
    preenchido = cv2.resize(preenchido, (sw, sh), interpolation=cv2.INTER_CUBIC)
    preenchido = cv2.GaussianBlur(preenchido, (0, 0), 1.2)
    mf = cv2.GaussianBlur(folga.astype(np.float32), (0, 0), 6)[..., None]
    fundo = (src * (1 - mf) + preenchido * mf).astype(np.uint8)
    d_fundo = cv2.inpaint(cv2.resize((d * 255).astype(np.uint8), (sw // k, sh // k), interpolation=cv2.INTER_AREA), mpeq, 9, cv2.INPAINT_TELEA)
    d_fundo = cv2.resize(d_fundo, (sw, sh)).astype(np.float32) / 255
    d_fundo = np.minimum(d_fundo, lim / 255.0)         # o fundo nunca fica "mais perto" que o recorte
    if desfoque > 0:                                   # foco no plano escolhido: o fundo desfoca, o recorte fica nítido
        fundo = cv2.GaussianBlur(fundo, (0, 0), 1.5 + 4 * desfoque)
    fx, fy = foco[0] * sw, foco[1] * sh
    cx = min(max(fx, W / 2), sw - W / 2); cy = min(max(fy, H / 2), sh - H / 2)
    xs, ys = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
    px, py = xs - W / 2 + cx, ys - H / 2 + cy
    n = int(round(dur * FPS)); amp = 0.075 * forca
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                             "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "16", "-preset", "medium",
                             "-pix_fmt", "yuv420p", str(saida)], stdin=subprocess.PIPE)
    um = np.ones_like(d)
    for q in range(n):
        t = _ease(q / max(1, n - 1))
        if mov == "sair":
            t = 1 - t
        mx, my = _deformar(fundo, d_fundo, px, py, fx, fy, cx, cy, mov, t, amp, 0.45)
        b = cv2.remap(fundo, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT).astype(np.float32)
        mx2, my2 = _deformar(src, um * float(np.percentile(d[mask > 0], 60)), px, py, fx, fy, cx, cy, mov, t, amp, 0.62)
        f = cv2.remap(src, mx2, my2, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT).astype(np.float32)
        a = cv2.remap(alfa, mx2, my2, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)[..., None]
        proc.stdin.write((b * (1 - a) + f * a).astype(np.uint8).tobytes())
    proc.stdin.close(); proc.wait()
    return saida


if __name__ == "__main__":
    a = sys.argv[1:]
    gerar(a[0], a[1], float(a[2]) if len(a) > 2 else 9.0, a[3] if len(a) > 3 else "entrar",
          (float(a[4]), float(a[5])) if len(a) > 5 else (0.5, 0.5), float(a[6]) if len(a) > 6 else 1.0,
          float(a[7]) if len(a) > 7 else 0.0)
