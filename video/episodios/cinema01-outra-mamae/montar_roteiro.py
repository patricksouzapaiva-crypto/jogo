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
import subprocess
import sys
from pathlib import Path

import falas as F

AQUI = Path(__file__).parent
falas, SEC, DIREC, _ = F.ler()
assert len(falas) == 231 and falas[180].startswith("Prova um"), "o ROTEIRO.md mudou: rever os índices"
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


def C(i, *cenas, com_vigia=False):
    b = batidas[i]; lista = []
    for x in cenas:
        c, em = (x if isinstance(x, tuple) else (x, None))
        c = dict(c)
        if em:
            c["em"] = em
        lista.append(c)
    b.pop("cena", None); b.pop("cenas", None)
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


def antes(i, cena, dur, som=None, db=-10, furo=False, sobra=0.0):
    """Algo que toca inteiro numa pausa da voz antes da fala i (sobra = quanto a voz pode entrar antes do fim)."""
    ANTES.setdefault(i, []).append((cena, dur, som, db, furo, sobra))


def peca(i, arq, sobra=2.2, db=-9):
    """Peça do formato (vídeo com som): toca antes da fala i; a voz entra nos últimos 'sobra' s (o título já na tela)."""
    d = dur_video(arq)
    antes(i, {"video": arq, "zoom": [1.0, 1.0], "tipo_cartao": True, "congelar": True, "sem_look": True}, d, som_de(arq), db,
          sobra=sobra)
    GOLPES.append(i)


def fala_filme(i, nome, db=-4):
    """Cena 🔊: o filme fala (dublagem), a voz espera; depois a narração segue sobre o último quadro congelado."""
    d = TRECHOS[nome]["dur"]
    antes(i, filme(nome, congelar=True), d + 0.25, str(AQUI / FP / f"{nome}.wav"), db, furo=True)


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
                if itens[-1][5] > 0:
                    ws = [w.strip('.,:;!?"“”') for w in falas[i].split()]
                    k = min(len(ws) - 1, max(1, int(itens[-1][5] * 2.4)))
                    baixo = [w.lower() for w in ws]
                    while k < len(ws) - 1 and (len(baixo[k]) < 3 or any(w.startswith(baixo[k]) for w in baixo[:k])):
                        # 22/11: o motor acha a 1ª palavra que COMEÇA assim ("na" = "Na", "e" = "Em")
                        k += 1
                    r["em"] = ws[k]
            novas += [r] + resto[1:]
        batidas[i].pop("cena", None); batidas[i]["cenas"] = novas
        pausa(i, round(total + 0.35, 2))


def cenas_de(b):
    return ([b["cena"]] if b.get("cena") else []) + b.get("cenas", [])


# ================================================================ GANCHO
fala_filme(0, "g_boanoite")
C(0, quarto(1))
fala_filme(1, "g_coracao")
C(4, armario(1, foco=((0.5, 0.5), (0.5, 0.42))))
C(6, img(ID + "ID20_outra_mamae_1.png", (1.0, 1.1), ((0.5, 0.45), (0.5, 0.35))))
peca(8, "identidade/abertura_v2.mp4", sobra=0.0, db=-7)
# ================================================================ O VIGIA APRESENTA
C(8, vigia())
C(12, ficha("OUTRA MAMÃE (Other Mommy) · 2026\nDireção: Rob Savage · Produção: James Wan\nJessica Chastain", "OUTRA MAMÃE"))
C(13, vigia((1.0, 1.05)))
C(14, ficha("INCIDENTS AROUND THE HOUSE\nJosh Malerman · 2024\n(o mesmo autor de Caixa de Pássaros)", "INCIDENTS AROUND THE HOUSE"))
C(15, ficha("CRÍTICA: 17% de aprovação\nESTREIA: US$ 45 milhões", "17%"))
C(18, filme("abertura"))
C(19, vigia((1.0, 1.05)))
# ================================================================ AS PISTAS
for n, i in enumerate((22, 27, 33, 36, 39, 42, 46), 1):
    peca(i, f"{PC}pista{n}.mp4")
fala_filme(23, "p1_coracao")
fala_filme(26, "p1_medium")
C(28, filme("p2_almoco"))
fala_filme(30, "p2_kelvin")
C(34, filme("p3_grande"))
C(35, armario(2))
C(37, filme("p4_segredos"))
fala_filme(40, "p5_frank")
fala_filme(43, "p6_pessoa"); fala_filme(43, "p6_existir")
fala_filme(47, "p7_trocar"); fala_filme(47, "p7_eu")
C(48, img(ID + "ID02_quadro_1.png", (1.0, 1.06)))
# ================================================================ TEORIA 1 — a fada que troca
peca(50, f"{PC}teoria1.mp4")
C(50, real("fussli_changeling", (1.0, 1.06)))
C(52, ficha("CHANGELING (Irlanda) · BORTBYTING (Suécia)\n\"o trocado\"", "o trocado"))
C(54, real("fussli_changeling", (1.06, 1.12), foco=((0.45, 0.6), (0.5, 0.62))))
C(57, img("imagens/IA01_berco_1", (1.0, 1.08), ((0.3, 0.6), (0.28, 0.62))))
C(61, img("imagens/IA01_berco_2", (1.0, 1.07), ((0.6, 0.5), (0.62, 0.52))))
peca(70, f"{PC}checklist1.mp4")
C(72, real("cleary_sun_1895", (1.0, 1.05)))
# ================================================================ O CASO REAL — Bridget Cleary
C(74, ficha("BRIDGET CLEARY · 26 anos\nBallyvadlea, Tipperary, Irlanda · março de 1895", "BRIDGET CLEARY"))
C(76, real("cleary_sun_1895", (1.05, 1.14), foco=((0.5, 0.3), (0.5, 0.36))))
C(79, img("imagens/IA02_lareira_1", (1.0, 1.07), ((0.4, 0.6), (0.38, 0.62))))
C(83, img("imagens/IA02_lareira_2", (1.0, 1.08), ((0.35, 0.6), (0.33, 0.62))))
C(85, real("cleary_sun_1895", (1.0, 1.05)))
fala_filme(88, "caso_cheiro")
# ================================================================ TEORIA 2 — o duplo
peca(92, f"{PC}teoria2.mp4")
C(92, real("rossetti_met") if tem_real("rossetti_met") else ficha("FETCH (Irlanda) · DOPPELGÄNGER (Alemanha)\no duplo de uma pessoa viva", "o duplo"))
C(96, filme("p2_almoco", congelar=True))
peca(98, f"{PC}checklist2.mp4")
# ================================================================ TEORIA 3 — o demônio trapaceiro
peca(102, f"{PC}teoria3.mp4")
C(102, real("lamashtu_bm") if tem_real("lamashtu_bm") else ficha("LAMASHTU · Mesopotâmia\no demônio que roubava recém-nascidos", "LAMASHTU"))
C(105, real("amuleto_mae_bebe_wellcome", (1.0, 1.06)))
fala_filme(107, "t3_ardiloso")
C(111, filme("t3_ritual"))
peca(113, f"{PC}checklist3.mp4")
# ================================================================ TEORIA 4 — a tulpa
peca(116, f"{PC}teoria4.mp4")
C(116, quarto(2))
C(117, ficha("ALEXANDRA DAVID-NÉEL\nMystiques et magiciens du Tibet · 1929\nTULPA: um ser criado pela mente", "TULPA"))
C(119, armario(2))
C(121, filme("t4_imaginaria"))
peca(124, f"{PC}checklist4.mp4")
# ================================================================ TEORIA 5 — a avó de Coraline
C(127, real("new_mother_n23", (1.0, 1.05)))
C(130, real("new_mother_n26", (1.0, 1.07)))
C(133, ficha("THE NEW MOTHER (1882) → CORALINE (2002) → OUTRA MAMÃE (2026)", "OUTRA MAMÃE"))
# ================================================================ A CIÊNCIA — Capgras
C(135, ficha("SÍNDROME DE CAPGRAS\nJoseph Capgras · 1923\n\"o meu parente foi trocado por um sósia\"", "CAPGRAS"))
C(136, img("imagens/IA03_retrato_1", (1.0, 1.08), ((0.55, 0.45), (0.6, 0.42))))
C(138, img("imagens/IA03_retrato_2", (1.0, 1.08), ((0.45, 0.5), (0.45, 0.46))))
fala_filme(140, "capgras")
# ================================================================ SPOILER
SPOILER_I = 142
peca(142, f"{PC}spoiler.mp4", sobra=0.6, db=-9)
C(142, filme("s_afundou"))
fala_filme(143, "s_mar")
C(144, filme("s_ruth"))
fala_filme(145, "s_inocencia")
C(146, filme("s_confissao"))
fala_filme(149, "s_sim")
fala_filme(151, "s_nao")
C(151, filme("s_avo"))
fala_filme(154, "s_pensar")
C(156, filme("s_escola"))
C(157, filme("pos_creditos"))
# ================================================================ LIVRO × FILME
C(158, ficha("INCIDENTS AROUND THE HOUSE\nJosh Malerman · 2024\nO LIVRO", "O LIVRO"))
C(160, quarto(1))
C(161, img("imagens/IA04_corredor_1", (1.0, 1.1), ((0.5, 0.5), (0.5, 0.48))))
C(164, img("imagens/IA04_corredor_2", (1.0, 1.1), ((0.5, 0.5), (0.5, 0.48))))
C(166, ficha("NO LIVRO, A CRIATURA VENCE\nNO FILME, A MENINA VENCE", "A MENINA VENCE"))
# ================================================================ O VEREDITO
peca(168, f"{PC}placar.mp4", sobra=1.0)
# 22/11 (rascunho 1): sem o quadro de cortiça vazio depois das peças — o último quadro da peça fica congelado na tela
C(169, filme("s_mar", congelar=True))
C(170, filme("s_nao", congelar=True))
C(171, {"video": f"{PC}placar.mp4", "zoom": [1.0, 1.04], "video_inicio": round(dur_video(f"{PC}placar.mp4") - 0.4, 2), "congelar": True, "sem_look": True, "entrada": "fundir", "duracao_entrada": 0.5})
peca(176, f"{PC}veredito.mp4", sobra=1.5)
# ================================================================ POR QUE A FADA TROCADORA
PROVAS = [180, 184, 187, 190, 195, 198, 202, 206, 209]
DEPOIS = [filme("p1_medium", congelar=True), filme("p2_kelvin", congelar=True), armario(2), real("cleary_sun_1895"),
          filme("p5_frank", congelar=True), filme("abertura"), filme("p7_trocar", congelar=True), img("imagens/IA05_parquinho_1", (1.0, 1.07), ((0.4, 0.75), (0.38, 0.78))),
          filme("s_nao", congelar=True)]
C(178, vigia())
PORQUE = f"{PC}porque.mp4"
for k, i in enumerate(PROVAS):   # a ficha da fada volta a cada prova e marca a linha da vez (porquê.mp4: marca k em 3+6k s)
    C(i, {"video": PORQUE, "zoom": [1.0, 1.0], "video_inicio": round(1.0 + 6 * k, 2), "sem_look": True, "entrada": "fundir",
          "duracao_entrada": 0.5})
    C(i + 1, DEPOIS[k])
    fx(i, None, "ep08_pincel", -10, atraso=2.0)
C(212, ficha("E POR QUE NÃO A TULPA?", "TULPA"))
C(213, quarto(1))
C(215, vigia())
# ================================================================ O FECHO
C(218, vigia((1.0, 1.05)))
C(220, filme("s_pensar", congelar=True))
C(221, filme("pos_creditos"))
C(223, vigia((1.0, 1.06)))


montar_antes()

TRILHA_SOM = "cin01_trilha"
roteiro = {
    "modo": "cenas", "formato": "16:9", "tema": "vigia", "avatar": "vigia_hd",
    "voz_arquivo": "audio/voz_com_vinheta_limpa.wav",
    "transcrever_pedacos": 75,
    "alinhamento_forcado": True,
    "look": {"preset": "noite_fria", "forca": 0.7, "halacao": 0.25},
    "cintilar": 0.03, "apertar_pausas": False, "digitacao_db": -19,
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
        if c.get("tipo") == "texto" and "em" not in c and not c.get("parada"):
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
        if len(cs) != 1 or cs[0].get("tipo") != "texto" or cs[0].get("em"):
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
             ("fada", "TEORIA 1 — UMA FADA QUE TROCA PESSOAS"), ("cleary", "O CASO REAL — BRIDGET CLEARY, 1895"),
             ("duplo", "TEORIA 2 — O DUPLO"), ("demonio", "TEORIA 3 — O DEMÔNIO TRAPACEIRO"),
             ("tulpa", "TEORIA 4 — UMA COISA CRIADA PELO DESEJO"), ("avo", "TEORIA 5 — A AVÓ DE CORALINE"),
             ("capgras", "A CIÊNCIA — A SÍNDROME DE CAPGRAS"), ("spoiler", "⚠️ SPOILER — O FINAL EXPLICADO"),
             ("livro", "LIVRO × FILME — OS DOIS FINAIS"), ("veredito", "O VEREDITO"), ("porque", "POR QUE A FADA TROCADORA"),
             ("fecho", "O FECHO")]
    ini = [0.0] + [T0[SEC[s]] - batidas[SEC[s]].get("pausa_antes_s", 0) for _, s in nomes[1:]]
    secoes = [[n, round(ini[k], 2), round(ini[k + 1] if k + 1 < len(ini) else fim, 2)] for k, (n, _) in enumerate(nomes)]
    furos = [[round(T0[i] + a, 2), round(T0[i] + b, 2)] for i, a, b in FUROS]
    plano = {"secoes": secoes, "fim": round(fim, 2), "furos": furos, "veredito": round(T0[176] - 1.0, 2)}
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
        if not v or v.startswith("camera3d") or c.get("congelar") or not (AQUI / v).exists():
            continue   # congelada: o último quadro segura de propósito
        fim = ini[k + 1][0] if k + 1 < len(ini) else t + 6
        d = float(sp.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(AQUI / v)],
                         capture_output=True, text=True).stdout) - float(c.get("video_inicio", 0))
        if d / float(c.get("velocidade", 1)) < (fim - t) + 1.2:
            print(f"!! CLIPE CURTO fala {i}: {Path(v).name} tem {d:.1f}s, a cena pede {(fim - t) + 1.2:.1f}s — dividir a cena")


conferir_clipes()
sem = [i for i, b in enumerate(batidas) if not cenas_de(b)]
(AQUI / "roteiro.json").write_text(json.dumps(roteiro, ensure_ascii=False, indent=1), encoding="utf-8")
n_cenas = sum(len(cenas_de(b)) for b in batidas)
print(f"{len(batidas)} falas, {n_cenas} cenas, falas sem cena (continuam a anterior): {sem}")
print("pausa total:", round(sum(b.get("pausa_antes_s", 0) for b in batidas), 1), "s")
