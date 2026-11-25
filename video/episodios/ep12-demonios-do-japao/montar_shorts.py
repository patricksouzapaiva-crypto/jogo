"""Monta os 3 Shorts (9:16) do Ep. 12 (25/11; cópia do montar_shorts do Ep. 11, que veio do Ep. 10) a partir da narração e das cenas do episódio (15/11), no molde do Ep. 08:
gancho no primeiro quadro, cada Short é um teaser (termina em aberto) e fecha com o Vigia chamando pro episódio.
Os tempos das palavras saem de audio/alinhamento.json (a narração final, com os ganchos).
Uso: python3 montar_shorts.py → shorts/*.json + vozes; depois: gerar.py shorts/<nome>.json shorts_final/<nome>.mp4"""
import copy, json, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "painel"))
from gerar import tokens  # noqa: E402

AQUI = Path(__file__).parent
longo = json.load(open(AQUI / "roteiro.json"))
VOZ = AQUI / longo["voz_arquivo"]
(AQUI / "shorts").mkdir(exist_ok=True)
MAX_VOZ = 45.0
tempos = json.load(open(AQUI / "audio" / "alinhamento.json"))
ini, k = [], 0
for b in longo["batidas"]:
    ini.append(k); k += len(tokens(b["fala"]))
ini.append(k)
assert k <= len(tempos), (k, len(tempos))

SHORTS = [
    # 1. o caso real de Matsudo (2022): os bonecos pregados, o bilhete, a câmera, o senhor de 72 anos, o crime foi o prego
    {"nome": "s1_matsudo", "de": 0, "ate": 5, "titulo": "Não seja visto.", "ambiente": "ep08_campo_noite"},
    # 2. a praia: a mulher do mar com o bebê que vira pedra… e o ushi-oni saindo da água (termina em aberto)
    {"nome": "s2_praia", "de": 125, "ate": 129, "titulo": "Use luvas.", "ambiente": "ep12_mar_noite"},
    # 3. a Sesshō-seki: a pedra que mata rachou em 2022 — "se ela saiu… talvez não esteja sozinha"
    {"nome": "s3_pedra", "de": 140, "ate": 145, "titulo": "Ela saiu da pedra?", "ambiente": "ep08_campo_noite"},
]

def ajustar_cena(c):
    """Cena do longo (16:9) → vertical: imagem/vídeo cobrem a tela; foco volta pro meio na horizontal."""
    for campo in ("imagem", "video"):
        if c.get(campo):
            c[campo] = "../" + c[campo]
    for m in c.get("mensagens", []):
        if m.get("imagem"):
            m["imagem"] = "../" + m["imagem"]
    for lado in c.get("lados", []):
        if lado.get("imagem"):
            lado["imagem"] = "../" + lado["imagem"]
    if c.get("imagem") or c.get("video"):
        c["encaixe"] = "cobrir"
        if c.get("foco"):
            c["foco"] = [[0.5, f[1]] for f in c["foco"]]
        c.pop("dof", None)
    ks = c.get("kanji")
    for K in (ks if isinstance(ks, list) else [ks] if ks else []):   # no vertical: horizontal, no alto da tela
        n = max(1, len(K.get("texto", "")))
        K.update({"vertical": False, "x": 0.5, "y": 0.2, "tam": round(min(0.14, 0.85 * 1080 / (n * 1920)), 3),
                  "lado_legenda": "baixo"})


for S in SHORTS:
    usar = list(range(S["de"], S["ate"] + 1))
    p0, p1 = ini[usar[0]], ini[usar[-1] + 1] - 1
    t0 = max(0.0, tempos[p0][0] - 0.12)
    t1 = tempos[p1][1] + 0.6
    if p1 + 1 < len(tempos):
        t1 = min(t1, tempos[p1 + 1][0] - 0.05)
    arq = AQUI / "shorts" / f"{S['nome']}_voz.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t0:.3f}", "-to", f"{t1:.3f}", "-i", str(VOZ),
                    "-af", "afade=t=in:d=0.02,areverse,afade=t=in:d=0.04,areverse", str(arq)], check=True)
    total = t1 - t0
    if total > MAX_VOZ:
        print(f"!! {S['nome']}: {total:.1f}s de voz passa de {MAX_VOZ}s")
    bat = [copy.deepcopy(longo["batidas"][i]) for i in usar]
    for j, x in enumerate(bat):
        for ch in ("musica", "ambiente"):
            x.pop(ch, None)
        p = x.pop("pausa_antes_s", None)
        if p and j > 0:
            x["pausa_antes_s"] = min(p, 1.2)
        # 21/11: no Short a narração não para nas fichas (ficaria por cima da legenda): sai a ficha, fica a imagem
        if x.get("cenas"):
            x["cenas"] = [c for c in x["cenas"] if c.get("tipo") != "texto"]
            if x["cenas"]:
                x["cenas"][0].pop("em", None)
            else:
                x.pop("cenas")
        if x.get("cena", {}).get("tipo") == "texto":
            x.pop("cena")
        for c in ([x["cena"]] if x.get("cena") else []) + x.get("cenas", []):
            ajustar_cena(c)
    if S.get("primeira_cena_de") is not None:
        b0 = longo["batidas"][S["primeira_cena_de"]]
        c = copy.deepcopy(b0["cena"] if b0.get("cena") else b0["cenas"][0]); ajustar_cena(c)
        c.pop("em", None); bat[0].pop("cenas", None); bat[0]["cena"] = c
    if not (bat[0].get("cena") or bat[0].get("cenas")):
        raise SystemExit(f"{S['nome']}: a 1ª batida precisa de cena")
    c0 = bat[0]["cena"] if bat[0].get("cena") else bat[0]["cenas"][0]
    c0["entrada"] = "corte"; c0.pop("antecipar", None)   # gancho: imagem no 1º quadro
    r = {k: v for k, v in longo.items() if k not in ("batidas", "abertura", "cta", "voz_arquivo", "ambiente_inicial",
                                                     "titulo_ep", "musica")}
    r.update({"formato": "9:16", "voz_arquivo": arq.name, "batidas": bat, "cauda": 1.0, "apertar_pausas": False,
              "vigia_padrao": False, "cena_minima": 2.0, "musica": {"som": "ep12_trilha", "volume_db": -27},
              "cta": {"titulo": S["titulo"], "canal": "Último Abrigo", "subtitulo": "Episódio completo no canal",
                      "fundo": "../../../painel/cenarios/abrigo_vertical.png", "pose": "c_cafe_convite", "duracao": 3.4}})
    if S.get("ambiente"):
        r["ambiente_inicial"] = [{"som": S["ambiente"], "volume_db": -20}]
    (AQUI / "shorts" / f"{S['nome']}.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    print(S["nome"], f"{total:.1f}s de narração")
