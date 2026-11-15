"""Monta os 3 Shorts (9:16) do Ep. 09 a partir da narração e das cenas do episódio (15/11), no molde do Ep. 08:
gancho no primeiro quadro, cada Short é um teaser (termina em aberto) e fecha com o Vigia chamando pro episódio.
Os tempos das palavras saem de audio/alinhamento_voz_personagens.json (o alinhamento da voz final, com as trocas).
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
tempos = json.load(open(AQUI / "audio" / "alinhamento_voz_personagens.json"))
ini, k = [], 0
for b in longo["batidas"]:
    ini.append(k); k += len(tokens(b["fala"]))
ini.append(k)
assert k == len(tempos), (k, len(tempos))

SHORTS = [
    # 1. o gancho: o áudio do Rafa no elevador de um prédio que não tem dez andares
    {"nome": "s1_elevador_rafa", "de": 0, "ate": 4, "titulo": "O que voltou da montanha?", "ambiente": "ep09_mata_noite"},
    # 2. o Jangsan-beom: o bicho que imita a voz da sua família
    {"nome": "s2_jangsan_beom", "de": 88, "ate": 92, "titulo": "Confirma por mensagem antes de ir."},
    # 3. o Jogo do Elevador: as regras, até "Você chegou."
    {"nome": "s3_jogo_do_elevador", "de": 150, "ate": 159, "titulo": "E do outro lado?",
     "primeira_cena_de": 153},  # a 150 abre num cartão de texto (quadro vazio no 1º segundo): começa no elevador
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
              "vigia_padrao": False, "cena_minima": 2.0, "musica": {"som": "ep08_japones_longa", "volume_db": -29},
              "cta": {"titulo": S["titulo"], "canal": "Último Abrigo", "subtitulo": "Episódio completo no canal",
                      "fundo": "../../../painel/cenarios/abrigo_vertical.png", "pose": "c_cafe_convite", "duracao": 3.4}})
    if S.get("ambiente"):
        r["ambiente_inicial"] = [{"som": S["ambiente"], "volume_db": -20}]
    (AQUI / "shorts" / f"{S['nome']}.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    print(S["nome"], f"{total:.1f}s de narração")
