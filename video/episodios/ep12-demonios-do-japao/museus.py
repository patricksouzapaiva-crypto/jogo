"""Busca obras em domínio público (CC0) no Met, Cleveland e Art Institute of Chicago.
O Commons bloqueou este ambiente (429); estes acervos são CC0 e liberam imagem grande.
Uso: python3 museus.py            -> busca e baixa miniaturas em museus/<tema>/
     python3 museus.py grande ID  -> (ver baixar_museus.py)"""
import json, os, sys, time, urllib.parse, urllib.request
AQUI = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "EpisodeResearch/1.0 (educational documentary)"}
TEMAS = {
 "hannya": "hannya", "mascara_noh_demonio": "noh mask", "hashihime": "hashihime",
 "kanawa": "kanawa", "ushi_no_koku": "ushi no koku mairi", "dojoji": "dojoji",
 "kiyohime": "kiyohime", "shuten": "shuten doji", "raiko": "raiko", "oeyama": "oeyama",
 "ibaraki": "ibaraki", "tamamo": "tamamo", "raposa_nove": "nine-tailed", "kitsune": "fox yoshitoshi",
 "tsuchigumo": "tsuchigumo", "aranha": "spider", "jorogumo": "jorogumo",
 "takiyasha": "takiyasha", "yamauba": "yamauba", "ushioni": "ushi-oni", "nureonna": "nure-onna",
 "kappa": "kappa", "tengu": "tengu", "oni": "oni", "oni_hokusai": "hokusai ghost",
 "oni_kuniyoshi": "kuniyoshi monster", "yoshitoshi_demonio": "yoshitoshi demon", "yoshitoshi_fantasma": "yoshitoshi hundred ghost",
 "hyakki": "hyakki yagyo", "desfile": "night parade demons", "inferno": "hell", "jigoku": "jigoku",
 "enma": "enma", "tenjin": "tenjin engi", "michizane": "sugawara michizane", "raijin": "raijin thunder god",
 "tsukumogami": "tsukumogami", "shoki": "shoki demon", "setsubun": "setsubun", "kyosai": "kyosai",
 "rokurokubi": "rokurokubi", "yokai": "yokai", "bakemono": "bakemono", "watanabe": "watanabe no tsuna",
 "rashomon": "rashomon", "kintoki": "kintoki", "ryu": "japanese dragon print",
}
def get(url, tent=4):
    for t in range(tent):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                return r.read()
        except Exception as e:
            print("  erro", e, url[:90]); time.sleep(5 * (t + 1))
    return None
def jget(url):
    b = get(url); return json.loads(b) if b else None
def met(q, n=14):
    s = jget("https://collectionapi.metmuseum.org/public/collection/v1/search?hasImages=true&q=" + urllib.parse.quote(q))
    out = []
    for oid in (s or {}).get("objectIDs") or []:
        if len(out) >= n: break
        o = jget(f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{oid}")
        if not o or not o.get("isPublicDomain") or not o.get("primaryImage"): continue
        if o.get("department") not in ("Asian Art",) and "Japan" not in (o.get("culture") or ""): continue
        out.append(dict(fonte="Met", id=str(oid), titulo=o.get("title"), artista=o.get("artistDisplayName"),
            data=o.get("objectDate"), mini=o.get("primaryImageSmall"), grande=o.get("primaryImage"),
            credito=f"The Metropolitan Museum of Art, {o.get('creditLine')} (CC0)", link=o.get("objectURL")))
    return out
def cleveland(q, n=14):
    s = jget("https://openaccess-api.clevelandart.org/api/artworks/?cc0=1&has_image=1&limit=%d&q=%s" % (n, urllib.parse.quote(q)))
    out = []
    for o in (s or {}).get("data", []):
        im = o.get("images") or {}
        if not im.get("web"): continue
        if not any("Japan" in c for c in (o.get("culture") or [])): continue
        g = (im.get("print") or im.get("full") or im.get("web"))["url"]
        out.append(dict(fonte="Cleveland", id=str(o["id"]), titulo=o.get("title"),
            artista=", ".join(c.get("description", "") for c in o.get("creators") or []), data=o.get("creation_date"),
            mini=im["web"]["url"], grande=g, credito="The Cleveland Museum of Art (CC0)", link=o.get("url")))
    return out
def aic(q, n=14):
    s = jget("https://api.artic.edu/api/v1/artworks/search?limit=%d&fields=id,title,artist_display,date_display,image_id,is_public_domain,place_of_origin&q=%s" % (n * 2, urllib.parse.quote(q)))
    out = []
    for o in (s or {}).get("data", []):
        if not o.get("is_public_domain") or not o.get("image_id"): continue
        if "Japan" not in (o.get("place_of_origin") or ""): continue
        base = f"https://www.artic.edu/iiif/2/{o['image_id']}"
        out.append(dict(fonte="AIC", id=str(o["id"]), titulo=o.get("title"), artista=o.get("artist_display"),
            data=o.get("date_display"), mini=base + "/full/400,/0/default.jpg", grande=base + "/full/3000,/0/default.jpg",
            credito="Art Institute of Chicago (CC0)", link=f"https://www.artic.edu/artworks/{o['id']}"))
        if len(out) >= n: break
    return out
if __name__ == "__main__":
    cat_p = os.path.join(AQUI, "museus", "catalogo.json")
    cat = json.load(open(cat_p)) if os.path.exists(cat_p) else {}
    temas = sys.argv[1:] or list(TEMAS)
    for tema in temas:
        if tema in cat: continue
        q = TEMAS[tema]; print("==", tema, q)
        itens = []
        for f in (cleveland, aic):  # busca do Met responde 410; Met só por ID conhecido
            try: itens += f(q)
            except Exception as e: print("  falhou", f.__name__, e)
        d = os.path.join(AQUI, "museus", tema); os.makedirs(d, exist_ok=True)
        for i, it in enumerate(itens):
            p = os.path.join(d, f"{i:02d}.jpg")
            if not os.path.exists(p):
                b = get(it["mini"])
                if b: open(p, "wb").write(b)
            it["mini_arq"] = os.path.relpath(p, AQUI)
        cat[tema] = itens; print("  ", len(itens), "itens")
        json.dump(cat, open(cat_p, "w"), ensure_ascii=False, indent=1)
