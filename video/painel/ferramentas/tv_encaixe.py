"""Coloca um clipe DENTRO da tela de uma TV que aparece numa imagem ou num vídeo (Ep. 09 v4, 15/11).
- base = imagem (.jpg/.png/.webp) ou vídeo (.mp4). Num vídeo com câmera andando, a tela é RASTREADA: pontos do
  gabinete da TV seguidos por fluxo óptico (Lucas-Kanade) → homografia quadro a quadro aplicada aos 4 cantos.
- o clipe entra em perspectiva (warpPerspective) com cara de tubo: preto e branco levemente verde, linhas, chuvisco,
  vidro curvo (cantos escurecidos), brilho que vaza;
- a LUZ do clipe ilumina a sala: o brilho médio da tela em cada quadro clareia a base (mais perto da TV, mais forte);
- saída com o som do clipe (para entrar nos respiros da narração).
Uso: python3 tv_encaixe.py BASE CLIPE SAIDA.mp4 "x1,y1 x2,y2 x3,y3 x4,y4" [--dur 12] [--ini 0] [--zoom 1.08]
     cantos da tela em pixels da base, na ordem: sup-esq, sup-dir, inf-dir, inf-esq."""
import subprocess, sys
import cv2
import numpy as np

a = sys.argv[1:]
BASE, CLIPE, SAIDA, CANTOS = a[:4]
opt = {a[i][2:]: float(a[i + 1]) for i in range(4, len(a) - 1, 2) if a[i].startswith("--")}
DUR, INI, ZOOM = opt.get("dur", 12.0), opt.get("ini", 0.0), opt.get("zoom", 1.08)
FPS, W, H = 30, 1920, 1080
cantos0 = np.float32([[float(v) for v in p.split(",")] for p in CANTOS.split()])

eh_video = BASE.lower().endswith((".mp4", ".mov", ".webm"))
if eh_video:
    cb = cv2.VideoCapture(BASE); fb = cb.get(cv2.CAP_PROP_FPS) or 24; nb = int(cb.get(cv2.CAP_PROP_FRAME_COUNT))
    bases = []
    while True:
        ok, q = cb.read()
        if not ok: break
        bases.append(q)
else:
    bases = [cv2.imread(BASE)]; fb = FPS; nb = 1
bh, bw = bases[0].shape[:2]
# rastreio: pontos bons perto da TV (retângulo da tela ampliado), fluxo óptico de quadro em quadro
cantos_q = [cantos0]
if eh_video and len(bases) > 1:
    x0, y0 = cantos0.min(0); x1, y1 = cantos0.max(0); mw, mh = (x1 - x0) * 0.6, (y1 - y0) * 0.6
    masc = np.zeros((bh, bw), np.uint8); masc[int(max(0, y0 - mh)):int(min(bh, y1 + mh)), int(max(0, x0 - mw)):int(min(bw, x1 + mw))] = 255
    masc[int(y0):int(y1), int(x0):int(x1)] = 0                                  # a tela em si não (ela muda)
    g0 = cv2.cvtColor(bases[0], cv2.COLOR_BGR2GRAY)
    p0 = cv2.goodFeaturesToTrack(g0, 300, 0.01, 6, mask=masc)
    acum = np.eye(3)
    for k in range(1, len(bases)):
        g1 = cv2.cvtColor(bases[k], cv2.COLOR_BGR2GRAY)
        p1, st, _ = cv2.calcOpticalFlowPyrLK(g0, g1, p0, None, winSize=(21, 21), maxLevel=3)
        bons0, bons1 = p0[st == 1], p1[st == 1]
        Hm, _ = cv2.findHomography(bons0, bons1, cv2.RANSAC, 3.0) if len(bons0) >= 8 else (None, None)
        if Hm is not None:
            acum = Hm @ acum
        cantos_q.append(cv2.perspectiveTransform(cantos0[None], acum)[0])
        g0, p0 = g1, bons1.reshape(-1, 1, 2)
        if len(p0) < 60:                                                         # repõe pontos quando muitos se perdem
            p0 = cv2.goodFeaturesToTrack(g1, 300, 0.01, 6, mask=masc)
    # suaviza a trilha dos cantos (tira o tremor do rastreio)
    c = np.array(cantos_q); k = 5
    cantos_q = [c[max(0, i - k):i + k + 1].mean(0) for i in range(len(c))]

# o clipe (quadros 640×480) e o som
cc = cv2.VideoCapture(CLIPE); fc = cc.get(cv2.CAP_PROP_FPS) or 30
cc.set(cv2.CAP_PROP_POS_MSEC, INI * 1000)
clip = []
while len(clip) < int(DUR * fc):
    ok, q = cc.read()
    if not ok: break
    clip.append(cv2.resize(q, (640, 480)))
rng = np.random.default_rng(3)
linhas = np.ones((480, 640, 1), np.float32); linhas[::3] = 0.7
yy, xx = np.mgrid[0:480, 0:640]; vin = 1 - 0.55 * (((xx - 320) / 320) ** 2 + ((yy - 240) / 240) ** 2) ** 1.4
vin = np.clip(vin, 0, 1)[..., None].astype(np.float32)

def tubo(q, t):
    g = cv2.cvtColor(q, cv2.COLOR_BGR2GRAY).astype(np.float32)
    g = np.clip((g - 128) * 1.25 + 128 + 10, 0, 255)
    banda = ((t * 0.35) % 1.3 - 0.15) * 480
    ruido = rng.normal(0, 14, (480, 640)) * (1 + 2.2 * np.exp(-((yy - banda) / 22.0) ** 2))
    g = np.clip(g + ruido, 0, 255)
    img = np.stack([g * 0.9, g * 1.0, g * 0.88], -1) * linhas * vin                # fósforo levemente verde
    tremor = 0.9 + 0.1 * np.sin(t * 23) * np.sin(t * 7.7 + 1)
    return np.clip(img * tremor, 0, 255).astype(np.uint8)

N = int(DUR * FPS)
pipe = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                         "-ss", f"{INI}", "-t", f"{DUR}", "-i", CLIPE, "-map", "0:v", "-map", "1:a?", "-c:v", "libx264", "-crf", "16",
                         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest", SAIDA], stdin=subprocess.PIPE)
for i in range(N):
    t = i / FPS
    kb = min(len(bases) - 1, int(t * fb)) if eh_video else 0
    base = bases[kb].copy(); cq = cantos_q[min(kb, len(cantos_q) - 1)]
    q = clip[min(len(clip) - 1, int(t * fc))] if clip else np.zeros((480, 640, 3), np.uint8)
    tela = tubo(q, t)
    M = cv2.getPerspectiveTransform(np.float32([[0, 0], [640, 0], [640, 480], [0, 480]]), np.float32(cq))
    quente = cv2.warpPerspective(tela, M, (bw, bh))
    mask = cv2.warpPerspective(np.full((480, 640), 255, np.uint8), M, (bw, bh))
    mask = cv2.GaussianBlur(mask, (3, 3), 0).astype(np.float32)[..., None] / 255
    out = base.astype(np.float32) * (1 - mask) + quente.astype(np.float32) * mask
    # a luz da tela na sala: clareia em volta da TV conforme o brilho do clipe
    lum = tela.mean() / 255.0
    cx, cy = cq.mean(0); r = np.hypot(*(cq.max(0) - cq.min(0))) * 2.2
    Y, X = np.ogrid[:bh, :bw]; luz = np.exp(-((X - cx) ** 2 + (Y - cy) ** 2) / (2 * r * r))[..., None]
    out = out * (1 + 0.55 * lum * luz * (1 - mask)) + np.array([14, 18, 16]) * lum * luz * (1 - mask)
    brilho = cv2.GaussianBlur(quente, (0, 0), 18).astype(np.float32)                  # o vidro "vaza" luz
    out = np.clip(out + brilho * 0.35, 0, 255).astype(np.uint8)
    # câmera: aproximação lenta na TV
    z = 1 + (ZOOM - 1) * (t / DUR)
    Mz = cv2.getRotationMatrix2D((float(cx), float(cy)), 0, z)
    out = cv2.warpAffine(out, Mz, (bw, bh), borderMode=cv2.BORDER_REFLECT)
    out = cv2.resize(out, (W, H), interpolation=cv2.INTER_CUBIC)
    pipe.stdin.write(out.tobytes())
pipe.stdin.close(); pipe.wait()
print("ok", SAIDA)
