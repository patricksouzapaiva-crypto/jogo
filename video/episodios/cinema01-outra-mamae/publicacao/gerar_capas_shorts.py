"""Capas dos 3 Shorts (1080×1920) do O QUE É A CRIATURA? #1 — mesmo estilo das capas v4 (letra Montserrat Black em
degradê, contorno, sombra 3D, tarja vermelha), 23/11: com quadros do filme, a pedido do usuário (os Shorts também usam trechos curtos do filme). 23/11 (pesquisa): no feed e na busca o Short aparece cortado em QUADRADO (o meio 1080×1080) — o texto e o assunto
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


def capa_filme(arq, cx, linhas, tag, nome, y, luz=1.2, limpar=4, tinta=(1.0, 1.0, 1.0), y_tag=None):
    """23/11 (usuário: "quero cenas do filme para as capas"): quadro do filme em pé, o rosto/corpo no meio; o texto fica
    onde não cobre o rosto, sempre dentro do quadrado do feed (y 420–1500)."""
    im = cb.base(arq, cx, 0.5, 1.0, limpar=limpar, luz=luz)
    im = grade(im, sat=1.3, contraste=1.2, brilho=1.12, tinta=tinta)
    im = vinheta(im, 0.4, 0.5, 0.5)
    c = letreiro(im, linhas, cb.W / 2, y, alinhar="centro", entre=1.0)
    tarja(c, tag, 90, y_tag if y_tag is not None else y - 120, 58)
    salvar(c, nome)


# a "mãe" sorrindo (o sorriso perfeito demais); o texto embaixo do rosto
capa_filme("q_609.png", 0.47, [("ELA FOI", MONT, 140, BRANCO), ("TROCADA?", MONT, 160, OURO)], "CASO REAL · 1895",
           "capa_short1_cleary.jpg", 1150, luz=1.2, limpar=3, tinta=(1.05, 1.0, 0.95))
# a coisa dobrada debaixo da mesa
capa_filme("q_704.9.png", 0.66, [("CRIADO PELA", MONT, 120, BRANCO), ("MENTE", MONT, 165, SANGUE)],
           "TULPA", "capa_short2_tulpa.jpg", 1170, luz=1.1, limpar=3, y_tag=1060)   # o texto embaixo do rosto
# Bela no túnel vermelho; o texto em cima
capa_filme("q_3027.png", 0.37, [("NÃO ERA", MONT, 140, BRANCO), ("SEU FILHO", MONT, 140, OURO)], "O TROCADO",
           "capa_short3_trocado.jpg", 520, luz=1.5, limpar=4, y_tag=420)
