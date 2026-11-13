"""Monta os 3 Shorts (9:16, ~35 s) do Ep. 08 a partir da narração e das cenas do episódio (13/11).
Mesmas regras do Ep. 06: gancho no primeiro meio segundo, cada Short é um teaser (termina em aberto) + chamada
"episódio completo no canal" e o recurso "Vídeo relacionado" no YouTube.
Os tempos das palavras saem da própria voz_personagens.wav (Whisper + alinhamento do gerar.py, guardados em
audio/alinhamento_personagens.json), porque o alinhamento.json antigo é da narração ANTES da troca das vozes.
Uso: python3 montar_shorts.py → shorts/*.json + vozes; depois: gerar.py shorts/<nome>.json shorts_final/<nome>.mp4"""
import copy, json, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "painel"))
from gerar import tokens, transcrever, alinhar, ajustar_inicios  # noqa: E402

AQUI = Path(__file__).parent
longo = json.load(open(AQUI / "roteiro.json"))
VOZ = AQUI / longo["voz_arquivo"]
(AQUI / "shorts").mkdir(exist_ok=True)
MAX_VOZ = 32.0

palavras = [w for b in longo["batidas"] for w in tokens(b["fala"])]
cache = AQUI / "audio" / "alinhamento_personagens.json"
if cache.exists():
    tempos = json.load(open(cache))
else:
    ouvidas = transcrever(VOZ, " ".join(b["fala"] for b in longo["batidas"]))
    tempos, casadas = alinhar(palavras, ouvidas)
    tempos = ajustar_inicios(VOZ, tempos)
    json.dump(tempos, open(cache, "w")); print(f"alinhamento: {casadas:.0%}")
ini, k = [], 0
for b in longo["batidas"]:
    ini.append(k); k += len(tokens(b["fala"]))
ini.append(k)

SHORTS = [
    # 1. o gancho do episódio: o áudio da Dani no trem e a placa escrita à mão
    {"nome": "s1_kisaragi", "de": 0, "ate": 4, "titulo": "Ela desceu numa estação que não existe.",
     "ambiente": "ep08_trem_dentro"},
    # 2. a Sadako não é nova: o poço da Okiku e o cabelo da Oiwa
    {"nome": "s2_sadako", "de": 63, "ate": 67, "titulo": "A Sadako tem trezentos anos."},
    # 3. "Eu sou bonita?" — a Kuchisake-onna
    {"nome": "s3_eu_sou_bonita", "de": 80, "ate": 85, "titulo": "E agora?", "primeira_cena_de": 81},
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
        c.pop("dof", None)                       # o desfoque foi calculado para o quadro horizontal
    if c.get("kanji"):   # no vertical: escrito na horizontal, no alto da tela, legenda embaixo (longe da legenda falada)
        K = c["kanji"]; n = max(1, len(K.get("texto", "")))
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
        for c in ([x["cena"]] if x.get("cena") else []) + x.get("cenas", []):
            ajustar_cena(c)
    if S.get("primeira_cena_de") is not None:
        c = copy.deepcopy(longo["batidas"][S["primeira_cena_de"]]["cena"]); ajustar_cena(c)
        c["entrada"] = "corte"; c.pop("antecipar", None)
        bat[0]["cena"] = c
    if not (bat[0].get("cena") or bat[0].get("cenas")):
        raise SystemExit(f"{S['nome']}: a 1ª batida precisa de cena")
    bat[0]["cena"]["entrada"] = "corte"; bat[0]["cena"].pop("antecipar", None)   # gancho: imagem no 1º quadro
    r = {k: v for k, v in longo.items() if k not in ("batidas", "abertura", "cta", "voz_arquivo", "ambiente_inicial")}
    r.update({"formato": "9:16", "voz_arquivo": arq.name, "batidas": bat, "cauda": 1.0, "apertar_pausas": False,
              "vigia_padrao": False, "musica": {"som": "ep08_japones_longa", "volume_db": -31},
              "cta": {"titulo": S["titulo"], "canal": "Último Abrigo", "subtitulo": "Episódio completo no canal",
                      "fundo": "../../../painel/cenarios/abrigo_vertical.png", "pose": "c_cafe_convite", "duracao": 3.4}})
    if S.get("ambiente"):
        r["ambiente_inicial"] = [{"som": S["ambiente"], "volume_db": -18}]
    (AQUI / "shorts" / f"{S['nome']}.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    print(S["nome"], f"{total:.1f}s de narração")
