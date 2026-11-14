"""Gera ../roteiro_en.json (vídeo inteiro em inglês) a partir do roteiro.json em português + traducao_en.py."""
import copy, json, sys
from pathlib import Path
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from traducao_en import EN, GERAL  # noqa: E402

r = json.load(open(AQUI.parent / "roteiro.json", encoding="utf-8"))
en = copy.deepcopy(r)
avisos = []


def ancora(i, pt):
    if pt is None:
        return None
    mapa = EN[i][1]
    if pt in mapa:
        return mapa[pt]
    avisos.append(f"batida {i}: âncora '{pt}' sem tradução (usa o início da fala)")
    return None


for i, b in enumerate(en["batidas"]):
    fala, mapa, texto, verm = EN[i]
    b["fala"] = fala
    for x in b.get("enfase", []) + b.get("sons", []):
        if "em" in x:
            novo = ancora(i, x["em"])
            if novo: x["em"] = novo
            else: x.pop("em")
    for k in ("musica", "ambiente"):
        if isinstance(b.get(k), dict) and b[k].get("em"):
            novo = ancora(i, b[k]["em"])
            if novo: b[k]["em"] = novo
            else: b[k].pop("em")
    for c in ([b["cena"]] if b.get("cena") else []) + b.get("cenas", []):
        if c.get("em"):
            novo = ancora(i, c["em"])
            if novo: c["em"] = novo
            else: c.pop("em")
        if c.get("tipo") == "texto":
            c["texto"] = texto or fala.strip('"')
            if verm: c["vermelho"] = verm
            else: c.pop("vermelho", None)
        if c.get("legenda_cartao"):
            c["legenda_cartao"] = GERAL["legenda_cartao"]
    if i in (0, 1, 2, 96):
        b["voz_fx"] = "telefone"

# 14/11: em inglês a narração é mais rápida e as telas de texto sumiam antes de dar para ler (aviso leitura do
# 1º render). Deficit medido (s) por batida de texto: digita mais rápido e ganha uma pausa antes da próxima fala.
DEFICIT = {0: 5.5, 1: 6.2, 2: 5.6, 3: 3.0, 4: 4.6, 5: 2.2, 16: 1.2, 30: 1.3, 35: 1.0, 66: 2.4, 87: 0.7,
           94: 3.3, 95: 0.4, 96: 1.6}
for i, d in DEFICIT.items():
    c = en["batidas"][i]["cena"]
    n = len(c["texto"])
    cps_velho = c.get("cps") or 22
    cps = 34 if i in (0, 1, 2, 96) else max(cps_velho, 28 if n > 25 else cps_velho)
    c["cps"] = cps
    falta = d - (n / cps_velho - n / cps)
    if falta > 0 and i + 1 < len(en["batidas"]):
        prox = en["batidas"][i + 1]
        prox["pausa_antes_s"] = round(prox.get("pausa_antes_s", 0) + min(3.0, falta + 0.3), 2)

en["batidas"][6]["pausa_antes_s"] = round(en["abertura"]["duracao"] + en["abertura"].get("segurar", 0) + 0.8 + 1.5, 2)  # abertura + leitura de "And Rafael was gone."
en["idioma"] = "en"
en["voz_arquivo"] = "en/voz_completa_en.wav"
en["abertura"]["texto"] = GERAL["abertura"]
en["legendas"]["destaques"] = GERAL["legendas_destaques"]
en["cta"].update(GERAL["cta"])
en["cta"]["botao"], en["cta"]["botao_ok"] = "SUBSCRIBE", "SUBSCRIBED"
json.dump(en, open(AQUI.parent / "roteiro_en.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("roteiro_en.json pronto;", len(en["batidas"]), "batidas")
for a in avisos:
    print("  ", a)
