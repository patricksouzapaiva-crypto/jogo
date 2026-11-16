"""Imagens e vídeos REAIS do Wikimedia Commons para o Ep. 11 (16/11): o peso documental do episódio (dossiê).
Pedido do usuário: "procure as imagens reais, cenas de documentários e tudo que faça ter um peso maior no episódio".
Para cada busca: arquivos de imagem (≥ 1000 px) e vídeo, baixados em até 1920 px em reais/<código>_<n>.<ext>, com
título, autor, licença e link anotados em reais/CREDITOS.md (as licenças CC BY / BY-SA exigem crédito na descrição).
Uso: python3 buscar_reais.py [código ...]"""
import json, re, sys, time, html
from pathlib import Path
import requests

AQUI = Path(__file__).parent; SAI = AQUI / "reais"; SAI.mkdir(exist_ok=True)
API = "https://commons.wikimedia.org/w/api.php"
S = requests.Session(); S.headers["User-Agent"] = "UltimoAbrigoResearch/1.0 (documentary research script)"
# código: (busca no Commons, quantos)  — o código diz onde entra no roteiro
BUSCAS = {"PACOTE": (None, 0), "C3_rok": ("Rök runestone", 4), "C1_tollund": ("Tollund Man", 4), "T_halsingland": ("Hälsingland forest winter", 4), "C2_blot": ("blót sacrifice painting", 3)}
PACOTE = {"C1_01_real": "Tollundmanden_DO-10895_original.jpg", "C1_02_real": "Grauballe Man, Moesgaard Museum 1.jpg", "C1_02b_real": "Grauballe_Man_discovery.jpg",
          "C1_04_real": "Olaus Magnus - On the Glorious Temple Devoted to the Nordic Gods.jpg",
          "C3_01_real": "The_Rök_Runestone.jpg"}

limpa = lambda s: html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()
creditos = json.loads((SAI / "creditos.json").read_text()) if (SAI / "creditos.json").exists() else {}


def pedir(params):   # o Commons devolve 429 / página de erro quando apertamos: espera e tenta de novo
    for k in range(6):
        r = S.get(API, params=params, timeout=60)
        try: return r.json()
        except ValueError: time.sleep(5 + 10 * k)
    return {}


def info(titulos):
    r = pedir(dict( action="query", format="json", prop="imageinfo", titles="|".join(titulos),
                     iiprop="url|size|mime|extmetadata", iiurlwidth=1920))
    return [p for p in r.get("query", {}).get("pages", {}).values() if "imageinfo" in p]


def baixar(cod, p, minimo=1000):
    ii = p["imageinfo"][0]; mime = ii.get("mime", ""); md = ii.get("extmetadata", {})
    video = mime.startswith("video")
    if not video and (ii.get("width", 0) < minimo or not mime.startswith("image")): return False
    url = ii["url"] if video else (ii.get("thumburl") or ii["url"])
    ext = Path(url.split("?")[0]).suffix.lower() or ".jpg"
    if video and ii.get("size", 0) > 120e6: return False
    arq = SAI / f"{cod}{ext}"
    if not arq.exists():
        for k in range(4):
            r = S.get(url, timeout=180)
            if r.status_code == 200: arq.write_bytes(r.content); break
            time.sleep(3 + 5 * k)
        else:
            return False
    creditos[arq.name] = {"titulo": p["title"].replace("File:", ""), "autor": limpa(md.get("Artist", {}).get("value")),
                          "licenca": limpa(md.get("LicenseShortName", {}).get("value")), "link": ii.get("descriptionurl"),
                          "descricao": limpa(md.get("ImageDescription", {}).get("value"))[:200]}
    print(" ", arq.name, "·", creditos[arq.name]["licenca"], flush=True)
    return True


so = set(sys.argv[1:])
for cod, (q, n) in BUSCAS.items():
    if so and cod not in so: continue
    print(cod, flush=True)
    if cod == "PACOTE":
        for nome, f in PACOTE.items():
            for p in info(["File:" + f]): baixar(nome, p, 0)
            time.sleep(1)
        continue
    r = pedir({"action": "query", "format": "json", "list": "search", "srsearch": q, "srnamespace": 6, "srlimit": n * 3})
    tit = [x["title"] for x in r.get("query", {}).get("search", [])]
    k = 0
    for p in info(tit[:40]) if tit else []:
        if k >= n: break
        if baixar(f"{cod}_{k + 1:02d}", p): k += 1
        time.sleep(0.6)
    (SAI / "creditos.json").write_text(json.dumps(creditos, ensure_ascii=False, indent=1))
    time.sleep(1)
(SAI / "creditos.json").write_text(json.dumps(creditos, ensure_ascii=False, indent=1))
linhas = ["# Imagens e vídeos reais (Wikimedia Commons) — créditos", "", "| Arquivo | Título | Autor | Licença | Link |", "|---|---|---|---|---|"]
for a, c in sorted(creditos.items()):
    linhas.append(f"| {a} | {c['titulo'][:70]} | {c['autor'][:50]} | {c['licenca']} | {c['link']} |")
(SAI / "CREDITOS.md").write_text("\n".join(linhas) + "\n")
print("total:", len(creditos))
