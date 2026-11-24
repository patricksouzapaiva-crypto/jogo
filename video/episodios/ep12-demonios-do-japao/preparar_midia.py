"""Ep. 12 (24/11): prepara as imagens REAIS para a montagem.
1) reais_prontos/<nome>.jpg (1920×1080): a obra INTEIRA num papel washi escuro, sobre ela mesma desfocada, com o
   crédito embaixo (obra · artista · ano · acervo). Para os closes de detalhe a montagem usa o original (reais/).
2) rolos/<nome>.mp4: os rolos horizontais viram um travelling da direita para a esquerda (como se lê um emaki).
Fora do git (repositório público). Uso: python3 preparar_midia.py [nome ...]"""
import json, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

Image.MAX_IMAGE_PIXELS = None
AQUI = Path(__file__).parent
R, RP, RO = AQUI / "reais", AQUI / "reais_prontos", AQUI / "rolos"
RP.mkdir(exist_ok=True); RO.mkdir(exist_ok=True)
F_CRED = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 21)
F_TAG = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 21)
COM = "WIKIMEDIA COMMONS"
# crédito das imagens do Commons (obras antigas = domínio público; fotos = licença do autor, ver descrição do vídeo)
CRED = {
 "enryakuji": ("Enryaku-ji, monte Hiei", "foto", COM), "hannya_preto": ("Máscara Hannya do teatro Nō", "", COM),
 "hashihime_sekien": ("Hashihime", "Toriyama Sekien, 1781", COM), "hyakki_tsukumogami": ("Tsukumogami emaki", "séc. XVI", COM),
 "kifune_1": ("Santuário Kifune, Kyoto", "foto", COM), "kifune_2": ("Santuário Kifune, Kyoto", "foto", COM),
 "kifune_3": ("Santuário Kifune, Kyoto", "foto", COM), "kubizuka_1": ("Kubizuka Daimyōjin, Oinosaka", "foto", COM),
 "kubizuka_2": ("Kubizuka Daimyōjin, Oinosaka", "foto", COM), "kubizuka_3": ("Kubizuka Daimyōjin, Oinosaka", "foto", COM),
 **{f"kyosai_{i}": ("Kyōsai Hyakki Gadan", "Kawanabe Kyōsai, 1889", COM) for i in range(1, 9)},
 "modoribashi": ("Ichijō Modoribashi, Kyoto", "foto", COM), "nureonna_7": ("Nure-onna", "Bakemono no e, séc. XVIII", COM),
 "nureonna_sekien": ("Nure-onna", "Toriyama Sekien, 1776", COM), "pedra_2018": ("Sesshō-seki, Nasu (2018)", "foto", COM),
 "pedra_2022": ("Sesshō-seki rachada (2022)", "foto", COM), "pedra_rachada": ("Sesshō-seki rachada (2022)", "foto", COM),
 "pedra_tochigi": ("Sesshō-seki, Nasu", "foto", COM), "ritual_mulher": ("Ushi no toki mairi", "Hokusai Manga, séc. XIX", COM),
 "ritual_sekien": ("Ushi no toki mairi", "Toriyama Sekien, 1779", COM), "sarugatsuji": ("Saru-ga-tsuji, Palácio Imperial de Kyoto", "foto", COM),
 "sekien_kamaitachi": ("Kamaitachi", "Toriyama Sekien, 1776", COM), "sekien_kappa": ("Kappa", "Toriyama Sekien, 1776", COM),
 "sekien_nue": ("Nue", "Toriyama Sekien, 1776", COM), "sekien_rokurokubi": ("Rokurokubi", "Toriyama Sekien, 1776", COM),
 "sekien_satori": ("Satori", "Toriyama Sekien, 1776", COM), "sekien_tengu": ("Tengu", "Toriyama Sekien, 1776", COM),
 "sekien_yamauba": ("Yamauba", "Toriyama Sekien, 1776", COM), "setsubun_hokusai": ("Setsubun", "Katsushika Hokusai", COM),
 "shuten_oeyama_1927": ("Shuten-dōji", "ilustração de 1927", COM), "shuten_sekien": ("Shuten-dōji", "Toriyama Sekien, 1781", COM),
 "tamamo_rijks": ("Tamamo-no-Mae", "Rijksmuseum", COM), "tamamo_xilo": ("Tamamo-no-Mae", "Tsukioka Yoshitoshi", COM),
 "tsuchigumo_14": ("Tsuchigumo sōshi", "séc. XIV", COM), "tsuchigumo_rijks": ("Raikō e o tsuchigumo", "Utagawa Kuniyoshi", COM),
 "ushioni_rolo": ("Ushi-oni", "Hyakkai zukan, 1737", COM), "ushioni_sekien": ("Ushi-oni", "Toriyama Sekien, 1776", COM),
 "ushioni_suushi": ("Ushi-oni", "Bakemono zukushi, séc. XIX", COM), "yamauba_paris": ("Yamauba", "Utagawa Kuniyoshi", COM),
}
MUS = json.load(open(R / "museus.json"))
ROLOS = {"ROLO_hyakki_aic": 34.0, "hyakki_1": 40.0, "hyakki_2": 40.0, "shuten_rolo_cbl": 30.0, "tsuchigumo_14": 30.0,
         "ushioni_suushi": 22.0}


def credito(nome):
    if nome in MUS:
        m = MUS[nome]
        acervo = "CLEVELAND MUSEUM OF ART" if m["fonte"] == "Cleveland" else "ART INSTITUTE OF CHICAGO"
        artista = (m.get("artista") or "").split("(")[0].split("\n")[0].strip(" ,")
        return (m["titulo"] or "")[:60], f"{artista}{', ' if artista and m.get('data') else ''}{m.get('data') or ''}", acervo + " · CC0"
    t, a, f = CRED.get(nome, (nome, "", COM))
    return t, a, f


def quadro(arq):
    nome = arq.stem
    rest = AQUI / "reais_restauradas" / arq.name          # 24/11: a versão restaurada, se houver (restaurar.py)
    im = ImageOps.exif_transpose(Image.open(rest if rest.exists() else arq)).convert("RGB")
    fundo = ImageOps.fit(im, (1920, 1080)).resize((240, 135)).filter(ImageFilter.GaussianBlur(6)).resize((1920, 1080))
    fundo = ImageEnhance.Brightness(ImageEnhance.Color(fundo).enhance(0.35)).enhance(0.22)
    mh, mw = 900, 1720
    r = min(mw / im.width, mh / im.height)
    obra = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
    b = 10
    papel = Image.new("RGB", (obra.width + 2 * b, obra.height + 2 * b), (36, 30, 26)); papel.paste(obra, (b, b))
    sombra = Image.new("RGBA", (papel.width + 80, papel.height + 80), (0, 0, 0, 0))
    ImageDraw.Draw(sombra).rectangle((40, 40, 40 + papel.width, 40 + papel.height), fill=(0, 0, 0, 190))
    sombra = sombra.filter(ImageFilter.GaussianBlur(22))
    x, y = (1920 - papel.width) // 2, 40 + (920 - papel.height) // 2
    fundo = fundo.convert("RGBA"); fundo.alpha_composite(sombra, (x - 40 + 8, y - 40 + 12)); fundo = fundo.convert("RGB")
    fundo.paste(papel, (x, y))
    d = ImageDraw.Draw(fundo)
    t, a, f = credito(nome)
    linha = __import__("re").sub(r"[^\x00-\u024f\u1e00-\u1eff]+", "", " · ".join(s for s in (t, a) if s)).replace("  ", " ")
    larg = d.textlength(linha + "   " + f, font=F_CRED)
    x0 = (1920 - larg) / 2
    d.text((x0, 1032), linha, font=F_CRED, fill=(214, 204, 188))
    d.text((x0 + d.textlength(linha + "   ", font=F_CRED), 1032), f, font=F_TAG, fill=(186, 52, 44))
    fundo.save(RP / (nome + ".jpg"), quality=92)


def rolo(arq, dur):
    """Travelling num rolo horizontal: altura 1080 (o rolo cheio na tela), da direita para a esquerda."""
    nome = arq.stem
    im = Image.open(arq).convert("RGB")
    h = 1080; w = round(im.width * h / im.height)
    if w < 2400:   # rolo curto: menos travelling
        h = round(1080 * 1.25); w = round(im.width * h / im.height)
    tmp = RO / f"_{nome}.png"; im.resize((w, h), Image.LANCZOS).save(tmp)
    desl = w - 1920
    vf = f"crop=1920:1080:x='{desl}-{desl}*(0.5-0.5*cos(PI*t/{dur}))':y={(h - 1080) // 2},fps=30,format=yuv420p"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", str(tmp), "-t", str(dur), "-vf", vf, "-c:v", "libx264",
                    "-crf", "17", "-preset", "medium", str(RO / f"{nome}.mp4")], check=True)
    tmp.unlink()


alvo = set(sys.argv[1:])
for arq in sorted(list(R.glob("*.jpg")) + list(R.glob("*.png"))):
    if alvo and arq.stem not in alvo:
        continue
    if arq.stem in ROLOS:
        if arq.stem in ("ROLO_hyakki_aic", "shuten_rolo_cbl", "tsuchigumo_14", "ushioni_suushi") or Image.open(arq).height >= 600:
            if not (RO / f"{arq.stem}.mp4").exists():
                rolo(arq, ROLOS[arq.stem]); print("rolo", arq.stem, flush=True)
    quadro(arq); print("ok", arq.stem, flush=True)
# rolo do casamento das assombrações (49 trechos de 3400×2545): junta em faixas e faz o travelling
