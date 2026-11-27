"""Monta roteiro.json do O QUE É A CRIATURA? #2 — Obsessão (27/11; molde do montar_roteiro.py do #1).
Formato julgamento (roteiro v4): gancho → as 7 pistas → os 4 suspeitos (Ato I) → 2 provas de fora → spoiler → o
julgamento (um cai por vez) → o veredito → por que é o pior dos quatro → prova a prova → o salgueiro → o fecho.
- Peças da identidade do #2 (identidade/pecas/: abertura, pista, teoria, suspeito, checklist, placar, veredito, spoiler)
  entram como no #1: vídeo pronto com o próprio som, numa pausa da voz (peca/peca_falada) ou sob a narração (sob).
- Trecho do filme (cortar_filmes.py; 🔊 = dublagem): o Vigia se cala, o filme fala com a fala escrita em amarelo; depois a
  narração segue sobre a ilustração. 27/11 (usuário: "cadência nas trocas de cenas, nada de corte seco"): todo trecho
  nasce do preto e volta ao preto, e as trocas de imagem são fusões curtas que terminam antes da voz (ritmo()).
- Ilustrações do usuário (imagens/NN_*.png, fora do git) com câmera 3D; imagens reais em reais_prontos/.
Regras: Vigia na apresentação, nas viradas e no fecho; nenhum rosto de IA; cena >= 4 s; legenda só em português.
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
assert len(falas) == 354, "o ROTEIRO.md mudou: rever o mapa"


def I(comeco, depois=0):
    """22/11: índice da fala pelo começo do texto (o roteiro muda de ordem; números fixos quebravam)."""
    ach = [k for k, f in enumerate(falas) if f.startswith(comeco) and k >= depois]
    assert ach, comeco
    return ach[0]
batidas = [{"fala": f} for f in falas]
VIGIA = {"imagem": "../../painel/cenarios/abrigo_16x9.png", "vigia": True}
C3D = AQUI / "camera3d"; C3D.mkdir(exist_ok=True)
ALI = Path(__import__("os").environ.get("ALINHAMENTO") or AQUI / "audio" / "alinhamento.json")
FP = "filmes_prontos/"; RP = "reais_prontos/"; PC = "identidade/pecas/"
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



# 27/11 — Content ID (lição do #1): o filme entra SÓ nos trechos das falas-pista (cortar_filmes.py), nunca de fundo. Todo o
# resto é ilustração ORIGINAL sem rosto (as 19 do usuário, PEDIDO_ILUSTRACOES.md → imagens/NN_*.png), imagem real
# (reais_prontos/) ou peça da identidade do #2 (identidade/pecas/). Ilustração ganha câmera 3D por profundidade, com o
# movimento alternando a cada uso (a mesma imagem nunca volta igual).
IL = {p.stem.split("_", 1)[1]: p for p in sorted((AQUI / "imagens").glob("[0-9][0-9]_*.png"))}
ATMOS = {"mago_lamparina": {"vela": 0.7}, "boneca_pote": {"vela": 0.6}, "tabua_prego": {"vela": 0.5}, "po_cha": {"vela": 0.4},
         "pata_macaco": {"vela": 0.5}, "noiva_dybbuk": {"neblina": 0.4}, "no_salgueiro": {"neblina": 0.5},
         "genio_jarro": {"fumaca": 0.4}, "sala": {"poeira": 0.35}, "caixa_loja": {"poeira": 0.45},
         "prateleira_vazia": {"poeira": 0.45}, "quarto_3h": {"poeira": 0.3}}
# um som discreto da biblioteca na ilustração (entra suave, sob a voz; no máximo 2 vezes por som)
SOM_IL = {"galho_carro": ("ep11_galho_quebra", -16, 2.0), "tabua_prego": ("ep12_martelo_prego", -17, 3.0),
          "telefone": ("chuva_externa", -20, 7.0), "nikki_carro": ("chuva_externa", -21, 7.0), "mago_lamparina": ("ep08_vela", -17, 4.0),
          "boneca_pote": ("ep08_vela", -18, 4.0), "porta_banheiro": ("ep09_sn_porta_rangido_lento", -18, 6.0),
          "quarto_3h": ("ep07_respiracao_nuca", -19, 6.0), "genio_jarro": ("ep12_mar_noite", -19, 7.0),
          "noiva_dybbuk": ("ep09_sn_sussurro_fantasma", -19, 4.0), "no_salgueiro": ("ep06_riacho", -21, 7.0),
          "sala": ("casa_noite", -21, 7.0), "comprimidos": ("ep07_quarto_silencio", -20, 6.0)}
_USO = {}
_MOVS = ("entrar", "lado", "entrar", "lado_esq", "sair")
_FOCOS = ((0.5, 0.5), (0.45, 0.5), (0.55, 0.48), (0.5, 0.55), (0.42, 0.5))


def il(nome, foco=None, mov=None):
    """a ilustração NN_<nome>.png, com câmera 3D (movimento e foco alternando a cada uso)"""
    arq = IL[nome]; n = _USO[nome] = _USO.get(nome, 0) + 1
    mv = mov or _MOVS[(n + len(nome)) % len(_MOVS)]
    c = c3(str(arq.relative_to(AQUI)), mv, foco or _FOCOS[(n + len(nome)) % len(_FOCOS)], forca=0.85)
    if nome in ATMOS:
        c["atmos"] = ATMOS[nome]
    c["_il"] = nome
    return c


def som_ilustr(i, c):   # (substitui a do #1: aqui o nome vem da própria cena)
    nome = c.pop("_il", None)
    if not nome or nome not in SOM_IL or _SOM_USO.get(nome, 0) >= 2:
        return
    _SOM_USO[nome] = _SOM_USO.get(nome, 0) + 1
    som, db, ate = SOM_IL[nome]
    fx(i, c.get("em"), som, db, ate=ate, saida=1.2, entrada=0.6, _il=True)


def fala_filme(i, nome, db=0):   # noqa: F811 — trecho mudo (sem .wav) também entra na pausa, com a trilha por baixo
    d = TRECHOS[nome]["dur"]
    w = AQUI / FP / f"{nome}.wav"
    antes(i, filme(nome, congelar=True), d + 0.25, str(w) if w.exists() else None, db, furo=w.exists())
    FALAS_FILME.append((i, nome))


def flash(i, sobra=1.0):
    """27/11 (usuário, aprovado no teste): o flash borrado (~2 s) da Nikki atacando a Sarah; a voz entra antes dele acabar."""
    antes(i, filme("g_flash", congelar=True), TRECHOS.get("g_flash", {}).get("dur", 2.05), str(AQUI / FP / "g_flash.wav"), -2,
          furo=True, sobra=sobra)


def sob(i, arq, ate=None, segurar=None, db=-10):
    """peça que roda SOB a narração a partir da fala i (as tábuas do Ato I, os placares do julgamento)"""
    return checklist_falado(i, arq, db=db, inicio=i, ate=ate, segurar=segurar)


def tabua(t, vermelho=None):
    """ficha lida pela narração (a máquina de escrever digita enquanto a voz lê)"""
    return ficha(t, vermelho)


# ================================================================ GANCHO
fala_filme(0, "g_sorriso"); fala_filme(0, "g_sala")      # abre no plano mais perturbador, sem logo
C(0, il("sala", (0.45, 0.45), "entrar"))
C(I("Babada."), il("sala", (0.45, 0.7), "entrar"))        # desce para o chão molhado
fala_filme(I("E, quando ele abriu a porta"), "g_espera")
C(I("E, quando ele abriu a porta"), il("porta_banheiro", mov="entrar"))
flash(I("E quem fica no caminho, morre"))
C(I("E quem fica no caminho, morre"), il("nikki_carro", mov="entrar"))
fala_filme(I("Tudo isso por causa"), "g_desejo")
C(I("Tudo isso por causa"), il("caixa_loja"))
C(I("Ele pediu para ser"), il("galho_carro", (0.45, 0.45)))
C(I("O filme nunca diz"), il("maos_sofa"))
C(I("Eu fui atrás."), vigia((1.0, 1.05)))
C(I("E a resposta está num papiro"), real("papiro_magico_0", (1.0, 1.08)))
C(I("num enforcamento"), real("blandy_execucao_2", (1.0, 1.08)))
C(I("e num galho de salgueiro guardado"), il("no_salgueiro", (0.6, 0.45), "entrar"))
C(I("No final, você vai saber"), il("prateleira_vazia"))
peca(I("Eu sou o Vigia."), f"{PC}abertura.mp4", sobra=3.0, db=-7)
# ================================================================ O VIGIA APRESENTA
C(I("Eu sou o Vigia."), vigia())
C(I("Se você ainda não é inscrito"), vigia((1.02, 1.08), ((0.55, 0.48), (0.56, 0.45))))
# ================================================================ AS PISTAS
for n, txt in enumerate(("Pista um.", "Pista dois.", "Pista três.", "Pista quatro.", "Pista cinco.", "Pista seis.", "Pista sete."), 1):
    peca_falada(I(txt), f"{PC}pista{n}.mp4")
fala_filme(I("Um desejo por pessoa."), "p1_caixa"); C(I("Um desejo por pessoa."), il("caixa_loja", (0.6, 0.4)))
fala_filme(I("Só acaba de um jeito"), "p1_morrer"); C(I("Só acaba de um jeito"), il("porta_banheiro"))
C(I("Está escrito na caixa"), il("caixa_loja", (0.62, 0.45), "lado"))
C(I("Acontece quando você quebra"), il("galho_carro", (0.42, 0.42), "entrar"))
fala_filme(I("Depois do desejo, a Nikki"), "p3_carro"); C(I("Depois do desejo, a Nikki"), il("nikki_carro"))
fala_filme(I("Não aguenta três horas"), "p3_horas"); C(I("Não aguenta três horas"), il("quarto_3h"))
C(I("E quando ele sai de casa"), il("sala", (0.45, 0.5), "sair"))
fala_filme(I("Quem fica entre ela"), "p4_festa"); C(I("Quem fica entre ela"), il("festa"))
fala_filme(I("Quando o Bear liga"), "p5_telefone"); C(I("Quando o Bear liga"), il("telefone"))
fala_filme(I("E, uma madrugada"), "p5_madrugada"); C(I("E, uma madrugada"), il("quarto_3h", (0.72, 0.45), "entrar"))
fala_filme(I("O Bear pergunta se o amor"), "p6_escolheu"); C(I("O Bear pergunta se o amor"), il("maos_sofa", (0.4, 0.6)))
C(I("O pedido foi ao pé da letra"), il("galho_carro", (0.5, 0.5), "sair"))
C(I("Mais do que a família dela"), il("festa", (0.55, 0.4), "entrar"))
sob(I("Sete pistas."), f"{PC}placar.mp4", ate=I("O primeiro suspeito é o mais óbvio"))
# ================================================================ SUSPEITO 1 — O GÊNIO
k = I("O primeiro suspeito é o mais óbvio"); peca_falada(k, f"{PC}teoria1.mp4"); C(k, real("mil_noites_0", (1.0, 1.06)))
C(I("Nas Mil e Uma Noites"), real("pescador_genio_0", (1.0, 1.08)))
C(I("Abre o lacre"), il("genio_jarro", (0.75, 0.3), "entrar"))
k = I("Os folcloristas catalogaram"); C(k, tabua("ATU 331 · \"O ESPÍRITO NA GARRAFA\"\nATU 750A · \"OS TRÊS DESEJOS\"", "ATU 331")); falada(k)
C(I("E o desejo de gênio tem uma marca"), real("pescador_genio_1", (1.0, 1.06)))
C(I("Mas a tradição do jinn"), real("mil_noites_1", (1.0, 1.08)))
C(I("Os jinn são feitos de fogo"), il("genio_jarro", (0.7, 0.35), "lado"))
C(I("E, na crença popular"), real("pescador_genio_2", (1.0, 1.07)))
C(I("Há relatos de jinn"), il("festa", (0.5, 0.45)))
sob(I("Um objeto que guarda um ser."), f"{PC}suspeito1.mp4", ate=I("Parece perfeito."), segurar=1.0)
C(I("Parece perfeito."), il("galho_carro", (0.45, 0.45), "entrar"))
# ================================================================ SUSPEITO 2 — A AMARRAÇÃO
k = I("O segundo suspeito é o mais antigo"); peca_falada(k, f"{PC}teoria2.mp4")
C(I("Na British Library"), real("papiro_magico_0", (1.0, 1.1), foco=((0.5, 0.5), (0.5, 0.42))))
C(I("E boa parte dele é sobre"), il("mago_lamparina", (0.6, 0.6)))
k = I("Os gregos chamavam esse feitiço"); C(k, tabua("AGOGÉ · \"o que conduz\"\nPapiro 121 · British Library · séc. IV", "AGOGÉ")); falada(k, k + 1)
C(I("Uma receita manda escrever"), il("mago_lamparina", (0.3, 0.7), "lado"))
C(I("Outra manda acender"), il("mago_lamparina", (0.25, 0.3), "entrar"))
C(I("E a vítima, diz o papiro"), il("quarto_3h", (0.7, 0.4)))
C(I("E havia as tábuas de chumbo"), real("defixio_1", (1.0, 1.08)))
C(I("O nome da pessoa era riscado"), il("tabua_prego", (0.5, 0.55), "entrar"))
C(I("Os gregos chamavam isso de katadesmos"), real("katadesmos_0", (1.0, 1.08)))
C(I("Em português, a palavra"), real("defixio_2", (1.0, 1.06)))
C(I("A Idade Média trocou"), real("filtro_amor_0", (1.0, 1.08)))
C(I("Tristão e Isolda"), real("tristao_pocao_0", (1.0, 1.07)))
C(I("E em Veneza"), real("tristao_pocao_1", (1.0, 1.06)))
sob(I("Um objeto que precisa ser quebrado."), f"{PC}suspeito2.mp4", ate=I("Parece perfeito também."), segurar=1.0)
C(I("Parece perfeito também."), il("telefone", (0.4, 0.4), "entrar"))
# ================================================================ SUSPEITO 3 — O DYBBUK
k = I("Entre mil novecentos e doze"); peca_falada(k, f"{PC}teoria3.mp4"); C(k, real("ansky_1910", (1.0, 1.07)))
C(I("E encontrou uma coisa"), real("dybbuk_filme_0", (1.0, 1.07)))
C(I("O dybbuk é a alma"), il("noiva_dybbuk", (0.5, 0.45)))
C(I("Daí nasceu a peça"), real("dybbuk_22", (1.0, 1.08)))
C(I("Uma noiva, Leah"), real("dybbuk_peca_0", (1.0, 1.06)))
C(I("E, no dia do casamento"), il("noiva_dybbuk", (0.35, 0.55), "entrar"))
sob(I("Um amor que entra no corpo de uma moça."), f"{PC}suspeito3.mp4", ate=I("E a madrugada em que a Nikki"), segurar=1.0)
C(I("E a madrugada em que a Nikki"), il("quarto_3h", (0.72, 0.4), "lado_esq"))
C(I("Três suspeitos"), vigia((1.0, 1.05)))
# ================================================================ SUSPEITO 4 — A PATA DO MACACO
k = I("O último suspeito é o que"); peca_falada(k, f"{PC}teoria4.mp4")
C(I("Em setembro de mil novecentos e dois"), real("pata_macaco_0", (1.0, 1.08)))
C(I("Um sargento volta da Índia"), il("pata_macaco", (0.48, 0.62), "entrar"))
C(I("A família pede dinheiro"), il("pata_macaco", (0.6, 0.4), "lado"))
C(I("E o diretor de Obsessão admite"), il("caixa_loja", (0.65, 0.4), "entrar"))
C(I("Ele só trocou a pata"), il("galho_carro", (0.5, 0.5), "lado"))
sob(I("O objeto que cumpre."), f"{PC}suspeito4.mp4", ate=I("Quatro suspeitos."), segurar=0.8)
sob(I("Quatro suspeitos."), f"{PC}placar.mp4", ate=I("Antes de julgar"))
C(I("Antes de julgar"), vigia((1.02, 1.07)))
# ================================================================ A CIÊNCIA — EROTOMANIA
k = I("A primeira prova vem da medicina"); C(k, tabua("SÍNDROME DE DE CLÉRAMBAULT\nParis · 1921 · \"erotomania\"", "DE CLÉRAMBAULT")); falada(k, k + 1)
C(I("Desde mil novecentos e dezoito"), real("george_v_0", (1.0, 1.08)))
C(I("A medicina chamou isso"), real("george_v_2", (1.0, 1.07)))
C(I("Obsessão é a erotomania ao contrário"), il("maos_sofa", (0.45, 0.6), "entrar"))
C(I("Guarda isso."), vigia((1.0, 1.05)))
# ================================================================ O CASO REAL — MARY BLANDY
C(I("A segunda prova é um processo"), real("blandy_retrato", (1.0, 1.06)))
k = I("Henley-on-Thames"); C(k, tabua("MARY BLANDY · 31 anos\nHenley-on-Thames, Inglaterra · 1751", "MARY BLANDY")); falada(k, k + 1)
C(I("Mary Blandy, trinta e um anos"), real("blandy_retrato", (1.06, 1.14), foco=((0.5, 0.4), (0.5, 0.36))))
C(I("Então Cranstoun manda"), il("po_cha", (0.6, 0.35)))
C(I("Mary põe o pó no chá"), il("po_cha", (0.55, 0.55), "entrar"))
C(I("O pó era arsênico"), real("blandy_execucao_3", (1.0, 1.07)))
C(I("Mary é julgada em Oxford"), real("blandy_execucao_2", (1.04, 1.12), foco=((0.5, 0.4), (0.5, 0.35))))
C(I("Até o fim, ela jurou"), real("blandy_retrato", (1.0, 1.05)))
C(I("Guarda isso também."), vigia((1.0, 1.05)))
# ================================================================ SPOILER
k = I("A partir daqui, eu conto o final")   # o aviso é lido na narração, sobre a peça
peca_falada(k, f"{PC}spoiler.mp4", entra=1.2); falada(k, k + 1)
C(I("No terço final"), il("nikki_carro", (0.7, 0.45), "entrar"))
fala_filme(I("E diz para ele: a culpa"), "s_culpa"); C(I("E diz para ele: a culpa"), il("maos_sofa"))
C(I("O Bear volta à loja"), il("prateleira_vazia", (0.5, 0.5), "entrar"))
fala_filme(I("alguém fazer um desejo contrário"), "s_saidas"); C(I("alguém fazer um desejo contrário"), il("caixa_loja", (0.55, 0.5), "sair"))
C(I("Ele implora ao amigo Ian"), il("galho_carro", (0.45, 0.4), "lado_esq"))
fala_filme(I("Então sobra só uma porta"), "s_sempre"); C(I("Então sobra só uma porta"), il("porta_banheiro", (0.55, 0.45), "entrar"))
C(I("E toma veneno."), il("comprimidos"))
fala_filme(I("Só que, do lado de fora"), "s_galho"); C(I("Só que, do lado de fora"), il("porta_banheiro", (0.4, 0.5), "lado"))
C(I("Ela quebra o galho."), il("galho_carro", (0.42, 0.45), "entrar"))
C(I("O Bear tenta vomitar"), il("comprimidos", (0.4, 0.6), "entrar"))
fala_filme(I("E morre no colo dela"), "s_abraco"); C(I("E morre no colo dela"), il("maos_sofa", (0.45, 0.6), "entrar"))
fala_filme(I("E, no segundo em que ele morre"), "s_volta"); C(I("E, no segundo em que ele morre"), il("maos_sofa", (0.3, 0.5), "sair"))
fala_filme(I("e pergunta: o que você fez"), "s_oque"); C(I("e pergunta: o que você fez"), il("sala", (0.45, 0.45), "entrar"))
C(I("O desejo só acaba com a morte"), il("porta_banheiro", (0.5, 0.5), "sair"))
k = I("E o diretor filmou um final diferente"); C(k, tabua("O FINAL QUE NÃO FOI\nRomeu e Julieta · filmado e descartado", "descartado")); falada(k, k + 1)
C(I("No filme, a Nikki fica viva"), il("prateleira_vazia", (0.4, 0.45)))
# ================================================================ ATO II — O JULGAMENTO
k = I("Agora, com tudo na mesa"); peca_falada(k, f"{PC}placar.mp4", entra=1.0)
C(I("A pata do macaco é o avô"), il("pata_macaco", (0.5, 0.6), "entrar"))
C(I("E o diretor disse o contrário"), il("galho_carro", (0.5, 0.45)))
C(I("O veneno não está no galho"), il("comprimidos", (0.5, 0.55)))
sob(I("A pata do macaco explica de onde"), f"{PC}checklist4.mp4", ate=I("O gênio parecia perfeito"), segurar=1.2)
C(I("O gênio parecia perfeito"), il("genio_jarro", (0.72, 0.32), "entrar"))
C(I("O jinn apaixonado"), real("mil_noites_0", (1.04, 1.1)))
C(I("A coisa na Nikki não quer nada"), il("maos_sofa", (0.4, 0.55)))
sob(I("E o diretor foi direto"), f"{PC}checklist1.mp4", ate=I("Sobram dois."), segurar=0.8)
peca_falada(I("Sobram dois."), f"{PC}placar_d2.mp4", entra=4.5)
C(I("O dybbuk e a amarração explicam"), il("noiva_dybbuk", (0.5, 0.5), "lado"))
C(I("O que separa os dois"), vigia((1.02, 1.08), ((0.55, 0.48), (0.56, 0.45))))
C(I("No dybbuk, quem ama é o morto"), il("noiva_dybbuk", (0.4, 0.45), "entrar"))
C(I("Na amarração, quem ama"), il("tabua_prego", (0.5, 0.5), "lado"))
C(I("Lembra da erotomania"), real("george_v_2", (1.04, 1.1)))
C(I("A Nikki não sente amor"), il("sala", (0.45, 0.4), "lado"))
C(I("E lembra da frase do telefone"), il("telefone", (0.45, 0.4), "lado"))
C(I("E a \"outra\" da madrugada"), il("quarto_3h", (0.7, 0.45)))
C(I("E a prova final é o fim do filme"), il("maos_sofa", (0.4, 0.6)))
sob(I("Um dybbuk não sairia"), f"{PC}checklist3.mp4", ate=I("O meu veredito"))
# ================================================================ O VEREDITO
peca(I("O meu veredito"), f"{PC}veredito.mp4", sobra=3.0)   # silêncio com motivo: o sinete sela, e a voz entra
C(I("O meu veredito"), vigia((1.0, 1.05)))
C(I("E, se você acha que amarração"), vigia((1.02, 1.08), ((0.55, 0.48), (0.56, 0.45))))
# ================================================================ POR QUE É O PIOR DOS QUATRO
peca_falada(I("Pensa nos outros três."), f"{PC}placar_d3.mp4", entra=4.5)
C(I("O gênio quer alguma coisa"), il("genio_jarro", (0.75, 0.3), "sair"))
C(I("O dybbuk é um morto"), il("noiva_dybbuk", (0.5, 0.4), "sair"))
C(I("A pata do macaco é um objeto"), il("pata_macaco", (0.5, 0.6), "sair"))
C(I("A amarração não quer nada"), il("tabua_prego", (0.5, 0.55), "entrar"))
C(I("Ela é presa em uma pessoa viva"), il("galho_carro", (0.5, 0.5), "entrar"))
k = I("No Museu do Louvre"); C(k, tabua("MUSEU DO LOUVRE · E 27145\nEgito romano · séc. III–IV", "E 27145")); falada(k)
C(I("É uma boneca de barro"), il("boneca_pote", (0.45, 0.55), "entrar"))
C(I("Ela foi achada dentro"), il("boneca_pote", (0.62, 0.6), "lado"))
C(I("E a tábua diz quem fez"), real("defixio_1", (1.04, 1.12)))
C(I("Os papiros de magia trazem"), real("papiro_magico_0", (1.04, 1.12), foco=((0.5, 0.6), (0.5, 0.66))))
k = I("São treze agulhas."); C(k, tabua("TREZE AGULHAS\ncérebro · olhos · ouvidos · boca\nentranhas · mãos · sexo · pés", "TREZE AGULHAS")); falada(k, k + 8)
C(I("Para ela não ver mais ninguém"), il("boneca_pote", (0.45, 0.5), "entrar"))
C(I("E o texto da tábua não pede"), il("tabua_prego", (0.55, 0.6), "entrar"))
C(I("Ele chama os espíritos dos mortos"), il("mago_lamparina", (0.5, 0.45), "sair"))
k = I("Que ela não coma."); C(k, tabua("QUE ELA NÃO COMA. NÃO BEBA. NÃO DURMA.\nNÃO SAIA DE CASA.\nATÉ QUE ELA VENHA ATÉ MIM.", "ATÉ QUE ELA VENHA ATÉ MIM.")); falada(k, k + 5)
C(I("E se ela resistir"), real("katadesmos_0", (1.06, 1.14)))
k = I("E a última ordem"); C(k, tabua("\"…POR TODA A DURAÇÃO\nDA VIDA DELE.\"", "DA VIDA DELE.")); falada(k, k + 1)
pausa(I("Não da vida dela."), 1.2)   # [pausa] do roteiro: a frase assenta
C(I("Mil e setecentos anos antes"), il("boneca_pote", (0.5, 0.5), "sair"))
fala_filme(I("Exatamente o que o homem do telefone"), "p1_morrer"); C(I("Exatamente o que o homem do telefone"), il("telefone", (0.5, 0.45), "entrar"))
C(I("E agora você entende"), vigia((1.0, 1.05)))
C(I("A pessoa amarrada não desaparece"), il("quarto_3h", (0.72, 0.45), "entrar"))
C(I("Vendo o próprio corpo"), il("festa", (0.55, 0.45)))
C(I("Vendo as próprias mãos"), il("nikki_carro", (0.7, 0.45), "lado"))
C(I("A não ser pedir, de madrugada"), il("quarto_3h", (0.4, 0.6), "sair"))
C(I("O gênio te dá o que você pediu"), vigia((1.0, 1.05)))
C(I("A amarração faz uma coisa pior"), vigia((1.02, 1.09), ((0.55, 0.48), (0.56, 0.44))))
C(I("E repara no que a coisa"), il("porta_banheiro", (0.42, 0.5), "entrar"))
C(I("Uma amarração não termina"), il("no_salgueiro", (0.6, 0.45), "lado"))
C(I("E o Bear comprou isso"), il("caixa_loja", (0.6, 0.45), "entrar"))
# ================================================================ POR QUE A AMARRAÇÃO (prova a prova)
PROVAS = [I(t) for t in ("Prova um.", "Prova dois.", "Prova três.", "Prova quatro.", "Prova cinco.", "Prova seis.", "Prova sete.")]
TITULOS = ["ELA TEM REGRAS", "O GALHO PRECISA SER QUEBRADO", "ELA NÃO SOSSEGA", "QUEM ATRAPALHA, MORRE",
           "A NIKKI DE VERDADE ESTÁ LÁ DENTRO", "\"TER ESCOLHIDO ISSO PRA ELA\"", "\"A PESSOA QUE ELA MAIS AMA NO MUNDO\""]
DEPOIS = [real("papiro_magico_0", (1.0, 1.06)), il("tabua_prego", (0.5, 0.5), "lado"), il("quarto_3h", (0.7, 0.45), "lado"),
          real("blandy_execucao_2", (1.0, 1.06)), il("telefone", (0.45, 0.45), "sair"), il("mago_lamparina", (0.55, 0.5), "lado"),
          il("galho_carro", (0.45, 0.45), "entrar")]
for n, (k, t, c) in enumerate(zip(PROVAS, TITULOS, DEPOIS), 1):
    C(k, tabua(f"PROVA {n}\n{t}", f"PROVA {n}")); falada(k); C(k + 1, c)
C(I("Prende a pessoa dentro de si"), il("maos_sofa", (0.4, 0.6), "entrar"))
# ================================================================ POR QUE UM SALGUEIRO
C(I("E tem uma última coisa"), real("salgueiro_gravura_0", (1.0, 1.08)))
C(I("O diretor diz que inventou"), il("caixa_loja", (0.62, 0.42), "lado"))
C(I("Mas escolheu, talvez sem saber"), real("salgueiro_gravura_1", (1.0, 1.08)))
C(I("Num museu da Cornualha"), il("no_salgueiro", (0.62, 0.42), "entrar"))
C(I("O objeto do filme existe"), il("galho_carro", (0.45, 0.45), "entrar"))
C(I("A diferença é que, no filme"), il("galho_carro", (0.42, 0.42), "sair"))
# ================================================================ O FECHO
C(I("Obsessão é a amarração vista de dentro"), vigia((1.0, 1.05)))
C(I("Por dezesseis séculos"), il("mago_lamparina", (0.5, 0.5), "entrar"))
C(I("O filme é o primeiro"), il("sala", (0.45, 0.45), "entrar"))
C(I("Existe só uma pessoa presa"), il("telefone", (0.5, 0.4), "sair"))
C(I("E pedindo, de madrugada"), il("quarto_3h", (0.72, 0.45), "sair"))
C(I("E você, concordou com o julgamento"), vigia((1.0, 1.06)))

for _i, _n in FALAS_FILME:   # o filme corta no fim do trecho; a narração segue sobre a ilustração
    if not cenas_de(batidas[_i]):
        raise SystemExit(f"fala {_i} ({_n}): trecho do filme sem cena para depois")

montar_antes()


TRILHA_SOM = "cin02_trilha"
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
    "legendas": {"destaques": ["Obsessão", "Nikki", "amarração", "dybbuk", "jinn", "gênio", "Pata do Macaco", "agogé",
                               "katadesmos", "defixio", "Mary Blandy", "erotomania", "Louvre", "salgueiro", "veredito"]},
    "musica": {"som": TRILHA_SOM, "volume_db": -13},
    "cta": {"titulo": "Cuidado com o que você deseja.", "canal": "Último Abrigo",
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
    for k, (t, c) in enumerate(inicios):   # 23/11: conferência — cena animada com menos de 4 s seria engolida pelo motor
        if "ANIM_" in str(c.get("video", "")):
            d = (inicios[k + 1][0] if k + 1 < len(inicios) else t + 20) - t
            print(f"animação {Path(c['video']).stem}: {t:.1f}s, {d:.1f}s na tela" + ("  <<< CURTA" if d < 4.2 else ""))
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
    # (nome do motivo em trilha/compor.py, fala onde a seção começa)
    nomes = [("gancho", 0), ("apresenta", I("Eu sou o Vigia.")), ("pistas", I("Pista um.")),
             ("genio", I("O primeiro suspeito é o mais óbvio")), ("amarracao", I("O segundo suspeito é o mais antigo")),
             ("dybbuk", I("Entre mil novecentos e doze")), ("pata", I("O último suspeito é o que")),
             ("erotomania", I("A primeira prova vem da medicina")), ("blandy", I("A segunda prova é um processo")),
             ("spoiler", I("A partir daqui, eu conto o final")), ("julgamento", I("Agora, com tudo na mesa")),
             ("decisao", I("O dybbuk e a amarração explicam")), ("veredito", I("O meu veredito")),
             ("pior", I("Pensa nos outros três.")), ("louvre", I("No Museu do Louvre")),
             ("porque", I("Prova um.")), ("salgueiro", I("E tem uma última coisa")),
             ("fecho", I("Obsessão é a amarração vista de dentro"))]
    ini = [0.0] + [T0[k] - batidas[k].get("pausa_antes_s", 0) for _, k in nomes[1:]]
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
_m, _s = divmod(int(T0[I("O meu veredito")] - 12), 60)   # quem não viu o filme pula direto para o veredito
_pular = f"{_m}:{_s:02d}"
_sp = AQUI / PC / "spoiler.txt"
if not (AQUI / PC / "spoiler.mp4").exists() or not _sp.exists() or _sp.read_text() != _pular:
    print("spoiler: pule para", _pular, "— renderizando a peça", flush=True)
    if not __import__("os").environ.get("TESTE"):
        subprocess.run([sys.executable, "feitico.py", "spoiler", "pecas/spoiler.mp4", _pular], cwd=AQUI / "identidade", check=True)
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
