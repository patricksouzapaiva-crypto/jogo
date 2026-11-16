"""Monta roteiro.json do Ep. 10 — Tailândia / Isan: "Por que o terror tailandês nunca deixa você em paz?" (16/11).
Molde do Ep. 09 v4 (gancho sem Vigia; TEMA, APARTE e FECHO com o Vigia; capítulos de lenda; a história do Mateus; o
fecho). Identidade do episódio: o PHA YANT 3D nos cartões de capítulo (cartoes.py), a câmera de segurança (efeito
cctv do tailandia.js) e o obturador do dossiê nos cortes secos; material REAL com crédito (preparar_midia.py): fotos
do Commons, filme de arquivo de 1969 e os trailers de Inhuman Kiss e The Medium.
Regras da casa: Vigia só no TEMA/APARTE/FECHO; nenhum rosto de IA (V10 cortado em 3,2 s, antes do rosto); cena >= 3 s;
legenda só em português; tailandês/khom só nos panos e nas fichas.
Uso: python3 montar_roteiro.py  → roteiro.json (+ camera3d/*.mp4 na primeira vez). Teste sem a narração inteira:
ALINHAMENTO=audio/estimado.json (python3 estimar_alinhamento.py)."""
import hashlib
import json
import sys
from pathlib import Path

import falas as F

AQUI = Path(__file__).parent
falas, PERS, SEC, PAUSAS, _ = F.ler()
assert len(falas) == 125 and PERS.get(101) == "mateus" and PERS.get(90) == "camila", "o ROTEIRO.md mudou: rever os índices"
batidas = [{"fala": f} for f in falas]
for i, s in PAUSAS.items():
    batidas[i]["pausa_antes_s"] = s


def P(nome):
    return nome if nome.endswith((".jpg", ".png")) else nome + ".jpg"


VIGIA = {"imagem": "../../painel/cenarios/abrigo_16x9.png", "vigia": True}
C3D = AQUI / "camera3d"; C3D.mkdir(exist_ok=True)
# 14/11: os tempos vêm da VOZ FINAL (com os personagens, que são mais longos): senão a câmera 3D sai curta e o motor desacelera
ALI = Path(__import__("os").environ.get("ALINHAMENTO") or next(p for p in (AQUI / "audio" / "alinhamento_voz_personagens.json",
                                                                           AQUI / "audio" / "alinhamento.json") if p.exists()))   # teste: ALINHAMENTO=estimado.json


# ------------------------------------------------------------------ ajudantes
def vigia(z=(1.0, 1.04), foco=((0.55, 0.5), (0.57, 0.48))):
    return dict(VIGIA, zoom=list(z), foco=[list(foco[0]), list(foco[1])])


def img(nome, z=(1.0, 1.08), foco=None, **kw):
    c = {"imagem": P(nome), "zoom": list(z), **kw}
    if foco:
        c["foco"] = [list(foco[0]), list(foco[1])]
    return c


def c3(nome, mov="entrar", foco=(0.5, 0.5), forca=1.0, desfoque=0.0, **kw):
    """Câmera 3D: a câmera anda dentro da imagem (profundidade real). O vídeo é gerado no fim, com a duração da cena."""
    arq = P(nome)
    return {"imagem": arq, "zoom": [1.0, 1.0], "_c3d": {"mov": mov, "foco": list(foco), "forca": forca,
                                                                    "desfoque": desfoque}, **kw}


def vid(nome, z=(1.0, 1.04), **kw):
    return {"video": CL + nome + ".mp4", "zoom": list(z), **kw}


def filme(nome, **kw):
    """Trecho de filme já na moldura de arquivo (cortar_filmes.py): sem zoom (a moldura e o crédito não podem crescer)."""
    return {"video": FP + nome + ".mp4", "zoom": [1.0, 1.0], **kw}


def cel(c, hora, sinal=None, vertical=False):
    c = dict(c); c["celular"] = {"hora": hora, **({"sinal": sinal} if sinal else {}), **({"vertical": True} if vertical else {})}
    c.setdefault("mao", 0.15 if vertical else 0.5)
    return c


def texto(t, vermelho=None, estilo="maquina", **kw):
    return {"tipo": "texto", "texto": t, "estilo": estilo, **({"vermelho": vermelho} if vermelho else {}), **kw}


def ficha(t, vermelho=None):
    """FICHA de documentário (dado real, com fonte): máquina de escrever, devagar o bastante para ler."""
    return texto(t, vermelho, cps=40)


def K(texto_k, x=0.82, y=0.5, modo="luz", legenda=None, **kw):
    return {"texto": texto_k, "x": x, "y": y, "modo": modo, **({"legenda": legenda} if legenda else {}), **kw}


def C(i, *cenas, com_vigia=False):
    b = batidas[i]; lista = []
    for x in cenas:
        c, em = (x if isinstance(x, tuple) else (x, None))
        c = dict(c)
        if em:
            c["em"] = em
        if com_vigia:
            c["com_vigia"] = True
        lista.append(c)
    b.pop("cena", None); b.pop("cenas", None)
    if len(lista) == 1 and "em" not in lista[0]:
        b["cena"] = lista[0]
    else:
        b["cenas"] = lista


def T(i, entrada, dur=None):
    c = batidas[i].get("cena") or batidas[i]["cenas"][0]
    c["entrada"] = entrada
    if dur:
        c["duracao_entrada"] = dur


def saida_lenta(i_seguinte, segurar, transicao="fundir", dur=1.6):
    b = batidas[i_seguinte]
    b["pausa_antes_s"] = round(b.get("pausa_antes_s", 0) + segurar + dur, 2)
    (b.get("cena") or b["cenas"][0]).update({"entrada": transicao, "duracao_entrada": dur, "antecipar": dur})


def pausa(i, s):
    batidas[i]["pausa_antes_s"] = round(batidas[i].get("pausa_antes_s", 0) + s, 2)


def amb(i, som, db=-20, em=None):
    batidas[i]["ambiente"] = {"som": som, "volume_db": db, **({"em": em} if em else {})}


def fx(i, em, som, db, depois=False, atraso=0.0, **kw):
    """kw (15/11, desenho de som): pan (-1 esq … +1 dir), reverso, eco, tom (semitons), ate (corta em s), saida (fade s),
    arquivo (um wav nosso no lugar de painel/sons)."""
    batidas[i].setdefault("sons", []).append({"em": em, "som": som, "volume_db": db, "depois": depois, "atraso": atraso, **kw})


def musica(i, faixa, db, em=None, atraso=0.0):
    batidas[i]["musica"] = {"som": f"ep09_m{faixa}", "volume_db": db, **({"em": em} if em else {}), **({"atraso": atraso} if atraso else {})}



# ================================================================ Ep. 10 — material
R = "imagens/recebidas/"
RP = "reais_prontos/"
FP = "filmes_prontos/"
CL = "clipes/"
DATA = "18-09-2025"


def IA(cod, v=1):
    return f"{R}{cod}_variacao_{v}.jpg"


def real(nome, z=(1.0, 1.035), **kw):
    """Foto real do Commons já no papel de dossiê com o crédito (preparar_midia.py): zoom mínimo, o crédito não sai."""
    return {"imagem": RP + nome + ".jpg", "zoom": list(z), **kw}


def filme(nome, **kw):
    """Trecho de filme/arquivo já na moldura (preparar_midia.py): sem zoom."""
    return {"video": FP + nome + ".mp4", "zoom": [1.0, 1.0], **kw}


def clipe(nome, ate=None, inicio=0.0, cam=None, hora=None, queda=None, z=(1.0, 1.03), **kw):
    """Clipe do Flow (CLIPES.md). ate: corta o arquivo antes do erro da IA. cam/hora: por cima, a câmera de segurança."""
    arq = CL + nome + ".mp4"
    if ate:
        saida = AQUI / CL / f"{nome}_ate{ate}.mp4"
        if not saida.exists():
            __import__("subprocess").run(["ffmpeg", "-v", "error", "-y", "-i", str(AQUI / arq), "-t", str(ate), "-an", "-c:v", "libx264",
                                          "-crf", "16", str(saida)], check=True)
        arq = CL + saida.name
    c = {"video": arq, "zoom": list(z), **({"video_inicio": inicio} if inicio else {}), **kw}
    if cam:
        c["efeitos"] = {"cctv": {"cam": cam, "hora": hora or "02:40:00", "data": DATA, **({"queda": queda} if queda is not None else {})}}
    return c


def cctv(c, cam, hora, queda=None):
    c = dict(c); c["efeitos"] = {"cctv": {"cam": cam, "hora": hora, "data": DATA, **({"queda": queda} if queda is not None else {})}}
    return c


def obt(c, dur=0.55):
    """Corte seco de dossiê: o obturador fecha e abre num flash (tailandia.js) — com o estalo (fx em obt_som)."""
    c = dict(c); c["entrada"] = "obturador"; c["duracao_entrada"] = dur
    return c


def obt_som(i, em=None, db=-15):
    fx(i, em, "ep10_obturador", db, atraso=-0.3 if em is None else -0.15)


def seco(c):
    c = dict(c); c["entrada"] = "corte"
    return c


TRILHA_SOM = "ep10_trilha"
TRILHA = {"som": TRILHA_SOM, "volume_db": -30}
CARTAO = 7.6


def capitulo(i, n, cena, em):
    """Cartão do capítulo = o PHA YANT 3D (cartoes.py): vídeo pronto de 7,6 s, com a música do capítulo e o pano.
    A trilha de fundo sai durante o cartão e VOLTA de onde estaria (continuar) na fala seguinte."""
    cap = {"video": f"cartoes/cap{n}.mp4", "zoom": [1.0, 1.0], "antecipar": CARTAO, "antecipar_fixo": True,
           "entrada": "corte", "tipo_cartao": True, "congelar": True}   # nunca desacelerar: o som do cartão é separado
    cena = dict(cena); cena["entrada"] = "fundir"; cena["duracao_entrada"] = 0.9
    C(i, cap, (cena, em))
    pausa(i, CARTAO - 0.2)
    som = AQUI / "cartoes" / f"cap{n}_som.wav"
    if not som.exists():
        __import__("subprocess").run(["ffmpeg", "-v", "error", "-y", "-i", str(AQUI / "cartoes" / f"cap{n}.mp4"), "-vn", "-ac", "2",
                                      "-ar", "48000", str(som)], check=True)
    fx(i, None, f"cartao{n}", -11, atraso=-CARTAO + 0.05, arquivo=str(som))
    batidas[i]["musica"] = {"som": "nenhum", "atraso": -CARTAO - 0.6}
    batidas[i + 1]["musica"] = {**TRILHA, "continuar": True}


HIST = []                          # grupo do TCC visto do celular da CAMILA ("eu")


def chat(i, *novas, sons=True, legenda=True):
    msgs = [dict(m, apos=-30) for m in HIST[-6:]]
    for m in novas:
        m = dict(m); m.setdefault("apos", 0.3)
        msgs.append(m); HIST.append({k: v for k, v in m.items() if k not in ("apos", "em", "digitando")})
        if sons and "em" not in m:
            fx(i, None, "ep08_msg", -19, atraso=m["apos"])
        elif sons:
            fx(i, m["em"], "ep08_msg", -19)
    C(i, {"tipo": "chat", "grupo": "TCC - Documentário Isan 🎓", "membros": "Mateus, Camila, Prof. Henrique", "mensagens": msgs})
    if not legenda:
        batidas[i]["sem_legenda"] = True


def zoom(nome, z=(1.0, 1.08), foco=((0.5, 0.5), (0.5, 0.48)), **kw):
    return img(nome, z, foco, **kw)


# ================================================================ GANCHO — sem Vigia
C(0, c3(IA("G01", 2), "entrar", (0.5, 0.5), 1.0, 0.2))
C(1, zoom(IA("G01", 1), (1.0, 1.07), ((0.45, 0.5), (0.48, 0.5))))
C(2, seco(zoom(IA("G02", 1), (1.0, 1.06), ((0.42, 0.5), (0.42, 0.45)))))
C(3, obt(clipe("V01_A", cam="CAM 01 - CORREDOR", hora="03:17:40")))
obt_som(3)
C(4, obt(zoom(IA("G04a", 1), (1.0, 1.05))), (obt(zoom(IA("G04b", 2), (1.0, 1.06), ((0.4, 0.55), (0.4, 0.6)))), "vazia"),
  (obt(zoom(IA("G04c", 1), (1.02, 1.1), ((0.45, 0.5), (0.42, 0.5)))), "tempo"))
obt_som(4); obt_som(4, "vazia"); obt_som(4, "tempo")
amb(0, "ep10_mata_noite", -22)
fx(0, None, "ep10_respiracao", -27, atraso=-0.4)
fx(3, None, "ep10_cctv_estatica", -24, ate=1.2, saida=0.5)
pausa(4, 0.5)

# ================================================================ TEMA — Vigia: o terror da hospedagem
C(5, vigia((1.0, 1.04)))
saida_lenta(5, 5.4, dur=2.2)
batidas[5]["cena"].update({"antecipar": 7.2, "antecipar_fixo": True})   # o título aparece sobre o Vigia
fx(5, None, "ep10_gongo", -18, atraso=-6.2)
# 6–7 continuam na cena do Vigia (16/11: troca Vigia→Vigia fazia um "fantasma" dele)
C(8, c3(IA("T01", 2), "entrar", (0.5, 0.55), 0.9, 0.2))
C(10, filme("arq_templo"))
C(11, ficha("ศาสนาผี · Satsana Phi\nReligião animista dos espíritos da Tailândia", "Satsana Phi"))
C(12, c3(IA("C1_02", 1), "entrar", (0.6, 0.45), 0.9, 0.2, atmos={"neblina": 0.3}))
C(13, vigia((1.04, 1.1), ((0.45, 0.48), (0.43, 0.46))))
amb(5, "nenhum"); amb(8, "ep10_arrozal_noite", -28); amb(11, "nenhum"); amb(12, "ep10_mata_quieta", -28); amb(13, "nenhum")
pausa(9, 0.4); pausa(11, 0.6); pausa(12, 1.0); pausa(12, 0.6); pausa(14, 0.8)

# ================================================================ CAPÍTULO 1 — o aluguel da terra e os famintos
capitulo(14, 1, real("C1_01_real"), "Se")
C(15, obt(real("C1_sanphraphum_07")))
obt_som(15)
C(16, ficha("ศาลพระภูมิ · San Phra Phum\nCasa dos espíritos guardiões da terra", "San Phra Phum"))
C(17, real("C1_sanphraphum_08"))
C(18, c3(IA("C1_03", 1), "entrar", (0.55, 0.5), 0.8, 0.2), (real("C1_oferenda_01"), "oferecendo"))
C(19, zoom(IA("C1_02", 2), (1.0, 1.07), ((0.5, 0.5), (0.55, 0.45))))
C(20, zoom(IA("C1_04", 1), (1.0, 1.08), ((0.5, 0.5), (0.65, 0.4))))
C(21, ficha("ผีตายโหง · Phi Tai Hong\nEspíritos de morte violenta ou súbita", "Phi Tai Hong"))
pausa(22, 2.4)
C(22, clipe("V03_A"))
C(23, clipe("V03_B"))
C(24, c3(IA("C1_05", 2), "entrar", (0.6, 0.55), 1.0, 0.3, atmos={"neblina": 0.4}))
C(25, zoom(IA("C1_04", 1), (1.15, 1.25), ((0.7, 0.35), (0.72, 0.33))))
C(26, zoom(IA("C1_05", 1), (1.0, 1.06), ((0.6, 0.6), (0.6, 0.62)), atmos={"neblina": 0.4}))
C(27, zoom(IA("C1_04", 2), (1.1, 1.22), ((0.45, 0.5), (0.4, 0.55))))
amb(15, "ep10_arrozal_noite", -28); amb(20, "nenhum"); amb(22, "ep10_mata_noite", -26); amb(27, "nenhum")
fx(25, "fome", "sub_drop", -21)
pausa(17, 0.5); pausa(19, 0.4); pausa(25, 0.6); pausa(27, 0.8); pausa(28, 0.8)

# ================================================================ CAPÍTULO 2 — as criaturas da noite
capitulo(28, 2, filme("arq_vila"), "Quando")
C(29, zoom(IA("C2_01", 2), (1.0, 1.1), ((0.6, 0.4), (0.58, 0.35))))
C(30, ficha("กระสือ · Krasue\nEspírito noturno da cabeça flutuante", "Krasue"))
pausa(31, 2.6)
C(31, c3(IA("C2_02", 1), "entrar", (0.5, 0.45), 0.8, 0.2))
C(32, zoom(IA("C2_02", 2), (1.0, 1.1), ((0.5, 0.5), (0.25, 0.55))))
C(33, zoom(IA("C2_03", 1), (1.0, 1.06), ((0.7, 0.4), (0.72, 0.38))), (filme("kiss_krasue"), "arrastando"))
C(34, obt(real("C2_01_real")))
obt_som(34)
C(35, zoom(IA("C2_04", 1), (1.0, 1.08), ((0.5, 0.5), (0.52, 0.55))))
C(36, zoom(IA("C2_02", 1), (1.06, 1.12), ((0.7, 0.45), (0.72, 0.42))))
C(37, ficha("ผีปอบ · Phi Pop\nEspírito parasita devorador de órgãos", "Phi Pop"))
pausa(38, 2.6)
C(38, c3(IA("C2_05", 1), "entrar", (0.5, 0.6), 0.9, 0.2))
C(39, zoom(IA("C2_05", 2), (1.0, 1.06), ((0.6, 0.55), (0.62, 0.55))))
C(40, filme("arq_canais"))
C(41, zoom(IA("C2_05", 3), (1.0, 1.1), ((0.45, 0.6), (0.5, 0.62))))
C(42, zoom(IA("C2_05", 4), (1.0, 1.06), ((0.4, 0.6), (0.42, 0.6))), (real("C2_palafita_01"), "expulsaram"))
amb(29, "ep10_vila_caes", -28); amb(33, "nenhum"); amb(35, "ep10_mata_noite", -27); amb(40, "nenhum"); amb(41, "ep10_mata_quieta", -27)
fx(32, "descola", "sub_drop", -20)
fx(30, None, "ep10_caes_uivando_2", -28, atraso=0.2, ate=4.0, saida=1.5)
pausa(30, 0.6); pausa(33, 0.4); pausa(35, 0.8); pausa(37, 0.6); pausa(41, 0.6); pausa(43, 0.8)

# ================================================================ CAPÍTULO 3 — os corpos emprestados e a magia proibida
capitulo(43, 3, c3(IA("C3_01", 1), "entrar", (0.5, 0.5), 0.9, 0.2, atmos={"poeira": 0.3}), "Para")
C(44, ficha("ร่างทรง · Rang Song\nLiteralmente “corpo receptor”: o médium ancestral", "Rang Song"))
pausa(45, 2.6)
C(45, obt(c3(IA("C3_02", 1), "entrar", (0.5, 0.45), 0.8, 0.2)), (filme("arq_velas"), "rituais"))
obt_som(45)
C(46, zoom(IA("C3_02", 2), (1.0, 1.06), ((0.5, 0.5), (0.5, 0.45))))
C(47, filme("arq_oferendas"))
C(48, zoom(IA("C3_03", 1), (1.0, 1.1), ((0.4, 0.55), (0.38, 0.55))))
C(49, clipe("V04_A"))
C(50, clipe("V04_B", ate=5.0), (zoom(IA("C3_03", 2), (1.0, 1.08), ((0.5, 0.5), (0.5, 0.45))), "punir"))
C(51, c3(IA("C3_04", 1), "entrar", (0.5, 0.5), 0.8, 0.1))
C(53, zoom(IA("C3_04", 2), (1.0, 1.08), ((0.6, 0.45), (0.6, 0.4))), (real("C3_02_real"), "Pha"))
C(54, real("C3_kumanthong_01"))
C(55, zoom(IA("C3_04", 1), (1.1, 1.35), ((0.25, 0.35), (0.22, 0.3))))
C(56, c3(IA("C3_03", 2), "entrar", (0.5, 0.5), 0.9, 0.2, atmos={"poeira": 0.3}))
C(57, zoom(IA("G04a", 2), (1.0, 1.06), ((0.45, 0.45), (0.45, 0.4))))
C(58, zoom(IA("G04a", 1), (1.06, 1.12), ((0.5, 0.45), (0.52, 0.45))))
C(59, zoom(IA("G04a", 2), (1.08, 1.22), ((0.48, 0.4), (0.48, 0.38))))
amb(44, "nenhum"); amb(46, "ep10_mata_quieta", -28); amb(51, "nenhum"); amb(56, "ep10_mata_noite", -28)
fx(49, None, "ep10_tambor_ritual_1", -24, ate=8.0, saida=2.5)
fx(55, "queixo", "sub_drop", -21)
fx(59, "selo", "ep10_tambor", -15)
pausa(48, 0.6); pausa(50, 0.6); pausa(55, 0.8); pausa(59, 0.4); pausa(60, 1.0)

# ================================================================ CAPÍTULO 4 — quando a câmera entrou na floresta
capitulo(60, 4, c3(IA("C4_01", 1), "entrar", (0.45, 0.45), 0.9, 0.3, atmos={"neblina": 0.4}), "Em")
C(61, ficha("ร่างทรง · Rang Song (The Medium)\n2021 · Dir. Banjong Pisanthanakun", "The Medium"))
pausa(62, 2.6)
C(62, real("T_phuhinrongkla_02"), (filme("medium_isan"), "longa"))
C(63, real("C4_phitakhon_03"))
C(64, clipe("V05_A", cam="CAM 03 - QUARTO", hora="03:02:11"), (cctv(zoom(IA("C4_02", 1), (1.0, 1.08), ((0.6, 0.55), (0.62, 0.55))), "CAM 03 - QUARTO", "03:02:19"), "corpo"))
C(65, filme("arq_oferendas", video_inicio=2.0), (filme("arq_velas"), "monges"))
C(66, clipe("V05_B", cam="CAM 03 - QUARTO", hora="03:41:56", congelar=True))
amb(61, "nenhum"); amb(64, "ep10_mata_quieta", -28); amb(65, "nenhum"); amb(66, "ep10_mata_quieta", -28)
fx(64, None, "ep10_cctv_estatica", -26, ate=1.0, saida=0.5)
pausa(62, 0.6); pausa(66, 0.6); pausa(67, 1.2)

# ================================================================ APARTE — Vigia: a hospedagem
C(67, vigia((1.0, 1.04)))
C(71, c3(IA("G02", 1), "entrar", (0.42, 0.5), 0.9, 0.2, atmos={"neblina": 0.3}))
C(72, vigia((1.04, 1.1), ((0.45, 0.48), (0.43, 0.46))))
C(73, zoom(IA("C2_03", 2), (1.0, 1.06), ((0.6, 0.45), (0.6, 0.42))))
C(74, vigia((1.08, 1.14), ((0.42, 0.45), (0.4, 0.43))))
amb(67, "nenhum")
fx(74, "pele", "sub_drop", -21)
pausa(71, 0.6); pausa(73, 0.4)

# ================================================================ MATEUS — 1: o trabalho de campo em Loei
C(75, zoom(IA("H01", 1), (1.0, 1.08), ((0.35, 0.5), (0.4, 0.5))))
C(76, zoom(IA("H01", 2), (1.0, 1.06), ((0.5, 0.55), (0.5, 0.55))))
C(77, real("T01_real"))
chat(78, {"de": "Mateus", "tipo": "foto", "imagem": IA("H01", 2), "hora": "09:12", "apos": 0.4},
     {"de": "Mateus", "texto": "material bruto do dia 1 tá na pasta 📁", "hora": "09:12", "apos": 1.4})
chat(79, {"de": "Mateus", "tipo": "audio", "duracao": "0:19", "hora": "16:40", "apos": 0.2})
C(80, zoom(IA("H03", 1), (1.0, 1.06), ((0.6, 0.5), (0.62, 0.45))))
C(81, zoom(IA("H03", 2), (1.0, 1.06), ((0.6, 0.45), (0.6, 0.42))), (real("C3_amuleto_02"), "panos"))
C(82, zoom(IA("H04", 1), (1.0, 1.06), ((0.4, 0.6), (0.4, 0.62))))
C(83, c3(IA("H04", 2), "entrar", (0.5, 0.6), 0.9, 0.2))
chat(84, {"de": "Mateus", "tipo": "foto", "imagem": IA("H05", 1), "hora": "03:17", "apos": 0.5, "em": "foto"})
C(85, obt(zoom(IA("H05", 1), (1.0, 1.06), ((0.5, 0.6), (0.5, 0.68)))), (zoom(IA("H05", 2), (1.0, 1.06), ((0.6, 0.5), (0.65, 0.5))), "lençol"))
obt_som(85)
amb(75, "nenhum"); amb(80, "ep10_arrozal_noite", -28); amb(82, "ep10_mata_noite", -24); amb(84, "nenhum"); amb(85, "ep10_vila_caes", -30)
fx(85, "cachorros", "ep10_caes_uivando_1", -22, ate=6.0, saida=2.0)
pausa(77, 0.6); pausa(81, 0.6); pausa(82, 0.6); pausa(86, 1.4)

# ================================================================ MATEUS — 2: as câmeras no corredor
C(86, zoom(IA("H06", 2), (1.0, 1.06)), (zoom(IA("H06", 1), (1.0, 1.06), ((0.35, 0.45), (0.3, 0.42))), "registrar"))
C(87, cctv(zoom(IA("H09", 1), (1.0, 1.03)), "CAM 01 - CORREDOR", "14:22:10"))
C(88, zoom(IA("H07", 1), (1.0, 1.08), ((0.55, 0.45), (0.55, 0.42))))
C(89, c3(IA("C3_02", 1), "entrar", (0.5, 0.45), 0.8, 0.2), (zoom(IA("C3_01", 2), (1.0, 1.08), ((0.5, 0.3), (0.5, 0.25))), "cordões"))
chat(90, {"de": "eu", "texto": "Mateus, isso ainda é seguro? Parece exatamente o que você descreveu sobre Phi Pop", "hora": "22:31", "apos": 0.2},
     {"de": "eu", "tipo": "audio", "duracao": "0:14", "hora": "22:32", "apos": 1.6})
chat(91, {"de": "Mateus", "tipo": "audio", "duracao": "0:21", "hora": "22:47", "apos": 0.2})
C(92, clipe("V07_A", cam="CAM 01 - CORREDOR", hora="23:00:04"))
C(93, zoom(IA("H06", 1), (1.0, 1.12), ((0.35, 0.45), (0.3, 0.4))))
C(94, seco(cctv(zoom(IA("H10", 1), (1.0, 1.02)), "CAM 01 - CORREDOR", "01:12:33")))
C(95, seco(cctv(zoom(IA("H11", 1), (1.0, 1.02)), "CAM 01 - CORREDOR", "02:40:07")), (clipe("V07x_B", cam="CAM 01 - CORREDOR", hora="02:40:09"), "disparou"))
amb(86, "nenhum"); amb(88, "ep10_mata_quieta", -28); amb(90, "nenhum"); amb(91, "ep10_chuva_mata", -28)
amb(92, "ep10_mata_quieta", -26); amb(94, "ep10_mata_quieta", -24)
fx(92, None, "ep10_tambor_ritual_2", -26, ate=7.0, saida=2.5)
fx(94, None, "ep10_cctv_estatica", -27, ate=0.8, saida=0.3)
fx(95, None, "ep10_cctv_estatica", -27, ate=0.8, saida=0.3)
fx(95, "disparou", "ep10_fogo_pano", -22, ate=3.0, saida=1.0)
pausa(89, 0.6); pausa(93, 0.6); pausa(95, 0.8); pausa(96, 1.4)

# ================================================================ MATEUS — 3: não abra a porta
C(96, clipe("V08_A", cam="CAM 01 - CORREDOR", hora="02:40:31"))
C(97, clipe("V08_B", cam="CAM 01 - CORREDOR", hora="02:40:44"))
C(98, cctv(zoom(IA("H12", 2), (1.0, 1.04)), "CAM 02 - PORTA", "02:41:02"))
C(99, zoom(IA("H07", 2), (1.0, 1.06), ((0.75, 0.5), (0.76, 0.48))))
C(100, zoom(IA("H13", 1), (1.0, 1.08), ((0.65, 0.55), (0.66, 0.55))))
chat(101, {"de": "Mateus", "tipo": "audio", "duracao": "0:11", "hora": "02:43", "apos": 0.2})
# 16/11 (rascunho 2, usuário: "a fala do professor não entra… fica sem sentido"): o Prof. Henrique responde com um
# ÁUDIO (vozes/gerar_professor.py, voz Orus, filtro de celular) na pausa, e a mensagem escrita chega logo depois
chat(102, {"de": "Prof. Henrique", "tipo": "audio", "duracao": "0:06", "hora": "02:44", "apos": -7.6, "cor": "#ff6b5e"},
     {"de": "Prof. Henrique", "texto": "MATEUS NÃO ABRE ESSA PORTA. LEMBRE DO QUE VOCÊ PESQUISOU SOBRE OS RANG SONG", "hora": "02:44",
      "apos": -1.4, "cor": "#ff6b5e"})
pausa(102, 8.0)
fx(102, None, "prof_henrique", 2, atraso=-7.2, arquivo=str(AQUI / "vozes" / "limpas_escolhidas" / "prof_cel.wav"))   # 16/11: a mensagem do professor chega e dá tempo de ler ANTES de "Mas Mateus já tinha guardado o celular"
C(103, clipe("V09_A", cam="CAM 01 - CORREDOR", hora="02:44:52"))
C(104, cctv(zoom(IA("H10", 2), (1.0, 1.03)), "CAM 01 - CORREDOR", "02:45:03"))
C(105, cctv(zoom(IA("H10", 2), (1.04, 1.1), ((0.5, 0.45), (0.5, 0.4))), "CAM 01 - CORREDOR", "02:45:09"))
C(106, obt(cctv(zoom(IA("H16", 2), (1.0, 1.04)), "CAM 01 - CORREDOR", "02:45:20")),
  (cctv(zoom(IA("H16", 2), (1.12, 1.3), ((0.55, 0.15), (0.55, 0.1))), "CAM 01 - CORREDOR", "02:45:23"), "desceu"))
obt_som(106)
C(107, cctv(zoom(IA("H16", 2), (1.3, 1.34), ((0.55, 0.15), (0.55, 0.12))), "CAM 01 - CORREDOR", "02:45:26", queda=1.6))
chat(108, {"de": "Mateus", "tipo": "foto", "imagem": IA("H17", 1), "hora": "06:12", "apos": 0.6},
     {"de": "Mateus", "tipo": "video", "imagem": IA("H18", 4), "hora": "06:12", "apos": 2.2})
C(109, obt(zoom(IA("H17", 1), (1.0, 1.06), ((0.4, 0.55), (0.38, 0.55)))))
obt_som(109)
C(110, clipe("V10_B", ate=3.2, cam="CAM 04 - QUARTO", hora="06:12:01", queda=3.0, z=(1.0, 1.02), congelar=True))
C(111, c3(IA("T01", 1), "entrar", (0.5, 0.5), 0.8, 0.2, atmos={"neblina": 0.4}))
C(112, zoom(IA("G01", 2), (1.0, 1.06), ((0.5, 0.5), (0.5, 0.48))))
C(113, c3(IA("C2_02", 2), "entrar", (0.12, 0.55), 0.9, 0.3, atmos={"neblina": 0.4}))
amb(96, "nenhum"); amb(98, "ep10_mata_quieta", -28); amb(103, "nenhum"); amb(106, "nenhum"); amb(108, "ep10_arrozal_noite", -30)
amb(110, "nenhum"); amb(111, "ep10_mata_noite", -27)
fx(96, None, "ep10_cctv_estatica", -27, ate=0.8, saida=0.3)
fx(98, "som", "ep09_choro_parede", -27, ate=7.0, saida=2.0)
fx(98, "som", "ep10_batida_madeira", -22, atraso=1.2)
fx(99, "chorando", "ep09_choro_parede", -25, ate=6.0, saida=2.0)
fx(103, None, "ep10_porta_madeira", -18, atraso=0.4)
fx(106, "desceu", "ep10_rangido_viga", -20)
fx(107, "caiu", "ep10_queda_wifi", -16)
fx(110, None, "ep10_cctv_estatica", -24, atraso=2.9, ate=2.5, saida=1.0)
fx(110, None, "sub_drop", -18, atraso=3.0)
pausa(97, 0.4); pausa(99, 0.6); pausa(103, 0.6); pausa(105, 0.8); pausa(107, 1.0); pausa(110, 0.6); pausa(111, 1.6); pausa(113, 0.6); pausa(114, 1.4)

# ================================================================ FECHO — Vigia
C(114, vigia((1.0, 1.04)))
C(115, zoom(IA("H17", 2), (1.0, 1.06), ((0.4, 0.6), (0.38, 0.62))))
C(116, vigia((1.02, 1.07)))
C(117, c3(IA("G02", 1), "sair", (0.42, 0.5), 0.9, 0.2, atmos={"neblina": 0.3}))
C(118, vigia((1.0, 1.05)))
C(119, zoom(IA("F01", 2), (1.0, 1.06), ((0.35, 0.5), (0.35, 0.45))), (real("F01_real"), "noiva"))
C(120, zoom(IA("F02", 1), (1.0, 1.08), ((0.3, 0.45), (0.32, 0.5))))
C(121, zoom(IA("F03", 1), (1.0, 1.06), ((0.55, 0.45), (0.55, 0.4))), (real("F_pret_02"), "gigantes"))
C(122, vigia((1.04, 1.1), ((0.45, 0.48), (0.43, 0.46))))
C(124, vigia((1.08, 1.14), ((0.42, 0.45), (0.4, 0.43))))
amb(114, "nenhum"); amb(119, "ep10_arrozal_noite", -30); amb(122, "nenhum")
fx(117, "casa", "ep10_tambor", -17)
fx(124, "nome", "ep10_batida_madeira", -20, atraso=0.6)
pausa(117, 0.8); pausa(121, 0.6); pausa(124, 0.4)

# ================================================================ VINHETA FIXA DE INSCRIÇÃO
batidas.append({"fala": F.VINHETA, "cta_inicio": True, "sem_legenda": True, "ambiente": {"som": "nenhum"},
                "musica": {"som": "vinheta_ultimo_abrigo", "volume_db": -20}})

voz = "audio/voz_personagens.wav" if (AQUI / "audio" / "voz_personagens.wav").exists() else "audio/voz_com_vinheta_limpa.wav"
roteiro = {
    "modo": "cenas", "formato": "16:9", "tema": "vigia", "avatar": "vigia_hd",
    "voz_arquivo": voz,
    "transcrever_pedacos": 75,
    "cintilar": 0.03, "apertar_pausas": False,
    "cena_minima": 3.0,
    "vigia_padrao": False,
    "cauda": 1.6, "chuva": 0, "grao": 0.14,
    "mix": {"musica_ganho_db": 12, "fundo_sob_voz": -9, "efeitos_sob_voz": -4, "voz_pro": True, "fundo_bolso": True,
            "efeitos_pico_max": -3},
    "legendas": {"destaques": ["Isan", "Tailândia", "Satsana Phi", "San Phra Phum", "Phi Tai Hong", "Krasue", "Phi Pop", "Rang Song",
                               "Saiyasat", "Pha Yant", "Nam Man Phrai", "Loei", "Mateus", "Niran", "Mo Tham", "hospedagem", "casa"]},
    "ambiente_inicial": [{"som": "ep10_mata_noite", "volume_db": -24}],
    "musica": TRILHA,
    "titulo_ep": {"antes_da_batida": 5, "linhas": ["O VIGIA · EPISÓDIO 10", "POR QUE O TERROR TAILANDÊS", "NUNCA DEIXA", "VOCÊ EM PAZ?"],
                  "vermelho": "EM PAZ?", "duracao": 5.6, "folga": 1.0, "centro": True},
    "cta": {"titulo": "Não pergunte quem é.", "canal": "Último Abrigo",
            "subtitulo": "Inscreva-se para mais casos do Vigia",
            "fundo": "../../painel/cenarios/abrigo_16x9.png", "pose": "c_cafe_convite",
            "antes": 0.6, "clique_em": "Inscreva-se", "duracao": 2.5},
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
        if c.get("tipo") == "texto" and "em" not in c:
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
if faltando:
    raise SystemExit("arquivos faltando: " + ", ".join(faltando))
sons_dir = AQUI.parents[1] / "painel" / "sons"
sons = {s["som"] for b in batidas for s in b.get("sons", []) if not s.get("arquivo")} | {b[k]["som"] for b in batidas for k in ("ambiente", "musica") if b.get(k)}
sem_som = sorted(s for s in sons if s not in ("nenhum", TRILHA_SOM) and not list(sons_dir.glob(s + ".*")))
if sem_som:
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
        if int(k) in (102,):   # 16/11: a pausa da mensagem do professor é de leitura, não é compensação
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
        cs = cenas_de(b); n = 3.6
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

    PROTEGE = {3, 4, 5, 14, 28, 43, 60, 82, 93, 94, 95, 98, 103, 104, 105, 106, 107, 110, 117, 124}   # sustos e silêncios: nunca continuar a anterior
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
    """16/11: a trilha UNIDA (sintetizar_isan_ep10.py: drone, cordas, ritual) feita sob medida para o episódio: cada parte
    cobre uma seção e a fusão de 18 s cai na virada da seção. Os tempos vêm do alinhamento + pausas (os mesmos do vídeo).
    Só regera quando o plano muda (guardado em painel/sons/ep10_trilha.plano)."""
    cum, T0 = 0.0, []
    for i in range(len(falas)):
        cum += batidas[i].get("pausa_antes_s", 0); T0.append(_ali[_ini[i]][0] + cum)
    fim = _ali[-1][1] + cum + 30
    secs = [(0, "drone"), (SEC["CAPÍTULO 1"], "cordas"), (SEC["CAPÍTULO 3"], "ritual"), (SEC["APARTE"], "drone"),
            (SEC["MATEUS — 2"], "cordas"), (SEC["MATEUS — 3"], "ritual"), (SEC["FECHO"], "drone")]
    S = [0.0] + [T0[i] - (CARTAO if i in (SEC["CAPÍTULO 1"], SEC["CAPÍTULO 3"]) else 0) for i, _ in secs[1:]] + [fim]
    F_ = 18.0
    partes = []
    for k, (_, nome) in enumerate(secs):
        d = S[k + 1] - S[k] + (F_ / 2 if k == 0 else F_) + (F_ / 2 if k == len(secs) - 1 else 0)
        partes.append(f"{nome}:{max(F_ + 4, round(d, 1))}")
    plano = ",".join(partes)
    sons = AQUI.parents[1] / "painel" / "sons"
    marca = sons / f"{TRILHA_SOM}.plano"
    if (sons / f"{TRILHA_SOM}.mp3").exists() and marca.exists() and marca.read_text() == plano:
        return
    print("trilha:", plano, flush=True)
    __import__("subprocess").run([sys.executable, str(AQUI.parents[1] / "painel" / "ferramentas" / "sintetizar_isan_ep10.py"), "unida",
                                  str(sons / f"{TRILHA_SOM}.mp3"), plano], check=True)
    marca.write_text(plano)


trilha_por_secoes()


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
        if not v or v.startswith("camera3d"):
            continue
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
