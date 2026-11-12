"""Monta os 3 Shorts (9:16, até 35 s) do Ep. 06 "A porta na mata" a partir da narração do episódio longo.
Regras da auditoria de 10/11 (guia, seção 13): ≤ 35 s, gancho no primeiro 0,5 s, cada Short é teaser do longo
(termina em aberto, chamada "episódio completo no canal" + recurso "Vídeo relacionado" no YouTube).
Uso: python3 montar_shorts.py   (gera shorts/*.json e recorta a voz; depois renderize cada um com gerar.py)"""
import copy, json, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "painel"))
from gerar import tokens  # noqa: E402

AQUI = Path(__file__).parent
longo = json.load(open(AQUI / "roteiro.json"))
VOZ = AQUI / longo["voz_arquivo"]
(AQUI / "shorts").mkdir(exist_ok=True)
MAX_VOZ = 31.0  # + 3,4 s de chamada final = ~35 s

palavras = [w for b in longo["batidas"] for w in tokens(b["fala"])]
tempos = json.load(open(AQUI / "audio" / "alinhamento.json"))   # mesma narração do longo
ini, k = [], 0
for b in longo["batidas"]:
    ini.append(k); k += len(tokens(b["fala"]))
ini.append(k)

SHORTS = [
    # 1. o gancho: as lanternas contadas — cinco bombeiros, seis luzes, a risada do Caio de boca fechada
    {"nome": "s1_eram_seis", "de": 0, "ate": 8, "titulo": "Quem era o sexto?"},
    # 2. as batidas: os cinco do mesmo lado da porta, e alguém bate — o Caio abre
    {"nome": "s2_alguem_bateu", "de": 39, "ate": 47, "pular": [46],  # 12/11: começa em "…quando bateram." para as
     "sem_prefixo": "Eles obedeceram.", "titulo": "O que passou pela porta?"},  # batidas reais abrirem o Short (≈35 s)
    # 3. a câmera: cinco na tela, seis no olho
    {"nome": "s3_aponta_a_camera", "de": 134, "ate": 143, "pular": [138], "titulo": "Quantos tem na sua casa?"},
]


def ajustar_cena(c):
    c.pop("lado", None); c.pop("revelar", None)
    if c.get("vigia"):
        c["imagem"] = "../../painel/cenarios/abrigo_vertical.png"
    for campo in ("imagem", "video"):
        if c.get(campo):
            c[campo] = "../" + c[campo]
    if c.get("imagem") or c.get("video"):
        c["encaixe"] = "cobrir"
        if c.get("foco") and c.get("zoom", [1])[0] <= 1.1:
            c["foco"] = [[0.5, f[1]] for f in c["foco"]]
    if c.get("tipo") == "texto":
        if c.get("estilo") == "maquina" and not c.get("tamanho"):
            c["tamanho"] = 84  # no vertical o texto precisa ser maior
        elif c.get("tamanho"):
            c["tamanho"] = int(c["tamanho"] * 1.45)
        if c.get("estilo") == "maquina" and not c.get("cps"):
            c["cps"] = 45 if len(c.get("texto", "")) > 40 else 30  # a digitação termina cedo: sobra tempo de ler
        elif c.get("cps") and c["cps"] < 20:
            c["cps"] = 20


for S in SHORTS:
    a, b = S["de"], S["ate"]
    usar = [i for i in range(a, b + 1) if i not in S.get("pular", [])]
    trechos = []  # sequências contíguas de batidas (o "pular" corta uma batida e emenda a voz)
    for i in usar:
        if trechos and trechos[-1][1] == i - 1:
            trechos[-1][1] = i
        else:
            trechos.append([i, i])
    partes, total = [], 0.0
    for n, (x, y) in enumerate(trechos):
        p0, p1 = ini[x], ini[y + 1] - 1
        if n == 0 and S.get("sem_prefixo"):
            p0 += len(tokens(S["sem_prefixo"]))   # corta as primeiras palavras da 1ª batida (voz e texto)
        t0 = tempos[p0][0] - (0.12 if n == 0 else 0.25)  # gancho: a 1ª palavra entra quase no 1º quadro
        if p0 > 0:
            t0 = max(t0, tempos[p0 - 1][1] + 0.05)
        t1 = tempos[p1][1] + 0.6
        if p1 + 1 < len(tempos):
            t1 = min(t1, tempos[p1 + 1][0] - 0.05)
        t0 = max(0.0, t0)
        parte = AQUI / "shorts" / f"_{S['nome']}_{n}.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t0:.3f}", "-to", f"{t1:.3f}", "-i", str(VOZ),
                        "-af", "afade=t=in:d=0.02,areverse,afade=t=in:d=0.03,areverse", str(parte)], check=True)
        partes.append(parte); total += t1 - t0
    if total > MAX_VOZ:
        print(f"!! {S['nome']}: {total:.1f}s de voz passa de {MAX_VOZ}s")
    arq = AQUI / "shorts" / f"{S['nome']}_voz.wav"
    ent = sum((["-i", str(q)] for q in partes), [])
    subprocess.run(["ffmpeg", "-v", "error", "-y", *ent, "-filter_complex",
                    "".join(f"[{i}:a]" for i in range(len(partes))) + f"concat=n={len(partes)}:v=0:a=1", str(arq)], check=True)
    for q in partes:
        q.unlink()
    bat = [copy.deepcopy(longo["batidas"][i]) for i in usar]
    if S.get("sem_prefixo"):
        assert bat[0]["fala"].startswith(S["sem_prefixo"])
        bat[0]["fala"] = bat[0]["fala"][len(S["sem_prefixo"]):].strip()
    for j, x in enumerate(bat):
        for ch in ("musica", "ambiente"):
            x.pop(ch, None)
        # as pausas do longo existem para dar tempo de ler as telas de texto: ficam, mas no máximo 1,2 s
        p = x.pop("pausa_antes_s", None)
        if p and j > 0:
            ant = bat[j - 1].get("cena") or (bat[j - 1].get("cenas") or [{}])[-1]
            x["pausa_antes_s"] = min(p, 2.4 if ant.get("tipo") == "texto" else 1.2)  # depois de tela de texto: tempo de ler
            if any(q.get("depois") for q in bat[j - 1].get("sons", [])):
                x["pausa_antes_s"] = min(p, 2.0)   # 12/11: pausa que isola um som-chave (batidas) fica inteira (guia, seção 16)
        for c in ([x["cena"]] if x.get("cena") else []) + x.get("cenas", []):
            ajustar_cena(c)
    if S.get("primeira_cena"):
        c = copy.deepcopy(S["primeira_cena"]); ajustar_cena(c)
        bat[0].pop("cenas", None); bat[0]["cena"] = c
    if not (bat[0].get("cena") or bat[0].get("cenas")):
        raise SystemExit(f"{S['nome']}: a 1ª batida precisa de cena")
    r = {k: v for k, v in longo.items() if k not in ("batidas", "abertura", "cta", "voz_arquivo", "preencher_pausas", "ambiente_inicial")}
    r.update({"formato": "9:16", "voz_arquivo": arq.name, "batidas": bat, "cauda": 1.0, "apertar_pausas": False,
              "vigia_padrao": False,
              "musica": {"som": "ep06_cx_tensao", "volume_db": -33},
              "ambiente_inicial": [{"som": "ep06_mata_muda", "volume_db": -19}],
              "cta": {"titulo": S["titulo"], "canal": "Último Abrigo", "subtitulo": "Episódio completo no canal",
                      "fundo": "../../../painel/cenarios/abrigo_vertical.png", "pose": "c_cafe_convite", "duracao": 3.4}})
    (AQUI / "shorts" / f"{S['nome']}.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    print(S["nome"], f"{total:.1f}s de narração")
