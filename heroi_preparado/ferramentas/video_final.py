"""Video final do heroi (usa so a folha pronta do Godot: heroi_atlas.png + heroi.json).

Parte 1: ele anda num quadrado (direita, baixo, esquerda, cima) e para entre os lados, respirando.
Parte 2: de perto, as 4 direcoes paradas respirando e depois andando no lugar.
"""
import itertools, json, os, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

AQUI = os.path.dirname(os.path.abspath(__file__))
ARTE = os.path.join(AQUI, "..", "JogoFazenda", "arte", "preparado", "heroi")
SAIDA = os.path.join(AQUI, "..", "revisao", "heroi_final_4_direcoes.mp4")
d = json.load(open(os.path.join(ARTE, "heroi.json")))
atlas = np.asarray(Image.open(os.path.join(ARTE, d["atlas"])).convert("RGBA"))
CW, CH = d["celula"]; PX, PY = d["pivot"]
VEL = d["velocidade_andar_px_s"]
FPS, TW, TH = 60, 1280, 720
fonte = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
fonte_p = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
VET = {"down": (0, 1), "left": (-1, 0), "right": (1, 0), "up": (0, -1)}


def quadro(anim, i):
    a = d["animacoes"][anim]
    return atlas[a["linha"] * CH:(a["linha"] + 1) * CH, i * CW:(i + 1) * CW]


def indice(anim, t):
    dur = d["animacoes"][anim]["duracoes"]
    t = t % sum(dur)
    for i, x in enumerate(dur):
        if t < x:
            return i
        t -= x
    return len(dur) - 1


def grama(W, H, seed=7):
    rng = np.random.default_rng(seed)
    a = np.zeros((H, W, 3), np.uint8); a[:] = (98, 150, 66)
    for _ in range(W * H // 30):
        x, y = rng.integers(0, W), rng.integers(0, H)
        a[y, x] = (84, 132, 56) if rng.random() < .6 else (118, 170, 80)
    for _ in range(W * H // 900):
        x, y = rng.integers(2, W - 3), rng.integers(4, H - 3)
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


def rotulo(img, texto, y=18, x=20):
    dr = ImageDraw.Draw(img)
    dr.rounded_rectangle((x, y, x + 20 + dr.textlength(texto, font=fonte), y + 48), 10, fill=(30, 30, 36))
    dr.text((x + 10, y + 6), texto, font=fonte, fill=(255, 255, 255))


def parte1():
    Z = 5
    W, H = TW // Z, TH // Z
    fundo = grama(W, H)
    roteiro = [("right", 2.0), ("parado", 1.6), ("down", 1.1), ("parado", 1.6),
               ("left", 2.0), ("parado", 1.6), ("up", 1.1), ("parado", 1.8)] * 2
    pos = np.array([70.0, 84.0]); direcao = "right"; t_anim = 0.0; andando = False
    for etapa, dur in roteiro:
        for _ in range(int(dur * FPS)):
            if etapa == "parado":
                if andando:
                    andando = False; t_anim = 0.0
                anim = f"idle_{direcao}"
            else:
                if not andando or etapa != direcao:
                    if not andando:
                        t_anim = d["animacoes"][f"walk_{etapa}"]["inicio"] * d["duracao_quadro_andar_s"]
                    andando = True; direcao = etapa
                anim = f"walk_{direcao}"
                pos += np.array(VET[direcao]) * VEL / FPS
            f = fundo.copy()
            cola(f, quadro(anim, indice(anim, t_anim)), int(round(pos[0])) - PX, int(round(pos[1])) - PY)
            t_anim += 1 / FPS
            img = Image.fromarray(f).resize((W * Z, H * Z), Image.NEAREST)
            rotulo(img, "Herói no jogo: anda e para respirando (tamanho real x5)")
            yield img


def parte2():
    Z = 7
    W, H = TW // Z, TH // Z
    base = np.zeros((H, W, 3), np.uint8); base[:] = (98, 150, 66)
    base[H - 14:] = (176, 132, 84)
    nomes = ["down", "left", "right", "up"]
    xs = [int(W * (i + 0.5) / 4) for i in range(4)]
    for tipo, seg, texto in (("idle", 4.5, "Parado respirando (de perto)"), ("walk", 3.0, "Andando no lugar (de perto)")):
        t = 0.0
        while t < seg:
            f = base.copy()
            for x, n in zip(xs, nomes):
                anim = f"{tipo}_{n}"
                cola(f, quadro(anim, indice(anim, t)), x - PX, H - 12 - PY)
            img = Image.new("RGB", (TW, TH), (176, 132, 84))
            img.paste(Image.fromarray(f).resize((W * Z, H * Z), Image.NEAREST), ((TW - W * Z) // 2, 0))
            rotulo(img, texto)
            dr = ImageDraw.Draw(img)
            for x, n in zip(xs, ["frente", "esquerda", "direita", "costas"]):
                dr.text((x * Z - dr.textlength(n, font=fonte_p) / 2, TH - 40), n, font=fonte_p, fill=(40, 30, 20))
            yield img
            t += 1 / FPS


if __name__ == "__main__":
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [ff, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{TW}x{TH}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", "-movflags", "+faststart", SAIDA]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = 0
    for img in itertools.chain(parte1(), parte2()):
        p.stdin.write(img.convert("RGB").tobytes()); n += 1
    p.stdin.close(); p.wait()
    print("ok", SAIDA, f"{n / FPS:.1f} s")
