"""Video de revisao: a mesma acao vista de lado, de frente e de costas, lado a lado (cada uma em loop)."""
import glob, json, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

AQUI = os.path.dirname(os.path.abspath(__file__))
ACOES = os.path.join(AQUI, "..", "revisao", "acoes")
acao = sys.argv[1] if len(sys.argv) > 1 else "enxada"
FPS, TW, TH, Z = 60, 1280, 720, 5
fonte = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)


def carrega(vista):
    pasta = os.path.join(ACOES, f"{acao}_{vista}")
    info = json.load(open(os.path.join(pasta, "info.json")))
    fs = sorted(glob.glob(os.path.join(pasta, f"{acao}_*.png")), key=lambda f: int(os.path.basename(f).split("_")[1]))
    quadros = [Image.open(f).convert("RGBA") for f in fs]
    parado = Image.open(os.path.join(pasta, "parado.png")).convert("RGBA")
    seq = [(parado, 0.5)] + [(q, d["duracao_s"]) for q, d in zip(quadros, info["quadros"])] * 2
    return seq, info["pivot"]


vistas = [("lado", "De lado"), ("frente", "De frente"), ("costas", "De costas")]
dados = [carrega(v) for v, _ in vistas]


def quadro_no_tempo(seq, t):
    tot = sum(d for _, d in seq)
    t %= tot
    for im, d in seq:
        if t < d:
            return im
        t -= d
    return seq[-1][0]


def tela(t, lento):
    W, H = TW // Z, TH // Z
    f = Image.new("RGBA", (W, H), (98, 150, 66, 255))
    dr = ImageDraw.Draw(f)
    dr.rectangle((0, H - 30, W, H), fill=(150, 108, 66))
    for i, (seq, (px, py)) in enumerate(dados):
        im = quadro_no_tempo(seq, t / lento)
        cx = int(W * (i + 0.5) / 3)
        f.alpha_composite(im, (cx - px, H - 24 - py))
    g = f.resize((W * Z, H * Z), Image.NEAREST).convert("RGB")
    dr = ImageDraw.Draw(g)
    for i, (_, nome) in enumerate(vistas):
        cx = int(TW * (i + 0.5) / 3)
        tw = dr.textlength(nome, font=fonte)
        dr.rounded_rectangle((cx - tw / 2 - 12, 14, cx + tw / 2 + 12, 54), 8, fill=(30, 30, 36))
        dr.text((cx - tw / 2, 19), nome, font=fonte, fill=(255, 255, 255))
    nomes = dict(enxada="Enxada", picareta="Picareta", machado="Machado", pa="Pa", foice="Foice",
                 regador="Regador", vara="Vara de pescar")
    dr.text((20, TH - 44), nomes.get(acao, acao), font=fonte, fill=(255, 255, 255))
    if lento > 1:
        txt = f"camera lenta ({lento}x)"
        dr.text((TW - dr.textlength(txt, font=fonte) - 20, TH - 44), txt, font=fonte, fill=(255, 255, 255))
    return g


saida = os.path.join(ACOES, f"heroi_{acao}_3_vistas.mp4")
p = subprocess.Popen([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                      "-s", f"{TW}x{TH}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "16",
                      "-pix_fmt", "yuv420p", "-movflags", "+faststart", saida], stdin=subprocess.PIPE)
n = 0
for seg, lento in ((6.0, 1), (6.0, 3)):
    for i in range(int(seg * FPS)):
        p.stdin.write(tela(i / FPS, lento).tobytes()); n += 1
p.stdin.close(); p.wait()
print("ok", saida, n / FPS, "s")
