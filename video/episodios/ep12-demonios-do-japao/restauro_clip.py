"""Ep. 12 (24/11): o momento da RESTAURAÇÃO na tela. A gravura entra como está (o arquivo antigo: pequena, borrada,
amarelada); uma linha de luz atravessa a imagem da esquerda para a direita e, por onde ela passa, fica a versão restaurada
(restaurar.py). Selo "RESTAURAÇÃO DIGITAL" em cima, dentro do quadro. Mesmo enquadramento e crédito de reais_prontos/.
Saída: rolos/restauro_<nome>.mp4 (7 s). Uso: python3 restauro_clip.py nome [nome ...]"""
import subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageFont, ImageOps

AQUI = Path(__file__).parent; W, H, FPS, DUR = 1920, 1080, 30, 7.0
F = ImageFont.truetype(str(AQUI.parents[1] / "painel" / "fontes" / "ShipporiMincho-800.ttf"), 26)
for nome in sys.argv[1:]:
    depois = Image.open(AQUI / "reais_prontos" / f"{nome}.jpg").convert("RGB")
    orig = ImageOps.exif_transpose(Image.open(AQUI / "reais" / f"{nome}.jpg")).convert("RGB")
    rest = Image.open(AQUI / "reais_restauradas" / f"{nome}.jpg")
    r = min(1720 / rest.width, 900 / rest.height); fw, fh = round(rest.width * r), round(rest.height * r)
    b = 10; x, y = (W - (fw + 2 * b)) // 2 + b, 40 + (920 - (fh + 2 * b)) // 2 + b
    velho = orig.resize((max(1, orig.width), orig.height)).resize((fw, fh), Image.BICUBIC)
    if orig.width < 1000: velho = velho.filter(ImageFilter.GaussianBlur(1.2))
    velho = ImageEnhance.Contrast(ImageEnhance.Color(velho).enhance(0.8)).enhance(0.88)
    amarelo = Image.new("RGB", velho.size, (226, 204, 150)); velho = Image.blend(velho, amarelo, 0.12)
    antes = depois.copy(); antes.paste(velho, (x, y))
    A, D = np.asarray(antes).astype(np.float32), np.asarray(depois).astype(np.float32)
    selo = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(selo); txt = "RESTAURAÇÃO DIGITAL"
    tw = d.textlength(txt, font=F); d.text(((W - tw) / 2, 8), txt, font=F, fill=(214, 70, 58, 255))
    S = np.asarray(selo).astype(np.float32) / 255
    p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-crf", "17", "-pix_fmt", "yuv420p", str(AQUI / "rolos" / f"restauro_{nome}.mp4")], stdin=subprocess.PIPE)
    xs = np.arange(W, dtype=np.float32)[None, :, None]
    for k in range(int(DUR * FPS)):
        t = k / FPS; u = np.clip((t - 1.6) / 2.2, 0, 1); u = u * u * (3 - 2 * u)
        lx = x - 40 + (fw + 80) * u
        m = np.clip((lx - xs) / 30, 0, 1)                          # à esquerda da linha: restaurada
        img = A * (1 - m) + D * m
        if 0 < u < 1:
            brilho = np.exp(-((xs - lx) / 9) ** 2) * 160 + np.exp(-((xs - lx) / 60) ** 2) * 40
            fora = np.zeros((H, 1, 1), np.float32); fora[y:y + fh] = 1
            img = img + brilho * fora * np.array([1.0, 0.92, 0.75], np.float32)
        a = np.clip((t - 1.4) / 0.5, 0, 1) * (1 - np.clip((t - 6.0) / 0.8, 0, 1))
        img = img * (1 - S[..., 3:4] * a) + S[..., :3] * 255 * S[..., 3:4] * a
        p.stdin.write(np.clip(img, 0, 255).astype(np.uint8).tobytes())
    p.stdin.close(); p.wait(); print("ok", nome)
