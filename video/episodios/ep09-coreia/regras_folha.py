"""Troca o texto da folha das regras (B04, gerada pelo Flow com regras genéricas) pelas 4 regras do roteiro, em
coreano manuscrito (Nanum Pen Script, OFL). Apaga a tinta antiga com inpaint (mantém a textura do papel).
Uso: python3 regras_folha.py imagens/B04_A.jpg imagens/B04_A_regras.jpg"""
import sys
import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path
FONTE = str(Path(__file__).resolve().parents[2] / "painel" / "fontes" / "NanumPenScript-Regular.ttf")
REGRAS = ["1. 자기 전에 선풍기를 꺼 주세요.",
          "2. F04호 벽을 두드리지 마세요.",
          "3. 3시 이후에 누가 이름을 불러도",
          "    대답하지 마세요.",
          "4. 이 층에서는 빨간색으로",
          "    아무것도 쓰지 마세요."]
ent, sai = sys.argv[1], sys.argv[2]
img = cv2.imread(ent); H, W = img.shape[:2]
g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
# papel = maior região clara perto do centro-alto
_, claro = cv2.threshold(g, 175, 255, cv2.THRESH_BINARY)
claro = cv2.morphologyEx(claro, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
n, lab, st, _ = cv2.connectedComponentsWithStats(claro)
i = max(range(1, n), key=lambda k: st[k, cv2.CC_STAT_AREA])
x, y, w, h = st[i, :4]; print("papel:", x, y, w, h)
comp = (lab == i).astype(np.uint8) * 255
cont, _ = cv2.findContours(comp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
papel = np.zeros_like(comp); cv2.fillPoly(papel, [cv2.convexHull(max(cont, key=cv2.contourArea))], 255)   # folha inteira
ret = np.zeros_like(comp); m_ = 26; ret[y + m_:y + h - m_, x + m_:x + w - m_] = 255   # retângulo da folha, sem as fitas
papel = cv2.max(cv2.erode(papel, np.ones((15, 15), np.uint8)), ret)
# tinta = pixels escuros dentro do papel
# papel limpo = cor e sombra do próprio papel (mediana grande apaga os traços), mais o ruído da foto
fundo = img
for _ in range(3):
    fundo = cv2.medianBlur(fundo, 61)
fundo = cv2.GaussianBlur(fundo, (0, 0), 6).astype(np.float32)
fundo += np.random.default_rng(9).normal(0, 2.8, fundo.shape)
m = cv2.GaussianBlur(cv2.erode(papel, np.ones((19, 19), np.uint8)).astype(np.float32) / 255, (0, 0), 6)[..., None]
limpo = (img.astype(np.float32) * (1 - m) + fundo * m).clip(0, 255).astype(np.uint8)
# texto novo, com leve inclinação e tinta de caneta
pil = Image.fromarray(cv2.cvtColor(limpo, cv2.COLOR_BGR2RGB)).convert("RGBA")
cam = Image.new("RGBA", pil.size, (0, 0, 0, 0)); d = ImageDraw.Draw(cam)
tam = int(h / 9.5); f = ImageFont.truetype(FONTE, tam)
while max(d.textlength(r, font=f) for r in REGRAS) > w * 0.86:
    tam -= 2; f = ImageFont.truetype(FONTE, tam)
y0 = y + h * 0.1; passo = (h * 0.82) / len(REGRAS)
rng = np.random.default_rng(4)
for k, r in enumerate(REGRAS):
    d.text((x + w * 0.07 + rng.uniform(-4, 4), y0 + k * passo + rng.uniform(-3, 3)), r, font=f, fill=(28, 30, 42, 235))
cam = cam.rotate(-0.8, resample=Image.BICUBIC, center=(x + w / 2, y + h / 2)).filter(ImageFilter.GaussianBlur(0.7))
pil.alpha_composite(cam)
out = np.array(pil.convert("RGB")).astype(np.float32)
out += rng.normal(0, 3.5, out.shape)                  # o ruído da foto de celular volta por cima do texto novo
Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(sai, quality=93); print("ok", sai)
