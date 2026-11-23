"""Monta os 3 Shorts (9:16) do O QUE É A CRIATURA? #1 (23/11; molde do montar_shorts do Ep. 11): gancho no 1º quadro,
cada Short é um teaser que termina em aberto e fecha com o Vigia chamando pro episódio.
23/11: a 1ª versão não tinha filme (a NBC Universal bloqueou o longo pelo Content ID); o usuário pediu cenas do filme
("vitaliza muito"), sabendo que os Shorts podem ser reivindicados: abertura com uma fala + 1–2 cenas sem som no meio
(formato vertical próprio, cortar_vertical.py). Saem do longo: os trechos 16:9, as peças (cartões, checklists) e as fichas.
Cada Short pode juntar vários trechos da narração ("blocos"); os tempos saem de audio/alinhamento.json.
Uso: python3 montar_shorts.py → shorts/*.json + vozes; depois: gerar.py shorts/<nome>.json publicacao/shorts_final/<nome>.mp4"""
import copy, json, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "painel"))
from gerar import tokens  # noqa: E402

AQUI = Path(__file__).parent
longo = json.load(open(AQUI / "roteiro.json"))
VOZ = AQUI / longo["voz_arquivo"]
(AQUI / "shorts").mkdir(exist_ok=True)
tempos = json.load(open(AQUI / "audio" / "alinhamento.json"))
ini, k = [], 0
for b in longo["batidas"]:
    ini.append(k); k += len(tokens(b["fala"]))
ini.append(k)
assert k <= len(tempos), (k, len(tempos))   # o alinhamento tem também a vinheta falada do fim


def il(nome, v=1, z=(1.0, 1.08)):
    return {"imagem": f"imagens/IL_{nome}_{v}.jpg", "zoom": list(z)}


def anim(nome):
    return {"video": f"imagens/ANIM_{nome}.mp4", "zoom": [1.0, 1.03], "congelar": True}


def foto(arq, z=(1.0, 1.08)):
    return {"imagem": arq, "zoom": list(z)}


JORNAL = "reais_prontos/cleary_sun_1895.jpg"
# 23/11 (usuário: "cenas do filme nos shorts, isso vitaliza muito"): cada Short ABRE com uma fala do filme (com a dublagem)
# e tem 1–2 cenas do filme sem som no meio (shorts/filme_*.mp4, de cortar_vertical.py). O resto segue com as ilustrações.
TRECHO = {"caso_cheiro": 3.1, "p6_existir": 3.6, "p7_eu": 3.6}   # duração dos trechos de abertura (s)


def filme_v(nome):
    return {"video": f"filme_{nome}.mp4", "zoom": [1.0, 1.0], "congelar": True, "_local": True}
SHORTS = [
    # 1. o caso real: o marido que queimou a esposa porque jurava que ela tinha sido trocada (fecha na rima das crianças)
    {"nome": "s1_cleary", "abre": "caso_cheiro", "blocos": [(7, 7), (144, 148), (150, 152), (154, 155)], "titulo": "Você é a esposa de Michael Cleary?",
     "cenas": {7: foto(JORNAL, (1.0, 1.12)), 144: foto("imagens/IA02_lareira_2.jpg"), 145: filme_v("b_outra_rosto"),
               146: filme_v("b_pais_briga"), 147: foto("imagens/IA02_lareira_1.jpg"), 148: foto(JORNAL, (1.1, 1.2)),
               150: foto("imagens/IA02_lareira_1.jpg", (1.1, 1.2)), 152: il("pos_creditos", 2),
               154: il("bela_cama", 2), 155: anim("porta_azul")}},
    # 2. a tulpa: o monge que Alexandra David-Néel criou com a mente e que começou a aparecer sozinho
    {"nome": "s2_tulpa", "abre": "p6_existir", "blocos": [(80, 87)], "titulo": "Ela criou um ser só com a mente.",
     "cenas": {80: il("outra_silhueta", 2), 81: il("maquete", 2), 83: anim("rasteja"), 85: il("maquete", 1),
               86: filme_v("b_bela_sozinha")}},
    # 3. o trocado: as fadas que levavam a criança e deixavam uma cópia no berço
    {"nome": "s3_trocado", "abre": "p7_eu", "blocos": [(118, 126)], "titulo": "Não era o seu filho.",
     "cenas": {118: foto("imagens/IA01_berco_1.jpg"), 119: foto("imagens/IA01_berco_2.jpg"),
               120: foto("reais_prontos/fussli_changeling.jpg", (1.05, 1.15)), 123: filme_v("b_mesa"),
               124: anim("abraco"), 126: filme_v("b_rosto_final")}},
]
FILME = ("filmes_prontos/",)   # os trechos 16:9 do longo (com moldura) não entram: no vertical entram os shorts/filme_*


def limpar(c):
    v = str(c.get("video", "")) + str(c.get("imagem", ""))
    return not (any(f in v for f in FILME) or c.get("tipo") == "texto" or c.get("tipo_cartao") or "identidade/" in v)


def ajustar_cena(c):
    local = c.pop("_local", False)
    for campo in ("imagem", "video"):
        if c.get(campo) and not local:
            c[campo] = "../" + c[campo]
    if c.get("imagem") or c.get("video"):
        c["encaixe"] = "cobrir"
        if c.get("foco"):
            c["foco"] = [[0.5, f[1]] for f in c["foco"]]
        c.pop("dof", None)
    for x in ("antecipar", "antecipar_fixo", "em"):
        c.pop(x, None)


for S in SHORTS:
    partes, bat, total = [], [], 0.0
    for n, (de, ate) in enumerate(S["blocos"]):
        p0, p1 = ini[de], ini[ate + 1] - 1
        t0 = max(0.0, tempos[p0][0] - 0.12)
        t1 = min(tempos[p1][1] + 0.5, tempos[p1 + 1][0] - 0.05) if p1 + 1 < len(tempos) else tempos[p1][1] + 0.5
        arq = AQUI / "shorts" / f"_{S['nome']}_{n}.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t0:.3f}", "-to", f"{t1:.3f}", "-i", str(VOZ), "-ar", "48000",
                        "-ac", "1", "-af", "afade=t=in:d=0.02,areverse,afade=t=in:d=0.06,areverse", str(arq)], check=True)
        partes.append(arq); total += t1 - t0
        for i in range(de, ate + 1):
            x = copy.deepcopy(longo["batidas"][i])
            for ch in ("musica", "ambiente", "sons", "sem_legenda"):
                x.pop(ch, None)
            p = x.pop("pausa_antes_s", None)
            if p and i != de:
                x["pausa_antes_s"] = min(p, 0.8)
            cs = [c for c in ([x.pop("cena")] if x.get("cena") else []) + x.pop("cenas", []) if limpar(c)]
            if i in S["cenas"]:
                cs = [copy.deepcopy(S["cenas"][i])]
            elif cs:
                cs = cs[:1]
            for c in cs:
                ajustar_cena(c)
            if cs:
                x["cena"] = cs[0]
            if i == de and n > 0:
                x["pausa_antes_s"] = 0.35   # respiro curto entre os trechos (o corte não pode soar emendado)
            bat.append(x)
    voz = AQUI / "shorts" / f"{S['nome']}_voz.wav"
    lista = AQUI / "shorts" / f"_{S['nome']}.txt"
    lista.write_text("".join(f"file '{p.name}'\n" for p in partes))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lista), "-c", "copy", str(voz)], check=True)
    for p in partes + [lista]:
        p.unlink()
    if not bat[0].get("cena"):
        raise SystemExit(f"{S['nome']}: a 1ª batida precisa de cena")
    bat[0]["cena"]["entrada"] = "corte"   # gancho: imagem no 1º quadro
    if S.get("abre"):   # a fala do filme toca ANTES da 1ª frase (como o fala_filme do longo): a voz espera
        d = TRECHO[S["abre"]] + 0.25
        clip = {"video": f"filme_{S['abre']}.mp4", "zoom": [1.0, 1.0], "congelar": True, "encaixe": "cobrir",
                "antecipar": round(d, 2), "antecipar_fixo": True, "entrada": "corte"}
        bat[0]["cenas"] = [clip, bat[0].pop("cena")]
        bat[0]["cenas"][1]["entrada"] = "corte"
        bat[0]["pausa_antes_s"] = round(d + 0.1, 2)
        bat[0]["sons"] = [{"em": None, "som": f"filme_{S['abre']}", "volume_db": 0, "depois": False,
                           "atraso": round(-d + 0.05, 2), "arquivo": str(AQUI / "shorts" / f"filme_{S['abre']}.wav")}]
    r = {k: v for k, v in longo.items() if k not in ("batidas", "cta", "voz_arquivo", "musica")}
    r.update({"formato": "9:16", "voz_arquivo": voz.name, "batidas": bat, "cauda": 1.0, "apertar_pausas": False,
              "vigia_padrao": False, "cena_minima": 2.0, "musica": {"som": "cin01_trilha", "volume_db": -24},
              "cta": {"titulo": S["titulo"], "canal": "Último Abrigo", "subtitulo": "Episódio completo no canal",
                      "fundo": "../../../painel/cenarios/abrigo_vertical.png", "pose": "c_cafe_convite", "duracao": 3.4}})
    (AQUI / "shorts" / f"{S['nome']}.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    print(S["nome"], f"{total:.1f}s de narração, {len(bat)} falas, trechos do filme: {json.dumps(r).count('filme_') // 1}")
