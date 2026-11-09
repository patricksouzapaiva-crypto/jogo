"""Busca fotos de uso livre para os vídeos (Pixabay, Openverse, Wikimedia Commons) e aplica o tratamento da série.

Uso:
  python3 buscar_imagens.py buscar <pasta> consultas.json        # baixa prévias + folha de contato + resultados.json
  python3 buscar_imagens.py baixar <pasta> <id1,id2,...> [saida]  # baixa em alta, trata (1920x1080) e grava CREDITOS.txt
  python3 buscar_imagens.py videos <pasta> consultas.json         # vídeos curtos do Pixabay: prévias + folha + resultados
  python3 buscar_imagens.py baixar_videos <pasta> <id[:ini[:dur]],...> [saida]
      # baixa em 1920x1080, sem áudio, corta (padrão: 0 s, 8 s) e aplica o mesmo tratamento "documento" das fotos
  python3 buscar_imagens.py arquivo <entrada> <saida.jpg>          # tratamento "arquivo" p/ imagem com pessoa (tira a cara de IA)

consultas.json: {"corredor": "dark hallway night", "avo": "elderly woman hands", ...}
Cada candidato recebe um id "<chave>_<n>" (ex.: corredor_3), que aparece na folha de contato.

Fontes, na ordem: Pixabay (precisa da variável PIXABAY_API_KEY; sem crédito obrigatório), Openverse (sem chave;
Flickr e outros acervos em Creative Commons, só licenças que permitem uso comercial) e Wikimedia Commons
(sem chave; ótimo para fotos de arquivo/históricas). Licenças CC BY / BY-SA exigem crédito: vai no CREDITOS.txt,
que deve ser copiado para a descrição do vídeo.
"""
import io, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

UA = {"User-Agent": "UltimoAbrigoEditor/1.0 (https://github.com/patricksouzapaiva-crypto/jogo) python-urllib"}


def abrir(url, tentativas=5):
    for _ in range(tentativas):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40).read()
        except urllib.error.HTTPError as e:
            if e.code != 429:
                raise
            espera = int(e.headers.get("retry-after", "30")) + 2
            print(f"  limite de pedidos, aguardando {espera}s")
            time.sleep(espera)
    raise RuntimeError("limite de pedidos")


def pixabay(q, n=8):
    chave = os.environ.get("PIXABAY_API_KEY")
    if not chave:
        return []
    d = json.loads(abrir("https://pixabay.com/api/?" + urllib.parse.urlencode(
        {"key": chave, "q": q, "image_type": "photo", "per_page": max(3, n), "safesearch": "false"})))
    return [{"fonte": "pixabay", "titulo": h.get("tags", ""), "prev": h["webformatURL"],
             "alta": h.get("largeImageURL") or h["webformatURL"], "w": h["imageWidth"], "h": h["imageHeight"],
             "licenca": "Pixabay Content License", "autor": h.get("user", "?"), "pagina": h["pageURL"]}
            for h in d.get("hits", [])[:n]]


def openverse(q, n=8):
    d = json.loads(abrir("https://api.openverse.org/v1/images/?" + urllib.parse.urlencode(
        {"q": q, "page_size": n * 2, "license_type": "commercial"})))
    out = []
    for r in d.get("results", []):
        if (r.get("width") or 0) < 1000:
            continue
        out.append({"fonte": "openverse/" + r.get("source", "?"), "titulo": r.get("title", ""),
                    "prev": r.get("thumbnail") or r["url"], "alta": r["url"], "w": r.get("width"), "h": r.get("height"),
                    "licenca": f"CC {r.get('license', '?').upper()} {r.get('license_version', '')}".strip(),
                    "autor": r.get("creator") or "?", "pagina": r.get("foreign_landing_url") or r["url"]})
    return out[:n]


def wikimedia(q, n=8):
    time.sleep(1.5)
    d = json.loads(abrir("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(
        {"action": "query", "generator": "search", "gsrsearch": q + " filetype:bitmap", "gsrnamespace": 6,
         "gsrlimit": n, "prop": "imageinfo", "iiprop": "url|size|extmetadata", "iiurlwidth": 500, "format": "json"})))
    out = []
    for p in sorted(d.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 0)):
        ii = p["imageinfo"][0]
        m = ii.get("extmetadata", {})
        if ii.get("width", 0) < 1200:
            continue
        out.append({"fonte": "wikimedia", "titulo": p["title"], "prev": ii["thumburl"],
                    "alta": ii["thumburl"].replace("/500px-", "/1920px-"), "original": ii["url"],
                    "w": ii["width"], "h": ii["height"], "licenca": m.get("LicenseShortName", {}).get("value", "?"),
                    "autor": re.sub("<[^>]+>", "", m.get("Artist", {}).get("value", "?")).strip(),
                    "pagina": ii.get("descriptionurl")})
    return out


def folha(arquivos, saida, cols=6, tw=320, th=200):
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (cols * tw, ((len(arquivos) + cols - 1) // cols) * (th + 18)), "black")
    d = ImageDraw.Draw(img)
    for i, f in enumerate(arquivos):
        im = Image.open(f).convert("RGB")
        im.thumbnail((tw - 4, th - 4))
        x, y = (i % cols) * tw, (i // cols) * (th + 18)
        img.paste(im, (x + 2, y + 2))
        d.text((x + 4, y + th), Path(f).stem, fill="yellow")
    img.save(saida)


def buscar(pasta, consultas, por_fonte=4):
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    res, arquivos = {}, []
    for chave, q in consultas.items():
        cands = []
        for fonte in (pixabay, openverse, wikimedia):
            try:
                cands += fonte(q, por_fonte)
            except Exception as e:
                print(f"  {fonte.__name__}: {e}")
        for i, c in enumerate(cands):
            f = pasta / f"{chave}_{i}.jpg"
            try:
                f.write_bytes(abrir(c["prev"]))
                arquivos.append(f)
            except Exception as e:
                print("  falha na prévia", f.name, e)
            time.sleep(0.4)
        res[chave] = cands
        print(chave, len(cands), "candidatas")
    json.dump(res, open(pasta / "resultados.json", "w"), ensure_ascii=False, indent=1)
    if arquivos:
        folha(arquivos, pasta / "folha.jpg")
        print("folha de contato:", pasta / "folha.jpg")


def tratar(im, W=1920, H=1080, borda=0.0):
    """Tratamento 'documento' da série: cobre 16:9, menos cor, mais escura, tom frio, contraste e vinheta."""
    import numpy as np
    from PIL import Image, ImageEnhance
    if borda:
        m, mh = int(im.width * borda), int(im.height * borda)
        im = im.crop((m, mh, im.width - m, im.height - mh))
    r = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
    l, t = (im.width - W) // 2, (im.height - H) // 2
    im = im.crop((l, t, l + W, t + H))
    im = ImageEnhance.Contrast(ImageEnhance.Color(im).enhance(0.35)).enhance(1.18)
    a = np.asarray(im).astype(np.float32) / 255
    a = a ** 1.35 * 0.85
    a[..., 0] *= 0.92
    a[..., 2] = np.minimum(1, a[..., 2] * 1.08 + 0.015)
    yy, xx = np.mgrid[0:H, 0:W]
    v = ((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2
    a *= (1 - 0.55 * np.clip(v / 2, 0, 1) ** 1.2)[..., None]
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))


def baixar(pasta, ids, saida=None):
    from PIL import Image
    pasta = Path(pasta)
    saida = Path(saida or pasta / "escolhidas")
    saida.mkdir(parents=True, exist_ok=True)
    res = json.load(open(pasta / "resultados.json"))
    creditos = []
    for k in ids:
        chave, i = k.rsplit("_", 1)
        c = res[chave][int(i)]
        try:
            b = abrir(c["alta"])
        except Exception:
            b = abrir(c.get("original", c["prev"]))
        tratar(Image.open(io.BytesIO(b)).convert("RGB")).save(saida / f"{k}.jpg", quality=93)
        creditos.append(f"{k}: \"{c['titulo']}\" — {c['autor']} — {c['licenca']} — {c['pagina']}")
        print(creditos[-1][:150])
        time.sleep(0.8)
    (saida / "CREDITOS.txt").write_text("\n".join(creditos) + "\n", encoding="utf-8")


# ---------- vídeos curtos (Pixabay; licença livre, sem crédito obrigatório) ----------
def pixabay_videos(q, n=8, max_dur=40):
    chave = os.environ.get("PIXABAY_API_KEY")
    if not chave:
        raise SystemExit("PIXABAY_API_KEY não definida")
    d = json.loads(abrir("https://pixabay.com/api/videos/?" + urllib.parse.urlencode(
        {"key": chave, "q": q, "per_page": 20, "safesearch": "false"})))
    out = []
    for h in d.get("hits", []):
        v = h["videos"]
        alta = next((v[k] for k in ("large", "medium") if v.get(k, {}).get("url") and v[k]["width"] >= 1280), None)
        if not alta or h.get("duration", 99) > max_dur or h.get("isAiGenerated"):
            continue
        out.append({"fonte": "pixabay-video", "titulo": h.get("tags", ""), "prev": v["medium"].get("thumbnail") or v["tiny"].get("thumbnail"),
                    "alta": alta["url"], "w": alta["width"], "h": alta["height"], "duracao": h.get("duration"),
                    "licenca": "Pixabay Content License", "autor": h.get("user", "?"), "pagina": h["pageURL"]})
        if len(out) >= n:
            break
    return out


def buscar_videos(pasta, consultas, n=6):
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    res, arquivos = {}, []
    for chave, q in consultas.items():
        try:
            cands = pixabay_videos(q, n)
        except Exception as e:
            print(f"  {chave}: {e}"); cands = []
        for i, c in enumerate(cands):
            f = pasta / f"{chave}_{i}.jpg"
            try:
                f.write_bytes(abrir(c["prev"])); arquivos.append(f)
            except Exception as e:
                print("  falha na prévia", f.name, e)
        res[chave] = cands
        print(chave, len(cands), "vídeos")
    json.dump(res, open(pasta / "resultados.json", "w"), ensure_ascii=False, indent=1)
    if arquivos:
        folha(arquivos, pasta / "folha.jpg")
        print("folha de contato:", pasta / "folha.jpg")


# mesmo espírito do tratar(): menos cor, mais escuro, frio, contraste, vinheta
FILTRO_DOC = ("scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=30,"
              "eq=saturation=0.35:contrast=1.18:gamma=0.78:brightness=-0.03,"
              "colorbalance=rs=-0.04:bs=0.05:rm=-0.03:bm=0.04,vignette=PI/4.2,format=yuv420p")


def baixar_videos(pasta, ids, saida=None):
    import subprocess, tempfile
    pasta = Path(pasta)
    saida = Path(saida or pasta / "escolhidos")
    saida.mkdir(parents=True, exist_ok=True)
    res = json.load(open(pasta / "resultados.json"))
    cred = saida / "CREDITOS.txt"
    creditos = cred.read_text(encoding="utf-8").splitlines() if cred.exists() else []
    for item in ids:
        k, *tempo = item.split(":")
        ini = float(tempo[0]) if tempo else 0.0
        dur = float(tempo[1]) if len(tempo) > 1 else 8.0
        chave, i = k.rsplit("_", 1)
        c = res[chave][int(i)]
        with tempfile.NamedTemporaryFile(suffix=".mp4") as tmp:
            tmp.write(abrir(c["alta"])); tmp.flush()
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{ini}", "-t", f"{dur}", "-i", tmp.name, "-an",
                            "-vf", FILTRO_DOC, "-c:v", "libx264", "-crf", "17", "-preset", "slow",
                            str(saida / f"{k}.mp4")], check=True)
        linha = f"{k}.mp4: \"{c['titulo']}\" — {c['autor']} — {c['licenca']} — {c['pagina']}"
        creditos = [x for x in creditos if not x.startswith(f"{k}.mp4:")] + [linha]
        print(linha[:150])
    cred.write_text("\n".join(creditos) + "\n", encoding="utf-8")


def tratar_arquivo(im, W=1920, H=1080, semente=3):
    """Tratamento "arquivo" (regra 09/11): toda imagem de IA com PESSOA vira cópia de cópia de um registro —
    alto contraste, pretos estourados, ruído e riscos verticais. Some a pele lisa/luz de cinema da IA e a
    imagem passa a ser "prova anexada ao caso"."""
    import numpy as np
    from PIL import Image, ImageFilter
    rng = np.random.default_rng(semente)
    r = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
    l, t = (im.width - W) // 2, (im.height - H) // 2
    im = im.crop((l, t, l + W, t + H))
    a = np.asarray(im).astype(np.float32) / 255
    lo, hi = np.percentile(a.mean(-1), [1, 99.5])
    a = np.clip((a - lo) / (hi - lo + 1e-6), 0, 1) ** 0.75
    g = np.asarray(Image.fromarray((a.mean(-1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.0))).astype(np.float32) / 255
    g = np.clip((g - 0.30) * 2.2, 0, 1)
    g = g + rng.normal(0, 0.10, g.shape)
    g = np.where(g > 0.5, 1 - (1 - g) * 0.25, g * 0.35)
    for _ in range(4):
        x = rng.integers(0, W); g[:, x:x + rng.integers(2, 5)] *= 0.55
    g = np.clip(g, 0, 1) * 0.92 + 0.04
    rgb = np.stack([g * 0.98, g * 0.96, g * 0.92], -1)
    return Image.fromarray((rgb * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) >= 3 and a[0] == "buscar":
        buscar(a[1], json.load(open(a[2], encoding="utf-8")))
    elif len(a) >= 3 and a[0] == "baixar":
        baixar(a[1], a[2].split(","), a[3] if len(a) > 3 else None)
    elif len(a) >= 3 and a[0] == "videos":
        buscar_videos(a[1], json.load(open(a[2], encoding="utf-8")))
    elif len(a) >= 3 and a[0] == "baixar_videos":
        baixar_videos(a[1], a[2].split(","), a[3] if len(a) > 3 else None)
    elif len(a) >= 3 and a[0] == "arquivo":
        from PIL import Image
        tratar_arquivo(Image.open(a[1]).convert("RGB")).save(a[2], quality=93)
    else:
        print(__doc__)
