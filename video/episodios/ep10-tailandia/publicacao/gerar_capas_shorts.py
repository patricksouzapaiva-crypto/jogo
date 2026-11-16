"""Capas dos 3 Shorts do Ep. 10 (1080×1920), no estilo aprovado das capas do longo (16/11): câmera de segurança em
visão noturna, texto enorme branco + vermelho com brilho, sem círculo e sem seta. Texto na zona segura (longe do topo,
da base e da coluna de botões à direita). Uso: python3 gerar_capas_shorts.py"""
from pathlib import Path
from PIL import Image
import gerar_capas_v2 as G   # reaproveita grade/falhas/texto/hud (gera as capas do longo também — rápido)

AQUI = Path(__file__).parent
W, H = 1080, 1920


def vertical(cod, cx, cy, zoom=1.0):
    img = Image.open(G.R / f"{cod}.jpg").convert("RGB"); iw, ih = img.size
    ch = ih / zoom; cw = ch * W / H
    x0 = min(max(0, cx * iw - cw / 2), iw - cw); y0 = min(max(0, cy * ih - ch / 2), ih - ch)
    return img.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, H), Image.LANCZOS)


def capa(cod, cx, cy, zoom, linhas, cores, tam, cam, hora, nome, modo="ir", luz=1.0):
    G.W, G.H = W, H
    img = vertical(cod, cx, cy, zoom)
    from PIL import ImageEnhance
    img = ImageEnhance.Brightness(img).enhance(luz)
    img = G.grade(img, modo)
    if modo == "ir":
        img = G.falha_cctv(img)
    im = img.convert("RGBA")
    G.texto(im, linhas, 60, 1060, cores, tam, ang=3)
    if cam:
        G.hud(im, cam, hora)
    G.salvar(im, nome)
    G.W, G.H = 1280, 720


capa("G03_variacao_2", 0.47, 0.5, 1.0, ["QUEM MORA", "NA CASA", "VAZIA?"], [G.BRANCO, G.BRANCO, G.VERM], [150, 150, 190],
     "CAM 01 - CORREDOR", "03:17:40", "capa_short1_casa_vazia.jpg", luz=1.1)
capa("C2_03_variacao_2", 0.63, 0.42, 1.0, ["RECOLHA", "AS ROUPAS", "DO VARAL"], [G.BRANCO, G.BRANCO, G.VERM], [150, 150, 170],
     None, None, "capa_short2_krasue.jpg", modo="sangue", luz=1.3)
capa("H18_variacao_4", 0.47, 0.5, 1.0, ["O QUE ELE", "ESTÁ", "COMENDO?"], [G.BRANCO, G.BRANCO, G.VERM], [150, 150, 170],
     "CAM 04 - QUARTO", "06:12:01", "capa_short3_carne_crua.jpg", luz=1.1)
