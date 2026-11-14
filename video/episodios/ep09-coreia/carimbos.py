"""Carimbos de data das imagens/clipes de IA → uma linha do tempo só (14/11).
Cada imagem veio com uma data inventada pela IA (14/10, 28/10, até 04/15) e a cozinha "acontecia" antes da volta da
Lívia. O usuário já reprovou data errada antes. Aqui: acha os pixels do carimbo dentro da caixa, apaga (inpaint) e
escreve a data certa no mesmo lugar, mesma altura e mesma cor.

Linha do tempo (2017): sáb 21/10 a subida e a noite da busca; ter 24/10 06:15 a Lívia no degrau; sex 27/10 03:12 a
cozinha, 04:03 o fórum; relatos do Jangsan-beom (fotos de "fórum") em 2013.
Originais ficam em imagens_v3/_orig/ (fora do git; também estão no histórico).
Uso: python3 carimbos.py            (imagens)   |   python3 carimbos.py video  (o clipe V05_A)"""
import shutil, subprocess, sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

AQUI = Path(__file__).parent
IM = AQUI / "imagens_v3"; ORIG = IM / "_orig"; ORIG.mkdir(exist_ok=True)
FONTE = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# nome → (caixa x0,y0,x1,y1 em PIXELS da imagem 1376×768, medida em volta do carimbo antigo; linhas novas; alinhamento;
#         fundo preto sólido como o rótulo original)
CARIMBOS = {
    "M01_A": ((1150, 716, 1350, 744), ["2017.10.21 17:40"], "dir", False),
    "M03_C": ((1040, 706, 1344, 742), ["2017.10.21 18:45"], "dir", False),
    "M05_B": ((972, 702, 1350, 756), ["2017.10.21 23:15"], "dir", False),
    "M06_B": ((1118, 716, 1346, 740), ["2017/10/24  06:15"], "dir", False),
    "M06_C": ((1080, 698, 1370, 764), ["06:15 AM - 2017/10/24", "Busan, KR"], "dir", False),
    "C01_A": ((1074, 702, 1342, 728), ["2017.10.27 03:12 AM"], "dir", False),
    "C01_C": ((1036, 670, 1314, 698), ["2017.10.27  03:10"], "dir", False),
    "C03_A": ((1102, 674, 1310, 706), ["2017.10.27"], "dir", False),
    "C03_B": ((1222, 716, 1354, 760), ["2017.10.27 03:15", "BUSAN"], "dir", False),
    "C05_A": ((1080, 704, 1342, 742), ["2017.10.27 04:03"], "dir", False),
    "M07_A": ((786, 652, 1160, 688), ["2013.08.17 BUSAN,KOREA"], "esq", True),
    "M07_B": ((870, 688, 1256, 742), ["2013/08/17 23:45"], "esq", False),
}


def corrigir(nome, caixa, linhas, alinhar, preto):
    src = ORIG / f"{nome}.jpg"
    if not src.exists():
        shutil.copy(IM / f"{nome}.jpg", src)
    arr = np.array(Image.open(src).convert("RGB"))
    x0, y0, x1, y1 = caixa
    reg = arr[y0:y1, x0:x1].reshape(-1, 3)
    lum = reg.mean(axis=1)
    cor = tuple(int(c) for c in np.median(reg[lum >= np.percentile(lum, 93)], axis=0))   # a cor do texto antigo
    if preto:
        img = Image.fromarray(arr); ImageDraw.Draw(img).rectangle([x0, y0, x1, y1], fill=(8, 8, 8))
    else:
        m = np.zeros(arr.shape[:2], np.uint8); m[y0 - 2:y1 + 2, x0 - 3:x1 + 3] = 255
        limpo = cv2.inpaint(cv2.cvtColor(arr, cv2.COLOR_RGB2BGR), m, 9, cv2.INPAINT_TELEA)
        img = Image.fromarray(cv2.cvtColor(limpo, cv2.COLOR_BGR2RGB))
    d = ImageDraw.Draw(img)
    n = len(linhas); alt = (y1 - y0) / n
    y = y0
    for k, ln in enumerate(linhas):
        tam = 8
        while True:                                      # maior fonte que cabe na largura e na altura da linha
            f = ImageFont.truetype(FONTE, tam + 1); bb = d.textbbox((0, 0), ln, font=f)
            if bb[2] - bb[0] > (x1 - x0) * (1.0 if k == 0 else 0.6) or bb[3] - bb[1] > alt * 0.8:
                break
            tam += 1
        f = ImageFont.truetype(FONTE, tam); bb = d.textbbox((0, 0), ln, font=f)
        tx = x1 - (bb[2] - bb[0]) if alinhar == "dir" else x0 + 4
        ty = y + (alt - (bb[3] - bb[1])) / 2
        d.text((tx - bb[0], ty - bb[1]), ln, font=f, fill=cor)
        y += alt
    img.save(IM / f"{nome}.jpg", quality=92)
    print("ok", nome, "cor", cor)


def video():
    """V05_A: o carimbo deforma ("AI6/AI7/AI8"): cobre a área com o próprio fundo (delogo) e escreve fixo."""
    ent = AQUI / "clipes_v3" / "V05_A.mp4"; orig = AQUI / "clipes_v3" / "_orig_V05_A.mp4"
    if not orig.exists():
        shutil.copy(ent, orig)
    # 1280×720: o carimbo fica em ~x 640–990, y 640–680 (conferido no quadro)
    filtro = ("delogo=x=996:y=652:w=258:h=32,"
              "drawtext=fontfile=" + FONTE + ":text='2017.10.27 03\\:12 AM':fontsize=22:fontcolor=0xd9b25a:"
              "x=1245-tw:y=659")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(orig), "-vf", filtro, "-an", "-c:v", "libx264", "-crf", "16",
                    str(ent)], check=True)
    print("ok V05_A")


if __name__ == "__main__":
    if sys.argv[1:] == ["video"]:
        video()
    else:
        for nome, args in CARIMBOS.items():
            if not sys.argv[1:] or nome in sys.argv[1:]:
                corrigir(nome, *args)
