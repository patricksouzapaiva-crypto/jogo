"""Prancha, GIF e video MP4 de uma acao (le revisao/acoes/<pasta>/info.json e os quadros)."""
import glob, itertools, json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

AQUI = os.path.dirname(os.path.abspath(__file__))
pasta = sys.argv[1]
nome = sys.argv[2] if len(sys.argv) > 2 else "enxada"
info = json.load(open(os.path.join(pasta, "info.json")))
px, py = info["pivot"]
quadros = [Image.open(f).convert("RGBA") for f in sorted(glob.glob(os.path.join(pasta, f"{nome}_*.png")),
                                                          key=lambda f: int(os.path.basename(f).split("_")[1]))]
duracoes = [q["duracao_s"] for q in info["quadros"]]
parado = Image.open(os.path.join(pasta, "parado.png")).convert("RGBA")
fonte = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
fonte_p = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)

# area util comum
bb = None
for im in quadros + [parado]:
    b = im.getbbox(); bb = b if bb is None else (min(bb[0], b[0]), min(bb[1], b[1]), max(bb[2], b[2]), max(bb[3], b[3]))
bb = (bb[0] - 2, bb[1] - 2, bb[2] + 2, py + 2)

# ---- prancha ----
Z = 5
w, h = bb[2] - bb[0], bb[3] - bb[1]
o = Image.new("RGB", ((w * Z + 8) * len(quadros), h * Z + 30), (96, 140, 70))
d = ImageDraw.Draw(o)
for i, (q, qi) in enumerate(zip(quadros, info["quadros"])):
    c = q.crop(bb).resize((w * Z, h * Z), Image.NEAREST)
    x0 = i * (w * Z + 8)
    o.paste(c, (x0, 0), c)
    d.line([(x0, (py - bb[1]) * Z), (x0 + w * Z, (py - bb[1]) * Z)], fill=(70, 100, 50), width=2)
    d.text((x0 + 4, h * Z + 6), f"{i} {qi['nome']} ({int(qi['duracao_s'] * 1000)} ms)", font=fonte_p, fill=(255, 255, 255))
o.save(os.path.join(pasta, "prancha_final.png"))

# ---- GIF (4x): parado, 3 golpes, parado ----
Zg = 4
seq = [(parado, 500)] + [(q, int(t * 1000)) for q, t in zip(quadros, duracoes)] * 3 + [(parado, 700)]
fr, du = [], []
for im, t in seq:
    c = Image.new("RGBA", (w, h), (96, 140, 70, 255)); c.alpha_composite(im.crop(bb))
    fr.append(c.resize((w * Zg, h * Zg), Image.NEAREST).convert("RGB")); du.append(t)
fr[0].save(os.path.join(pasta, f"{nome}_4x.gif"), save_all=True, append_images=fr[1:], duration=du, loop=0)

# ---- video MP4 ----
FPS, TW, TH = 60, 1280, 720


def tela(im, z, texto, chao=(150, 108, 66)):
    W, H = TW // z, TH // z
    f = Image.new("RGBA", (W, H), (98, 150, 66, 255))
    dr = ImageDraw.Draw(f)
    dr.rectangle((0, H - 22, W, H), fill=chao)
    f.alpha_composite(im, (W // 2 - px, H - 14 - py))
    g = Image.new("RGB", (TW, TH), (98, 150, 66))
    g.paste(f.resize((W * z, H * z), Image.NEAREST).convert("RGB"), ((TW - W * z) // 2, 0))
    dr = ImageDraw.Draw(g)
    dr.rounded_rectangle((20, 18, 40 + dr.textlength(texto, font=fonte), 66), 10, fill=(30, 30, 36))
    dr.text((30, 24), texto, font=fonte, fill=(255, 255, 255))
    return g


def gera():
    for z, vezes, lento, texto in ((6, 5, 1, f"{nome.capitalize()} (tamanho real x6)"), (9, 2, 3, "Camera lenta (3x mais devagar)")):
        for _ in range(int(0.6 * FPS)):
            yield tela(parado, z, texto)
        for _ in range(vezes):
            for q, t in zip(quadros, duracoes):
                img = tela(q, z, texto)
                for _ in range(max(1, round(t * lento * FPS))):
                    yield img
        for _ in range(int(0.6 * FPS)):
            yield tela(parado, z, texto)


ff = imageio_ffmpeg.get_ffmpeg_exe()
saida = os.path.join(pasta, f"heroi_{nome}_{os.path.basename(pasta.rstrip('/'))}.mp4")
p = subprocess.Popen([ff, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{TW}x{TH}", "-r", str(FPS), "-i", "-",
                      "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", "-movflags", "+faststart", saida], stdin=subprocess.PIPE)
n = 0
for img in gera():
    p.stdin.write(img.tobytes()); n += 1
p.stdin.close(); p.wait()
print("ok", saida, f"{n / FPS:.1f} s")
