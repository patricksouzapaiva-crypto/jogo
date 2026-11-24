"""Ep12: baixa as imagens reais escolhidas (Wikimedia Commons, via Special:FilePath — a API está limitando).
Escolhas em ESCOLHAS (chave → título do arquivo, ou "tema#índice" dos candidatos da busca). Os créditos/licença são
lidos depois (creditos.py) pela página de cada arquivo.  Uso: python3 baixar_reais.py"""
import json, time, urllib.parse, urllib.request
from pathlib import Path
UA = {"User-Agent": "VideoResearchTool/1.0 (image search for a video project) python-urllib"}
AQUI = Path(__file__).parent; SAI = AQUI / "reais"; SAI.mkdir(exist_ok=True)
cand = json.loads((AQUI / "busca" / "candidatos.json").read_text())
ESCOLHAS = {
    # gancho / o ritual
    "ritual_mulher": "A woman makes a cursing ritual ceremony.jpg", "ritual_sekien": "SekienUshi-no-tokimairi.jpg",
    "ritual_met": "MET DP119501.jpg", "ritual_kuniyoshi": "ushi_toki#2",
    # Hashihime / Kifune / ponte / Nō
    "hashihime_sekien": "SekienHashihime.jpg", "mascara_hashihime": "No-Maske Hashihime makffm.jpg",
    "modoribashi": "Itijo-modoribashi.jpg", "kifune_1": "Kifune Jinja Shrine 20150914.JPG", "kifune_2": "kifune#7",
    "kifune_3": "Kifune-jinja shrine 20160618-01.jpg", "mascara_kanawa": "Nō mask - Kanawa Type.JPG",
    "hashihime_santuario": "Hashihime Shrine.JPG",
    "hannya_bm": "Hannya, British Museum.jpg", "hannya_noh": "Noh Mask Hannya type.jpg", "hannya_preto": "hannya#5",
    "hannya_tnm": "hannya#2", "hannya_oni": "Oni Mask and Hannya Masks.jpg",
    "dojoji_rolo": "Dojoji engi emaki - p2.png", "dojoji_sekien": "SekienDojoji-no-kane.jpg", "dojoji_met": "MET DP114873.jpg",
    # desfile / Sekien / Kyōsai
    "hyakki_1": "Hyakki Yako 1.jpg", "hyakki_2": "Hyakki Yako 2.jpg", "hyakki_shinjuan": "Hyakki Yagyo emaki.jpg",
    "hyakki_tsukumogami": "Hyakki-Yagyo-Emaki Tsukumogami 1.jpg",
    "kyosai_1": "kyosai_hyakki#0", "kyosai_2": "kyosai_hyakki#1", "kyosai_3": "kyosai_hyakki#2", "kyosai_4": "kyosai_hyakki#3",
    "kyosai_5": "kyosai_hyakki#4", "kyosai_6": "kyosai_hyakki#5", "kyosai_7": "kyosai_hyakki#6", "kyosai_8": "kyosai_hyakki#7",
    "sekien_kamaitachi": "SekienKamaitachi.jpg", "sekien_kappa": "Kappa jap myth.jpg", "sekien_rokurokubi": "SekienRokurokubi.jpg",
    # Shuten-dōji
    "shuten_sekien": "SekienShuten-doji.jpg", "shuten_oeyama_1927": "Iwaya(1927)-p000-frontispiece-oeyama.jpg",
    "shuten_rolo_honolulu": "shuten#2", "shuten_kunimasa": "shuten#4", "shuten_mulheres": "Shutendoji Surrounded by Women LACMA M.84.31.32.jpg",
    "shuten_rolo_cbl": "oeyama#0", "raiko_oeyama_1": "raiko_shuten#0", "raiko_oeyama_2": "raiko_shuten#1", "raiko_oeyama_3": "raiko_shuten#2",
    "kubizuka_1": "kubizuka#0", "kubizuka_2": "kubizuka#2", "kubizuka_3": "kubizuka#4", "kubizuka_4": "kubizuka#9",
    # Tamamo / pedra
    "tamamo_xilo": "Tamamo-no-mae-woodblock.jpg", "tamamo_miura": "tamamo#3", "tamamo_met": "MET DP143383.jpg",
    "tamamo_rijks": "Tamamo no Mae en Miura Kuranosuke, RP-P-1958-436.jpg", "tamamo_sekien": "SekienTamamo-no-mae.jpg",
    "kyubi_hokusai": "kyubi#0", "kyubi_lacma": "Story of the Nine-tailed Fox LACMA M.2006.136.129.jpg",
    "pedra_rachada": "Splited Sessho-Seki.jpg", "pedra_2018": "180727 Sessho-seki Nasu Japan14.JPG",
    "pedra_jizos": "sesshoseki#2", "pedra_2022": "Sessho-Seki Park, May 2022.jpg", "pedra_tochigi": "Sessho-seki, Tochigi 01.jpg",
    # kimon / Setsubun
    "sarugatsuji": "Kyoto-gosho Sarugatsuji.JPG", "enryakuji": "Otsu Enryaku-ji 3.jpg", "setsubun_hokusai": "Hokusai Setsubun no Oni.jpg",
    # os piores
    "ushioni_suushi": "Suushi Ushioni.jpg", "ushioni_rolo": "29.Ushioni.jpg", "ushioni_sekien": "SekienUshioni.jpg",
    "ushioni_warei": "Warei Jinja Ushioni.JPG", "nureonna_rolo": "Nure-onna (cropped).jpg", "nureonna_7": "7.Nure-onna.jpg",
    "nureonna_sekien": "SekienNureonna.jpg", "yamauba_paris": "yamauba#1", "yamauba_lacma": "Yamauba at Mount Ashigara LACMA M.2006.136.255.jpg",
    "tsuchigumo_14": "tsuchigumo#0", "tsuchigumo_4": "tsuchigumo#2", "tsuchigumo_7": "tsuchigumo#9",
    "tsuchigumo_kuniyoshi": "Raiko tormented by the earth spider.jpg", "tsuchigumo_rijks": "tsuchigumo_kuniyoshi#8",
    # palpites (a API está fora: tenta pelo nome)
    "takiyasha": "Takiyasha the Witch and the Skeleton Spectre.jpg", "sekien_jorogumo": "SekienJorogumo.jpg",
    "sekien_satori": "SekienSatori.jpg", "sekien_tengu": "SekienTengu.jpg", "sekien_nue": "SekienNue.jpg",
    "sekien_yamauba": "SekienYamauba.jpg", "sekien_kappa2": "SekienKappa.jpg", "sekien_tsuchigumo": "SekienTsuchigumo.jpg",
    "sekien_hyakki_capa": "Toriyama Sekien - Gazu Hyakki Yagyo.jpg",
}
lista = json.loads((SAI / "baixadas.json").read_text()) if (SAI / "baixadas.json").exists() else {}
for chave, tit in ESCOLHAS.items():
    if chave in lista: continue
    if "#" in tit:
        t, i = tit.split("#"); tit = cand[t][int(i)]["titulo"]
    url = "https://commons.wikimedia.org/wiki/Special:FilePath/" + urllib.parse.quote(tit.replace(" ", "_")) + "?width=3000"
    dados = None
    for tent in range(5):   # o Commons devolve 429 quando pedimos rápido: espera e tenta de novo
        try:
            dados = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90).read(); break
        except urllib.error.HTTPError as e:
            if e.code != 429: break
            time.sleep(60 * (tent + 1))
    if dados is None:
        print("FALHOU", chave, tit, flush=True); time.sleep(10); continue
    ext = ".png" if tit.lower().endswith(".png") else ".jpg"
    (SAI / f"{chave}{ext}").write_bytes(dados)
    lista[chave] = {"arquivo": f"{chave}{ext}", "titulo": tit,
                    "fonte": "https://commons.wikimedia.org/wiki/File:" + urllib.parse.quote(tit.replace(" ", "_"))}
    (SAI / "baixadas.json").write_text(json.dumps(lista, ensure_ascii=False, indent=1))
    print("ok", chave, len(dados) // 1024, "KB", flush=True); time.sleep(12)
print("FIM")
