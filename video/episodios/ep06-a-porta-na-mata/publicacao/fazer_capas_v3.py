"""Capas do Ep. 06 — versão 3 (12/11): estilo FILMAGEM ACHADA (pedido do usuário: "mais sinistro, estilo filmes com
câmera filmando em primeira pessoa"). É a gravação da câmera do capacete de outro bombeiro (a história tem as
gravações do capacete): granulado, linhas de vídeo, lente distorcida, aberração de cor, REC, hora e "CAM 02".
Dois visuais: câmera comum de noite (cor quase morta, a porta azul ainda aparece) e visão noturna (verde).
O vulto na neblina ao lado da porta fica (sem rosto). Uso: python3 fazer_capas_v3.py"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


def amostrar(c, sy, sx):
    """Amostragem bilinear (sem scipy)."""
    sx = np.clip(sx, 0, W - 1.001); sy = np.clip(sy, 0, H - 1.001)
    x0 = sx.astype(int); y0 = sy.astype(int); fx = sx - x0; fy = sy - y0
    return (c[y0, x0] * (1 - fx) * (1 - fy) + c[y0, x0 + 1] * fx * (1 - fy)
            + c[y0 + 1, x0] * (1 - fx) * fy + c[y0 + 1, x0 + 1] * fx * fy)


def borrar(a, rx, ry):
    """Desfoque mais forte na horizontal: blur gaussiano do PIL numa imagem esticada na vertical."""
    im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
    esc = rx / max(ry, 1e-3)
    im = im.resize((W, int(H * esc)), Image.BICUBIC).filter(ImageFilter.GaussianBlur(rx)).resize((W, H), Image.BICUBIC)
    return np.asarray(im).astype(np.float32) / 255
from fazer_capas import texto
from fazer_capas_v2 import recorte, silhueta, W, H

AQUI = Path(__file__).parent
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
rng = np.random.default_rng(6)


def camera_noite(a):
    lum = a.mean(2, keepdims=True)
    azul = np.clip((a[..., 2] - a[..., 0]) * 4, 0, 1)[..., None]
    a = lum + (a - lum) * (0.25 + 0.9 * azul)                  # cor quase morta; só a tinta azul sobra
    a = np.clip((a - 0.12) / 0.8, 0, 1) ** 1.8                   # noite: preto esmagado, neblina vira cinza
    return a * np.array([0.9, 1.0, 1.02])


def visao_noturna(a):
    l = a.mean(2)
    l = np.clip((l - 0.1) / 0.75, 0, 1) ** 1.25
    return np.stack([l * 0.35, l * 1.0, l * 0.45], 2)


def lente(a, k=0.09, ab=3.0):
    """Barril + aberração cromática (vermelho e azul escorregam para as bordas)."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    nx, ny = (xx - W / 2) / (W / 2), (yy - H / 2) / (W / 2)
    r2 = nx ** 2 + ny ** 2
    out = np.empty_like(a)
    for c, desl in ((0, ab), (1, 0.0), (2, -ab)):
        f = (1 - k * r2) * (1 + desl / (W / 2) * np.sqrt(r2 + 1e-9))
        sx, sy = W / 2 + nx * f * (W / 2), H / 2 + ny * f * (W / 2)
        out[..., c] = amostrar(a[..., c], sy, sx)
    return out


def video_velho(a):
    a = borrar(a, 1.1, 0.6)                        # câmera pequena: borra mais na horizontal
    lum = a.mean(2, keepdims=True)
    a = a + rng.normal(0, 0.075, (H, W, 1)) * (0.4 + lum) + rng.normal(0, 0.02, (H, W, 3))   # granulado
    a *= np.where(np.arange(H) % 3 == 0, 0.86, 1.0)[:, None, None]                          # linhas
    fx = np.linspace(-1, 1, W)[None, :]; fy = np.linspace(-1, 1, H)[:, None]
    a *= (1 - 0.6 * np.clip((fx ** 2 + fy ** 2) / 1.6, 0, 1) ** 1.3)[..., None]          # vinheta de lente
    faixa = (np.abs(np.arange(H) - 610) < 7)[:, None, None]                             # faixa de tracking
    a = np.where(faixa, np.roll(a, 9, axis=1) * 1.15 + 0.03, a)
    return np.clip(a, 0, 1)


def hud(im, cor_hud=(235, 235, 235)):
    d = ImageDraw.Draw(im); f = ImageFont.truetype(MONO, 30); fp = ImageFont.truetype(MONO, 24)
    m, L = 26, 46
    for (x, y, sx, sy) in ((m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)):
        d.line([(x, y), (x + sx * L, y)], fill=cor_hud, width=4); d.line([(x, y), (x, y + sy * L)], fill=cor_hud, width=4)
    d.ellipse([60, 52, 84, 76], fill=(230, 20, 20)); d.text((94, 48), "REC", font=f, fill=cor_hud)
    d.text((W - 300, 48), "03:14:07", font=f, fill=cor_hud)
    bx = W - 130; d.rectangle([bx, 52, bx + 52, 76], outline=cor_hud, width=3); d.rectangle([bx + 52, 59, bx + 57, 69], fill=cor_hud)
    d.rectangle([bx + 5, 57, bx + 17, 71], fill=(230, 20, 20))                                     # bateria acabando
    d.text((60, H - 80), "CAM 02 · CAPACETE", font=fp, fill=cor_hud)
    return im


def capa(look, linhas, nome, vulto=True, tam=165):
    a = recorte("P05_A.jpg", 0.0, 0.48, 1.18)
    a = look(a)
    if vulto:
        a = silhueta(a, 1100, 200, 250, 0.82)
    a = video_velho(lente(a))
    im = Image.fromarray((a * 255).astype(np.uint8))
    im = texto(im, linhas, 40, (H - int(tam * 1.02) * len(linhas)) // 2 + 10, tam)
    hud(im).save(AQUI / nome, quality=93)


if __name__ == "__main__":
    capa(camera_noite, ["QUEM", "VOLTOU?"], "capa_v3_A_quem_voltou.jpg")
    capa(visao_noturna, ["QUEM", "VOLTOU?"], "capa_v3_B_quem_voltou_noturna.jpg")
    capa(camera_noite, ["CONTA", "DE NOVO."], "capa_v3_C_conta_de_novo.jpg", tam=150)
    print("ok")
