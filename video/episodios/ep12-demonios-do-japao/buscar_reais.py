"""Ep12: busca imagens reais no Wikimedia Commons (gravuras, rolos, fotos) para cada tema; guarda os candidatos com
miniatura em busca/candidatos.json e monta folhas de contato (busca/folha_<tema>.jpg) para escolher.
Uso: python3 buscar_reais.py  (pausa entre pedidos: o Commons limita a taxa)"""
import io, json, time, urllib.parse, urllib.request
from pathlib import Path
from PIL import Image, ImageDraw
UA = {"User-Agent": "VideoResearchTool/1.0 (image search for a video project) python-urllib"}
AQUI = Path(__file__).parent; B = AQUI / "busca"; B.mkdir(exist_ok=True)
SAIDA = B / "candidatos.json"
cand = json.loads(SAIDA.read_text()) if SAIDA.exists() else {}
TEMAS = {
    "ushi_toki_sekien": "Ushi no toki mairi Sekien", "ushi_toki": "ushi no koku mairi", "hashihime": "Hashihime",
    "kanawa": "Kanawa Noh", "kifune": "Kifune Shrine", "wara_ningyo": "straw doll curse Japan",
    "hyakki_emaki": "Hyakki Yagyo Emaki", "shinjuan": "Shinju-an Hyakki", "gazu_hyakki": "Gazu Hyakki Yagyo",
    "sekien": "Toriyama Sekien", "kyosai_hyakki": "Kyosai Hyakki", "shuten": "Shuten-doji", "oeyama": "Oeyama emaki",
    "raiko_shuten": "Raiko Shuten Kuniyoshi", "kubizuka": "Kubizuka Daimyojin", "tamamo": "Tamamo no Mae",
    "kyubi": "nine-tailed fox Hokusai", "sesshoseki": "Sesshoseki", "sarugatsuji": "Sarugatsuji Kyoto Gosho",
    "enryakuji": "Enryaku-ji", "setsubun": "Setsubun oni mamemaki", "hannya": "Hannya mask", "dojoji": "Kiyohime Dojoji",
    "ushioni": "Ushi-oni", "nureonna": "Nure-onna", "jorogumo": "Jorogumo", "yamauba": "Yamauba Kuniyoshi",
    "tsuchigumo": "Tsuchigumo soshi", "tsuchigumo_kuniyoshi": "Raiko tsuchigumo Kuniyoshi", "rokurokubi": "Rokurokubi",
    "kamaitachi": "Kamaitachi Sekien", "nue": "Nue Yoshitoshi", "orochi": "Yamata no Orochi Kuniyoshi",
    "omukade": "Tawara Toda centipede", "kappa": "Kappa Sekien", "tengu": "Tengu Kuniyoshi", "satori": "Satori Sekien",
    "takiyasha": "Takiyasha Kuniyoshi skeleton", "tsuna_ibaraki": "Watanabe no Tsuna Ibaraki", "rashomon": "Rashomon oni Yoshitoshi",
    "tenjin": "Kitano Tenjin Engi", "jigoku": "Jigoku zoshi", "enma": "Enma Daio scroll", "gozu_mezu": "Gozu Mezu",
    "yoshitoshi_36": "New Forms of Thirty-six Ghosts Yoshitoshi", "bakemono": "Bakemono zukushi", "oni_otsue": "Otsu-e oni",
    "momijigari": "Momijigari Noh", "tsukumogami": "Tsukumogami", "kappa_mao": "kappa mummy",
}


def api(**p):
    p.update({"format": "json"})
    for t in range(7):
        try:
            return json.loads(urllib.request.urlopen(urllib.request.Request(
                "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(p), headers=UA), timeout=40).read())
        except urllib.error.HTTPError as e:
            if e.code != 429: raise
            time.sleep(60 * (t + 1))
    raise RuntimeError("429")


def baixar(url):
    for t in range(5):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40).read()
        except urllib.error.HTTPError as e:
            if e.code != 429: raise
            time.sleep(30 * (t + 1))


SEM_FOLHA = __import__('os').environ.get('SEM_FOLHA')
for tema, q in TEMAS.items():
    if tema in cand: continue
    r = api(action="query", generator="search", gsrnamespace=6, gsrsearch=q + " filetype:bitmap", gsrlimit=12,
            prop="imageinfo", iiprop="url|size", iiurlwidth=360)
    pags = sorted((r.get("query") or {}).get("pages", {}).values(), key=lambda p: p.get("index", 99))
    lista = [{"titulo": p["title"][5:], "url": p["imageinfo"][0].get("thumburl"), "tam": [p["imageinfo"][0]["width"], p["imageinfo"][0]["height"]]}
             for p in pags if p.get("imageinfo")]
    cand[tema] = lista; SAIDA.write_text(json.dumps(cand, ensure_ascii=False, indent=1))
    if SEM_FOLHA:
        print('ok', tema, len(lista), flush=True); time.sleep(25); continue
    # folha de contato: 12 miniaturas numeradas
    folha = Image.new("RGB", (4 * 360, 3 * 400), (20, 20, 20)); d = ImageDraw.Draw(folha)
    for i, c in enumerate(lista[:12]):
        try:
            im = Image.open(io.BytesIO(baixar(c["url"]))).convert("RGB"); im.thumbnail((350, 350))
            folha.paste(im, ((i % 4) * 360 + 5, (i // 4) * 400 + 5))
        except Exception as e:
            pass
        d.text(((i % 4) * 360 + 6, (i // 4) * 400 + 362), f"{i} {c['tam'][0]}x{c['tam'][1]} {c['titulo'][:40]}", fill=(255, 255, 0))
        time.sleep(1.5)
    folha.save(B / f"folha_{tema}.jpg", quality=80)
    print("ok", tema, len(lista), flush=True); time.sleep(6)
print("FIM")
