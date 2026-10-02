"""Video MP4 do heroi andando de lado (usa os quadros prontos em revisao/lado)."""
import json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

AQUI = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(AQUI, "..", "revisao", "lado")
SAIDA = sys.argv[1] if len(sys.argv) > 1 else os.path.join(D, "heroi_andando_lado.mp4")
info = json.load(open(os.path.join(D, "info.json")))
DUR = info["duracao_ms"] / 1000
VEL = 47                                  # px do jogo por segundo (pes nao escorregam)
FPS = 60
Z = 6                                     # zoom do video (1 px do jogo = 6 px na tela)
LW, LH = 1280 // Z, 720 // Z              # cena em px do jogo
andar = [np.asarray(Image.open(os.path.join(D, f"andar_{k}.png")).convert("RGBA")) for k in range(8)]
parado = np.asarray(Image.open(os.path.join(D, "parado.png")).convert("RGBA"))
px, py = info["pivot"]
CHAO = 92
fonte = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)


def cenario():
    rng = np.random.default_rng(7)
    a = np.zeros((LH, LW, 3), np.uint8); a[:] = (98, 150, 66)
    for _ in range(LW * LH // 30):
        x, y = rng.integers(0, LW), rng.integers(0, LH)
        a[y, x] = (84, 132, 56) if rng.random() < .6 else (118, 170, 80)
    # trilha de terra onde ele anda
    y0, y1 = CHAO - 9, CHAO + 4
    a[y0:y1] = (176, 132, 84)
    for _ in range(LW * 3):
        x, y = rng.integers(0, LW), rng.integers(y0, y1)
        a[y, x] = (156, 112, 70) if rng.random() < .5 else (192, 150, 100)
    a[y0 - 1] = (122, 160, 72); a[y1] = (122, 160, 72)
    # tufos de capim
    for _ in range(26):
        x, y = rng.integers(2, LW - 3), rng.integers(4, LH - 3)
        if y0 - 3 <= y <= y1 + 2:
            continue
        for dx, dy in ((0, 0), (-1, 1), (1, 1), (0, -1)):
            a[y + dy, x + dx] = (64, 112, 44)
    return a


def cola(base, spr, x, y):
    h, w = spr.shape[:2]
    x0, y0 = max(x, 0), max(y, 0)
    x1, y1 = min(x + w, base.shape[1]), min(y + h, base.shape[0])
    if x1 <= x0 or y1 <= y0:
        return
    s = spr[y0 - y:y1 - y, x0 - x:x1 - x]
    m = s[..., 3] > 0
    base[y0:y1, x0:x1][m] = s[m, :3]


def rotulo(img, texto):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((20, 18, 40 + d.textlength(texto, font=fonte), 66), 10, fill=(30, 30, 36))
    d.text((30, 24), texto, font=fonte, fill=(255, 255, 255))


def quadros():
    fundo = cenario()
    # parte 1: atravessa a tela, volta, para no meio e segue
    roteiro = [("andar", -30, LW + 30), ("andar", -30, LW // 2), ("parado", 1.4), ("andar", LW // 2, LW + 30)]
    t_anim = 0.0
    for passo in roteiro:
        if passo[0] == "parado":
            for _ in range(int(passo[1] * FPS)):
                f = fundo.copy(); cola(f, parado, int(x) - px, CHAO - py)
                yield f, Z, "Andando no jogo (tamanho real x6)"
            t_anim = 0.0
            continue
        _, x, xf = passo
        while x < xf:
            k = int(t_anim / DUR) % 8
            f = fundo.copy(); cola(f, andar[k], int(x) - px, CHAO - py)
            yield f, Z, "Andando no jogo (tamanho real x6)"
            x += VEL / FPS; t_anim += 1 / FPS
    # parte 2: camera lenta, de perto
    Z2 = 9
    w2, h2 = 1280 // Z2, 720 // Z2
    perto = np.zeros((h2, w2, 3), np.uint8); perto[:] = (98, 150, 66)
    perto[h2 - 8:] = (176, 132, 84)
    t = 0.0
    while t < 8 * DUR * 2 * 2:            # 2 ciclos em camera lenta (metade da velocidade)
        k = int(t / (DUR * 2)) % 8
        f = perto.copy(); cola(f, andar[k], w2 // 2 - px, h2 - 8 - py + 2)
        yield f, Z2, "Camera lenta (metade da velocidade)"
        t += 1 / FPS


if __name__ == "__main__":
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [ff, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1280x720", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", "-movflags", "+faststart", SAIDA]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = 0
    for f, z, txt in quadros():
        img = Image.fromarray(f).resize((f.shape[1] * z, f.shape[0] * z), Image.NEAREST)
        tela = Image.new("RGB", (1280, 720), (98, 150, 66)); tela.paste(img, (0, 0))
        rotulo(tela, txt)
        p.stdin.write(tela.tobytes()); n += 1
    p.stdin.close(); p.wait()
    print("ok", SAIDA, f"{n / FPS:.1f} s")
