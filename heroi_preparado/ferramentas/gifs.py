import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
AQUI = os.path.dirname(os.path.abspath(__file__))
D = sys.argv[1] if len(sys.argv) > 1 else os.path.join(AQUI, '..', 'revisao', 'lado')
VIDEO = os.path.join(AQUI, '..', '..', '..', 'video', 'andar.png')  # tira do video de referencia (fora do repositorio)
info = json.load(open(f'{D}/info.json'))
DUR = info['duracao_ms']
andar = [Image.open(f'{D}/andar_{k}.png') for k in range(8)]
parado = Image.open(f'{D}/parado.png')
w, h = parado.size
px, py = info['pivot']

def grama(W, H, seed=3):
    rng = np.random.default_rng(seed)
    a = np.zeros((H, W, 3), np.uint8); a[:] = (98, 150, 66)
    for _ in range(W * H // 40):
        x, y = rng.integers(0, W), rng.integers(0, H)
        a[y, x] = (84, 132, 56) if rng.random() < .6 else (118, 170, 80)
    return Image.fromarray(a)

# ---------- 1) comparacao com o video ----------
if not os.path.exists(VIDEO):
    VIDEO = None
vid = Image.open(VIDEO).convert('RGB') if VIDEO else Image.new('RGB', (15 * 162, 234), (30, 30, 36))
n = 15; tw = vid.width // n
tiles = [vid.crop((i * tw, 0, (i + 1) * tw, vid.height)) for i in range(n)]
Z = 3
PW = max(tw, w * Z + 40); PH = max(vid.height, h * Z + 40)
fundo = grama(PW, PH, 5)
quadros, duracoes = [], []
T = 3000
VID_MS = 1000 / 15        # tiles do video = 1 a cada 2 quadros de 30 fps
ev = sorted({int(round(i * VID_MS)) for i in range(int(T / VID_MS) + 1)} | {i * DUR for i in range(T // DUR + 1)})
for t, prox in zip(ev[:-1], ev[1:]):
    iv = int((t + 0.5) // VID_MS) % n; ih = (t // DUR) % 8
    c = Image.new('RGB', (PW * 2 + 12, PH + 26), (30, 30, 36))
    c.paste(tiles[iv], (0, 26))
    f = fundo.copy().convert('RGBA')
    im = andar[ih].resize((w * Z, h * Z), Image.NEAREST)
    f.alpha_composite(im, (PW // 2 - px * Z, PH - 14 - py * Z))
    c.paste(f.convert('RGB'), (PW + 12, 26))
    d = ImageDraw.Draw(c)
    d.text((6, 7), 'VIDEO (referencia)', fill=(255, 255, 255))
    d.text((PW + 18, 7), 'HEROI - esqueleto (3x)', fill=(255, 255, 255))
    quadros.append(c); duracoes.append(max(10, prox - t))
quadros[0].save(f'{D}/heroi_lado_vs_video.gif', save_all=True, append_images=quadros[1:], duration=duracoes, loop=0)

# ---------- 2) andando no gramado (4x), para e volta ----------
Z = 4
VEL = info.get('vel_px_s', 47)
LW = 200; LH = h + 16
fundo = grama(LW, LH, 9).convert('RGBA')
quadros, duracoes = [], []
x = 20.0
seq = [('andar', k % 8) for k in range(24)] + [('parado', 0)] * 1 + [('andar', k % 8) for k in range(16)] + [('parado', 0)]
for tipo, k in seq:
    f = fundo.copy()
    im = parado if tipo == 'parado' else andar[k]
    f.alpha_composite(im, (int(round(x)) - px, LH - 6 - py))
    f = f.resize((LW * Z, LH * Z), Image.NEAREST).convert('RGB')
    quadros.append(f)
    if tipo == 'parado':
        duracoes.append(900)
    else:
        duracoes.append(DUR); x += VEL * DUR / 1000
    if x > LW + 20: x = -20
quadros[0].save(f'{D}/heroi_lado_andando_4x.gif', save_all=True, append_images=quadros[1:], duration=duracoes, loop=0)
print('ok', len(quadros))
