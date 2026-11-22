"""Monta roteiro.json do O QUE É A CRIATURA? #1 — Outra Mamãe (21/11; molde do montar_roteiro.py do Ep. 11).
Formato novo (dia de semana): um filme por vídeo, estudo da criatura. Pistas (cenas do filme) → teorias (folclore real,
fichas ✓/✗) → spoiler → livro × filme → UM veredito → o porquê, prova a prova → a pergunta para os comentários.
- Peças do formato (identidade/pecas/v6: pista, teoria, checklist, placar, veredito, spoiler, porquê) e a abertura
  (identidade/abertura_v2.mp4, aprovada) entram como os cartões do Ep. 11: vídeo pronto com o próprio som, numa pausa da voz.
- Cena do filme com 🔊 (cortar_filmes.py): o Vigia se cala, o filme fala (dublagem) com a fala escrita embaixo; depois
  a narração segue sobre o último quadro congelado ("prova" parada na tela), a não ser que outra cena entre.
- Imagens [IA] (PROMPTS_CENAS.md, geradas pelo usuário em 21/11) em imagens/ (fora do git): berço, lareira, retrato, corredor, parquinho.
Regras: Vigia na apresentação, no porquê e no fecho; nenhum rosto de IA; cena >= 4 s; legenda só em português.
Uso: python3 montar_roteiro.py → roteiro.json"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import falas as F

AQUI = Path(__file__).parent
falas, SEC, DIREC, _ = F.ler()
assert len(falas) == 253, "o ROTEIRO.md mudou: rever o mapa"


def I(comeco, depois=0):
    """22/11: índice da fala pelo começo do texto (o roteiro muda de ordem; números fixos quebravam)."""
    ach = [k for k, f in enumerate(falas) if f.startswith(comeco) and k >= depois]
    assert ach, comeco
    return ach[0]
batidas = [{"fala": f} for f in falas]
VIGIA = {"imagem": "../../painel/cenarios/abrigo_16x9.png", "vigia": True}
C3D = AQUI / "camera3d"; C3D.mkdir(exist_ok=True)
ALI = Path(__import__("os").environ.get("ALINHAMENTO") or AQUI / "audio" / "alinhamento.json")
FP = "filmes_prontos/"; RP = "reais_prontos/"; ID = "identidade/brutas/"; PC = "identidade/pecas/v6/"
TRECHOS = json.loads((AQUI / FP / "trechos.json").read_text())


def P(nome):
    return nome if nome.endswith((".jpg", ".png")) else nome + ".jpg"


def vigia(z=(1.0, 1.04), foco=((0.55, 0.5), (0.57, 0.48))):
    return dict(VIGIA, zoom=list(z), foco=[list(foco[0]), list(foco[1])])


def img(nome, z=(1.0, 1.08), foco=None, **kw):
    c = {"imagem": P(nome), "zoom": list(z), **kw}
    if foco:
        c["foco"] = [list(foco[0]), list(foco[1])]
    return c


def c3(nome, mov="entrar", foco=(0.5, 0.5), forca=1.0, desfoque=0.0, **kw):
    return {"imagem": P(nome), "zoom": [1.0, 1.0], "_c3d": {"mov": mov, "foco": list(foco), "forca": forca, "desfoque": desfoque}, **kw}


def filme(nome, **kw):
    """Trecho do filme já na moldura de arquivo: sem zoom (a moldura e o crédito não podem crescer)."""
    return {"video": FP + nome + ".mp4", "zoom": [1.0, 1.0], "congelar": True, **kw}   # trecho curto: segura o último quadro


def real(nome, z=(1.0, 1.035), **kw):
    return {"imagem": RP + P(nome), "zoom": list(z), **kw}


def tem_real(nome):
    return (AQUI / RP / P(nome)).exists()


def quarto(v=1, **kw):     # no lugar das imagens [IA] que ainda não chegaram
    return img(ID + f"ID03_quarto_{v}.png", (1.0, 1.07), **kw)


def armario(v=1, **kw):
    return img(ID + f"ID21_armario_vazio_{v}.png", (1.0, 1.07), **kw)


def texto(t, vermelho=None, estilo="maquina", **kw):
    return {"tipo": "texto", "texto": t, "estilo": estilo, **({"vermelho": vermelho} if vermelho else {}), **kw}


def ficha(t, vermelho=None):
    return texto(t, vermelho, cps=40)


# 23/11 (retenção, sem o filme de fundo): um som discreto da biblioteca nas ilustrações-chave (o ElevenLabs está sem
# crédito). Nada de susto: entra suave, sob a voz, e corta antes de cansar (no máximo 2 vezes por som no vídeo).
SOM_IL = {"porta_azul": ("ep09_sn_porta_rangido_lento", -17, 6.0), "mesa": ("ep06_estalo", -15, 2.0),
          "rasteja": ("ep09_sao_oleo_pele_1", -15, 6.0), "abraco": ("ep07_respiracao_nuca", -17, 6.0),
          "pos_creditos": ("ep09_sn_porta_assombrada", -16, 6.0), "uv": ("ep09_fluorescente_tenso", -19, 7.0),
          "carro": ("chuva_externa", -19, 7.0), "cozinha": ("ep09_cozinha", -21, 7.0), "ritual_sal": ("ep08_vela", -16, 3.0),
          "outra_silhueta": ("ep09_sn_sussurro_fantasma", -18, 2.0), "frank": ("ep09_fluorescente", -20, 6.0),
          "escada": ("passos_atrasados", -16, 4.0), "quarto_portas": ("ep09_jh_rangido_1", -18, 6.0)}
_SOM_USO = {}


def som_ilustr(i, c):
    m = __import__("re").search(r"/IL_(\w+?)_\d\.jpg$", c.get("imagem", ""))
    if not m or m.group(1) not in SOM_IL or _SOM_USO.get(m.group(1), 0) >= 2:
        return
    _SOM_USO[m.group(1)] = _SOM_USO.get(m.group(1), 0) + 1
    som, db, ate = SOM_IL[m.group(1)]
    fx(i, c.get("em"), som, db, ate=ate, saida=1.2, entrada=0.6, _il=True)


def C(i, *cenas, com_vigia=False):
    b = batidas[i]; lista = []
    for x in cenas:
        c, em = (x if isinstance(x, tuple) else (x, None))
        c = dict(c)
        if em:
            c["em"] = em
        lista.append(c)
    b.pop("cena", None); b.pop("cenas", None)
    for c in lista:
        som_ilustr(i, c)
    if len(lista) == 1 and "em" not in lista[0]:
        b["cena"] = lista[0]
    else:
        b["cenas"] = lista


def pausa(i, s):
    batidas[i]["pausa_antes_s"] = round(batidas[i].get("pausa_antes_s", 0) + s, 2)


def fx(i, em, som, db, depois=False, atraso=0.0, **kw):
    batidas[i].setdefault("sons", []).append({"em": em, "som": som, "volume_db": db, "depois": depois, "atraso": atraso, **kw})


def dur_video(arq):
    if not (AQUI / arq).exists() and __import__("os").environ.get("TESTE"):
        return 9.0                                     # teste do montador antes das peças ficarem prontas
    util = AQUI / (str(arq) + ".util")   # 23/11: peça com cauda (pecas.py CAUDA) — o tempo útil, sem a cauda
    if util.exists():
        return float(util.read_text())
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(AQUI / arq)],
                                capture_output=True, text=True).stdout)


def som_de(arq):
    w = AQUI / (str(arq) + ".som.wav")
    if not (AQUI / arq).exists() and __import__("os").environ.get("TESTE"):
        return str(w)
    if not w.exists():
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(AQUI / arq), "-vn", "-ac", "2", "-ar", "48000", str(w)], check=True)
    return str(w)


ANTES = {}      # fala → lista de (cena, duração, som, db) que tocam NA PAUSA antes dela (peças e falas do filme), em ordem
FUROS = []      # (fala, deslocamento) das falas do filme → a música desce (trilha)
GOLPES = []     # fala das peças → tímpano na trilha


_AL = {}


def _alinh():
    if not _AL:
        sys.path.insert(0, str(AQUI.parents[1] / "painel")); from gerar import tokens as _tk
        ali = json.load(open(ALI)); ini = [0]
        for f in falas[:-1]:
            ini.append(ini[-1] + len(_tk(f)))
        _AL.update(ali=ali, ini=ini, tk=_tk)
    return _AL


def t_fala(i):
    A = _alinh(); return A["ali"][A["ini"][i]][0]


def fim_fala(i):
    A = _alinh(); return A["ali"][A["ini"][i] + len(A["tk"](falas[i])) - 1][1]


def palavra_apos(i, s):
    """22/11: a palavra da fala i dita >= s segundos depois do começo dela (pelo alinhamento real, não por estimativa),
    que o motor não confunde com uma anterior (ele pega a 1ª palavra que COMEÇA assim)."""
    A = _alinh(); toks = A["tk"](falas[i]); t0 = t_fala(i)
    nz = [re.sub(r"[^\wà-ú]", "", w.lower()) for w in toks]
    k = 1
    while k < len(toks) - 1 and A["ali"][A["ini"][i] + k][0] - t0 < s:
        k += 1
    while k < len(toks) - 1 and (len(nz[k]) < 3 or any(w.startswith(nz[k]) for w in nz[:k])):
        k += 1
    return toks[k].strip('.,:;!?"“”')


def antes(i, cena, dur, som=None, db=-10, furo=False, sobra=0.0):
    """Algo que toca inteiro numa pausa da voz antes da fala i (sobra = quanto a voz pode entrar antes do fim)."""
    ANTES.setdefault(i, []).append((cena, dur, som, db, furo, sobra))


def peca(i, arq, sobra=1.0, db=-9):
    """Peça do formato (vídeo com som): toca antes da fala i; a voz entra nos últimos 'sobra' s (o título já na tela)."""
    d = dur_video(arq)
    antes(i, {"video": arq, "zoom": [1.0, 1.0], "tipo_cartao": True, "congelar": True, "sem_look": True}, d, som_de(arq), db,
          sobra=sobra)
    GOLPES.append(i)


FALAS_FILME = []


def fala_filme(i, nome, db=0):   # 22/11: o filme mais alto (era -4)
    """Cena 🔊: o filme fala (dublagem), a voz espera; depois a narração segue sobre o último quadro congelado."""
    d = TRECHOS[nome]["dur"]
    antes(i, filme(nome, congelar=True), d + 0.25, str(AQUI / FP / f"{nome}.wav"), db, furo=True)
    FALAS_FILME.append((i, nome))


def montar_antes():
    """Transforma ANTES em cenas + pausas + sons (como os cartões de capítulo do Ep. 11)."""
    for i, itens in ANTES.items():
        total = sum(d for _, d, *_ in itens) - itens[-1][5]
        resto = cenas_de(batidas[i])
        t = total
        novas = []
        for cena, d, som, db, furo, sobra in itens:
            c = dict(cena); c.update({"antecipar": round(t, 2), "antecipar_fixo": True, "entrada": "corte"})
            novas.append(c)
            if som:
                fx(i, None, Path(som).stem, db, atraso=round(-t + 0.05, 2), arquivo=som)
            if furo:
                FUROS.append((i, -t, -t + d))
            t -= d
        if resto:
            r = dict(resto[0]); r["em"] = r.get("em") or None
            if r["em"] is None:   # a peça ainda está terminando sob a voz: a cena da fala entra umas palavras depois
                r.pop("em")
                if itens[-1][5] > 0:   # 22/11 (usuário: "não termina de aparecer a escrita e já troca"): pelo tempo real
                    r["em"] = palavra_apos(i, itens[-1][5] + 0.3)
            novas += [r] + resto[1:]
        batidas[i].pop("cena", None); batidas[i]["cenas"] = novas
        pausa(i, round(total + 0.35, 2))


def cenas_de(b):
    return ([b["cena"]] if b.get("cena") else []) + b.get("cenas", [])


# 22/11 (rascunho 2 → 3, pedidos do usuário): o filme ROLA atrás da narração (cena que combina com a fala), nada de
# quadro congelado nem cortiça vazia; as fichas são LIDAS pela narração (sem legenda por cima); aviso de spoiler narrado.
SEM_LEG = set()


def falada(i0, i1=None):
    """A ficha que entra na fala i0 é lida pela própria narração (i0..i1): a legenda sai, sem pausa em silêncio."""
    for j in range(i0, (i1 if i1 is not None else i0) + 1):
        SEM_LEG.add(j)
    for c in cenas_de(batidas[i0]):
        if c.get("tipo") == "texto":
            c["falada"] = True


# 23/11 — a NBC Universal BLOQUEOU o vídeo (Content ID visual) pelos ~6 min de filme DE FUNDO. Decisão com o usuário:
# o filme fica só nas 18 falas-pista (comentário, 2–5 s cada, cortadas no fim da fala); todo o fundo vira ilustração
# ORIGINAL sem rosto (gerar_ilustracoes.py → imagens/IL_<nome>_<v>.jpg). Sem a ilustração ainda, entra uma imagem
# nossa provisória (só para o rascunho).
ILUSTR = {"b_porta_azul": "porta_azul", "b_espelho": "espelho", "p2_almoco": "almoco", "b_cozinha": "cozinha", "b_mesa": "mesa",
          "b_quarto_portas": "quarto_portas", "p4_segredos": "segredos", "b_pais_briga": "pais_briga",
          "b_outra_rosto": "outra_silhueta", "b_carro_outra": "carro", "b_bela_cama": "bela_cama", "b_maos_porta": "maos_porta",
          "b_ritual_sal": "ritual_sal", "b_uv": "uv", "b_rasteja": "rasteja", "t4_imaginaria": "maquete",
          "b_bela_sozinha": "bela_sozinha", "b_familia": "botas", "b_praca": "praca", "b_outro_lado": "outro_lado",
          "s_afundou": "afundou", "b_avo": "avo", "s_confissao": "confissao", "b_cicatriz": "cicatriz", "s_avo": "maos_avo",
          "b_familia_fim": "familia_fim", "s_escola": "escola", "pos_creditos": "pos_creditos", "b_medium": "medium",
          "b_frank_fim": "frank", "b_abraco": "abraco", "b_tunel": "tunel", "b_bolinhas": "bolinhas",
          "b_rosto_final": "espelho_rachado"}
RABO = {"g_boanoite": "bela_cama", "g_coracao": "porta_azul", "p1_coracao": "maos_porta", "p1_medium": "medium",
        "p2_kelvin": "cozinha", "p5_frank": "frank", "p6_pessoa": "abraco", "p7_trocar": "espelho", "t3_ardiloso": "medium",
        "capgras": "praca", "caso_cheiro": "lareira", "s_mar": "mar", "s_inocencia": "medium", "s_sim": "escada",
        "s_nao": "maos_avo", "s_pensar": "cicatriz"}
PROVISORIA = ["identidade/brutas/ID03_quarto_1.png", "imagens/IA04_corredor_1.jpg", "identidade/brutas/ID21_armario_vazio_1.png",
              "imagens/IA04_corredor_2.jpg", "identidade/brutas/ID03_quarto_2.png", "identidade/brutas/ID21_armario_vazio_2.png"]
_USO = {}
_MOV = [((1.0, 1.08), ((0.5, 0.5), (0.52, 0.47))), ((1.08, 1.0), ((0.45, 0.55), (0.5, 0.5))),
        ((1.0, 1.07), ((0.4, 0.5), (0.46, 0.5))), ((1.0, 1.07), ((0.6, 0.5), (0.54, 0.5)))]


# 23/11 (retenção): atmosfera viva por cima (motor.js: vela tremendo, neblina, poeira na luz, fumaça/vapor)
ATMOS = {"ritual_sal": {"vela": 0.7}, "medium": {"vela": 0.8}, "avo": {"vela": 0.6}, "confissao": {"vela": 0.4},
         "uv": {"fumaca": 0.4}, "cozinha": {"fumaca": 0.3}, "outra_silhueta": {"neblina": 0.5}, "segredos": {"neblina": 0.4},
         "pos_creditos": {"neblina": 0.3}, "rasteja": {"neblina": 0.3}, "espelho": {"neblina": 0.3}, "porta_azul": {"poeira": 0.4},
         "mesa": {"poeira": 0.5}, "quarto_portas": {"poeira": 0.3}, "maquete": {"poeira": 0.4}, "bela_sozinha": {"poeira": 0.5},
         "abraco": {"poeira": 0.3}, "escola": {"poeira": 0.4}, "almoco": {"poeira": 0.4}, "botas": {"poeira": 0.4},
         "lareira": {"fumaca": 0.3}}


def ilustr(chave):
    c = _ilustr(chave)
    if chave in ATMOS:
        c["atmos"] = ATMOS[chave]
    return c


def _ilustr(chave):
    """a ilustração da vez: alterna as versões _1/_2 e o movimento de câmera a cada uso"""
    if chave == "lareira":
        return img("imagens/IA02_lareira_2", (1.0, 1.07), ((0.4, 0.55), (0.44, 0.58)))
    n = _USO[chave] = _USO.get(chave, 0) + 1
    arq = f"imagens/IL_{chave}_{2 - n % 2}.jpg"
    if not (AQUI / arq).exists():
        arq = PROVISORIA[sum(_USO.values()) % len(PROVISORIA)]
    z, foco = _MOV[(n + len(chave)) % len(_MOV)]
    anim = AQUI / "imagens" / f"ANIM_{chave}.mp4"   # 23/11: a cena animada pelo usuário (Veo) entra no 1º uso
    if n == 1 and anim.exists():
        return {"video": f"imagens/ANIM_{chave}.mp4", "zoom": [1.0, 1.03], "congelar": True}
    if "/IL_" in arq and not __import__("os").environ.get("SEM_3D"):   # 23/11 (retenção): câmera 3D por profundidade
        mov = ("entrar", "lado", "entrar", "lado_esq", "sair")[(n + len(chave)) % 5]
        return c3(arq, mov, foco[0], forca=0.85)
    return img(arq, z, foco)


def F(nome, **kw):
    return ilustr(ILUSTR[nome])


def congelado(arq, menos=0.4):
    return {"video": arq, "zoom": [1.0, 1.04], "video_inicio": round(dur_video(arq) - menos, 2), "congelar": True, "sem_look": True,
            "entrada": "fundir", "duracao_entrada": 0.5}


def peca_falada(i, arq, entra=2.1, db=-9):   # respiro: a ficha abre e o título é datilografado antes da voz
    """22/11 (usuário: "o narrador conversando a maior parte do tempo"): a peça abre, e a voz entra 'entra' s depois."""
    peca(i, arq, sobra=round(dur_video(arq) - entra, 2), db=db)


T_PLACAR = 8.45   # pecas.py: o "N DE 7" carimba aos 8,45 s; o DESCARTADA 1,1 s depois


def checklist_falado(i, arq, db=-10, inicio=None, segurar=None, ate=None):
    """A lista de conferência roda SOB a narração e o "N de 7" cai quando a fala i começa (ou, com 'inicio', a ficha
    entra na fala 'inicio' — a avaliação — e as falas de antes ficam com as cenas do filme).
    22/11 (usuário: "depois do checklist fica uma tela preta", "check list e descartar"): a peça termina no carimbo
    DESCARTADA (sem escurecer); as cenas das falas que caem DURANTE a peça vão para depois dela; 'segurar' = pausa
    (s) antes da fala seguinte para o carimbo ser visto."""
    d = dur_video(arq)
    if inicio is None:
        cands = [j for j in range(i, max(-1, i - 12), -1) if t_fala(i) - t_fala(j) <= T_PLACAR + 0.3]
        j = cands[-1]
    else:
        j = inicio
    vi = round(min(1.2, max(0.0, T_PLACAR - (t_fala(i) - t_fala(j)))), 2) if inicio is None else 0.0
    C(j, {"video": arq, "zoom": [1.0, 1.0], "tipo_cartao": True, "congelar": True, "sem_look": True, "entrada": "fundir",
          "duracao_entrada": 0.4, **({"video_inicio": vi} if vi else {})})
    for k in range(j + 1, i + 1):
        batidas[k].pop("cena", None); batidas[k].pop("cenas", None)
        batidas[k]["sons"] = [x for x in batidas[k].get("sons", []) if not x.get("_il")]   # sem efeito sob a ficha
    fx(j, None, Path(som_de(arq)).stem, db, arquivo=som_de(arq))
    fim_peca = t_fala(j) + d - vi
    movidas = []
    k = i + 1
    while k < len(falas) and t_fala(k) < fim_peca - 0.3 and not ANTES.get(k) and (ate is None or k < ate):
        movidas += cenas_de(batidas[k]); batidas[k].pop("cena", None); batidas[k].pop("cenas", None)
        batidas[k]["sons"] = [x for x in batidas[k].get("sons", []) if not x.get("_il")]; k += 1
    if movidas and k < len(falas) and not cenas_de(batidas[k]) and not ANTES.get(k):
        C(k, movidas[-1])
    if segurar:
        pausa(ate if ate is not None else k, segurar)
    GOLPES.append(i)
    return j


# ================================================================ GANCHO
fala_filme(0, "g_boanoite")                  # a cena continua rolando sob a 1ª frase
fala_filme(1, "g_coracao")
C(I("O filme dá um nome"), F("b_porta_azul"))
C(I("Mas em nenhum momento"), F("b_espelho"))
# 23/11 (retenção): prévia do caso real no gancho — o motivo concreto para ficar até a metade
C(I("Em mil oitocentos e noventa e cinco, na Irlanda"), real("cleary_sun_1895", (1.0, 1.1), foco=((0.5, 0.25), (0.5, 0.32))))
C(I("Essa história é real"), img("imagens/IA02_lareira_2", (1.0, 1.08), ((0.4, 0.55), (0.45, 0.6))))
peca(I("Bem-vindo de volta"), "identidade/abertura_v2.mp4", sobra=4.0, db=-7)   # a voz entra quando o carimbo assenta
# ================================================================ O VIGIA APRESENTA
C(I("Bem-vindo de volta"), vigia())
# 23/11 (retenção): a apresentação virou UMA frase (ficha técnica, livro e bilheteria esfriavam os primeiros 40 s)
k = I("Outra Mamãe, de dois mil e vinte e seis"); C(k, ficha("OUTRA MAMÃE · 2026\nCRÍTICA: 17% · ESTREIA: US$ 45 milhões", "17%"))
k = I("E repara na frase"); C(k, ficha("\"UMA CHANCE DE SER HUMANO.\nO MILAGRE QUE CONFUNDIMOS\nCOM ALGO CORRIQUEIRO.\"\n— a frase que abre o filme", "UMA CHANCE DE SER HUMANO")); falada(k)
C(I("Guarda essa frase"), vigia((1.0, 1.05)))
C(I("Guarda essas sete"), vigia((1.02, 1.08), ((0.55, 0.48), (0.56, 0.45))))   # 23/11: a promessa, olho no olho
# ================================================================ AS PISTAS
for n, txt in enumerate(("Pista um.", "Pista dois.", "Pista três.", "Pista quatro.", "Pista cinco.", "Pista seis.", "Pista sete."), 1):
    peca_falada(I(txt), f"{PC}pista{n}.mp4")
fala_filme(I("Ela nunca entra à força"), "p1_coracao")
fala_filme(I("Até a médium"), "p1_medium")
C(I("Primeiro ela vira a mãe"), F("p2_almoco")); C(I("A mãe que nunca está"), F("b_cozinha"))
fala_filme(I("Depois o babá"), "p2_kelvin")
C(I("Ela cresce, encolhe"), F("b_mesa")); C(I("E Bela diz onde ela mora"), F("b_quarto_portas"))
C(I("Ela não aparece numa casa feliz"), F("p4_segredos")); C(I("Aparece numa casa"), F("b_pais_briga"))
fala_filme(I("Bela faz um pedido"), "p5_frank")
k = I("Ela não quer só a menina"); fala_filme(k, "p6_pessoa"); fala_filme(k, "p6_existir")
k = I("E Bela diz com todas as letras"); fala_filme(k, "p7_trocar"); fala_filme(k, "p7_eu")
C(I("Sete pistas."), F("b_outra_rosto"))
# ================================================================ TEORIA 1 — o duplo
k = I("A primeira teoria"); peca_falada(k, f"{PC}teoria1.mp4")   # 22/11: o p2_almoco entrava só 0.7 s antes da ficha
k = I("Na Irlanda, ela tem nome"); C(k, ficha("FETCH (Irlanda) · DOPPELGÄNGER (Alemanha)\no duplo de uma pessoa viva", "o duplo")); falada(k, k + 1)
C(I("Igual a ela"), F("b_carro_outra"))
C(I("Se vê à noite"), F("b_bela_cama"))
k = I("O duplo copia.")   # 22/11: a ficha entra na avaliação e termina com DESCARTADA (as cenas do filme ficam antes)
checklist_falado(k, f"{PC}checklist1.mp4", inicio=k, ate=I("Há quatro mil anos"), segurar=1.8)
# ================================================================ TEORIA 2 — o demônio trapaceiro
k = I("Há quatro mil anos"); peca_falada(k, f"{PC}teoria2.mp4")
C(k, real("lamashtu_bm") if tem_real("lamashtu_bm") else ficha("LAMASHTU · Mesopotâmia\no demônio que roubava recém-nascidos", "LAMASHTU"))
C(I("Séculos depois, no folclore judaico"), real("amuleto_mae_bebe_wellcome", (1.0, 1.06)))
fala_filme(I("E o próprio filme aposta"), "t3_ardiloso")
C(I("E existe uma regra muito antiga"), F("b_porta_azul"), (F("b_maos_porta"), "atravessam"))   # a fala é mais longa que o clipe
C(I("Só que o ritual da médium"), F("b_ritual_sal")); C(I("Só faz a coisa aparecer"), F("b_uv"))
k = I("O demônio explica a permissão, as cópias, o corpo")   # 22/11: o ritual com cenas do filme; a ficha só na avaliação
checklist_falado(k, f"{PC}checklist2.mp4", inicio=k, ate=I("Em mil novecentos e vinte e nove"), segurar=2.8)
# ================================================================ TEORIA 3 — a tulpa
k = I("Em mil novecentos e vinte e nove"); peca_falada(k, f"{PC}teoria3.mp4")
C(k, ficha("ALEXANDRA DAVID-NÉEL · 1929\nMystiques et magiciens du Tibet\nTULPA: um ser criado pela mente", "TULPA")); falada(k, k + 2)
C(I("Um monge baixinho"), F("b_rasteja"))
C(I("E a Outra Mamãe parece uma tulpa"), F("t4_imaginaria")); C(I("Nasceu numa menina sozinha"), F("b_bela_sozinha"))
checklist_falado(I("Seis de sete."), f"{PC}checklist3.mp4", ate=I("Antes da última teoria"))
C(I("Só não explica uma coisa"), (F("b_familia"), "tulpa"))   # 22/11: o filme volta logo depois do DESCARTADA
# ================================================================ OS PARENTES (22/11, usuário: "não dá pra saber se é uma teoria ou várias")
# r7: as falas das fichas estão NA narração (mesma leitura do TTS) — antes eram gravações à parte e a voz mudava
k = I("Antes da última teoria"); C(k, ficha("ANTES DA ÚLTIMA TEORIA:\nDOIS PARENTES DA OUTRA MAMÃE\n1 · NA LITERATURA", "DOIS PARENTES"))
falada(k, k + 2)
k = I("O segundo parente vem da medicina"); C(k, ficha("2 · NA MEDICINA", "NA MEDICINA")); falada(k)
# ================================================================ A AVÓ DE CORALINE
C(I("Em mil oitocentos e oitenta e dois"), real("new_mother_n23", (1.0, 1.05)))
C(I("No lugar dela, chega"), real("new_mother_n26", (1.0, 1.07)))
k = I("Cento e vinte anos depois"); C(k, ficha("THE NEW MOTHER (1882) → CORALINE (2002) → OUTRA MAMÃE (2026)", "OUTRA MAMÃE")); falada(k)
C(I("E Outra Mamãe é a neta"), F("b_outra_rosto"))
# ================================================================ A CIÊNCIA — Capgras
k = I("Em mil novecentos e vinte e três"); C(k, ficha("SÍNDROME DE CAPGRAS\nJoseph Capgras · 1923\n\"o meu parente foi trocado por um sósia\"", "CAPGRAS")); falada(k)
C(I("Hoje sabemos"), img("imagens/IA03_retrato_1", (1.0, 1.08), ((0.55, 0.45), (0.6, 0.42))))
C(I("Mas não sente mais nada"), F("b_praca"))
fala_filme(I("O medo do filme existe"), "capgras")
# ================================================================ AS FADAS DE VERDADE (contexto antes da teoria 4)
C(I("E agora, a última teoria"), vigia((1.0, 1.05)))   # 22/11: o b_rosto_final piscava 2.4 s; o Vigia conversa direto
C(I("No folclore da Irlanda e da Escócia"), real("fussli_changeling", (1.08, 1.16), foco=((0.4, 0.4), (0.42, 0.36))))
C(I("Elas roubavam o leite"), img("imagens/IA01_berco_2", (1.0, 1.07), ((0.6, 0.5), (0.62, 0.52))))
C(I("É por isso que ela entra"), F("b_maos_porta"))
# ================================================================ TEORIA 4 — a fada que troca
k = I("Na Irlanda, na Escócia e na Escandinávia"); peca_falada(k, f"{PC}teoria4.mp4"); C(k, real("fussli_changeling", (1.0, 1.06)))
k = I("Os irlandeses chamavam essa cópia"); C(k, ficha("CHANGELING (Irlanda) · BORTBYTING (Suécia)\n\"o trocado\"", "o trocado")); falada(k, k + 1)
C(I("O trocado."), real("fussli_changeling", (1.06, 1.12), foco=((0.45, 0.6), (0.5, 0.62))))
C(I("E por que as fadas queriam"), img("imagens/IA01_berco_1", (1.0, 1.08), ((0.3, 0.6), (0.28, 0.62))))
C(I("E elas viviam do outro lado"), F("b_outro_lado"))
C(I("Mas tem um detalhe"), F("b_ritual_sal"))
C(I("Uma porta aberta"), F("b_porta_azul"))
checklist_falado(I("Sete de sete."), f"{PC}checklist4.mp4")
C(I("Mas, em mil oitocentos e noventa e cinco"), real("cleary_sun_1895", (1.0, 1.05)))
# ================================================================ O CASO REAL — Bridget Cleary
k = I("Ballyvadlea"); C(k, ficha("BRIDGET CLEARY · 26 anos\nBallyvadlea, Tipperary, Irlanda · março de 1895", "BRIDGET CLEARY")); falada(k, k + 2)
C(I("O marido dela, Michael"), real("cleary_sun_1895", (1.05, 1.14), foco=((0.5, 0.3), (0.5, 0.36))))
C(I("Durante noites seguidas"), img("imagens/IA02_lareira_1", (1.0, 1.07), ((0.4, 0.6), (0.38, 0.62))))
C(I("Está registrado assim"), real("cleary_sun_1895", (1.1, 1.2), foco=((0.5, 0.55), (0.5, 0.62))))   # 22/11: 26 s na mesma lareira
C(I("Na noite de quinze de março"), img("imagens/IA02_lareira_1", (1.1, 1.18), ((0.55, 0.65), (0.6, 0.62))))
C(I("Na frente da família"), img("imagens/IA02_lareira_2", (1.0, 1.08), ((0.35, 0.6), (0.33, 0.62))))
C(I("Michael foi condenado"), img("imagens/IA02_lareira_1", (1.08, 1.14), ((0.6, 0.5), (0.62, 0.48))))
fala_filme(I("É Outra Mamãe ao contrário"), "caso_cheiro")
C(I("Em mil oitocentos e noventa e cinco, o marido"), F("b_pais_briga"))
# ================================================================ SPOILER
SPOILER_I = I("No meio do filme")
k = I("Atenção: a partir daqui")   # r7: o aviso é lido na própria narração, sobre a peça (sem legenda: está na tela)
peca_falada(k, f"{PC}spoiler.mp4", entra=1.2); falada(k, k + 1)
C(SPOILER_I, F("s_afundou"))
fala_filme(I("Para ver o mar"), "s_mar")
C(I("Na casa da avó Ruth"), F("b_avo"))
fala_filme(I("E a médium deixa"), "s_inocencia")
C(I("No terço final"), F("s_confissao")); C(I("Conta que Russ"), F("b_cicatriz"))
fala_filme(I("A menina sobe correndo"), "s_sim")
fala_filme(I("Mas no último segundo"), "s_nao")
C(I("Aceita ser humana"), F("s_avo")); C(I("E escolhe"), F("b_familia_fim"))
fala_filme(I("A criatura vai embora"), "s_pensar")
C(I("E no último discurso"), F("s_escola"))
C(I("E depois dos créditos"), F("pos_creditos"))
# ================================================================ LIVRO × FILME
k = I("No livro de Josh Malerman"); C(k, ficha("INCIDENTS AROUND THE HOUSE\nJosh Malerman · 2024\nO LIVRO", "O LIVRO")); falada(k)
C(I("Ela diz para a menina"), quarto(1))
C(I("Só que, no livro"), img("imagens/IA04_corredor_1", (1.0, 1.1), ((0.5, 0.5), (0.5, 0.48))))
C(I("Sozinha, ela diz sim"), img("imagens/IA04_corredor_2", (1.0, 1.1), ((0.5, 0.5), (0.5, 0.48))))
k = I("No livro, a criatura vence"); C(k, ficha("NO LIVRO, A CRIATURA VENCE\nNO FILME, A MENINA VENCE", "A MENINA VENCE"))
falada(k, k + 1)
C(I("Dois finais opostos"), F("b_quarto_portas"))
# ================================================================ O VEREDITO
k = I("Agora junta tudo"); peca_falada(k, f"{PC}placar.mp4", entra=1.0)
C(k + 1, F("b_outro_lado")); C(k + 2, F("b_familia_fim"))
C(I("O duplo cai primeiro"), congelado(f"{PC}placar.mp4")); C(I("O demônio explica a permissão e as cópias, mas"), F("b_uv"))
C(I("A tulpa chega muito perto"), F("t4_imaginaria")); C(I("Só uma teoria explica"), congelado(f"{PC}placar.mp4"))
peca(I("O meu veredito"), f"{PC}veredito.mp4", sobra=3.0)   # silêncio com motivo: o carimbo bate, e a voz entra
# ================================================================ POR QUE A FADA TROCADORA
PROVAS = [I(t) for t in ("Prova um.", "Prova dois.", "Prova três.", "Prova quatro.", "Prova cinco.", "Prova seis.",
                         "Prova sete.", "Prova oito.", "Prova nove.")]
DEPOIS = [  # (cena logo depois da prova, mais cenas) — o filme dá peso a cada prova
    (F("b_ritual_sal"), {"A médium disse a regra": F("b_medium")}),
    (F("b_cozinha"), {"A mãe, o babá": F("b_outro_lado")}),
    (F("b_mesa"), {"\"Ela mora atrás": F("b_maos_porta")}),
    (F("b_praca"), {"Foi assim com Bridget": real("cleary_sun_1895"), "A brecha não é a porta": F("b_pais_briga")}),
    (F("b_frank_fim"), {}),
    (F("b_abraco"), {"Nas lendas, o povo": ilustr("outra_silhueta")}),
    (F("b_carro_outra"), {"No livro, a troca": F("b_espelho")}),
    (F("b_tunel"), {"A Outra Mamãe afunda": F("b_bolinhas")}),
    (F("b_rosto_final"), {"Quando Bela aceita": F("b_familia_fim")}),
]
C(I("E eu não vou te deixar"), vigia())
PORQUE = f"{PC}porque.mp4"
for k, i in enumerate(PROVAS):   # a ficha da fada volta a cada prova e marca a linha da vez (porquê.mp4: marca k em 3+6k s)
    C(i, {"video": PORQUE, "zoom": [1.0, 1.0], "video_inicio": round(1.0 + 6 * k, 2), "sem_look": True, "entrada": "fundir",
          "duracao_entrada": 0.5})
    C(i + 1, DEPOIS[k][0])
    for txt, c in DEPOIS[k][1].items():
        C(I(txt, i), c)
    # 22/11 (usuário): sem rabisco nas provas — a narração, a cena e a música bastam; o rabisco só onde a tela escreve
C(I("A tulpa explica a solidão"), F("b_bela_sozinha"))
C(I("Mas uma tulpa nasce de alguém e some"), F("b_rasteja"))
C(I("Uma fada, sim"), vigia())
# ================================================================ O FECHO
C(I("A Outra Mamãe é a fada trocadora"), vigia((1.0, 1.05)))
C(I("Ela não arromba"), F("b_quarto_portas"))
C(I("Espera uma família"), F("b_cicatriz"))
C(I("E depois dos créditos", I("Ela não arromba")), F("pos_creditos"))
C(I("Enquanto uma família"), vigia((1.0, 1.06)))

for _i, _n in FALAS_FILME:   # 23/11: o filme corta no fim da fala — a narração segue sobre a ilustração (antes: 12 s de filme)
    if not cenas_de(batidas[_i]):
        C(_i, ilustr(RABO[_n]))

montar_antes()

TRILHA_SOM = "cin01_trilha"
roteiro = {
    "modo": "cenas", "formato": "16:9", "tema": "vigia", "avatar": "vigia_hd",
    "voz_arquivo": "audio/voz_com_vinheta_limpa.wav",
    "transcrever_pedacos": 75,
    "alinhamento_forcado": True,
    "look": {"preset": "noite_fria", "forca": 0.7, "halacao": 0.25},
    "cintilar": 0.03, "apertar_pausas": False, "digitacao_db": -23,
    "cena_minima": 4.0,
    "vigia_padrao": False,
    "cauda": 1.6, "chuva": 0, "grao": 0.12,
    "mix": {"musica_ganho_db": 12, "fundo_sob_voz": -8, "efeitos_sob_voz": -4, "voz_pro": True, "fundo_bolso": True,
            "efeitos_pico_max": -3},
    "legendas": {"destaques": ["Outra Mamãe", "changeling", "fada trocadora", "Bridget Cleary", "fetch", "doppelgänger",
                               "Lamashtu", "Lilith", "tulpa", "Capgras", "Coraline", "permissão", "trocar de lugar", "veredito"]},
    "musica": {"som": TRILHA_SOM, "volume_db": -13},
    "cta": {"titulo": "Não deixe ela entrar.", "canal": "Último Abrigo",
            "subtitulo": "Inscreva-se para mais arquivos do Vigia",
            "fundo": "../../painel/cenarios/abrigo_16x9.png", "pose": "c_cafe_convite",
            "antes": 0.6, "clique_em": "Inscreva-se", "duracao": 16.0, "escurecer": 0.9},
    "batidas": batidas,
}


_ali = json.load(open(ALI))
sys.path.insert(0, str(AQUI.parents[1] / "painel"))
from gerar import tokens as _tok  # noqa: E402
_ini = [sum(len(_tok(f)) for f in falas[:j]) for j in range(len(falas))]


def cenas_de(b):
    return ([b["cena"]] if b.get("cena") else []) + b.get("cenas", [])


for b in batidas:  # tela de texto não leva legenda (o texto já está na tela)
    for c in cenas_de(b):
        if c.get("tipo") == "texto" and "em" not in c and not c.get("parada") and not c.get("antecipar"):   # 22/11: ficha ANTES da fala (lida na pausa) não tira a legenda da fala
            b["sem_legenda"] = True
arqs = set()
for b in batidas:
    for c in cenas_de(b):
        for k in ("imagem", "video"):
            if c.get(k):
                arqs.add(c[k])
        for m in c.get("mensagens", []):
            if m.get("imagem"):
                arqs.add(m["imagem"])
        for l in c.get("lados", []):
            if l.get("imagem"):
                arqs.add(l["imagem"])
faltando = sorted(a for a in arqs if not (AQUI / a).exists())
if faltando and not __import__("os").environ.get("TESTE"):
    raise SystemExit("arquivos faltando: " + ", ".join(faltando))
sons_dir = AQUI.parents[1] / "painel" / "sons"
sons = {s["som"] for b in batidas for s in b.get("sons", []) if not s.get("arquivo")} | {b[k]["som"] for b in batidas for k in ("ambiente", "musica") if b.get(k)}
sem_som = sorted(s for s in sons if s not in ("nenhum", TRILHA_SOM) and not list(sons_dir.glob(s + ".*")))
if sem_som and not __import__("os").environ.get("TESTE"):
    raise SystemExit("sons faltando: " + ", ".join(sem_som))


def garantir_leitura():
    """Tela de texto: depois de digitada fica >= 1,5 s + 0,3 s por palavra. O que faltar entra como pausa na fala seguinte."""
    sys.path.insert(0, str(AQUI.parents[1] / "painel"))
    from gerar import tokens
    tempos = json.load(open(ALI))
    k, ini = 0, []
    for b in batidas:
        n = len(tokens(b["fala"])); ini.append(tempos[k][0]); k += n
    mudou = []
    for i, b in enumerate(batidas[:-1]):
        cs = cenas_de(b)
        if not cs or cs[-1].get("tipo") != "texto":
            continue
        c, prox = cs[-1], batidas[i + 1]
        if c.get("falada"):
            continue
        t1 = ini[i + 1] + prox.get("pausa_antes_s", 0) - (cenas_de(prox)[0].get("antecipar", 0) if cenas_de(prox) else 0)
        sobra = (t1 - ini[i]) - len(c["texto"]) / c.get("cps", 40)
        falta = 1.5 + 0.3 * len(c["texto"].split()) - sobra
        if falta > -0.45:   # 15/11: no máximo 1,2 s a mais (a narração continua por cima do texto)
            prox["pausa_antes_s"] = round(prox.get("pausa_antes_s", 0) + min(1.2, falta + 0.6), 2); mudou.append((i, round(falta, 1)))
    print("pausas aumentadas para dar tempo de leitura (fala, s):", mudou)


def aplicar_ajuste_pausas():
    arq = AQUI / "audio" / "ajuste_pausas.json"
    for k, d in (json.load(open(arq)) if arq.exists() else {}).items():
        if int(k) in (87, 123):   # respiros da trilha: não são compensação
            continue
        b = batidas[int(k)]
        if b.get("pausa_antes_s"):
            b["pausa_antes_s"] = round(max(0.3, b["pausa_antes_s"] + d), 2)


def ritmo():
    """13/11 (pedido do usuário): ritmo contínuo, nada de corte rápido nem troca no meio da frase.
    - cena comum fica >= 3,6 s; cena com kanji/linha do tempo fica >= 6,5 s depois que o kanji aparece;
    - se a frase seguinte é curta e a cena dela é uma imagem comum, ela CONTINUA a anterior (sem cortar);
    - se não dá pra continuar (tela de conversa, Vigia, vídeo...), a pausa antes dela cresce (até 2,5 s);
    - toda troca é uma fusão curta que termina ANTES da voz (a legenda nunca chega antes da imagem)."""
    from gerar import tokens as tk, norm
    t_ini = [_ali[_ini[i]][0] for i in range(len(falas))]

    def dur(i):
        return t_ini[i + 1] - t_ini[i] + batidas[i + 1].get("pausa_antes_s", 0) if i + 1 < len(falas) else 4.0

    def t_palavra(i, palavra):
        ws = [norm(w) for w in tk(falas[i])]
        alvo = norm(palavra)
        k = next((j for j, w in enumerate(ws) if w == alvo or w.startswith(alvo)), 0)
        return _ali[_ini[i] + k][0] - t_ini[i]

    def precisa(b, i):
        cs = cenas_de(b); n = 4.0   # 17/11: menos frases "continuando" a imagem anterior (imagem sempre no momento da frase)
        for c in cs:
            ks = c.get("kanji") or []
            ks = ks if isinstance(ks, list) else [ks]
            for K in ks:
                off = t_palavra(i, K["em"]) if K.get("em") else K.get("atraso", 0.5)
                n = max(n, off + (5.0 if K.get("legenda") or len(K.get("texto", "")) > 1 else 3.5))
            if c.get("linha"):
                n = max(n, 6.5)
            if c.get("tipo") == "texto":
                n = max(n, 4.0)
        return n

    def comum(b):
        cs = cenas_de(b)
        return len(cs) == 1 and not any(c.get(k) for c in cs for k in ("tipo", "vigia", "video", "celular", "kanji", "linha", "dof", "_c3d",
                                                                       "zoom_digital", "entrada"))
    def tipo_de(b):
        c = cenas_de(b)[0]
        return "vigia" if c.get("vigia") else c.get("tipo") or "imagem"

    PROTEGE = set(ANTES) | set(PROVAS) | {p + 1 for p in PROVAS}   # sustos e silêncios: nunca continuar a anterior
    continuadas, alongadas = [], []
    acc, falta = 0.0, 0.0
    for i, b in enumerate(batidas[:len(falas)]):
        if i == 0:
            acc, falta = dur(0), precisa(b, 0); continue
        if not cenas_de(b):
            acc += dur(i); continue
        tipo_ant = next((tipo_de(batidas[j]) for j in range(i - 1, -1, -1) if cenas_de(batidas[j])), None)
        if tipo_de(b) in ("chat", "vigia", "mapa") and tipo_de(b) == tipo_ant and not any(c.get("kanji") for c in cenas_de(b)):
            acc += dur(i); continue                   # mesma tela (conversa→conversa, Vigia→Vigia): não é corte
        if acc < falta and comum(b) and i not in PROTEGE:
            b.pop("cena", None); b.pop("cenas", None); continuadas.append(i); acc += dur(i); continue
        if acc < falta:
            extra = round(min(1.2, falta - acc), 2)   # 15/11: pausa longa sem nada acontecendo parece erro; b["pausa_antes_s"] = round(b.get("pausa_antes_s", 0) + extra, 2); alongadas.append((i, extra))
        acc, falta = dur(i), precisa(b, i)
    # fusões que terminam antes da voz
    for i, b in enumerate(batidas[1:len(falas)], 1):
        cs = cenas_de(b)
        if not cs:
            continue
        c = cs[0]
        if c.get("tipo") in ("capitulo", "talisma") or c.get("tipo_cartao") or c.get("entrada") == "corte" or c.pop("antecipar_fixo", False):
            continue
        ant = next((cenas_de(batidas[j]) for j in range(i - 1, -1, -1) if cenas_de(batidas[j])), [{}])[-1]
        if c.get("tipo") == "chat" and ant.get("tipo") == "chat":
            c["entrada"] = "corte"; continue          # conversa → conversa: a tela é a mesma
        padrao = {"nanquim": 1.3, "shoji": 0.9, "vela": 1.6, "queimar": 1.5, "rasgo": 0.9, "hanji": 1.2, "obturador": 0.55}.get(c.get("entrada"), 0.6)
        c.setdefault("entrada", "fundir"); c.setdefault("duracao_entrada", padrao)
        c["antecipar"] = round(min(c["duracao_entrada"], b.get("pausa_antes_s", 0) + 0.25), 2)
    print("frases que continuam a imagem anterior:", continuadas)
    print("pausas alongadas para o kanji/cena respirar (fala, s):", alongadas)


for _b in batidas:                                   # rascunho 1: tira TODO foco redondo (dof) das imagens
    for _c in cenas_de(_b):
        _c.pop("dof", None)

FICHA_L = {}


def fichas_paradas():
    """17/11 (usuário: "quando aparece a tela com descrição, tem que estar parado… calcula o tempo que a pessoa vai
    demorar para ler… com o barulho do teclado"): a FICHA entra numa pausa SÓ DELA — a narração para, a máquina de
    escrever digita, a tela fica o tempo de leitura e só então a voz volta, já sobre a imagem da frase."""
    from gerar import tokens as tk
    feitas = []
    for i, b in enumerate(batidas[:len(falas)]):
        cs = cenas_de(b)
        if len(cs) != 1 or cs[0].get("tipo") != "texto" or cs[0].get("em") or cs[0].get("falada"):
            continue
        f = dict(cs[0]); txt = f["texto"]
        L = round(0.3 + len(txt) / f.get("cps", 40) + 1.8 + 0.32 * len(txt.split()), 1)
        f.update({"antecipar": L, "antecipar_fixo": True, "entrada": "corte", "parada": True})
        ant = next((cenas_de(batidas[j])[-1] for j in range(i - 1, -1, -1) if cenas_de(batidas[j]) and
                    cenas_de(batidas[j])[-1].get("tipo") != "texto"), None)
        depois = {k: v for k, v in (ant or {}).items() if k not in ("em", "antecipar", "antecipar_fixo", "entrada", "duracao_entrada")}
        depois["em"] = tk(falas[i])[0]; depois["entrada"] = "fundir"; depois["duracao_entrada"] = 0.6
        b.pop("cena", None); b["cenas"] = [f, depois]
        pausa(i, L); feitas.append((i, L)); FICHA_L[i] = L
    print("fichas paradas (fala, s de leitura):", feitas)


fichas_paradas()
for _j in SEM_LEG:
    batidas[_j]["sem_legenda"] = True
ritmo()
garantir_leitura()
aplicar_ajuste_pausas()


def camera_3d():
    """Gera os vídeos da câmera 3D com a duração real de cada cena (até a próxima cena + margem da transição)."""
    sys.path.insert(0, str(AQUI.parents[1] / "painel" / "ferramentas"))
    import camera3d
    from gerar import tokens as tk, norm
    cum, T0 = 0.0, []
    for i in range(len(falas)):
        cum += batidas[i].get("pausa_antes_s", 0); T0.append(_ali[_ini[i]][0] + cum)
    inicios = []                                       # (tempo de início, cena) na ordem do vídeo
    for i, b in enumerate(batidas[:len(falas)]):
        for c in cenas_de(b):
            t = T0[i] - c.get("antecipar", 0)
            if c.get("em"):
                ws = [norm(w) for w in tk(falas[i])]; alvo = norm(c["em"])
                k = next((j for j, w in enumerate(ws) if w == alvo or w.startswith(alvo)), 0)
                t = T0[i] + _ali[_ini[i] + k][0] - _ali[_ini[i]][0]
            inicios.append((t, c))
    feitos = 0
    for k, (t, c) in enumerate(inicios):
        if "_c3d" not in c:
            continue
        p = c.pop("_c3d")
        if __import__("os").environ.get("SEM_3D"):        # teste rápido: fica a imagem parada com zoom leve
            c["zoom"] = [1.0, 1.06]; continue
        fim = inicios[k + 1][0] if k + 1 < len(inicios) else t + 20   # a última cena segue por baixo da vinheta falada
        dur = round(max(4.0, fim - t) + 2.5, 1)
        chave = hashlib.md5(json.dumps([c["imagem"], p], sort_keys=True).encode()).hexdigest()[:10]
        # reaproveita um vídeo do mesmo movimento se a duração for parecida (até 3 s mais longo): o motor usa só o começo
        prontos = sorted((float(f.stem.rsplit("_", 1)[1]), f) for f in C3D.glob(f"{Path(c['imagem']).stem}_{chave}_*.mp4"))
        arq = next((f for d_, f in prontos if dur <= d_ <= dur + 3.0), C3D / f"{Path(c['imagem']).stem}_{chave}_{dur}.mp4")
        if not arq.exists():
            camera3d.gerar(AQUI / c["imagem"], arq, dur, p["mov"], tuple(p["foco"]), p["forca"], p["desfoque"]); feitos += 1
        c["video"] = str(arq.relative_to(AQUI)); c.pop("imagem", None)
        c.pop("dof", None)                             # o foco de lente já está no próprio vídeo
    print("câmera 3D:", sum(1 for _, c in inicios if str(c.get("video", "")).startswith("camera3d")), "cenas,", feitos, "geradas agora")


def trilha_por_secoes():
    """A trilha (trilha/compor.py episodio) composta sobre os tempos desta montagem: cada seção com o seu motivo, a música
    desce 9 dB nas falas do filme e o veredito cai no carimbo. Só recompõe quando o plano muda."""
    cum, T0 = 0.0, []
    for i in range(len(falas)):
        cum += batidas[i].get("pausa_antes_s", 0); T0.append(_ali[_ini[i]][0] + cum)
    fim = _ali[-1][1] + cum + 24
    nomes = [("gancho", "GANCHO"), ("apresenta", "O VIGIA APRESENTA"), ("pistas", "AS PISTAS (sem spoiler)"),
             ("duplo", "TEORIA 1 — O DUPLO"), ("demonio", "TEORIA 2 — O DEMÔNIO TRAPACEIRO"),
             ("tulpa", "TEORIA 3 — UMA COISA CRIADA PELO DESEJO"), ("avo", "A AVÓ DE CORALINE"),
             ("capgras", "A CIÊNCIA — A SÍNDROME DE CAPGRAS"), ("fada", "AS FADAS DE VERDADE"),
             ("fada", "TEORIA 4 — UMA FADA QUE TROCA PESSOAS"), ("cleary", "O CASO REAL — BRIDGET CLEARY, 1895"),
             ("spoiler", "⚠️ SPOILER — O FINAL EXPLICADO"),
             ("livro", "LIVRO × FILME — OS DOIS FINAIS"), ("veredito", "O VEREDITO"), ("porque", "POR QUE A FADA TROCADORA"),
             ("fecho", "O FECHO")]
    ini = [0.0] + [T0[SEC[s]] - batidas[SEC[s]].get("pausa_antes_s", 0) for _, s in nomes[1:]]
    secoes = [[n, round(ini[k], 2), round(ini[k + 1] if k + 1 < len(ini) else fim, 2)] for k, (n, _) in enumerate(nomes)]
    furos = [[round(T0[i] + a, 2), round(T0[i] + b, 2)] for i, a, b in FUROS]
    plano = {"secoes": secoes, "fim": round(fim, 2), "furos": furos, "veredito": round(T0[I("O meu veredito")] - 1.0, 2)}
    sons = AQUI.parents[1] / "painel" / "sons"
    marca = sons / f"{TRILHA_SOM}.plano"; txt = json.dumps(plano)
    if (sons / f"{TRILHA_SOM}.mp3").exists() and marca.exists() and marca.read_text() == txt:
        return T0
    print("trilha: compondo", flush=True)
    (AQUI / "trilha" / "plano.json").write_text(txt)
    subprocess.run([sys.executable, str(AQUI / "trilha" / "compor.py"), "episodio", str(AQUI / "trilha" / "plano.json"),
                    str(sons / f"{TRILHA_SOM}.mp3")], check=True)
    marca.write_text(txt)
    return T0


T0 = trilha_por_secoes()
_m, _s = divmod(int(T0[SEC["LIVRO × FILME — OS DOIS FINAIS"]] - 3), 60)
_pular = f"{_m}:{_s:02d}"
_sp = AQUI / PC / "spoiler.txt"
if not (AQUI / PC / "spoiler.mp4").exists() or not _sp.exists() or _sp.read_text() != _pular:
    print("spoiler: pule para", _pular, "— renderizando a peça", flush=True)
    if not __import__("os").environ.get("TESTE"):
        subprocess.run([sys.executable, "pecas.py", "spoiler", f"pecas/v6/spoiler.mp4", _pular], cwd=AQUI / "identidade", check=True)
        _sp.write_text(_pular)


camera_3d()


def conferir_clipes():
    import subprocess as sp
    from gerar import tokens as tk, norm
    cum, T0 = 0.0, []
    for i in range(len(falas)):
        cum += batidas[i].get("pausa_antes_s", 0); T0.append(_ali[_ini[i]][0] + cum)
    ini = []
    for i, b in enumerate(batidas[:len(falas)]):
        for c in cenas_de(b):
            t = T0[i] - c.get("antecipar", 0)
            if c.get("em"):
                ws = [norm(w) for w in tk(falas[i])]; alvo = norm(c["em"])
                k = next((j for j, w in enumerate(ws) if w == alvo or w.startswith(alvo)), 0)
                t = T0[i] + _ali[_ini[i] + k][0] - _ali[_ini[i]][0]
            ini.append((t, i, c))
    for k, (t, i, c) in enumerate(ini):
        v = str(c.get("video", ""))
        if not v or v.startswith("camera3d") or not (AQUI / v).exists():
            continue
        if c.get("congelar") and not v.startswith(FP):
            continue   # peça congelada: o último quadro segura de propósito
        fim = ini[k + 1][0] if k + 1 < len(ini) else t + 6
        d = float(sp.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(AQUI / v)],
                         capture_output=True, text=True).stdout) - float(c.get("video_inicio", 0))
        if d / float(c.get("velocidade", 1)) < (fim - t) + 1.2:
            print(f"!! CLIPE CURTO fala {i}: {Path(v).name} tem {d:.1f}s, a cena pede {(fim - t) + 1.2:.1f}s — o filme para "
                  f"{(fim - t) + 1.2 - d:.1f}s")


conferir_clipes()
sem = [i for i, b in enumerate(batidas) if not cenas_de(b)]
for _b in batidas:   # 22/11 (usuário: "a narração muda, a voz sai diferente e com volume diferente"): as falas extras do
    for _so in _b.get("sons", []):   # Vigia entram na trilha da VOZ (mesma cadeia de locução), não como efeito
        if "/audio/extras/" in str(_so.get("arquivo", "")):
            _so["na_voz"] = True; _so["volume_db"] = 0
(AQUI / "roteiro.json").write_text(json.dumps(roteiro, ensure_ascii=False, indent=1), encoding="utf-8")
n_cenas = sum(len(cenas_de(b)) for b in batidas)
print(f"{len(batidas)} falas, {n_cenas} cenas, falas sem cena (continuam a anterior): {sem}")
print("pausa total:", round(sum(b.get("pausa_antes_s", 0) for b in batidas), 1), "s")
