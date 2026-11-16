"""Ep. 10 (16/11): prepara para a montagem o material REAL (o peso documental do episódio).
1) filmes_prontos/<nome>.mp4 — trechos dos trailers (Inhuman Kiss, The Medium) e do filme de arquivo de 1969
   (Rice Farmer in Thailand), na moldura de "arquivo" do Ep. 09: o trecho menor no centro, borda fina, fundo com ele
   mesmo desfocado e escuro, e o crédito EM CIMA (embaixo fica a legenda). Sem áudio (o som do trailer sai à parte
   em <nome>_som.wav, para entrar nos respiros).
2) reais_prontos/<nome>.jpg — as fotos do Wikimedia Commons em 1920×1080: a foto inteira (sem cortar) num
   "papel de dossiê" sobre ela mesma desfocada, com o crédito (autor · licença) — as licenças CC BY/BY-SA pedem.
Tudo fora do git (repositório público). Uso: python3 preparar_midia.py [filmes|fotos]"""
import json, subprocess, sys
from pathlib import Path

AQUI = Path(__file__).parent
FP = AQUI / "filmes_prontos"; FP.mkdir(exist_ok=True)
RP = AQUI / "reais_prontos"; RP.mkdir(exist_ok=True)
FONTE = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
KISS = "INHUMAN KISS (2019) · DIR. SITTISIRI MONGKOLSIRI"
MEDIUM = "THE MEDIUM (2021) · DIR. BANJONG PISANTHANAKUN · PROD. NA HONG-JIN"
ARQ = "RICE FARMER IN THAILAND (1969) · PUBLIC MEDIA INC. · INTERNET ARCHIVE"
# nome: (arquivo, [(ini, fim) ...], crédito, rótulo, recorte w:h:x:y)
TRECHOS = {
    "kiss_krasue": ("filmes/CAP2_InhumanKiss_corte8s.mp4", [(0.0, 8.0)], KISS, "TRECHO DE FILME", None),
    "medium_isan": ("filmes/CAP4_TheMedium_corte12s.mp4", [(0.0, 1.0), (5.2, 12.0)], MEDIUM, "TRECHO DE FILME", None),  # sem o letreiro "Isan"
    "arq_canais": ("filmes/arquivo/rice_farmer_thailand_1969.mp4", [(31.0, 39.0)], ARQ, "FILME DE ARQUIVO", "480:360:80:0"),
    "arq_vila": ("filmes/arquivo/rice_farmer_thailand_1969.mp4", [(346.0, 356.0)], ARQ, "FILME DE ARQUIVO", "480:360:80:0"),
    "arq_templo": ("filmes/arquivo/rice_farmer_thailand_1969.mp4", [(421.0, 429.0)], ARQ, "FILME DE ARQUIVO", "480:360:80:0"),
    "arq_velas": ("filmes/arquivo/rice_farmer_thailand_1969.mp4", [(464.0, 472.0)], ARQ, "FILME DE ARQUIVO", "480:360:80:0"),
    "arq_oferendas": ("filmes/arquivo/rice_farmer_thailand_1969.mp4", [(826.0, 834.0)], ARQ, "FILME DE ARQUIVO", "480:360:80:0"),
}


def filmes(pedidos):
    fw, fh = 1536, 864
    fx, fy = (1920 - fw) // 2, 120
    for nome in pedidos:
        src, segs, credito, rotulo, rec = TRECHOS[nome]
        fc = "".join(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS[v{k}];" for k, (a, b) in enumerate(segs))
        fc += "".join(f"[v{k}]" for k in range(len(segs))) + f"concat=n={len(segs)}:v=1:a=0[c];"
        arquivo = rotulo == "FILME DE ARQUIVO"
        # o filme de 1969 é 4:3 dentro de 640×360: tira as faixas pretas; um pouco mais lento (é 25 q/s, com grão)
        cor = ("eq=saturation=0.75:contrast=1.05:brightness=-0.04,noise=alls=10:allf=t" if arquivo else
               "eq=saturation=0.82:contrast=1.06:brightness=-0.03,noise=alls=7:allf=t")
        lento = "setpts=1.25*PTS,minterpolate=fps=30:mi_mode=blend," if arquivo else "fps=30,"
        qw = round(fh * 4 / 3) if arquivo else fw
        qx = (1920 - qw) // 2
        fc += (f"[c]{f'crop={rec},' if rec else ''}scale={qw}:{fh}:flags=lanczos,{lento}{cor},split[a][b];"
               f"[a]scale=480:270,boxblur=12:3,eq=brightness=-0.24:saturation=0.55,scale=1920:1080[fundo];"
               f"[b]pad={qw + 4}:{fh + 4}:2:2:color=0xb8b0a4@0.55[quadro];"
               f"[fundo][quadro]overlay={qx - 2}:{fy - 2},"
               f"drawtext=fontfile={FONTE}:text='{rotulo}':fontsize=22:fontcolor=0xc8302c:x={qx}:y={fy - 46},"
               f"drawtext=fontfile={FONTE}:text='{credito}':fontsize=22:fontcolor=0xd8d0c4:x={qx + (270 if arquivo else 230)}:y={fy - 46},"
               f"format=yuv420p[v]")
        saida = FP / f"{nome}.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(AQUI / src), "-filter_complex", fc, "-map", "[v]", "-an",
                        "-c:v", "libx264", "-crf", "22", "-preset", "medium", str(saida)], check=True)
        tem_som = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0",
                                  str(AQUI / src)], capture_output=True, text=True).stdout.strip()
        if not arquivo and tem_som:   # o som do trailer, para os respiros (os cortes do usuário vieram mudos)
            fa = "".join(f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS[a{k}];" for k, (a, b) in enumerate(segs))
            fa += "".join(f"[a{k}]" for k in range(len(segs))) + f"concat=n={len(segs)}:v=0:a=1[s]"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(AQUI / src), "-filter_complex", fa, "-map", "[s]", "-ac", "2",
                            "-ar", "48000", str(FP / f"{nome}_som.wav")], check=True)
        d = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(saida)],
                           capture_output=True, text=True).stdout.strip()
        print("ok", saida.name, d, "s", flush=True)


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


qual = sys.argv[1:] or ["filmes", "fotos"]
if "filmes" in qual:
    filmes([a for a in sys.argv[2:]] or list(TRECHOS))
if "fotos" in qual:
    fotos()
