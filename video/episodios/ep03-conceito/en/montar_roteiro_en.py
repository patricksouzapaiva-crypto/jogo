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
