"""Baixa em tamanho grande as obras escolhidas de museus/catalogo.json (CC0).
Saída: reais/<chave>.jpg + reais/museus.json com crédito e link."""
import json, os, time, urllib.request
AQUI = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "EpisodeResearch/1.0 (educational documentary)"}
ESC = {  # chave: tema#indice   (ROLO = rolo horizontal: baixar pela altura)
 "m_hannya_hokusai": "hannya#1", "m_ibaraki_esboco": "hannya#0", "m_mascara_kobeshimi": "mascara_noh_demonio#3",
 "m_kanawa": "kanawa#0", "m_ushinokoku": "ushi_no_koku#0", "m_dojoji_2": "dojoji#2", "m_dojoji_3": "dojoji#3",
 "m_raiko_cabeca": "raiko#0", "ROLO_oeyama_engi_1": "oeyama#0", "ROLO_oeyama_engi_2": "oeyama#1", "ROLO_oeyama_engi_3": "oeyama#2",
 "m_shuten_palacio": "oeyama#3", "m_yasumasa": "kitsune#1", "m_toki": "kitsune#2", "m_asajigahara": "kitsune#9",
 "m_shirazunoyabu": "kitsune#11", "m_caldeirao": "kitsune#6", "m_kezori": "kitsune#10",
 "m_tsuchigumo_noh": "tsuchigumo#0", "m_tsuchigumo_raiko": "aranha#2", "m_tsuchigumo_kuniyoshi": "watanabe#10",
 "m_yamauba": "yamauba#1", "m_yamauba_kintaro": "yamauba#6", "m_tengu_rei": "tengu#3", "m_kurama_tengu": "tengu#4",
 "m_otsue_oni": "oni#2", "m_ukiyo_matabei": "oni#1", "m_shoki_espada": "shoki#9", "m_shoki_tigre": "kyosai#14",
 "m_shoki_esboco": "shoki#11", "ROLO_hyakki_aic": "hyakki#0", "m_rei_inferno": "inferno#1", "m_jigokudayu": "inferno#2",
 "m_jigoku_livro": "jigoku#0", "m_tenjin_engi": "tenjin#0", "m_michizane_retrato": "michizane#0",
 "m_michizane_trovao": "michizane#12", "m_michizane_ator": "michizane#7", "m_raijin_estatua": "raijin#0",
 "m_raijin_biombo": "raijin#1", "m_raijin_momoyogusa": "raijin#2", "m_raijin_caido": "raijin#4",
 "m_kyosai_lesma": "kyosai#9", "m_kyosai_luta": "kyosai#4", "m_susanoo_monstros": "yokai#0",
 "m_rashomon_tsuna": "rashomon#1", "m_rashomon_noh": "rashomon#2", "m_setsubun": "setsubun#0",
 "ROLO_casamento_bakemono": "bakemono#0",
}
def get(u):
    for t in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=120) as r: return r.read()
        except Exception as e: print("  erro", e); time.sleep(8 * (t + 1))
cat = json.load(open(os.path.join(AQUI, "museus/catalogo.json")))
reg_p = os.path.join(AQUI, "reais/museus.json")
reg = json.load(open(reg_p)) if os.path.exists(reg_p) else {}
for chave, ref in ESC.items():
    p = os.path.join(AQUI, "reais", chave + ".jpg")
    if os.path.exists(p): continue
    tema, i = ref.split("#"); it = cat[tema][int(i)]
    url = it["grande"]
    if chave.startswith("ROLO") and it["fonte"] == "AIC": url = url.replace("/full/3000,/", "/full/,2000/")
    b = get(url)
    if not b and it["fonte"] == "AIC": b = get(url.replace("3000,", "1686,").replace(",2000", ",1200"))
    if not b: print("FALHOU", chave); continue
    open(p, "wb").write(b); print("ok", chave, len(b) // 1024, "KB")
    reg[chave] = {k: it[k] for k in ("fonte", "titulo", "artista", "data", "credito", "link")}
    json.dump(reg, open(reg_p, "w"), ensure_ascii=False, indent=1)
