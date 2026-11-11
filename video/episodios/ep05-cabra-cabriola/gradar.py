"""Correção de cor do Ep. 05 — um "look" único para todo o material da história (imagens de IA + fotos reais),
como um colorista faz: 1) igualar os planos, 2) curva de cópia de cinema, 3) paleta, 4) defeitos ópticos de película.
O grão em movimento, a vinheta e o tom frio geral são do motor (por quadro) — aqui NÃO se grava grão na imagem
(grão gravado "anda" junto com o zoom e denuncia a foto parada).

Paleta: tudo quase sem cor e frio; a ÚNICA cor viva do episódio é o âmbar das luzes de dentro de casa
(bandeira da porta, abajur, fresta). É ela que guia o olho — e é nela que a Cabra aparece.

Saída: grade/<nome>.jpg (não vai pro git: é só rodar de novo).   Uso: python3 gradar.py"""
import numpy as np
from pathlib import Path
from PIL import Image, ImageFilter

AQUI = Path(__file__).parent
SAI = AQUI / "grade"; SAI.mkdir(exist_ok=True)
LUMA = np.array([0.2126, 0.7152, 0.0722], np.float32)
ALVO_MEIO = 0.11   # luminância média-alvo dos planos (escuro de cinema, não breu)


def borrar(a, raio):
    return np.asarray(Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(raio)), np.float32) / 255


def gradar(arq, ia):
    im = Image.open(arq).convert("RGB")
    if im.width > 2400:
        im = im.resize((2400, round(im.height * 2400 / im.width)), Image.LANCZOS)
    w, h = im.size
    if ia:
        # 4a) lente: a IA entrega nitidez de computador; película + lente antiga são mais moles,
        #     com franja de cor só nas bordas do quadro
        im = im.filter(ImageFilter.GaussianBlur(w / 2400 * 1.1))
        r, g, b = im.split(); d = max(1, round(w * 0.0012))
        r = r.resize((w + 2 * d, h + 2 * d), Image.BICUBIC).crop((d, d, w + d, h + d))
        im = Image.merge("RGB", (r, g, b))
    a = np.asarray(im, np.float32) / 255
    a = a ** 2.2                                                    # trabalha em luz linear, como na pós de cinema
    lum = (a * LUMA).sum(2, keepdims=True)

    # 1) igualar os planos: leva a exposição média de cada imagem para perto do mesmo alvo (no máx. −0,5 / +0,3 stop)
    meio = float(np.exp(np.log(lum + 1e-4).mean()))
    alvo = (ALVO_MEIO ** 2.2)
    ganho = np.clip((alvo / meio) ** 0.5, 2 ** -0.5, 2 ** 0.3)
    a *= ganho; lum *= ganho

    # 3) paleta — saturação de "bleach bypass": pouca cor no geral, menos ainda nas sombras
    sat = (0.45 if ia else 0.85) * (0.55 + 0.45 * np.clip(lum * 6, 0, 1))
    croma = a - lum
    if ia:
        # o âmbar das luzes de casa sobrevive (um pouco mais que o resto); verdes/azuis da IA somem
        quente = np.clip((a[..., :1] - a[..., 2:3]) / (lum + 0.02), 0, 1)
        sat = sat * (1 + 1.0 * quente)
    a = lum + croma * sat
    # sombras frias (verde-azuladas), altas luzes âmbar: contraste de cor = profundidade
    s = np.clip(1 - lum / 0.18, 0, 1) ** 1.5
    hl = np.clip((lum - 0.25) / 0.6, 0, 1)
    a = a * (1 + s * np.array([-0.16, 0.02, 0.10], np.float32)) * (1 + hl * np.array([0.07, 0.01, -0.10], np.float32) * (0.6 if ia else 1.0))

    # 4b) halação: na película, a luz forte atravessa o filme, bate no fundo e volta — brilho vermelho-alaranjado
    #     em volta das fontes de luz. É o que mais "vende" filme de verdade.
    fonte = np.clip((lum[..., 0] - 0.45) / 0.5, 0, 1)
    halo = borrar(fonte, w * 0.010)[..., None]
    a += halo * np.array([0.13, 0.038, 0.008], np.float32)
    a += borrar(fonte, w * 0.035)[..., None] * 0.035                # um véu leve de brilho (lente velha)

    # 2) curva de cópia: ombro suave (a luz não "estoura" como no digital) e pé levantado (preto de filme, não de tela)
    a = np.clip(a, 0, None)
    a = a / (1 + a * 0.75) * 1.62                                    # ombro
    a = np.clip(a, 0, 1) ** (1 / 2.2)
    a = (a - 0.5) * 1.08 + 0.5                                       # contraste de cópia
    a = 0.028 + np.clip(a, 0, 1) * 0.945                             # pé: preto 7/255, branco 248/255
    Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)).save(SAI / (arq.stem + ".jpg"), quality=94)
    return meio ** (1 / 2.2), float(ganho)


if __name__ == "__main__":
    for pasta, ia in (("imagens", True), ("imagens_reais", False)):
        for arq in sorted((AQUI / pasta).glob("*.[jp][pn]g")):
            m, g = gradar(arq, ia)
            print(f"{arq.name:38s} meio {m:.2f}  ganho {g:+.2f}x")
