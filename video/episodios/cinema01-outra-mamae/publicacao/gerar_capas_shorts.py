"""Capas dos 3 Shorts (1080×1920) do O QUE É A CRIATURA? #1 — mesmo estilo das capas v4 (letra Montserrat Black em
degradê, contorno, sombra 3D, tarja vermelha), com as imagens do PRÓPRIO Short (nenhum quadro do filme: os Shorts não
usam o filme). 23/11 (pesquisa): no feed e na busca o Short aparece cortado em QUADRADO (o meio 1080×1080) — o texto e o assunto
ficam dentro dessa faixa do meio (y 420–1500); 2–4 palavras, contorno forte, um assunto só.
Uso: python3 gerar_capas_shorts.py → capa_short1_cleary.jpg, capa_short2_tulpa.jpg, capa_short3_trocado.jpg"""
import capas_base as cb
from capas_base import BRANCO, MONT, OURO, SANGUE, grade, letreiro, tarja, vinheta, salvar

cb.W, cb.H = 1080, 1920


def topo_escuro(im, ate=0.5, forca=0.8):
    import numpy as np
    from PIL import Image
    y = np.linspace(0, 1, cb.H)[:, None, None]
    g = np.clip(1 - y / ate, 0, 1)
    a = np.asarray(im).astype(np.float32) * (1 - forca * g ** 1.4)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def capa(arq, cx, linhas, tag, nome, tinta=(1.0, 1.0, 1.0), brilho=1.25, zoom=1.0):
    im = cb.base(arq, cx, 0.5, zoom)
    im = grade(im, sat=1.3, contraste=1.22, brilho=brilho, tinta=tinta)
    im = vinheta(topo_escuro(im, 0.62, 0.75), 0.35, 0.5, 0.6)
    c = letreiro(im, linhas, cb.W / 2, 560, alinhar="centro", entre=1.0)   # dentro do quadrado do meio
    tarja(c, tag, 90, 440, 58)
    salvar(c, nome)


capa("IA02_lareira_1.jpg", 0.42, [("ELA FOI", MONT, 150, BRANCO), ("TROCADA?", MONT, 170, OURO)], "CASO REAL · 1895",
     "capa_short1_cleary.jpg", tinta=(1.08, 0.97, 0.9))
capa("IL_rasteja_1.jpg", 0.5, [("CRIADO", MONT, 150, BRANCO), ("PELA", MONT, 150, BRANCO), ("MENTE", MONT, 175, SANGUE)],
     "TULPA", "capa_short2_tulpa.jpg", tinta=(0.95, 1.03, 1.0), brilho=1.35)
capa("IA01_berco_2.jpg", 0.55, [("NÃO ERA", MONT, 150, BRANCO), ("SEU FILHO", MONT, 150, OURO)], "O TROCADO",
     "capa_short3_trocado.jpg", tinta=(0.95, 1.0, 1.08), brilho=1.4)
