"""Imagens reais do episódio (Wikimedia Commons): baixa o original, guarda licença/autor/fonte em reais/creditos.json.
Uso: python3 baixar_reais.py  (pausa entre pedidos: o Commons limita a taxa)"""
import json, re, sys, time, urllib.parse, urllib.request
from pathlib import Path
UA = {"User-Agent": "VideoResearchTool/1.0 (image search for a video project) python-urllib"}
AQUI = Path(__file__).parent; SAI = AQUI / "reais"; SAI.mkdir(exist_ok=True)
CRED = SAI / "creditos.json"
cred = json.loads(CRED.read_text()) if CRED.exists() else {}
ARQS = {
    "blandy_execucao": "The execution of Miss Mary Blandy Wellcome L0040863.jpg",
    "blandy_antes": "Mary (Molly) Blandy before her execution, 1752 Wellcome L0036006.jpg",
    "blandy_retrato": "Mary-blandy-1.jpg",
    "blandy_blackguardiana": "Blackguardiana - Mary Blandy.jpg",
    "dybbuk_1922": "Dybbuk1922.jpg",
    "dybbuk_22": "Dybbuk22.png",
    "ansky_1910": "An-ski 1910.jpg",
    "pata_macaco_02": "MonkeysPaw02.jpg",
}
BUSCAS = {"kitab_bulhan": "Kitab al-Bulhan", "clerambault": "Clérambault", "habima": "Habima Dybbuk Rovina",
          "defixio_louvre": "defixio Louvre", "boneca_louvre": "Louvre E 27145", "filtro_morgan": "De Morgan Love Potion",
          "bulhan_jinn": "Book of Wonders Bodleian jinn"}


def api(**p):
    p.update({"format": "json"})
    for t in range(7):
        try:
            return json.loads(urllib.request.urlopen(urllib.request.Request(
                "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(p), headers=UA), timeout=40).read())
        except urllib.error.HTTPError as e:
            if e.code != 429: raise
            time.sleep(90 * (t + 1))
    raise RuntimeError("429")


def limpar(h):
    return re.sub(r"<[^>]+>", "", h or "").strip()


def baixar(chave, titulo):
    if chave in cred and (SAI / cred[chave]["arquivo"]).exists():
        return
    r = api(action="query", titles="File:" + titulo, prop="imageinfo", iiprop="url|extmetadata|size", iiurlwidth=2400)
    pg = next(iter(r["query"]["pages"].values()))
    if "imageinfo" not in pg:
        print("não achei", titulo); return
    ii = pg["imageinfo"][0]; md = ii.get("extmetadata", {})
    url = ii.get("thumburl") or ii["url"]
    ext = ".png" if url.lower().endswith(".png") else ".jpg"
    arq = f"{chave}{ext}"
    for t in range(7):
        try:
            (SAI / arq).write_bytes(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()); break
        except urllib.error.HTTPError as e:
            if e.code != 429: raise
            time.sleep(90 * (t + 1))
    cred[chave] = {"arquivo": arq, "titulo": titulo, "licenca": limpar(md.get("LicenseShortName", {}).get("value")),
                   "autor": limpar(md.get("Artist", {}).get("value"))[:200], "credito": limpar(md.get("Credit", {}).get("value"))[:200],
                   "fonte": "https://commons.wikimedia.org/wiki/File:" + urllib.parse.quote(titulo.replace(" ", "_")),
                   "tamanho": [ii.get("width"), ii.get("height")]}
    CRED.write_text(json.dumps(cred, ensure_ascii=False, indent=1))
    print("ok", chave, cred[chave]["licenca"], cred[chave]["tamanho"])
    time.sleep(12)


for k, t in ARQS.items():
    baixar(k, t)
for k, q in BUSCAS.items():
    r = api(action="query", list="search", srnamespace=6, srsearch=q, srlimit=6)
    print("##", k, [x["title"][5:90] for x in r["query"]["search"]]); time.sleep(12)
