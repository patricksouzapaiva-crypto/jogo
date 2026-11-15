"""Monta roteiro.json do Ep. 09 v4 (15/11: molde do Ep. 08 — tema novo, capítulos 1–3 de lendas, aparte do han, a
história do Rafa e o fecho novo; identidade coreana: talismã, sombra, água, TV de tubo; trilha única do Ep. 08). Antes: v3 "O que voltou da montanha" (falas.py: cada frase do ROTEIRO.md = 1 batida).
Regras da casa (QUALIDADE.md): Vigia só no tema/fecho, com o título ao lado dele; música o episódio inteiro, uma
faixa por parte; ninguém de frente (a criatura e a irmã falsa nunca mostram o rosto); SEM foco redondo; zoom só
onde o assunto inteiro cabe; kanji em "luz"/"sangue" (nunca tinta preta no escuro), com tempo de leitura.
Sustos liberados (13/11) "desde que bem construídos": silêncio ANTES (a música sai uma frase antes), ameaça
anunciada pela narração, corte seco + cordas, rosto nunca mostrado, saída lenta depois.
Uso: python3 montar_roteiro.py  → roteiro.json (+ camera3d/*.mp4 na primeira vez)
"""
import hashlib
import json
import sys
from pathlib import Path

import falas as F

AQUI = Path(__file__).parent
falas, PERS, SEC, PAUSAS, _ = F.ler()
assert len(falas) == 242 and falas[221] == '"Oppa. Você voltou."' and PERS.get(211) == "rafa_falso", \
    "o ROTEIRO.md mudou: rever os índices"
batidas = [{"fala": f} for f in falas]
for i, s in PAUSAS.items():
    batidas[i]["pausa_antes_s"] = s

I, IV2, CL, FP = "imagens_v3/", "imagens/", "clipes_v3/", "filmes_prontos/"
E, X, CL4 = "imagens_v4/escolhidas/", "imagens_v4/extras/", "clipes_v4/"
TRILHA = {"som": "ep08_japones_longa", "volume_db": -30}      # 15/11: a trilha do Ep. 08 no episódio inteiro, +2 dB
# v3 → v4: cada imagem antiga da história do Rafa aponta para a escolhida nova (imagens_v4/SELECAO.md); as que ficaram
# do v3 (a criatura, a cozinha, o corredor, a menina do estábulo) continuam em imagens_v3/
MAPA = {"M01_A": E + "M01", "M01_B": X + "M01_B", "M01_C": E + "M01", "M02_A": E + "M03", "M02_B": E + "M02", "M02_C": X + "M03_A",
        "M03_A": E + "M04", "M03_B": X + "M04_B", "M04_A": E + "M06", "M04_D": X + "M06_B", "M05_A": E + "M07", "M05_B": X + "M07_B",
        "M06_A": X + "M08_A", "M06_B": E + "M08", "M06_C": X + "M08_A", "C02_B": E + "C03", "C02_C": X + "C03_B",
        "C04_A": X + "C06_A", "C04_B": E + "C06", "C05_A": E + "C07", "C05_B": X + "C07_A", "C05_C": E + "C07",
        "J01_A": E + "J01", "J01_B": X + "J01_B", "J03_A": E + "J04", "J03_B": X + "J04_B", "J04_A": E + "J05", "J04_B": X + "J05_A",
        "H01_A": E + "H01", "H01_B": X + "H01_B", "H02_A": E + "H03", "H02_B": X + "H03_B", "H03_A": E + "H04", "H03_B": X + "H04_A",
        "H03_C": E + "H04", "H04_A": E + "H05", "H04_B": X + "H05_B", "H05_A": E + "H06", "H05_B": X + "H06_B", "H05_C": E + "H06",
        "H06_A": X + "H07_A", "H06_B": E + "H07", "H07_A": E + "H08", "H07_B": X + "H08_B", "H08_B": E + "H09", "H08_C": X + "H09_A",
        "H09_A": E + "H11", "H09_B": X + "H11_B", "H10_C": E + "H12"}


def P(nome):
    """Caminho da imagem: aceita um caminho pronto (com "/") ou um código v3 (traduzido pelo MAPA)."""
    if "/" in nome:
        return nome if nome.endswith(".jpg") else nome + ".jpg"
    return MAPA[nome] + ".jpg" if nome in MAPA else I + nome + ".jpg"


_CORTES = {}


def vid4(nome, video_inicio=0.0, dur_max=None, **kw):
    """Clipe do Flow v4 (CLIPES_V4.md): dur_max corta o arquivo antes do erro da IA (rosto, vela andando…)."""
    arq = CL4 + nome + "_A.mp4"
    if dur_max:
        saida = AQUI / CL4 / f"{nome}_A_ate{dur_max}.mp4"
        if not saida.exists():
            __import__("subprocess").run(["ffmpeg", "-v", "error", "-y", "-i", str(AQUI / arq), "-t", str(dur_max), "-an", "-c:v", "libx264",
                                          "-crf", "16", str(saida)], check=True)
        arq = CL4 + saida.name
    return {"video": arq, "zoom": [1.0, 1.03], **({"video_inicio": video_inicio} if video_inicio else {}), **kw}
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


def capitulo(i, n, titulo, sub, imagem, cena, em, selo="恨"):
    """15/11 v4: cartão de capítulo = o TALISMÃ (coreia.js): o papel amarelo desce, o pincel de cinábrio escreve 제N장, o
    carimbo bate com o gongo e o título entra; a cena seguinte entra QUEIMANDO o talismã (brasas)."""
    cap = {"tipo": "talisma", "numero": f"제{n}장", "numero_pt": f"Capítulo {n}", "titulo": titulo, "ano": sub, "selo": selo,
           "imagem": imagem, "antecipar": 5.4, "entrada": "hanji", "duracao_entrada": 1.0}
    cena = dict(cena); cena["entrada"] = "queimar"; cena["duracao_entrada"] = 1.5
    C(i, cap, (cena, em))
    pausa(i, 5.6)
    fx(i, None, "ep09_papel", -16, atraso=-5.35)
    fx(i, None, "ep08_pincel", -14, atraso=-4.85)
    fx(i, None, "ep09_gut_jing_1", -12, atraso=-3.5)                  # o carimbo bate (1,9 s depois do talismã entrar)
    fx(i, None, "ep08_tinta", -18, atraso=-3.1)


HIST = []                          # grupo "Família 🏠" visto do celular da MÃE ("eu")


def chat(i, *novas, sons=True):
    msgs = [dict(m, apos=-30) for m in HIST[-6:]]
    for m in novas:
        m = dict(m); m.setdefault("apos", 0.3)
        msgs.append(m); HIST.append({k: v for k, v in m.items() if k not in ("apos", "em", "digitando")})
        if sons and "em" not in m:
            fx(i, None, "ep08_msg", -19, atraso=m["apos"])
        elif sons:
            fx(i, m["em"], "ep08_msg", -19)
    C(i, {"tipo": "chat", "grupo": "Família 🏠", "membros": "Mãe, Pai, Rafa, Lívia", "mensagens": msgs})
    batidas[i]["sem_legenda"] = True


def pincel(i, em, db=-16, atraso=0.0):
    fx(i, em, "ep08_kanji", db, atraso=atraso)


def HAN(tam, x=0.5, **kw):                                                  # o elemento-marca: cada vez maior
    return K("한", x, 0.5, "luz", "han", tam=tam, **kw)               # rascunho 1: "tinta" (preto) sumia no escuro

# ================================================================ GANCHO — sem Vigia (03:00 em Busan / 15:00 em BH)
C(0, {"tipo": "relogios", "lados": [{"nome": "Busan", "hora": "03:00", "imagem": E + "H03.jpg", "brilho": 0.6},
                                     {"nome": "Belo Horizonte", "hora": "15:00", "imagem": IV2 + "F01_A.jpg", "brilho": 0.75}]})
chat(1, {"de": "Rafa", "tipo": "audio", "duracao": "0:06", "hora": "15:00", "em": "áudio", "digitando": 0.6})
C(2, vid4("V20"), (c3(E + "H04.jpg", "entrar", (0.6, 0.45), 0.8, 0.2), "subindo"))                                                        # o Rafa encostado no elevador; a luz acende
C(3, {"tipo": "elevador", "sequencia": [[4, 0.4], [2, 0.9], [6, 1.4], [2, 1.9], [10, 2.4]],
      "andar": [[2, 1.2], [3, 1.8], [4, 2.4], [5, 3.0], [6, 3.6], [7, 4.2], [8, 4.8], [9, 5.4], [10, 6.0], [11, 6.6], [12, 7.2]]})
T(3, "fundir", 1.2)
C(4, vid4("V17", video_inicio=4.0, atmos={"neblina": 0.3}), (img(E + "M08.jpg", (1.0, 1.06), ((0.4, 0.5), (0.42, 0.48))), "voltou"))              # a irmã no degrau, de costas
C(5, c3(E + "M04.jpg", "entrar", (0.5, 0.5), 1.0, 0.3))                  # a mata escura
amb(0, "ep09_motor_elevador", -24)
batidas[3]["ambiente"] = {"som": "ep09_motor_elevador", "volume_db": -14}   # o motor SOZINHO nos 4 s
fx(3, None, "ep09_elevador", -20, atraso=-0.9)
amb(4, "ep09_mata_noite", -26)
pausa(5, 0.4)

# ================================================================ TEMA — Vigia: "o japonês é regra, o coreano é dívida"
C(6, vigia((1.0, 1.04)))
saida_lenta(6, 5.4, dur=2.2)
batidas[6]["cena"].update({"antecipar": 7.2, "antecipar_fixo": True})   # o título nunca aparece em cima da mata
fx(6, None, "ep09_jing", -17, atraso=-6.2)
C(7, vigia((1.0, 1.05)), (filme("wailing_vila"), "lá"), (vigia((1.03, 1.07)), "Não"))                  # "no Japão… regra" → o Vigia; a Coreia entra
C(8, c3(E + "M01.jpg", "lado", (0.45, 0.45), 0.8, 0.0))                  # Busan, o mar e a montanha
C(9, vigia((1.0, 1.06)))
C(10, img(E + "T07.jpg", (1.0, 1.08), ((0.5, 0.5), (0.5, 0.45)), kanji=K("빚", 0.8, 0.45, "sangue", "bit · dívida", tam=0.3, atraso=0.2)))
pincel(10, None, atraso=0.1)
C(11, vid4("V15"), (img(E + "T06.jpg", (1.0, 1.08), ((0.5, 0.5), (0.5, 0.45))), "deve"))                                                        # o altar da xamã: o que se deve aos mortos
C(12, vid4("V08"), (img(E + "A06.jpg", (1.06, 1.12), ((0.5, 0.4), (0.5, 0.36))), "voz"))                                                        # ela na porta
C(13, c3(E + "A01.jpg", "entrar", (0.3, 0.3), 0.8, 0.0), (c3(E + "H01.jpg", "entrar", (0.5, 0.45), 0.8, 0.0), "hospital"))
C(14, vigia((1.04, 1.1), ((0.45, 0.48), (0.43, 0.46))))
amb(6, "nenhum"); amb(11, "ep09_lenda_joseon", -27); amb(13, "nenhum")
pausa(8, 0.5); pausa(10, 0.8); pausa(12, 0.5); pausa(14, 0.6)

# ================================================================ CAPÍTULO 1 — Arang, o quarto do magistrado (séc. XVI)
capitulo(15, 1, "O quarto do magistrado", "Miryang · séc. XVI", E + "A02.jpg",
         c3(E + "A01.jpg", "entrar", (0.3, 0.35), 0.9, 0.2), "Miryang", selo="恨")
C(16, img(E + "A02.jpg", (1.0, 1.06), ((0.5, 0.6), (0.5, 0.62))))
C(17, c3(E + "A01.jpg", "lado", (0.6, 0.6), 0.8, 0.0))                   # a cidade lá embaixo; o pai indo embora
C(18, img(X + "A03_A.jpg", (1.0, 1.05), ((0.5, 0.55), (0.5, 0.55))))
C(19, c3(E + "A02.jpg", "entrar", (0.45, 0.65), 0.9, 0.2))
C(20, img(E + "A03.jpg", (1.0, 1.08), ((0.5, 0.65), (0.6, 0.72)), kanji=K("死", 0.18, 0.45, "sangue", "sa · morte", tam=0.26, atraso=0.6)))
pincel(20, None, atraso=0.5)
C(21, img(X + "A03_A.jpg", (1.08, 1.14), ((0.4, 0.7), (0.38, 0.72))))
C(22, c3(E + "A01.jpg", "sair", (0.3, 0.35), 0.8, 0.0))
C(23, vid4("V09"), (img(E + "A04.jpg", (1.0, 1.05), ((0.5, 0.5), (0.5, 0.47))), "nenhum"))                                                        # o magistrado que aceitou
C(24, img(E + "A04.jpg", (1.0, 1.03), ((0.5, 0.5), (0.5, 0.5))))         # "Ficou acordado." — quase parado
C(25, {"tipo": "sombra", "chega": [0.6, 4.6], "vela": [0.1, 0.8]})       # a vela treme; a sombra dela cresce no papel
C(26, vid4("V08"), (img(E + "A06.jpg", (1.1, 1.18), ((0.5, 0.55), (0.5, 0.6))), "Sangue"))
C(27, img(E + "A06.jpg", (1.0, 1.08), ((0.5, 0.4), (0.5, 0.35))))
C(28, vid4("V07", dur_max=4.0), (img(E + "A04.jpg", (1.05, 1.1), ((0.5, 0.45), (0.5, 0.42))), "perguntou"))
C(29, c3(E + "A07.jpg", "entrar", (0.6, 0.65), 0.9, 0.3, atmos={"neblina": 0.4}))   # o bambuzal, a pá
C(30, img(E + "A07.jpg", (1.05, 1.12), ((0.6, 0.7), (0.62, 0.72))))
C(31, img(E + "A04.jpg", (1.0, 1.06), ((0.5, 0.45), (0.5, 0.42))))
C(32, img(E + "A05.jpg", (1.0, 1.06), ((0.5, 0.5), (0.5, 0.45)), kanji=K("원한", 0.18, 0.45, "luz", "wonhan · a mágoa", tam=0.22, em="ouvida")))
pincel(32, "ouvida")
C(33, c3(E + "A08.jpg", "entrar", (0.4, 0.5), 0.8, 0.0))
amb(15, "nenhum"); amb(16, "ep09_lenda_joseon", -26); amb(25, "nenhum"); amb(26, "ep09_lenda_joseon", -26); amb(33, "ep09_lago", -30)
fx(19, None, "ep08_vela", -24)
fx(25, "vela", "ep08_vela", -18); fx(25, "papel", "ep09_papel", -16); fx(25, "papel", "ep09_sn_porta_rangido_lento", -22, ate=2.5, saida=0.5)
fx(26, "Sangue", "sub_drop", -20)
fx(30, "cavar", "ep05_raspar", -26, tom=-4)
pausa(18, 0.6); pausa(21, 0.6); pausa(24, 1.4); pausa(25, 0.8); pausa(27, 0.8); pausa(31, 0.8); pausa(32, 0.6); pausa(33, 1.4)

# ================================================================ CAPÍTULO 2 — as irmãs do lago (séc. XVII)
capitulo(34, 2, "As irmãs do lago", "Cheolsan · séc. XVII", E + "I05.jpg",
         c3(E + "I01.jpg", "entrar", (0.5, 0.5), 0.9, 0.2), "Cem", selo="怨")
C(35, c3(E + "I02.jpg", "entrar", (0.5, 0.6), 0.8, 0.2))
C(36, img(E + "I03.jpg", (1.0, 1.06), ((0.55, 0.45), (0.55, 0.42))))
C(37, img(X + "I03_A.jpg", (1.0, 1.06), ((0.5, 0.6), (0.45, 0.65))), (img(E + "I04.jpg", (1.0, 1.08), ((0.5, 0.65), (0.5, 0.7))), "ensanguentado"))
C(38, img(E + "I01.jpg", (1.05, 1.1), ((0.5, 0.55), (0.5, 0.55))))
C(39, img(E + "I03.jpg", (1.08, 1.12), ((0.5, 0.45), (0.5, 0.45))))
C(40, {"tipo": "agua", "imagem": E + "I05.jpg", "horizonte": 0.55, "zoom": [1.0, 1.0]})
C(41, vid4("V10"))                                                        # ela entra no lago
C(42, {"tipo": "agua", "imagem": E + "I07.jpg", "horizonte": 0.45, "afunda": [0.5, 0.42, 2.2], "zoom": [1.0, 1.0]})
C(43, img(E + "A02.jpg", (1.0, 1.06), ((0.5, 0.6), (0.5, 0.62))))
C(44, vid4("V11"), (img(E + "I08.jpg", (1.0, 1.08), ((0.45, 0.4), (0.45, 0.36))), "pingando"))                                                        # as duas, pingando
C(45, img(E + "I04.jpg", (1.1, 1.18), ((0.5, 0.65), (0.5, 0.68)), kanji=K("쥐", 0.82, 0.45, "sangue", "jwi · rato", tam=0.26, em="rato")))
pincel(45, "rato")
C(46, ficha("장화홍련전 · Janghwa e Hongryeon\nconto da era Joseon · Cheolsan", "Janghwa e Hongryeon"))
C(47, img(E + "I08.jpg", (1.06, 1.14), ((0.4, 0.4), (0.4, 0.35))))
C(48, vid4("V12", dur_max=4.5), (img(E + "I09.jpg", (1.0, 1.1), ((0.5, 0.5), (0.5, 0.45)), kanji=K("처녀귀신", 0.8, 0.45, "luz", "cheonyeo gwishin", tam=0.16, atraso=0.2)), "cheonyeo"),
      (img(E + "A06.jpg", (1.0, 1.08), ((0.5, 0.4), (0.5, 0.36))), "Porque"))
pincel(48, "cheonyeo")
amb(34, "nenhum"); amb(35, "ep09_lenda_joseon", -26); amb(40, "ep09_lago", -24); amb(43, "ep09_lenda_joseon", -27); amb(47, "ep09_lenda_mata", -27)
fx(41, None, "ep09_lago", -22, saida=2.0)
fx(44, "pingando", "ep09_sn_respiracao_medo", -30)
fx(45, "rato", "sub_drop", -21)
pausa(39, 0.8); pausa(41, 0.6); pausa(42, 1.2); pausa(45, 0.8); pausa(48, 1.2)

# ================================================================ CAPÍTULO 3 — o que não tem rosto (1977 → 2024)
capitulo(49, 3, "O que não tem rosto", "1977 → 2024", E + "T01.jpg",
         vid4("V13", dur_max=5.0), "E", selo="無")
C(50, img(E + "T01.jpg", (1.0, 1.08), ((0.57, 0.48), (0.57, 0.46)), kanji=K("달걀귀신", 0.2, 0.45, "luz", "dalgyal gwishin · o fantasma do ovo", tam=0.15, atraso=0.4)))
pincel(50, None, atraso=0.3)
C(51, img(E + "T01.jpg", (1.3, 1.5), ((0.57, 0.48), (0.57, 0.47))))
C(53, img(E + "T01.jpg", (1.6, 1.9), ((0.57, 0.48), (0.57, 0.48))))      # "quem vê… morre": chega na cabeça lisa
C(54, {"tipo": "crt", "imagem": E + "T03.jpg", "liga": 0.3, "rolar": [3.5]})
C(55, img(E + "T02.jpg", (1.0, 1.08), ((0.5, 0.45), (0.52, 0.4))))
C(56, c3(E + "T02.jpg", "entrar", (0.5, 0.35), 0.8, 0.0))
C(57, {"video": "tv/TV_deokdaegol.mp4", "zoom": [1.0, 1.0]})             # a TV da sala: o 덕대골 (KBS, 1996), com o grito
C(58, filme("exhuma_noite"))
C(59, {"video": "tv/TV_wolha.mp4", "zoom": [1.0, 1.0]}, (img(E + "T04.jpg", (1.05, 1.15), ((0.6, 0.5), (0.62, 0.48))), "cova"))
C(60, filme("wc_noite"), (img(E + "T05.jpg", (1.0, 1.08), ((0.5, 0.5), (0.5, 0.48))), "abriu"))
C(61, filme("irmas_chegada"))
C(62, filme("exhuma_cova"), (vid4("V14"), "primeiro"), (img(E + "T06.jpg", (1.0, 1.08), ((0.5, 0.5), (0.5, 0.45))), "visto"))
amb(49, "nenhum"); amb(50, "ep09_lenda_hospital", -27); amb(54, "nenhum"); amb(58, "ep09_lenda_mata", -28)
fx(53, "morre", "sub_drop", -18); fx(53, "morre", "ep09_jing", -24)
fx(54, None, "ep08_tv_chiado", -24, ate=3.0, saida=1.0)
fx(57, None, "tv_deokdaegol", -18, arquivo=str(AQUI / "tv" / "TV_deokdaegol_som.wav"))   # o grito da TV no respiro
fx(59, None, "tv_wolha", -24, arquivo=str(AQUI / "tv" / "TV_wolha_som.wav"))
for _i, _f in ((60, "wc_noite"), (61, "irmas_chegada"), (62, "exhuma_cova")):
    fx(_i, None, "som_" + _f, -26, arquivo=str(AQUI / "filmes_prontos" / f"{_f}_som.wav"))
pausa(53, 1.2); pausa(58, 2.4); pausa(58, 0.4); pausa(60, 0.6); pausa(61, 1.0); pausa(62, 1.0); pausa(63, 1.0)

# ================================================================ APARTE — Vigia: o han
C(63, vigia((1.0, 1.04)))
C(64, img(E + "A06.jpg", (1.0, 1.05), ((0.5, 0.45), (0.5, 0.42))), (img(E + "I08.jpg", (1.0, 1.05), ((0.45, 0.45), (0.45, 0.42))), "irmãs"),
      (img(E + "T04.jpg", (1.0, 1.05), ((0.5, 0.5), (0.5, 0.48))), "Wol"))
C(65, vigia((1.0, 1.05), ((0.5, 0.5), (0.48, 0.48))), (img(E + "T07.jpg", (1.0, 1.06), ((0.5, 0.5), (0.5, 0.45)), kanji=HAN(0.34, 0.5)), "han"))
pincel(65, "han")
C(66, img(E + "A05.jpg", (1.04, 1.1), ((0.5, 0.45), (0.5, 0.42))))
C(67, vigia((1.03, 1.08), ((0.45, 0.48), (0.43, 0.46))))
C(68, vid4("V11"), (img(X + "I03_A.jpg", (1.0, 1.06), ((0.5, 0.5), (0.5, 0.45))), "família"))
C(69, vigia((1.05, 1.12), ((0.42, 0.45), (0.38, 0.42))))
C(70, c3(E + "H01.jpg", "entrar", (0.5, 0.45), 0.9, 0.2))
C(71, texto("A internet.", "internet.", "impacto", cps=14, tamanho=120))
amb(63, "nenhum"); amb(66, "ep09_lenda_joseon", -28); amb(69, "nenhum")
fx(65, "han", "ep09_jing", -20)
fx(71, None, "estatica_cctv", -26, ate=1.5, saida=0.6)
pausa(65, 0.6); pausa(68, 0.6); pausa(70, 0.6); pausa(72, 1.6)

# ================================================================ O RAFA — 1: a montanha
C(72, img("M01_A", (1.0, 1.06), ((0.5, 0.5), (0.45, 0.5))))
C(73, vid4("V16"), (img(E + "M02.jpg", (1.0, 1.06), ((0.5, 0.5), (0.5, 0.45))), "passar"))           # a Lívia filmando, de costas
C(74, c3("M01_C", "lado", (0.6, 0.4), 0.8, 0.0))                         # os prédios e a montanha atrás
C(75, c3("M02_B", "entrar", (0.6, 0.45), 0.9, 0.2))                      # ela na frente, na trilha
C(76, c3("M03_C", "entrar", (0.55, 0.55), 0.9, 0.2))                     # a curva vazia
C(77, img("M03_A", (1.0, 1.05), ((0.5, 0.5), (0.5, 0.5))))
C(78, c3("M03_B", "lado", (0.25, 0.5), 0.9, 0.3))                        # a mata do lado esquerdo
C(79, vid("V01_B", (1.0, 1.03)))
C(80, img("M02_A", (1.0, 1.06), ((0.55, 0.5), (0.58, 0.45))))           # o caminho por onde ela foi
C(81, c3("M03_C", "lado", (0.75, 0.5), 0.8, 0.0))                        # o lado direito da trilha
C(82, c3("M03_B", "entrar", (0.3, 0.5), 1.0, 0.3))
C(84, img("M03_B", (1.0, 1.04), ((0.5, 0.55), (0.5, 0.55))))             # "O Rafa não foi." — câmera quase parada
C(85, vid("V01_A", (1.0, 1.03)), (img("M03_C", (1.0, 1.05), ((0.5, 0.55), (0.5, 0.52))), "Do"))
C(86, img("M03_A", (1.05, 1.1), ((0.3, 0.5), (0.3, 0.5))))
amb(72, "ep09_mata_noite", -30); amb(76, "ep09_mata_noite", -24)
batidas[83]["ambiente"] = {"som": "ep09_mata_noite", "volume_db": -20}
fx(79, None, "respiracao_nuca", -30, atraso=-0.6)
pausa(77, 0.8); pausa(82, 0.6); pausa(85, 0.8); pausa(86, 1.6)

# ================================================================ PARTE 1 — o que mora no monte Jangsan
capitulo(87, 4, "O que mora no monte Jangsan", "장산범 · Busan", P("M07_A"),
         img("M01_C", (1.0, 1.06), ((0.6, 0.45), (0.62, 0.42))), "Em", selo="虎")
C(88, vid4("V18"), (img("M07_A", (1.0, 1.06), ((0.55, 0.45), (0.56, 0.43))), "Que"))             # o bicho branco entre as árvores (foto borrada)
C(89, vid("V01_B", (1.0, 1.03)))
C(90, ficha("장산범 · Jangsan-beom\n\"o tigre do Jangsan\"", "\"o tigre do Jangsan\""))
C(91, c3("M02_A", "entrar", (0.45, 0.5), 0.9, 0.3))
C(92, img("M07_A", (1.0, 1.06), ((0.55, 0.45), (0.57, 0.42))))
C(93, img("M07_C", (1.16, 1.2), ((0.55, 0.45), (0.56, 0.44)), kanji=K("장산범", 0.2, 0.5, "luz", "Jangsan-beom", em="Jangsan")))
pincel(93, "Jangsan")
C(94, img("M01_A", (1.0, 1.06), ((0.6, 0.45), (0.62, 0.45))))
C(95, img("M07_A", (1.0, 1.05), ((0.55, 0.45), (0.56, 0.43))), (filme("mimic_menina"), "mulher"),
      (c3("M07_B", "entrar", (0.47, 0.4), 0.7, 0.0), "caverna"))
C(96, img("M02_B", (1.0, 1.06), ((0.5, 0.5), (0.55, 0.45))))
C(97, img("M03_A", (1.0, 1.06), ((0.5, 0.5), (0.5, 0.5)), kanji=K("목소리", 0.8, 0.5, "luz", "moksori · a voz", em="voz")))
pincel(97, "voz")
amb(87, "nenhum"); amb(89, "ep09_mata_noite", -26); amb(95, "nenhum"); amb(96, "ep09_mata_noite", -26)
pausa(88, 0.6); pausa(92, 1.0); pausa(94, 0.6); pausa(97, 1.2)

# ================================================================ O RAFA — 2: os tênis
C(98, c3("M05_A", "entrar", (0.5, 0.55), 0.8, 0.2))
C(99, c3("M05_B", "entrar", (0.6, 0.5), 0.8, 0.0))                       # voluntários de colete, lanternas
C(100, c3("M04_A", "entrar", (0.5, 0.75), 0.9, 0.3, atmos={"neblina": 0.4}))   # os tênis lado a lado
C(101, img("M04_D", (1.05, 1.12), ((0.5, 0.7), (0.5, 0.72)), atmos={"neblina": 0.3}))
chat(102, {"de": "eu", "tipo": "audio", "duracao": "0:09", "hora": "08:14", "apos": 0.2})
chat(103, {"de": "eu", "tipo": "audio", "duracao": "0:04", "hora": "09:02", "apos": 0.1})
C(104, c3("M06_B", "entrar", (0.6, 0.6), 0.8, 0.2, atmos={"neblina": 0.4}))
# 45 "Era a Lívia." continua o degrau (44)
C(106, vid("V06_A", (1.0, 1.03)))                                         # (o sol na neblina cresce depois de ~4 s)
C(107, vid("V06_B", (1.0, 1.03)))
chat(108, {"de": "eu", "texto": "❤️" * 30, "hora": "06:31", "apos": 0.2},
     {"de": "Pai", "texto": "graças a Deus 🙏", "hora": "06:32", "apos": 0.9})
C(109, c3("C05_B", "entrar", (0.45, 0.6), 0.8, 0.3))                       # o Rafa no escuro, o celular na mão
C(110, img("M06_C", (1.0, 1.06), ((0.3, 0.45), (0.3, 0.4))))
C(111, img("M06_B", (1.12, 1.18), ((0.62, 0.45), (0.62, 0.42)), kanji=K("오빠", 0.22, 0.5, "sangue", "oppa", tam=0.3, atraso=0.05)))
pincel(111, None, atraso=-0.2)
C(112, img("M06_A", (1.0, 1.05), ((0.5, 0.5), (0.5, 0.45))))
C(113, img("M06_C", (1.08, 1.14), ((0.35, 0.4), (0.35, 0.38))))
amb(98, "ep09_mata_noite", -26); amb(102, "ep09_sala_bh", -30); amb(104, "ep09_mata_noite", -30)
pausa(101, 0.8); pausa(105, 0.6); pausa(109, 0.8); pausa(111, 0.6); pausa(113, 1.6)

# ================================================================ PARTE 2 — a irmã raposa (era Joseon)
capitulo(114, 5, "A irmã raposa", "여우누이 · Yeou Nui", P("J01_A"),
         img("J01_A", (1.0, 1.06), ((0.4, 0.55), (0.42, 0.55))), "Existe", selo="狐")
C(115, ficha("여우누이 · A Irmã Raposa\nmais de 75 versões", "75 versões"))
C(116, img("J01_B", (1.0, 1.06), ((0.4, 0.55), (0.42, 0.5))))
C(117, c3("J02_A", "entrar", (0.55, 0.55), 0.8, 0.0))                     # a menina de hanbok, de costas
C(118, c3("J01_C", "entrar", (0.45, 0.6), 0.9, 0.3, atmos={"neblina": 0.4}))   # o estábulo à noite
C(119, img("J01_A", (1.0, 1.08), ((0.3, 0.6), (0.25, 0.6))))
C(120, vid4("V19", video_inicio=3.0), (c3("J02_B", "entrar", (0.5, 0.5), 1.0, 0.3, atmos={"poeira": 0.3}), "entrar"))
C(121, img("J01_B", (1.1, 1.18), ((0.3, 0.75), (0.28, 0.78))))
C(122, img("J04_B", (1.0, 1.06), ((0.45, 0.55), (0.5, 0.55))))
C(123, img("J03_C", (1.0, 1.06), ((0.5, 0.55), (0.5, 0.5))))
C(124, img("J02_C", (1.0, 1.06), ((0.4, 0.55), (0.42, 0.5)), kanji=K("간", 0.82, 0.5, "sangue", "gan · fígado", tam=0.3, atraso=1.0)))
pincel(124, None, atraso=1.0)
C(125, img("J04_B", (1.0, 1.06), ((0.7, 0.5), (0.75, 0.55))))           # os dois irmãos com as trouxas
C(126, c3("J03_A", "entrar", (0.5, 0.55), 0.9, 0.0, atmos={"neblina": 0.5}))   # a vila vazia
C(127, c3("J04_A", "entrar", (0.3, 0.5), 0.8, 0.2))                       # ela na porta, de costas
C(128, img("J04_A", (1.12, 1.18), ((0.32, 0.5), (0.32, 0.48)), kanji=K("오빠", 0.8, 0.45, "sangue", "oppa", tam=0.26, atraso=0.05)))
C(129, img("J03_B", (1.0, 1.06), ((0.5, 0.5), (0.55, 0.5)), atmos={"neblina": 0.5}))
C(130, img("J04_B", (1.05, 1.1), ((0.72, 0.55), (0.72, 0.55))))             # os dois que faltavam
C(131, c3("J02_C", "entrar", (0.45, 0.45), 0.9, 0.3))
C(132, img("J03_C", (1.0, 1.06), ((0.5, 0.5), (0.5, 0.45)), atmos={"neblina": 0.5}))
amb(114, "nenhum"); amb(118, "ep09_lago", -30); amb(126, "nenhum")
fx(121, None, "ep09_buk", -20, atraso=-0.4)
pausa(117, 0.8); pausa(121, 1.0); pausa(124, 0.8); pausa(127, 0.6); pausa(129, 0.8); pausa(130, 0.8); pausa(132, 1.6)

# ================================================================ O RAFA — 3: o óleo (SUSTO 1)
chat(133, {"de": "Lívia", "tipo": "foto", "imagem": P("M01_B"), "hora": "21:10", "apos": 0.3},
     {"de": "Lívia", "texto": "busan à noite 😍", "hora": "21:10", "apos": 1.0})
C(134, c3("C02_C", "entrar", (0.4, 0.5), 0.8, 0.2))                        # a mesa da cozinha, à noite
C(135, c3("C04_B", "entrar", (0.6, 0.65), 0.9, 0.2))                       # a coleira e a tigela na calçada
chat(136, {"de": "Rafa", "tipo": "foto", "imagem": P("C04_A"), "hora": "07:40", "apos": 0.2},
     {"de": "Rafa", "texto": "dois cachorros mortos no prédio da frente. sem marca nenhuma", "hora": "07:41", "apos": 0.9})
chat(137, {"de": "Pai", "tipo": "audio", "duracao": "0:05", "hora": "07:52", "apos": 0.1})
C(138, c3("C05_A", "entrar", (0.6, 0.55), 0.8, 0.2))                       # o Rafa sentado na cama de madrugada
C(139, c3("C03_B", "entrar", (0.75, 0.45), 0.9, 0.3))                      # do corredor: a luz da cozinha acesa
C(140, vid("V05_A", (1.0, 1.03)))                                          # ela de costas na pia (carimbo refeito)
C(141, img("C01_A", (1.05, 1.12), ((0.55, 0.45), (0.56, 0.42))))
C(142, c3("C02_B", "entrar", (0.3, 0.6), 0.9, 0.4))                        # o vidro de óleo
C(143, img("C01_C", (1.05, 1.15), ((0.55, 0.45), (0.56, 0.4))))
C(144, img("C01_B", (1.0, 1.03), ((0.5, 0.5), (0.5, 0.5))))                # o passo para trás: câmera parada
C(145, c3("C03_B", "sair", (0.4, 0.5), 0.7, 0.0))                          # o corredor, o quarto dela atrás dele
# SUSTO 1: a voz vem do quarto (atrás) — corte seco para a porta do quarto entreaberta, escura; a cozinha não se mexe
C(146, img("C03_A", (1.28, 1.3), ((0.33, 0.5), (0.33, 0.5))))                # a porta do quarto, entreaberta, escura
T(146, "corte")
C(147, img("C01_A_apagada", (1.0, 1.04), ((0.55, 0.45), (0.55, 0.45))))
C(148, {"imagem": IV2 + "F01_B.jpg", "zoom": [1.0, 1.06], "foco": [[0.6, 0.6], [0.62, 0.62]]})       # a mãe no sofá em BH
amb(134, "ep09_corredor", -28); amb(138, "geladeira", -30); amb(147, "geladeira", -32); amb(148, "ep09_sala_bh", -28)
batidas[143]["musica"] = {"som": "nenhum", "em": "ombro"}                  # silêncio total ANTES do susto
fx(144, "trás", "ep07_respiracao_nuca", -26)
fx(146, None, "stinger_cordas", -10, atraso=-0.05)
fx(147, "apagada", "ep09_jing", -24)
batidas[147]["musica"] = dict(TRILHA, continuar=True)   # volta logo depois do susto 1
pausa(140, 0.8); pausa(142, 0.8); pausa(145, 0.6); pausa(147, 0.8); pausa(148, 1.0)
batidas[144]["pausa_antes_s"] = 1.2      # 15/11: o "silêncio total" da cozinha era 2,4 s ("demora gigante") — 1,2 s

# ================================================================ PARTE 3 — o elevador
capitulo(149, 6, "O elevador", "엘리베이터 게임 · o jogo", P("H04_A"),
         img("H04_A", (1.0, 1.06), ((0.5, 0.5), (0.52, 0.45))), "Existe", selo="四")
C(150, ficha("엘리베이터 게임\no Jogo do Elevador", "o Jogo do Elevador"))
C(151, img("H03_B", (1.0, 1.06), ((0.45, 0.5), (0.45, 0.45))))
C(152, c3("H03_C", "entrar", (0.45, 0.45), 0.8, 0.0))
C(153, img("H03_B", (1.0, 1.05), ((0.45, 0.5), (0.45, 0.47))), (vid("V02_B", (1.4, 1.42), foco=[[0.62, 0.5], [0.62, 0.5]]), "nesta"))                       # 4 → 2 → 6 → 2 → 10 (a placa de hangul inventado fica fora)
C(154, img("H04_C", (1.0, 1.06), ((0.45, 0.45), (0.47, 0.42))))
C(155, c3("H05_C", "entrar", (0.5, 0.65), 0.8, 0.2))                       # os pés descalços entrando
C(156, img("H05_A", (1.0, 1.06), ((0.5, 0.5), (0.55, 0.55))))
C(157, img("H04_B", (1.0, 1.08), ((0.55, 0.45), (0.55, 0.5))))
C(158, c3("H03_A", "entrar", (0.45, 0.4), 0.8, 0.2))
C(159, texto("Você chegou.", "chegou.", "impacto", cps=10, tamanho=130))
C(160, c3("H06_B", "entrar", (0.5, 0.45), 1.0, 0.3))                      # o outro lado: o corredor igual, vazio
C(161, img("H05_B", (1.0, 1.06), ((0.6, 0.45), (0.6, 0.5))))
C(162, c3("C05_C", "entrar", (0.4, 0.55), 0.8, 0.3))                      # o Rafa às 4h, a tela do celular
C(163, img("C05_A", (1.05, 1.12), ((0.62, 0.5), (0.64, 0.5))))
C(164, texto("\"Quem volta da montanha nunca é quem subiu.\nO de verdade fica do outro lado.\"",
             "nunca é quem subiu.\"", cps=22, tamanho=64))   # o texto fica a frase inteira (tempo de leitura)
amb(149, "nenhum"); amb(151, "ep09_motor_elevador", -28); amb(162, "geladeira", -32)
fx(153, None, "ep09_elevador", -26, atraso=0.4)
pausa(153, 0.6); pausa(156, 0.8); pausa(158, 0.6); pausa(159, 0.8); pausa(161, 1.0); pausa(163, 0.6); pausa(164, 0.8)

# ================================================================ PARTE 4 — o hospital (Gonjiam)
capitulo(165, 7, "O hospital", "사 · 4 · morte", P("H01_B"),
         img("H04_A", (1.0, 1.08), ((0.45, 0.5), (0.48, 0.48)),
             kanji=[K("사", 0.2, 0.45, "sangue", "sa · quatro", tam=0.26, em="sa"),
                    K("死", 0.8, 0.45, "sangue", "sa · morte", tam=0.26, em="morte", glitch=True)]), "Na", selo="死")
pincel(165, "sa"); pincel(165, "morte")
C(166, c3("H01_A", "entrar", (0.5, 0.45), 0.8, 0.0))
C(167, ficha("곤지암 · Gonjiam\nabandonado nos anos 90", "abandonado"))
C(168, c3("H01_B", "entrar", (0.45, 0.45), 0.9, 0.2))
C(169, img("H02_A", (1.0, 1.06), ((0.5, 0.5), (0.55, 0.45))))
C(170, c3("H01_C", "lado", (0.4, 0.45), 0.8, 0.0))
C(171, c3("H01_A", "entrar", (0.45, 0.6), 0.8, 0.0))
C(172, filme("gonjiam_mato"), (c3("H02_B", "entrar", (0.5, 0.4), 0.8, 0.2), "grupo"),   # a lanterna ficou quase preta na moldura
      (c3("H07_B", "entrar", (0.5, 0.5), 0.9, 0.3), "porta"))
C(173, img("H07_C", (1.0, 1.08), ((0.5, 0.45), (0.5, 0.42)), kanji=K("402", 0.82, 0.45, "luz", None, tam=0.24, em="402")))
C(174, c3("C05_B", "entrar", (0.45, 0.55), 0.8, 0.2))
C(175, img("H01_C", (1.0, 1.05), ((0.5, 0.5), (0.5, 0.48))))
amb(165, "nenhum"); amb(166, "ep09_hospital", -28); amb(172, "nenhum"); amb(173, "ep09_hospital", -28)
pausa(166, 0.6); pausa(169, 0.6); pausa(170, 0.6); pausa(173, 0.8); pausa(175, 1.4)

# ================================================================ O RAFA — 4: o ritual
C(176, c3("H01_B", "entrar", (0.5, 0.5), 0.9, 0.3))
C(177, c3("H02_C", "entrar", (0.6, 0.45), 0.9, 0.3))
C(178, c3("H03_B", "entrar", (0.45, 0.45), 0.8, 0.3))
C(179, vid4("V20"))                                        # a luz acende, o botão (placa fora do quadro)
C(180, img("H04_A", (1.0, 1.06), ((0.5, 0.45), (0.5, 0.42))))
C(181, img("H04_C", (1.0, 1.08), ((0.45, 0.4), (0.45, 0.38))))
C(182, c3("H03_C", "entrar", (0.45, 0.45), 0.9, 0.3))                     # o áudio do gancho, agora no lugar certo
C(183, vid("V02_B", (1.4, 1.42), foco=[[0.62, 0.5], [0.62, 0.5]], video_inicio=0.5))
C(184, img("H03_A", (1.0, 1.04), ((0.45, 0.5), (0.45, 0.5))))
C(185, img("H04_C", (1.1, 1.18), ((0.4, 0.4), (0.4, 0.4))))
C(186, vid("V03_B", (1.35, 1.37), foco=[[0.62, 0.5], [0.62, 0.5]]))
C(187, c3("H05_A", "entrar", (0.62, 0.55), 0.9, 0.3))                     # os pés descalços, oleosos, do lado dos tênis
C(188, img("H03_B", (1.0, 1.03), ((0.45, 0.5), (0.45, 0.5))))
C(189, img("H05_B", (1.05, 1.12), ((0.6, 0.4), (0.62, 0.38))))
C(191, img("H03_A", (1.08, 1.12), ((0.45, 0.45), (0.45, 0.45))))
C(193, img("H04_B", (1.1, 1.18), ((0.4, 0.75), (0.4, 0.78))))
C(194, c3("H03_C", "sair", (0.45, 0.45), 0.8, 0.0))
amb(176, "ep09_hospital", -26); amb(179, "ep09_motor_elevador", -26)
fx(179, "acendeu", "ep07_luz_volta", -24)
fx(181, None, "ep09_elevador", -26, atraso=-0.3)
fx(186, "abriu", "ep09_elevador", -22)
fx(187, "passos", "passos_atrasados", -24)
fx(189, "orelha", "ep07_respiracao_nuca", -20)
fx(193, "um", "tecla", -22)
pausa(177, 0.6); pausa(178, 1.2); pausa(184, 1.2); pausa(185, 0.8); pausa(188, 1.0); pausa(191, 1.0); pausa(194, 1.2)

# ================================================================ O RAFA — 5: o outro lado (SUSTO 2)
C(195, vid("V04_A", (1.0, 1.03)))
C(196, c3("H06_A", "entrar", (0.5, 0.45), 1.0, 0.2))
C(197, vid4("V21"))
C(198, vid("V04_B", (1.0, 1.03)), (img("H07_A", (1.0, 1.08), ((0.5, 0.45), (0.5, 0.4)),
                                       kanji=K("402", 0.8, 0.45, "sangue", None, tam=0.24, em="quatrocentos")), "quatrocentos"))
C(199, c3("H07_A", "entrar", (0.5, 0.7), 1.0, 0.3))                       # as pegadas oleosas até a porta
C(200, img("H07_B", (1.15, 1.22), ((0.5, 0.45), (0.5, 0.45))))
C(201, img("H07_C", (1.1, 1.16), ((0.5, 0.45), (0.5, 0.45))))
C(203, img("H07_B", (1.22, 1.28), ((0.5, 0.45), (0.5, 0.45))))
# SUSTO 2: 3 s de silêncio (só a porta rangendo); a sala vazia (a cama, à esquerda) → CORTE para ela no canto
# 144: a sala vazia = só a cama (ela começa em x 0,65 da H08_A)
C(204, img(E + "H10.jpg", (1.0, 1.04), ((0.5, 0.5), (0.5, 0.5))), (img("H08_B", (1.0, 1.04), ((0.55, 0.6), (0.55, 0.6))), "canto"))
batidas[204]["cenas"][1]["entrada"] = "corte"
batidas[204]["cenas"][0].update({"entrada": "corte", "antecipar": 1.4})   # a sala aparece no fim do silêncio, depois do rangido
C(205, vid4("V22"), (img(E + "H09.jpg", (1.08, 1.14), ((0.55, 0.5), (0.55, 0.48))), "disse"))
C(207, img("H09_A", (1.15, 1.2), ((0.62, 0.72), (0.62, 0.72))))           # as mãos
C(208, vid("V04_A", (1.0, 1.03)), (img("H03_C", (1.0, 1.05), ((0.45, 0.45), (0.45, 0.42))), "elevador"))
C(209, img("H04_B", (1.1, 1.16), ((0.4, 0.75), (0.4, 0.78))))
C(210, img("H06_C", (1.0, 1.05), ((0.5, 0.45), (0.5, 0.45))))
C(211, c3("H06_B", "sair", (0.5, 0.45), 0.9, 0.3))
amb(195, "ep09_fluorescente", -24); amb(209, "ep09_motor_elevador", -28); amb(211, "ep09_fluorescente", -26)
batidas[203]["musica"] = {"som": "nenhum"}
batidas[205]["musica"] = dict(TRILHA, continuar=True)   # volta logo depois do susto 2
batidas[203]["ambiente"] = {"som": "ep09_fluorescente", "volume_db": -30}
pausa(204, 3.0)                                                           # os 3 s de silêncio antes da sala
fx(204, None, "ep06_porta_range", -22, atraso=-2.8)
fx(204, "canto", "stinger_cordas", -12)
fx(200, "ouvido", "ep09_choro_parede", -26)
fx(211, "Lívia", "ep09_elevador", -26, depois=True)
pausa(199, 0.6); pausa(201, 0.8); pausa(205, 0.6); pausa(207, 0.8); pausa(209, 0.6)

# ================================================================ O RAFA — 6: a ligação (SUSTO 3)
C(212, c3("H02_B", "entrar", (0.5, 0.4), 0.9, 0.3))
C(213, c3("H09_A", "entrar", (0.6, 0.55), 0.8, 0.2))
C(214, img("H09_B", (1.0, 1.06), ((0.5, 0.55), (0.45, 0.55))))
C(216, {"imagem": IV2 + "F01_A.jpg", "zoom": [1.0, 1.06], "foco": [[0.6, 0.6], [0.62, 0.6]]})
C(218, img("H10_C", (1.0, 1.08), ((0.5, 0.5), (0.52, 0.45))))
C(219, img("H10_C", (1.0, 1.12), ((0.5, 0.5), (0.5, 0.48))))            # entra na tela do celular: ela de costas no sofá
C(220, vid4("V23", dur_max=5.6))   # a tela inteira no quadro (0,43–0,58 × 0,27–0,74)
# SUSTO 3: corta NO movimento (o rosto nunca aparece): tela preta, 2 s, a voz no escuro
C(221, texto("", None, cps=40))
T(221, "corte")
C(222, img("H09_B", (1.0, 1.04), ((0.7, 0.5), (0.72, 0.5))))
C(223, img("H09_B", (1.05, 1.1), ((0.72, 0.55), (0.72, 0.55))))
C(224, img("H09_A", (1.2, 1.3), ((0.62, 0.72), (0.62, 0.74))))
amb(212, "ep09_mata_noite", -30); amb(216, "ep09_sala_bh", -28); amb(221, "nenhum"); amb(222, "ep09_mata_noite", -32)
batidas[220]["musica"] = {"som": "nenhum", "em": "rosto"}
fx(221, None, "stinger_cordas", -12, atraso=-0.05)
batidas[222]["musica"] = dict(TRILHA, continuar=True)   # volta depois do susto 3 (o óleo na mão)
fx(224, "escorregadia", "ep09_jing", -24)
pausa(218, 0.6); pausa(220, 0.6); pausa(222, 2.0); pausa(223, 0.8); pausa(224, 0.6)


# ================================================================ FECHO — Vigia (corte seco do silêncio)
C(225, c3(E + "H01.jpg", "sair", (0.5, 0.45), 0.8, 0.0))
T(225, "corte")
C(226, c3(E + "M01.jpg", "lado", (0.6, 0.4), 0.8, 0.0))
C(227, vigia((1.0, 1.04)))
C(228, img(I + "C01_B.jpg", (1.0, 1.06), ((0.55, 0.45), (0.56, 0.42))))
C(229, vigia((1.0, 1.05)), (img(E + "T07.jpg", (1.0, 1.06), ((0.5, 0.5), (0.5, 0.45)), kanji=K("빚", 0.8, 0.45, "sangue", "bit · dívida", tam=0.3, em="dívida")), "Coreia"))
pincel(229, "dívida")
C(230, vigia((1.0, 1.06)))
C(231, {"tipo": "agua", "imagem": E + "I05.jpg", "horizonte": 0.55, "afunda": [0.42, 0.62, 2.6], "zoom": [1.0, 1.0]})
C(232, filme("bunshin_ritual"), (img(E + "T05.jpg", (1.05, 1.12), ((0.5, 0.5), (0.5, 0.48))), "nunca"))
C(233, img(E + "T05.jpg", (1.0, 1.1), ((0.5, 0.5), (0.5, 0.48))))
C(234, vid4("V15"), (img(E + "A06.jpg", (1.0, 1.06), ((0.5, 0.4), (0.5, 0.36))), "Com"))
C(235, vigia((1.0, 1.05)))                                                # a pergunta para os comentários
C(236, img(E + "J05.jpg", (1.0, 1.06), ((0.3, 0.5), (0.32, 0.5)), kanji=K("오빠", 0.82, 0.45, "sangue", "oppa", tam=0.3, atraso=0.8)))
C(237, vigia((1.04, 1.1), ((0.42, 0.45), (0.4, 0.43))))
C(238, vigia((1.05, 1.12), ((0.4, 0.45), (0.36, 0.42))))
C(240, vigia((1.0, 1.05)))
C(241, c3(E + "H09.jpg", "entrar", (0.6, 0.5), 0.9, 0.4))
amb(225, "nenhum"); amb(231, "ep09_lago", -26); amb(232, "nenhum"); amb(235, "nenhum"); amb(241, "ep09_mata_noite", -28)
fx(232, None, "som_bunshin", -26, arquivo=str(AQUI / "filmes_prontos" / "bunshin_ritual_som.wav"))
pausa(226, 0.6); pausa(228, 0.8); pausa(229, 0.6); pausa(233, 0.8); pausa(234, 0.6); pausa(235, 0.8); pausa(236, 0.8)
pausa(238, 0.6); pausa(240, 0.6); pausa(241, 0.8)


# ================================================================ DESENHO DE SOM (15/11)
# Pedido do usuário: "áudio é extremamente importante em terror, música e efeitos fazem grande diferença".
# - ambientes em CAMADAS (desenho_som.py): o lugar + um grave de tensão por baixo — nunca fica "vazio";
# - som no ESPAÇO (fone de ouvido): o que vem da esquerda/de trás/de perto é posicionado (pan);
# - efeitos no tempo da palavra; gongo AO CONTRÁRIO crescendo até o momento ruim; sub grave dando peso aos sustos.
LIVIA1 = str(AQUI / "vozes" / "limpas_escolhidas" / "livia1_Despina_lote.wav")
for i, som, db in [(4, "ep09_amanhecer_tenso", -26), (5, "ep09_mata_tensa", -22), (72, "ep09_mata_tensa", -32),
                   (75, "ep09_mata_tensa", -25), (89, "ep09_mata_tensa", -25), (96, "ep09_mata_tensa", -25),
                   (98, "ep09_mata_tensa", -24), (104, "ep09_amanhecer_tenso", -26), (134, "ep09_cozinha", -28),
                   (138, "ep09_cozinha", -25), (147, "ep09_cozinha", -28), (151, "ep09_elevador_tenso", -28),
                   (162, "ep09_cozinha", -30), (166, "ep09_hospital_tenso", -26), (173, "ep09_hospital_tenso", -26),
                   (176, "ep09_hospital_tenso", -24), (179, "ep09_elevador_tenso", -22), (195, "ep09_fluorescente_tenso", -24),
                   (203, "ep09_fluorescente_tenso", -30), (209, "ep09_elevador_tenso", -26), (211, "ep09_fluorescente_tenso", -26),
                   (212, "ep09_amanhecer_tenso", -28), (222, "ep09_amanhecer_tenso", -30), (241, "ep09_mata_tensa", -28)]:
    batidas[i]["ambiente"] = {"som": som, "volume_db": db}
batidas[83]["ambiente"] = {"som": "ep09_mata_tensa", "volume_db": -19}          # a segunda chamada: a mata "chega perto"
# O RAFA — 1: um galho estala do lado da voz; a voz dela repete longe enquanto ele espera; e PARA no meio da palavra
fx(78, "voz", "ep06_estalo", -27, pan=-0.6)
fx(85, "chamar", "voz_livia_longe", -31, arquivo=LIVIA1, pan=-0.8, eco=2.0, saida=0.6)
fx(85, "minutos", "voz_livia_longe", -33, arquivo=LIVIA1, pan=-0.85, eco=2.5, saida=0.6)
fx(86, None, "voz_cortada", -25, arquivo=LIVIA1, pan=-0.7, eco=1.5, ate=0.55, atraso=-1.3)   # "no meio de uma palavra"
# PARTE 1
fx(92, "não", "sub_drop", -24)
# O RAFA — 2: o gongo ao contrário cresce até o "Oppa" (ela, calma demais); o grave quando cai a ficha
fx(100, "tênis", "ep09_buk", -24)
fx(111, None, "ep09_jing", -24, reverso=True, atraso=-6.0)
fx(113, "coreano", "sub_drop", -23)
# PARTE 2: o fígado; a vila vazia; "mais dois"
fx(120, "puxou", "ep05_raspar", -26, tom=-3)
fx(126, None, "ep06_vento_capacete", -27, saida=2.0)
fx(130, "dois", "sub_drop", -23)
# O RAFA — 3: a cozinha (luz, mão molhada, o vidro, o assoalho) e o SUSTO 1 com peso grave
fx(139, "acesa", "tecla", -26)
fx(141, "molhado", "ep05_raspar", -31, tom=4, saida=1.0)
fx(142, "vidro", "ep08_bate_vidro", -28)
fx(144, "passo", "ep06_estalo", -25)
fx(146, None, "sub_drop", -15, atraso=-0.05)
fx(147, "apagada", "tecla", -22)
# PARTE 3: cada botão apertado no tempo do número
for w in ("quatro", "Dois", "Seis", "Dez"):
    fx(153, w, "tecla", -22)
fx(153, "Seis", "tecla", -22, atraso=0.62)                               # o segundo "dois"
fx(155, "entrar", "ep09_elevador", -26)
fx(156, "olha", "ep07_respiracao_nuca", -29, pan=-0.8)
fx(159, None, "braam_horror", -20)
# PARTE 4
fx(170, "CNN", "estatica_cctv", -30, saida=1.5)
# O RAFA — 4: o ritual — o muro, o elevador morto, cada botão, a porta, os passos e a respiração À ESQUERDA dele
fx(176, "muro", "metal_parada", -26)
fx(177, "parado", "ep07_corrente_longe", -29, saida=2.0)
for w in ("Quatro", "Dois", "Seis", "Dez"):
    fx(183, w, "tecla", -20)
fx(183, "Seis", "tecla", -20, atraso=0.62)
fx(185, None, "tecla", -18)
batidas[187]["sons"] = [s_ for s_ in batidas[187].get("sons", []) if s_["som"] != "passos_atrasados"]
fx(187, "passos", "passos_atrasados", -24, pan=-0.5)
batidas[189]["sons"] = [s_ for s_ in batidas[189].get("sons", []) if s_["som"] != "ep07_respiracao_nuca"]
fx(189, "orelha", "ep07_respiracao_nuca", -20, pan=-0.85)
fx(194, None, "riser_tensao", -22)
# O RAFA — 5: a porta abre no outro lado; os passos dele; SUSTO 2 com o grave
fx(195, None, "ep09_elevador", -24, atraso=-0.4)
fx(199, "andando", "passos_atrasados", -28)
fx(204, "canto", "sub_drop", -16)
fx(208, "Voltaram", "passos_atrasados", -25)
fx(209, "um", "tecla", -22)
# O RAFA — 6: a câmera virando; o gongo ao contrário cresce até ela virar o rosto → corte, cordas e o grave
fx(218, "virou", "whoosh", -26)
fx(221, None, "ep09_jing", -23, reverso=True, atraso=-6.0)
fx(221, None, "sub_drop", -15, atraso=-0.05)
fx(224, "escorregadia", "sub_drop", -22)
# FECHO: a última frase com uma respiração colada no ouvido
fx(241, None, "ep07_respiracao_nuca", -27, pan=-0.85, atraso=0.3)


# ---------------------------------------------------------------- SONNISS (15/11): efeitos profissionais no lugar dos fracos
def tira(i, som):
    batidas[i]["sons"] = [s_ for s_ in batidas[i].get("sons", []) if s_["som"] != som]


SN = "ep09_sn_"
fx(3, None, SN + "elevador_shepard", -27, atraso=-4.0, ate=4.5, saida=1.0)   # "ele tá subindo": o som que nunca para de subir
fx(88, None, SN + "respiracao_pulsante", -27, ate=24, saida=4.0)          # a criatura: uma respiração grande, pulsando, na mata
tira(146, "stinger_cordas"); fx(146, None, SN + "stinger_cello", -9, atraso=-0.05, ate=4.0, saida=2.0)
tira(139, "tecla"); fx(139, "acesa", SN + "interruptor", -22)
tira(147, "tecla"); fx(147, "apagada", SN + "interruptor", -20)
tira(159, "braam_horror"); fx(159, None, SN + "horror_momento", -19, ate=6.0, saida=2.5)
fx(183, None, SN + "coracao_panico", -27, ate=14, saida=3.0)              # o coração dele acelera nos botões
tira(186, "ep09_elevador"); fx(186, "abriu", SN + "elevador_porta_sobe", -24, ate=3.5, saida=0.8)
tira(187, "passos_atrasados")
for k, d in enumerate((0.0, 0.62, 1.25, 1.9)):                          # pés descalços na chapa de metal, à esquerda
    fx(187, "passos", SN + f"descalco_metal_{k % 3 + 1}", -24 + k * 1.5, atraso=d, pan=-0.55 + k * 0.08)
tira(189, "ep07_respiracao_nuca"); fx(189, "orelha", SN + "sussurro_fantasma", -21, pan=-0.9)
tira(194, "riser_tensao"); fx(194, None, SN + "elevador_shepard", -21, ate=9.0, saida=2.5)
fx(195, None, SN + "elevador_mecanismo", -26, atraso=-1.0)
tira(204, "ep06_porta_range"); fx(204, None, SN + "porta_rangido_lento", -21, atraso=-2.9, ate=3.2, saida=0.4)
tira(204, "stinger_cordas"); fx(204, "canto", SN + "horror_boom", -9, ate=4.0, saida=1.5)
fx(210, "fechava", SN + "elevador_porta_fecha", -24)
tira(221, "stinger_cordas"); fx(221, None, SN + "stinger_swell", -9, atraso=-0.05, ate=5.0, saida=2.5)
fx(221, None, SN + "piano_horror_reverso", -24, atraso=-11.0)              # o piano ao contrário cresce até ela virar o rosto
fx(144, "passo", SN + "respiracao_medo", -26)


# ---------------------------------------------------------------- TERROR ASIÁTICO (15/11)
# O loop ambiente (montar_loop.py) é a cama das LENDAS; a paleta de ataques (gayageum, haegeum, piri, janggu, buk+jing)
# fica para os momentos marcados: revelação, susto e ritual. Nada foi descartado (pedido do usuário).
AH = "ep09_ah_"
for i, som, db in [(87, "ep09_lenda_mata", -27), (89, "ep09_lenda_mata", -26), (96, "ep09_lenda_mata", -26),
                   (114, "ep09_lenda_joseon", -27), (118, "ep09_lenda_joseon", -26), (126, "ep09_lenda_joseon", -26),
                   (149, "ep09_lenda_elevador", -27), (151, "ep09_lenda_elevador", -26),
                   (165, "ep09_lenda_hospital", -27), (166, "ep09_lenda_hospital", -26), (173, "ep09_lenda_hospital", -26)]:
    batidas[i]["ambiente"] = {"som": som, "volume_db": db}
# revelações: o golpe dissonante do gayageum
fx(113, "coreano", AH + "gayageum_golpe_1", -17, ate=4.5, saida=2.0)
fx(129, "pais", AH + "gayageum_golpe_2", -18, ate=4.5, saida=2.0)
fx(186, "quatro", AH + "gayageum_golpe_1", -17, ate=4.5, saida=2.0)
fx(165, "morte", AH + "geomungo_grave_1", -19, ate=4.0, saida=1.5)
# o ritual: o janggu acelerando enquanto ele aperta os botões; o piri chorando quando a porta abre no 5º andar
fx(183, None, AH + "janggu_ritual_1", -21, atraso=-0.8, ate=9.0, saida=2.5)
fx(153, "nesta", AH + "janggu_ritual_2", -25, ate=8.0, saida=2.5)
fx(187, None, AH + "piri_lamento_1", -27, ate=6.0, saida=2.5)
# sustos: o grito do haegeum junto do impacto; a flauta soprando depois (a saída lenta)
fx(204, "canto", AH + "haegeum_grito_1", -20, ate=4.0, saida=1.5)
fx(147, "apagada", AH + "daegeum_sopro_1", -26, ate=6.0, saida=2.5)
fx(222, None, AH + "daegeum_sopro_2", -27, ate=6.0, saida=2.5)
fx(94, None, AH + "ajaeng_drone_1", -27, ate=9.0, saida=3.0)            # "Ninguém nunca provou que ele existe."

# ================================================================ VINHETA FIXA DE INSCRIÇÃO
batidas.append({"fala": F.VINHETA, "cta_inicio": True, "sem_legenda": True, "ambiente": {"som": "nenhum"},
                "musica": {"som": "vinheta_ultimo_abrigo", "volume_db": -20}})

voz = "audio/voz_personagens.wav" if (AQUI / "audio" / "voz_personagens.wav").exists() else "audio/voz_com_vinheta_limpa.wav"
roteiro = {
    "modo": "cenas", "formato": "16:9", "tema": "vigia", "avatar": "vigia_hd",
    "voz_arquivo": voz,
    "transcrever_pedacos": 75,                # no arquivo inteiro o Whisper pulava o fecho
    "cintilar": 0.03, "apertar_pausas": False,
    "cena_minima": 3.0,                       # 15/11: nenhuma cena curta demais (gerar.respirar_cenas)   # REGRA: nunca encurtar as pausas da narração
    "vigia_padrao": False,
    "cauda": 1.6, "chuva": 0, "grao": 0.14,
    # 13/11: trilha mais presente que no Ep. 08 (+4 dB), mas o rascunho 1 abafava a voz: -3 dB nas faixas e -9 sob a voz
    "mix": {"musica_ganho_db": 12, "fundo_sob_voz": -9, "efeitos_sob_voz": -4, "voz_pro": True, "fundo_bolso": True,
            "efeitos_pico_max": -3},
    "legendas": {"destaques": ["Coreia", "dívida", "han", "Arang", "Miryang", "Janghwa", "ovo", "Jangsan", "Oppa", "óleo", "gergelim", "quatro", "402", "Gonjiam", "não olha"]},
    "ambiente_inicial": [{"som": "ep09_motor_elevador", "volume_db": -24}],
    "musica": TRILHA,
    "titulo_ep": {"antes_da_batida": 6, "linhas": ["O VIGIA · EPISÓDIO 09", "O QUE VOLTOU", "DA MONTANHA"], "vermelho": "MONTANHA",
                  "duracao": 5.2, "folga": 1.0, "x": 0.55},
    "cta": {"titulo": "Confirma por mensagem antes de ir.", "canal": "Último Abrigo",
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
batidas[221].pop("sem_legenda", None)
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
sem_som = sorted(s for s in sons if s != "nenhum" and not list(sons_dir.glob(s + ".*")))
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

    PROTEGE = {3, 5, 24, 25, 53, 57, 71, 84, 86, 113, 132, 144, 146, 147, 203, 204, 218, 219, 220, 221, 222, 224, 241}   # sustos e silêncios: nunca continuar a anterior
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
        if c.get("tipo") in ("capitulo", "talisma") or c.get("entrada") == "corte" or c.pop("antecipar_fixo", False):
            continue
        ant = next((cenas_de(batidas[j]) for j in range(i - 1, -1, -1) if cenas_de(batidas[j])), [{}])[-1]
        if c.get("tipo") == "chat" and ant.get("tipo") == "chat":
            c["entrada"] = "corte"; continue          # conversa → conversa: a tela é a mesma
        padrao = {"nanquim": 1.3, "shoji": 0.9, "vela": 1.6, "queimar": 1.5, "rasgo": 0.9, "hanji": 1.2}.get(c.get("entrada"), 0.6)
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
