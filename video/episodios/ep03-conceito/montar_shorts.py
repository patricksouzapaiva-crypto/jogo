"""Monta os 3 Shorts de divulgação (9:16) do Ep. 03 a partir da narração do episódio longo.
Uso: python3 montar_shorts.py   (gera shorts/*.json e recorta a voz; depois renderize cada um com gerar.py)"""
import copy, json, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "painel"))
from gerar import tokens, transcrever, alinhar  # noqa: E402

AQUI = Path(__file__).parent
longo = json.load(open(AQUI / "roteiro.json"))
VOZ = AQUI / longo["voz_arquivo"]
POS = json.load(open(AQUI / "criatura_posicoes.json"))
(AQUI / "shorts").mkdir(exist_ok=True)

# tempo de cada palavra do roteiro dentro da narração completa (cacheado)
cache = AQUI / "shorts" / "alinhamento.json"
palavras = [w for b in longo["batidas"] for w in tokens(b["fala"])]
if cache.exists():
    tempos = json.load(open(cache))
else:
    tempos, casadas = alinhar(palavras, transcrever(VOZ, ""))
    print(f"alinhamento: {casadas:.0%} das palavras reconhecidas")
    json.dump(tempos, open(cache, "w"))
ini, k = [], 0
for b in longo["batidas"]:
    ini.append(k); k += len(tokens(b["fala"]))
ini.append(k)


def foco_vertical(nome):
    """No 9:16 só ~1/3 da largura aparece: centraliza perto da criatura, mas sem colocá-la no meio."""
    if nome not in POS:
        return None
    x = POS[nome]["x"]
    x = x + 0.07 if x < 0.5 else x - 0.07
    return min(0.84, max(0.16, x))


SHORTS = [
    {"nome": "s1_a_mensagem", "de": 0, "ate": 5, "titulo": "O que aconteceu com o Rafael?",
     "inicio": 1.1,  # a mensagem do telefone não é reconhecida pelo Whisper: começo medido pelo silêncio
     "musica": [(3, "trilha_tensa_1", None, -22)]},
    {"nome": "s2_encontre_a_criatura", "de": 78, "ate": 86, "titulo": "Achou ela?", "subtitulo": "A resposta está no vídeo completo",
     "musica": [(78, "trilha_tensa_2", None, -22)],
     # aqui as fotos da mesa viram as próprias fotos com ela escondida (sem revelar)
     "imagens": {78: "H4", 79: "H3", 80: "H1", 81: "H1", 82: "H2", 83: "H2", 85: "H6", 86: "H7"},
     "extras": {84: [("H3", None), ("H4", "Na"), ("H5", "No")]}},
    {"nome": "s3_o_microfone", "de": 36, "ate": 41, "titulo": "Até onde os passos foram?",
     "musica": [(36, "trilha_tensa_2", None, -22), (39, "silencio", "outro", -40)]},
]

MAPA_POSES = {}  # o Ep. 03 já usa as poses do vigia_hd

for S in SHORTS:
    a, b = S["de"], S["ate"]
    p0, p1 = ini[a], ini[b + 1] - 1
    t0 = tempos[p0][0] - 0.25
    if p0 > 0:
        t0 = max(t0, tempos[p0 - 1][1] + 0.05)
    t1 = tempos[p1][1] + 0.6
    if p1 + 1 < len(tempos):
        t1 = min(t1, tempos[p1 + 1][0] - 0.05)
    t0 = max(0.0, S.get("inicio", t0))
    arq = AQUI / "shorts" / f"{S['nome']}_voz.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t0:.3f}", "-to", f"{t1:.3f}", "-i", str(VOZ),
                    "-af", "afade=t=in:d=0.04", str(arq)], check=True)
    bat = copy.deepcopy(longo["batidas"][a:b + 1])
    for i, x in enumerate(bat, start=a):
        for ch in ("musica", "ambiente", "pausa_antes_s"):
            x.pop(ch, None)
        if i in S.get("imagens", {}):
            x["cena"] = {"imagem": f"imagens/{S['imagens'][i]}.png", "zoom": [1.0, 1.07]}
        if i in S.get("extras", {}):
            x.pop("cena", None)
            x["cenas"] = [{"imagem": f"imagens/{n}.png", "zoom": [1.0, 1.07], **({"em": em} if em else {})}
                          for n, em in S["extras"][i]]
        for c in ([x["cena"]] if x.get("cena") else []) + x.get("cenas", []):
            c.pop("lado", None); c.pop("revelar", None)
            if c.get("vigia"):
                c["imagem"] = "../../painel/cenarios/abrigo_vertical.png"
            if c.get("imagem"):
                c["imagem"] = "../" + c["imagem"]
                c["encaixe"] = "cobrir"
                fx = foco_vertical(Path(c["imagem"]).stem)
                if fx is not None:
                    c["foco"] = [[fx, 0.5], [fx, 0.46]]
                elif c.get("foco"):
                    c["foco"] = [[0.5, f[1]] for f in c["foco"]]
            if c.get("tipo") == "texto" and not c.get("tamanho") and c.get("estilo") == "maquina":
                c["tamanho"] = 84  # no vertical o texto precisa ser maior
            elif c.get("tipo") == "texto" and c.get("tamanho"):
                c["tamanho"] = int(c["tamanho"] * 1.45)
    if not (bat[0].get("cena") or bat[0].get("cenas")):
        raise SystemExit(f"{S['nome']}: a 1ª batida precisa de cena")
    for (i, som, em, db) in S["musica"]:
        bat[i - a]["musica"] = {"som": som, "volume_db": db, **({"em": em} if em else {})}
    r = {k: v for k, v in longo.items() if k not in ("batidas", "abertura", "cta", "voz_arquivo", "preencher_pausas")}
    r.update({"formato": "9:16", "voz_arquivo": arq.name, "batidas": bat, "cauda": 1.0, "apertar_pausas": False,
              "musica": {"som": "silencio", "volume_db": -40}, "ambiente_inicial": [],
              "cta": {"titulo": S["titulo"], "canal": "Último Abrigo", "subtitulo": S.get("subtitulo", "História completa no canal"),
                      "fundo": "../../../painel/cenarios/abrigo_vertical.png", "pose": "c_cafe_convite", "duracao": 3.4}})
    (AQUI / "shorts" / f"{S['nome']}.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    print(S["nome"], f"{t1 - t0:.1f}s de narração")
