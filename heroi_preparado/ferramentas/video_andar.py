"""Video MP4 + GIF do heroi andando numa direcao (frente, costas, lado_esq ou lado).

Uso: python3 video_andar.py frente
Le os quadros prontos em revisao/<direcao>/ (parado.png, andar_0..7.png, info.json).
"""
import json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

AQUI = os.path.dirname(os.path.abspath(__file__))
DIRECAO = sys.argv[1] if len(sys.argv) > 1 else "frente"
D = os.path.join(AQUI, "..", "revisao", DIRECAO)
info = json.load(open(os.path.join(D, "info.json")))
DUR = info["duracao_ms"] / 1000
VEL = 47                                  # px do jogo por segundo (mesma do lado)
FPS = 60
# direcao do movimento na tela
MOV = {"frente": (0, 1), "costas": (0, -1), "lado": (1, 0), "lado_esq": (-1, 0)}[DIRECAO]
NOME = {"frente": "de frente", "costas": "de costas", "lado": "de lado", "lado_esq": "para a esquerda"}[DIRECAO]
Z = 5 if MOV[0] == 0 else 6               # andando na vertical: um pouco mais de cena
TW, TH = 1280, 720
LW, LH = TW // Z, TH // Z
TRILHA_X = int(LW * 0.62)                # trilha vertical fora do rotulo
andar = [np.asarray(Image.open(os.path.join(D, f"andar_{k}.png")).convert("RGBA")) for k in range(8)]
parado = np.asarray(Image.open(os.path.join(D, "parado.png")).convert("RGBA"))
px, py = info["pivot"]
fonte = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)


def grama(W, H, seed=7):
    rng = np.random.default_rng(seed)
    a = np.zeros((H, W, 3), np.uint8); a[:] = (98, 150, 66)
    for _ in range(W * H // 30):
        x, y = rng.integers(0, W), rng.integers(0, H)
        a[y, x] = (84, 132, 56) if rng.random() < .6 else (118, 170, 80)
    return a, rng


def cenario():
    a, rng = grama(LW, LH)
    if MOV[0] == 0:                       # trilha vertical no meio
        x0, x1 = TRILHA_X - 13, TRILHA_X + 13
        a[:, x0:x1] = (176, 132, 84)
        for _ in range(LH * 3):
            x, y = rng.integers(x0, x1), rng.integers(0, LH)
            a[y, x] = (156, 112, 70) if rng.random() < .5 else (192, 150, 100)
        a[:, x0 - 1] = (122, 160, 72); a[:, x1] = (122, 160, 72)
        faixa = lambda x, y: x0 - 3 <= x <= x1 + 2
    else:                                 # trilha horizontal
        y0, y1 = 92 - 9, 92 + 4
        a[y0:y1] = (176, 132, 84)
        for _ in range(LW * 3):
            x, y = rng.integers(0, LW), rng.integers(y0, y1)
            a[y, x] = (156, 112, 70) if rng.random() < .5 else (192, 150, 100)
        a[y0 - 1] = (122, 160, 72); a[y1] = (122, 160, 72)
        faixa = lambda x, y: y0 - 3 <= y <= y1 + 2
    for _ in range(26):
        x, y = rng.integers(2, LW - 3), rng.integers(4, LH - 3)
        if faixa(x, y):
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


def roteiro():
    """Posicoes (em px do jogo, ao longo do movimento) de cada trecho."""
    if MOV[0] == 0:
        ini, fim, meio = -8, LH + 70, LH // 2 + 30
        if MOV[1] < 0:
            ini, fim, meio = LH + 70, -8, LH // 2 + 30
    else:
        ini, fim, meio = -30, LW + 30, LW // 2
        if MOV[0] < 0:
            ini, fim = LW + 30, -30
    return [("andar", ini, fim), ("andar", ini, meio), ("parado", 1.4), ("andar", meio, fim)]


def posicao(s):
    """s = posicao ao longo do movimento -> (x, y) dos pes na cena."""
    if MOV[0] == 0:
        return TRILHA_X, s
    return s, 92


def quadros():
    fundo = cenario()
    texto = f"Andando {NOME} (tamanho real x{Z})"
    t_anim = 0.0
    s = 0
    for passo in roteiro():
        if passo[0] == "parado":
            for _ in range(int(passo[1] * FPS)):
                f = fundo.copy(); x, y = posicao(s); cola(f, parado, int(x) - px, int(y) - py)
                yield f, Z, texto
            t_anim = 0.0
            continue
        _, s, sf = passo
        sentido = 1 if sf > s else -1
        while (sf - s) * sentido > 0:
            k = int(t_anim / DUR) % 8
            f = fundo.copy(); x, y = posicao(s); cola(f, andar[k], int(x) - px, int(y) - py)
            yield f, Z, texto
            s += sentido * VEL / FPS; t_anim += 1 / FPS
    # camera lenta, de perto
    Z2 = 9
    w2, h2 = TW // Z2, TH // Z2
    perto = np.zeros((h2, w2, 3), np.uint8); perto[:] = (98, 150, 66)
    perto[h2 - 8:] = (176, 132, 84)
    t = 0.0
    while t < 8 * DUR * 2 * 2:
        k = int(t / (DUR * 2)) % 8
        f = perto.copy(); cola(f, andar[k], w2 // 2 - px, h2 - 8 - py + 2)
        yield f, Z2, "Camera lenta (metade da velocidade)"
        t += 1 / FPS


def gif():
    """GIF ampliado 4x: anda, para e volta a andar."""
    Zg = 4
    if MOV[0] == 0:
        GW, GH = 90, 150
    else:
        GW, GH = 200, andar[0].shape[0] + 16
    fundo, _ = grama(GW, GH, 9)
    seq = [("andar", k % 8) for k in range(24)] + [("parado", 0)] + [("andar", k % 8) for k in range(16)] + [("parado", 0)]
    quadros_, dur = [], []
    if MOV[0] == 0:
        s = -6 if MOV[1] > 0 else GH + 70
    else:
        s = 20 if MOV[0] > 0 else GW - 20
    for tipo, k in seq:
        f = fundo.copy()
        x, y = (GW // 2, s) if MOV[0] == 0 else (s, GH - 6)
        cola(f, parado if tipo == "parado" else andar[k], int(round(x)) - px, int(round(y)) - py)
        quadros_.append(Image.fromarray(f).resize((GW * Zg, GH * Zg), Image.NEAREST))
        if tipo == "parado":
            dur.append(900)
        else:
            dur.append(int(DUR * 1000)); s += (MOV[1] if MOV[0] == 0 else MOV[0]) * VEL * DUR
        lim = GH if MOV[0] == 0 else GW
        if s > lim + 70: s = -6
        if s < -30: s = lim + 70 if MOV[0] == 0 else lim + 20
    quadros_[0].save(os.path.join(D, f"heroi_{DIRECAO}_andando_4x.gif"), save_all=True, append_images=quadros_[1:], duration=dur, loop=0)


if __name__ == "__main__":
    saida = os.path.join(D, f"heroi_andando_{DIRECAO}.mp4")
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [ff, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{TW}x{TH}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", "-movflags", "+faststart", saida]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = 0
    for f, z, txt in quadros():
        img = Image.fromarray(f).resize((f.shape[1] * z, f.shape[0] * z), Image.NEAREST)
        tela = Image.new("RGB", (TW, TH), (98, 150, 66)); tela.paste(img, (0, 0))
        rotulo(tela, txt)
        p.stdin.write(tela.tobytes()); n += 1
    p.stdin.close(); p.wait()
    gif()
    print("ok", saida, f"{n / FPS:.1f} s")
