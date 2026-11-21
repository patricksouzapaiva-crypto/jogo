"""Capas dos 3 Shorts do Ep. 11 (1080×1920), no estilo das capas do longo (21/11): visão noturna de câmera, texto
enorme branco + vermelho com brilho, sem círculo e sem seta. Texto na zona segura (longe do topo, da base e da coluna
de botões à direita). A criatura é sempre a mesma do clímax. Uso: python3 gerar_capas_shorts.py"""
from pathlib import Path
from PIL import Image, ImageEnhance
import gerar_capas as G   # reaproveita grade/falhas/texto/hud (gera as capas do longo também — rápido)

AQUI = Path(__file__).parent
W, H = 1080, 1920


def vertical(cod, cx, cy, zoom=1.0):
    img = Image.open(next((G.R / cod.rsplit("_", 1)[0]).glob(cod + ".*"))).convert("RGB"); iw, ih = img.size
    ch = ih / zoom; cw = ch * W / H
    x0 = min(max(0, cx * iw - cw / 2), iw - cw); y0 = min(max(0, cy * ih - ch / 2), ih - ch)
    return img.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, H), Image.LANCZOS)


def capa(cod, cx, cy, zoom, linhas, cores, tam, cam, hora, nome, luz=1.0):
    G.W, G.H = W, H
    img = ImageEnhance.Brightness(vertical(cod, cx, cy, zoom)).enhance(luz)
    im = G.falha_cctv(G.grade(img, "ir")).convert("RGBA")
    G.texto(im, linhas, 60, 1060, cores, tam, ang=3)
    G.hud(im, cam, hora)
    G.salvar(im, nome)
    G.W, G.H = 1280, 720


capa("H03_04", 0.5, 0.5, 1.0, ["VOCÊ OUVE", "ALGUÉM", "CANTANDO?"], [G.BRANCO, G.BRANCO, G.VERM], [150, 150, 170],
     "CAM 01 - CABANA", "02:10:44", "capa_short1_canto.jpg", luz=1.1)
capa("C2_02_01", 0.45, 0.5, 1.0, ["O INVERNO", "ESCOLHE", "QUEM FICA"], [G.BRANCO, G.BRANCO, G.VERM], [150, 150, 170],
     "CAM 04 - PENHASCO", "05:47:02", "capa_short2_penhasco.jpg", luz=1.15)
capa("C3_03_02", 0.5, 0.45, 1.0, ["VOCÊ É", "O", "PAGAMENTO"], [G.BRANCO, G.VERM, G.VERM], [160, 160, 150],
     "CAM 02 - CLAREIRA", "02:58:13", "capa_short3_clareira.jpg")
