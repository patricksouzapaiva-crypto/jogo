"""GIF de conferencia: andar da esquerda ao lado do andar da direita espelhado (so para comparar
ritmo, altura e tamanho; o espelhado nao e usado no jogo)."""
import json, os
from PIL import Image, ImageDraw, ImageFont, ImageOps

AQUI = os.path.dirname(os.path.abspath(__file__))
REV = os.path.join(AQUI, "..", "revisao")
Z, W, H = 5, 62, 74
fonte = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
esq = [Image.open(os.path.join(REV, "lado_esq", f"andar_{k}.png")) for k in range(8)]
dir_ = [ImageOps.mirror(Image.open(os.path.join(REV, "lado", f"andar_{k}.png"))) for k in range(8)]
ie = json.load(open(os.path.join(REV, "lado_esq", "info.json")))
idr = json.load(open(os.path.join(REV, "lado", "info.json")))
pe = ie["pivot"]; pd = (idr["tamanho"][0] - 1 - idr["pivot"][0], idr["pivot"][1])
quadros = []
for k in range(32):
    c = Image.new("RGB", (2 * (W * Z + 20) + 20, H * Z + 44), (96, 140, 70))
    d = ImageDraw.Draw(c)
    for i, (im, pv, nome) in enumerate(((esq[k % 8], pe, "ESQUERDA (desenho dela)"),
                                        (dir_[k % 8], pd, "DIREITA espelhada (so p/ comparar)"))):
        base = Image.new("RGBA", (W, H), (0, 0, 0, 0)); base.alpha_composite(im, (W // 2 - pv[0], H - 3 - pv[1]))
        big = base.resize((W * Z, H * Z), Image.NEAREST)
        x0 = 20 + i * (W * Z + 20); c.paste(big, (x0, 36), big)
        d.text((x0, 8), nome, font=fonte, fill=(255, 255, 255))
    quadros.append(c)
quadros[0].save(os.path.join(REV, "lado_esq", "esquerda_vs_direita_espelhada.gif"), save_all=True,
                append_images=quadros[1:], duration=75, loop=0)
print("ok")
