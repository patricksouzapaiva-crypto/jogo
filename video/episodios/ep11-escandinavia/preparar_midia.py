"""Ep. 11 (16/11): prepara as fotos REAIS do Wikimedia Commons (reais/) para a montagem — reais_prontos/<nome>.jpg em
1920×1080: a foto inteira num "papel de dossiê" sobre ela mesma desfocada, com o crédito (autor · licença) em cima
(as licenças CC BY/BY-SA pedem). Mesmo desenho do Ep. 10. Fora do git (repositório público). Uso: python3 preparar_midia.py"""
import json, sys
from pathlib import Path

AQUI = Path(__file__).parent
RP = AQUI / "reais_prontos"; RP.mkdir(exist_ok=True)
FONTE = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"


def fotos():
    from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance, ImageOps
    cred = json.load(open(AQUI / "reais" / "creditos.json"))
    f_rot = ImageFont.truetype(FONTE, 22)
    for arq in sorted((AQUI / "reais").glob("*.jpg")):
        c = cred.get(arq.name, {})
        im = ImageOps.exif_transpose(Image.open(arq)).convert("RGB")
        fundo = ImageOps.fit(im, (1920, 1080)).resize((480, 270)).filter(ImageFilter.GaussianBlur(10)).resize((1920, 1080))
        fundo = ImageEnhance.Brightness(ImageEnhance.Color(fundo).enhance(0.5)).enhance(0.35)
        # a foto inteira, num papel claro com borda (foto de dossiê), levemente torta
        mh, mw = 820, 1500
        r = min(mw / im.width, mh / im.height)
        foto = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
        foto = ImageEnhance.Color(foto).enhance(0.85)
        b = 18
        papel = Image.new("RGB", (foto.width + 2 * b, foto.height + 2 * b), (226, 219, 204)); papel.paste(foto, (b, b))
        papel = papel.rotate(-0.8 if hash(arq.stem) % 2 else 0.8, resample=Image.BICUBIC, expand=True, fillcolor=(0, 0, 0, 0)).convert("RGBA")
        sombra = Image.new("RGBA", papel.size, (0, 0, 0, 0)); sombra.paste((0, 0, 0, 160), mask=papel.split()[3])
        sombra = sombra.filter(ImageFilter.GaussianBlur(14))
        x, y = (1920 - papel.width) // 2, 120 + (850 - papel.height) // 2
        fundo = fundo.convert("RGBA"); fundo.alpha_composite(sombra, (x + 10, y + 14)); fundo.alpha_composite(papel, (x, y))
        d = ImageDraw.Draw(fundo)
        autor = (c.get("autor") or "autor desconhecido").replace("Unknown authorUnknown author", "autor desconhecido")[:48]
        d.text((212, 70), "FOTO REAL", font=f_rot, fill=(200, 48, 44))
        d.text((212 + 150, 70), f"{autor} · {c.get('licenca', '')} · WIKIMEDIA COMMONS".upper(), font=f_rot, fill=(216, 208, 196))
        fundo.convert("RGB").save(RP / arq.name, quality=92)
        print("ok", arq.name, flush=True)


fotos()
