"""Video de teste da pesca: usa os quadros da vara (revisao/acoes/vara_lado) e desenha, no tamanho do
jogo, a linha (da ponta da vara ate a boia), a boia voando, caindo na agua, balancando, afundando na
mordida e voltando ao recolher. No jogo, a linha e a boia sao desenhadas pelo codigo do jogo do mesmo
jeito (a posicao da ponta da vara em cada quadro esta no info.json)."""
import glob, json, math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

AQUI = os.path.dirname(os.path.abspath(__file__))
PASTA = sys.argv[1] if len(sys.argv) > 1 else os.path.join(AQUI, "..", "revisao", "acoes", "vara_lado")
info = json.load(open(os.path.join(PASTA, "info.json")))
px, py = info["pivot"]
arqs = sorted(glob.glob(os.path.join(PASTA, "vara_*.png")), key=lambda f: int(os.path.basename(f).split("_")[1]))
Q = {}
for f, qi in zip(arqs, info["quadros"]):
    Q[qi["nome"]] = (np.asarray(Image.open(f).convert("RGBA")), qi["ponta_ferramenta"])
parado = np.asarray(Image.open(os.path.join(PASTA, "parado.png")).convert("RGBA"))
FPS, Z = 60, 5
TW, TH = 1280, 720
W, H = TW // Z, TH // Z
HX, CHAO = 70, 96                     # pes do heroi na cena
AGUA_X, AGUA_Y = 112, 92              # onde comeca o lago
POUSO = (172, 104)                    # onde a boia cai
LINHA = (236, 236, 226); CONT = (36, 20, 14)
fonte = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)


def cenario():
    rng = np.random.default_rng(3)
    a = np.zeros((H, W, 3), np.uint8); a[:] = (98, 150, 66)
    for _ in range(W * H // 30):
        x, y = rng.integers(0, W), rng.integers(0, H)
        a[y, x] = (84, 132, 56) if rng.random() < .6 else (118, 170, 80)
    a[AGUA_Y:, AGUA_X:] = (62, 128, 190)
    a[AGUA_Y:AGUA_Y + 2, AGUA_X:] = (150, 120, 80)            # margem de terra
    a[AGUA_Y:, AGUA_X:AGUA_X + 2] = (150, 120, 80)
    for _ in range(60):
        x, y = rng.integers(AGUA_X + 4, W), rng.integers(AGUA_Y + 4, H)
        a[y, x:x + 3] = (112, 176, 226)
    return a


def cola(base, spr, x, y):
    h, w = spr.shape[:2]
    x0, y0 = max(x, 0), max(y, 0); x1, y1 = min(x + w, base.shape[1]), min(y + h, base.shape[0])
    if x1 <= x0 or y1 <= y0:
        return
    s = spr[y0 - y:y1 - y, x0 - x:x1 - x]; m = s[..., 3] > 0
    base[y0:y1, x0:x1][m] = s[m, :3]


def ponto(img, x, y, cor):
    x, y = int(round(x)), int(round(y))
    if 0 <= x < W and 0 <= y < H:
        img[y, x] = cor


def linha(img, a, b, curva):
    n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1]))) * 2 + 2
    for i in range(n + 1):
        t = i / n
        x = a[0] + (b[0] - a[0]) * t
        y = a[1] + (b[1] - a[1]) * t + curva * 4 * t * (1 - t)
        ponto(img, x, y, LINHA)


def boia(img, x, y, afunda=0):
    x, y = int(round(x)), int(round(y + afunda))
    for dx in (-2, -1, 0, 1, 2):
        for dy in (-3, -2, -1, 0, 1):
            if abs(dx) == 2 or dy in (-3, 1):
                ponto(img, x + dx, y + dy, CONT)
    for dx in (-1, 0, 1):
        ponto(img, x + dx, y - 2, (224, 64, 52)); ponto(img, x + dx, y - 1, (224, 64, 52)); ponto(img, x + dx, y, (246, 246, 240))


def roteiro():
    """Lista de (quadro, boia(x,y) ou None, afundar, curva, ondinha)"""
    seq = []
    def add(nome, seg, boia_fn=None, curva=0.0, onda=0):
        n = max(1, round(seg * FPS))
        for i in range(n):
            seq.append((nome, boia_fn(i / n) if boia_fn else None, curva, onda))
    add("parado", 0.5)
    add("segurar", 0.3)
    add("recuar", 0.18)
    add("lancar", 0.06)
    # boia voa num arco ate o lago enquanto ele termina o movimento
    def voo(t, ini=None):
        x0, y0 = ini
        x = x0 + (POUSO[0] - x0) * t
        y = y0 + (POUSO[1] - y0) * t - 30 * math.sin(math.pi * t)
        return (x, y, 0)
    tip = lambda nome: (HX - px + Q[nome][1][0], CHAO - py + Q[nome][1][1])
    ini = tip("lancar")
    seq_voo = []
    for nome, seg in (("soltar", 0.14), ("esperar_a", 0.36)):
        n = round(seg * FPS)
        for i in range(n):
            seq_voo.append(nome)
    for i, nome in enumerate(seq_voo):
        t = (i + 1) / len(seq_voo)
        seq.append((nome, voo(t, ini), 2.0, 0))
    # esperando: a boia balanca; perto do fim, duas mordidas (afunda)
    T = 2.4; n = round(T * FPS)
    for i in range(n):
        t = i / FPS
        nome = "esperar_a" if int(t / 0.4) % 2 == 0 else "esperar_b"
        afunda = 1 if math.sin(t * 6) > 0.6 else 0
        if t > 1.7:
            afunda = 3 if int((t - 1.7) / 0.18) % 2 == 0 else 0
        seq.append((nome, (POUSO[0], POUSO[1], afunda), 3.0, 1 + (i // 20) % 3))
    for i in range(round(0.12 * FPS)):
        seq.append(("fisgar", (POUSO[0] - 3, POUSO[1], 1), 0.0, 2))
    # recolhendo: a boia vem ate a margem e sai da agua
    T = 1.4; n = round(T * FPS)
    for i in range(n):
        t = i / n
        nome = "recolher_a" if int(i / (0.12 * FPS)) % 2 == 0 else "recolher_b"
        x = POUSO[0] + (AGUA_X + 4 - POUSO[0]) * t
        seq.append((nome, (x, POUSO[1], 0), 0.5, 0))
    add("segurar", 0.5)
    add("parado", 0.6)
    return seq


def quadros():
    fundo = cenario()
    for nome, b, curva, onda in roteiro():
        img = fundo.copy()
        if nome == "parado":
            cola(img, parado, HX - px, CHAO - py)
        else:
            spr, pt = Q[nome]
            cola(img, spr, HX - px, CHAO - py)
            if b is not None:
                tx, ty = HX - px + pt[0], CHAO - py + pt[1]
                if onda:
                    for dx in range(-2 - onda, 3 + onda):
                        ponto(img, b[0] + dx, b[1] + 2, (150, 200, 238))
                linha(img, (tx, ty), (b[0], b[1] - 2 + b[2]), curva)
                boia(img, b[0], b[1], b[2])
        g = Image.fromarray(img).resize((W * Z, H * Z), Image.NEAREST)
        d = ImageDraw.Draw(g)
        texto = "Pescando (tamanho real x5) - linha e boia feitas pelo jogo"
        d.rounded_rectangle((20, 18, 40 + d.textlength(texto, font=fonte), 66), 10, fill=(30, 30, 36))
        d.text((30, 24), texto, font=fonte, fill=(255, 255, 255))
        yield g


if __name__ == "__main__":
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    saida = os.path.join(PASTA, "heroi_pescando_lado.mp4")
    p = subprocess.Popen([ff, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{TW}x{TH}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
                          "-movflags", "+faststart", saida], stdin=subprocess.PIPE)
    n = 0
    for _ in range(2):
        for g in quadros():
            p.stdin.write(g.tobytes()); n += 1
    p.stdin.close(); p.wait()
    print("ok", saida, f"{n / FPS:.1f} s")
