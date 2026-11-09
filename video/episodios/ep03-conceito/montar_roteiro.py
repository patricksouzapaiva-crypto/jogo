"""Monta roteiro.json do Ep. 03 "Mais perto." a partir de falas.json (texto + tag de imagem de cada fala).
Regras (usuário, 09/11): narração inteira, SEM encurtar pausas; pausas longas ganham troca de enquadramento,
reação do Vigia e a trilha subindo (automixar). Uso: python montar_roteiro.py
"""
import json
from pathlib import Path

AQUI = Path(__file__).parent
falas = json.load(open(AQUI / "falas.json"))
crit = json.load(open(AQUI / "criatura_posicoes.json"))

# ponto do Rafael em cada imagem (para aproximar nele, nunca na criatura durante a história)
RAF = {"H1": (0.62, 0.55), "H2": (0.40, 0.42), "H3": (0.42, 0.40), "H4": (0.22, 0.42), "H5": (0.72, 0.55),
       "H6": (0.36, 0.45), "H7": (0.74, 0.52), "H8": (0.55, 0.42), "H9": (0.5, 0.5),
       "R2": (0.5, 0.5), "R3": (0.5, 0.5), "R4": (0.55, 0.45), "R5": (0.45, 0.5), "R6": (0.45, 0.6), "R7": (0.5, 0.45)}
VIGIA = {"imagem": "../../painel/cenarios/abrigo_16x9.png", "vigia": True}


def cena(tag, k):
    """k-ésima vez seguida na mesma imagem -> enquadramento diferente (aberto, aproxima, detalhe...)."""
    if tag == "V":
        return dict(VIGIA, zoom=[1.0, 1.04], foco=[[0.55, 0.5], [0.57, 0.48]])
    if tag == "R1":
        return {"tipo": "cartao", "imagem": "imagens/R1.png", "legenda_cartao": "EPFL · Suíça · 2014",
                "zoom": [1.0, 1.06], "giro": -1.5 if k % 2 == 0 else 1.2}
    fx, fy = RAF.get(tag, (0.5, 0.5))
    planos = [([1.0, 1.06], [[0.5, 0.5], [0.5 + (fx - 0.5) * 0.3, 0.5 + (fy - 0.5) * 0.3]]),
              ([1.18, 1.26], [[fx, fy], [fx, fy - 0.03]]),
              ([1.06, 1.0], [[0.5 + (fx - 0.5) * 0.5, 0.5], [0.5, 0.5]]),
              ([1.3, 1.36], [[fx, fy - 0.05], [fx + 0.01, fy - 0.07]])]
    z, f = planos[k % len(planos)]
    c = {"imagem": f"imagens/{tag}.png", "zoom": z, "foco": f}
    if tag == "H8":
        c["encaixe"] = "cobrir"
    return c


batidas, ultima, rep = [], None, 0
for i, f in enumerate(falas):
    tag = f["tag"]
    b = {"fala": f["fala"]}
    if tag == "P":
        txt = f["fala"]
        if f["voz"].startswith("rafael"):
            b["cena"] = {"tipo": "texto", "texto": "MENSAGEM DE VOZ · 03:40\n" + txt.strip('"'),
                         "vermelho": "sei." if "sei" in txt else "fotos.", "estilo": "maquina", "tamanho": 60}
        else:
            curto = len(txt) < 30
            b["cena"] = {"tipo": "texto", "texto": txt, "estilo": "impacto" if curto else "maquina",
                         **({"cps": 12} if curto else {})}
        ultima, rep = "P", 0
    elif tag.endswith("r"):  # revelação: a mesma imagem, foco na criatura, círculo vermelho
        h = tag[:-1]
        p = crit[h]
        b["cena"] = {"imagem": f"imagens/{h}.png", "zoom": [1.0, 1.12], "foco": [[0.5, 0.5], [p["x"], p["y"]]],
                     **({"encaixe": "cobrir"} if h == "H8" else {}),
                     "revelar": {"x": p["x"], "y": p["y"], "r": p["r"], "atraso": 0.5, "duracao": 1.6,
                                 "clara": f"imagens/{h}_clara.png"}}
        b["sons"] = [{"em": f["fala"].split()[0], "som": "sub_drop", "volume_db": -12}]
        b["pausa_antes_s"] = 1.6   # mais tempo em cada imagem: dá tempo de achar (e de querer voltar)
        ultima, rep = tag, 0
    else:
        if tag != ultima:
            rep = 0
            b["cena"] = cena(tag, 0)
        elif tag != "V" and rep % 2 == 1:  # mesma imagem: novo enquadramento a cada 2 falas
            b["cena"] = cena(tag, rep // 2 + 1)
        rep += 1
        ultima = tag
    batidas.append(b)


def achar(t):
    for i, b in enumerate(batidas):
        if t in b["fala"]:
            return i
    raise SystemExit("não achei: " + t)


def efeito(trecho, em, som, db, depois=False, atraso=0.0):
    batidas[achar(trecho)].setdefault("sons", []).append(
        {"em": em, "som": som, "volume_db": db, "depois": depois, "atraso": atraso})


def mus(trecho, som, em=None, db=-22):
    batidas[achar(trecho)]["musica"] = {"som": som, "volume_db": db, **({"em": em} if em else {})}


def enf(trecho, em, pose, seg=1.8):
    batidas[achar(trecho)].setdefault("enfase", []).append({"em": em, "pose": pose, "segurar": seg})


# ---- trilha e silêncios
mus("Essa foi a última mensagem", "drone_tensao", None, -26)
mus("Boa noite. Bem-vindo de volta", "trilha_tensa_1", None, -22)
mus("Com o tempo, a sensação deixou", "trilha_tensa_2", None, -22)
mus("Até a noite em que, escovando", "silencio")
mus("Depois daquela noite, o Rafael mudou", "trilha_tensa_2", None, -22)
mus("Uma curiosidade, já que estamos", "trilha_tensa_1", None, -24)
mus("Numa madrugada, ele imprimiu todas", "silencio")
mus("O Rafael pegou uma caneta vermelha", "trilha_tensa_2", None, -24)
mus("Três e quarenta da manhã.", "silencio")
mus("O Lucas chegou de manhã", "trilha_tensa_1", None, -24)
mus("Ela sempre esteve nas imagens", "silencio")
mus("O Rafael não desapareceu porque", "trilha_tensa_1", None, -22)

# ---- efeitos (sustos depois da palavra; no máximo ~1 forte a cada 30 s)
efeito("E o Rafael não estava lá.", "lá", "braam_horror", -6, depois=True)
efeito("O silêncio parava junto", "junto", "passos_atrasados", -4, depois=True)
efeito("E, logo depois de cada passo dele", "passo", "passos_atrasados", -4, depois=True)
efeito("os passos continuaram", "quarto", "stinger_cordas", -8, depois=True)
efeito("Era frio. Como se alguém", "respirando", "respiracao_nuca", -2, depois=True)
efeito("que corrente de ar", "aqui", "respiracao_nuca", -4, depois=True)
efeito('"Não procura ela."', "ela", "sub_drop", -6, depois=True)
efeito("Uma forma. Alta. Magra demais.", "Parada", "riser_tensao", -8, depois=True)
efeito("Em todas.", "todas", "braam_horror", -6, depois=True)
efeito("Era alguém. Sempre foi.", "foi", "sub_drop", -6, depois=True)
efeito("Abriu a câmera frontal", "atrás", "riser_tensao", -6, depois=True)
efeito("Ela estava ali.", "ali", "braam_horror", -2, depois=True)
efeito("E, pela primeira vez, ela não estava parada.", "parada", "stinger_cordas", -4, depois=True)
efeito("Algumas… nunca.", "nunca", "sub_drop", -8, depois=True)
efeito("não olha pra trás.", "trás", "respiracao_nuca", -2, depois=True, atraso=0.6)

# ---- ênfases do Vigia (o resto é conversa automática nas pausas)
enf("Boa noite. Bem-vindo de volta", "Boa", "c_cafe_convite", 2.2)
enf("Faz um teste agora", "Faz", "s_silencio", 2.4)
enf("Sentiu?", "Sentiu", "s_encarando", 2.0)
enf("Uma curiosidade, já que estamos", "Uma", "c_cafe_indicador", 2.0)
enf("Guarde isso.", "Guarde", "c_dedo_explicando", 1.6)
enf("A gente tenta provar", "provar", "c_pensativo_queixo", 1.8)
enf("Em todas.", "todas", "e_maos_na_boca", 2.0)
enf("Ela estava ali.", "ali", "e_aterrorizado_maos", 2.0)
enf("E, pela primeira vez, ela não estava parada.", "parada", "e_medo_gola", 2.2)
enf("Existe mesmo um atraso.", "atraso", "c_dedo_explicando", 1.6)
enf("Ela sempre esteve nas imagens", "Ela", "s_sorriso_sombrio", 2.2)
enf("Durante todo esse vídeo", "Durante", "c_sussurrando", 2.4)
enf("E nem você… nem o Rafael", "perceberam", "s_encarando", 1.8)
enf("Se você não acredita", "volta", "e_apontando", 2.0)
enf("Agora você sabe onde olhar.", "olhar", "s_sorriso_sombrio", 2.2)
efeito("E nem você… nem o Rafael", "perceberam", "riser_tensao", -8, depois=True)
enf("Ele desapareceu porque descobriu.", "descobriu", "s_encarando", 2.0)
enf("E você… acabou de ver", "você", "e_apontando", 2.0)
enf("não olha pra trás.", "olha", "s_silencio", 9)

# apartes longos: intercalar ilustrações para não ficar 30 s no mesmo plano
batidas[achar("Aquele arrepio no corredor")]["cena"] = {"imagem": "imagens/H3.png", "zoom": [1.1, 1.22], "foco": [[0.55, 0.45], [0.6, 0.35]]}
batidas[achar("E você vira. E não tem ninguém.")]["cena"] = {"tipo": "texto", "texto": "E não tem ninguém.", "vermelho": "ninguém.", "estilo": "impacto", "cps": 12}
batidas[achar("Todo mundo já sentiu isso.")]["cena"] = dict(VIGIA, zoom=[1.04, 1.0], foco=[[0.6, 0.45], [0.55, 0.5]])
batidas[achar("Cada um dos seus olhos tem um ponto cego")]["cena"] = {"tipo": "texto", "texto": "ponto cego.", "vermelho": "cego.", "estilo": "impacto", "tamanho": 140, "cps": 10}
batidas[achar("Você nunca percebe. Porque o seu cérebro")]["cena"] = dict(VIGIA, zoom=[1.0, 1.05], foco=[[0.5, 0.5], [0.55, 0.45]])
batidas[achar("Só presta atenção na sua nuca.")]["cena"] = {"tipo": "texto", "texto": "Não olha pra trás.", "vermelho": "trás.", "estilo": "impacto", "cps": 12}
batidas[achar("Sentiu?")]["cena"] = dict(VIGIA, zoom=[1.08, 1.12], foco=[[0.3, 0.6], [0.3, 0.6]])
for t in ("E você vira. E não tem ninguém.", "Cada um dos seus olhos tem um ponto cego", "Só presta atenção na sua nuca."):
    batidas[achar(t)]["sem_legenda"] = False

# lado do Vigia: oposto ao Rafael quando ele está à esquerda
for b in batidas:
    c = b.get("cena")
    if c and c.get("imagem", "").startswith("imagens/H"):
        fx = RAF.get(Path(c["imagem"]).stem, (0.5, 0.5))[0]
        c["lado"] = "dir" if fx < 0.45 else "esq"

roteiro = {
    "modo": "cenas", "formato": "16:9", "tema": "vigia", "avatar": "vigia_hd",
    "voz_arquivo": "audio/voz_completa_v2.wav", "apertar_pausas": False,
    "preencher_pausas": {"min": 1.3},
    "cauda": 1.6, "chuva": 0, "grao": 0.14,
    "mix": {"musica_ganho_db": 12, "fundo_sob_voz": -8, "efeitos_sob_voz": -3},
    "legendas": {"destaques": ["atrás", "perto", "todas", "procura", "ela"]},
    "ambiente_inicial": [], "musica": {"som": "silencio", "volume_db": -40},
    "abertura": {"texto": "O VIGIA\nEP. 03 · MAIS PERTO.", "duracao": 3.2, "antes_da_batida": 6,
                 "sons": [{"som": "braam_horror", "t": 0.2, "volume_db": -6}]},
    "cta": {"titulo": "Gostou dessa história?", "canal": "Último Abrigo", "subtitulo": "Inscreva-se para mais casos do Vigia",
            "fundo": "../../painel/cenarios/abrigo_16x9.png", "pose": "c_cafe_convite", "duracao": 3.8},
    "batidas": batidas,
}
for b in batidas:  # tela de texto não leva legenda embaixo (o texto já está na tela), salvo os apartes
    if b.get("cena", {}).get("tipo") == "texto" and b.get("sem_legenda") is not False:
        b["sem_legenda"] = True
(AQUI / "roteiro.json").write_text(json.dumps(roteiro, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(batidas), "batidas,", sum(1 for b in batidas if b.get("cena")), "cortes")
