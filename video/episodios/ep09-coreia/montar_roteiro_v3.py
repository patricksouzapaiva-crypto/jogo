"""Monta roteiro.json do Ep. 09 v3 "O que voltou da montanha" (falas.py: cada frase do ROTEIRO.md = 1 batida).
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
assert len(falas) == 175 and falas[161] == '"Oppa. Você voltou."' and PERS.get(151) == "rafa_falso", \
    "o ROTEIRO.md mudou: rever os índices"
batidas = [{"fala": f} for f in falas]
for i, s in PAUSAS.items():
    batidas[i]["pausa_antes_s"] = s

I, IV2, CL, FP = "imagens_v3/", "imagens/", "clipes_v3/", "filmes_prontos/"
VIGIA = {"imagem": "../../painel/cenarios/abrigo_16x9.png", "vigia": True}
C3D = AQUI / "camera3d"; C3D.mkdir(exist_ok=True)
# 14/11: os tempos vêm da VOZ FINAL (com os personagens, que são mais longos): senão a câmera 3D sai curta e o motor desacelera
ALI = Path(__import__("os").environ.get("ALINHAMENTO") or next(p for p in (AQUI / "audio" / "alinhamento_voz_personagens.json",
                                                                           AQUI / "audio" / "alinhamento.json") if p.exists()))   # teste: ALINHAMENTO=estimado.json


# ------------------------------------------------------------------ ajudantes
def vigia(z=(1.0, 1.04), foco=((0.55, 0.5), (0.57, 0.48))):
    return dict(VIGIA, zoom=list(z), foco=[list(foco[0]), list(foco[1])])


def img(nome, z=(1.0, 1.08), foco=None, **kw):
    c = {"imagem": I + nome + ".jpg", "zoom": list(z), **kw}
    if foco:
        c["foco"] = [list(foco[0]), list(foco[1])]
    return c


def c3(nome, mov="entrar", foco=(0.5, 0.5), forca=1.0, desfoque=0.0, **kw):
    """Câmera 3D: a câmera anda dentro da imagem (profundidade real). O vídeo é gerado no fim, com a duração da cena."""
    arq = nome if "/" in nome else I + nome + ".jpg"            # também aceita as bases dos clipes (clipes/base_V0x.jpg)
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


def capitulo(i, n, titulo, sub, imagem, cena, em):
    """Cartão de capítulo (제N장) na pausa antes da fala, com o buk (tambor coreano) longe; depois a cena entra."""
    cap = {"tipo": "capitulo", "numero": f"제{n}장", "numero_pt": f"Capítulo {n}", "titulo": titulo, "ano": sub,
           "imagem": imagem, "antecipar": 4.8, "entrada": "nanquim", "atmos": {"poeira": 0.5}}
    cena = dict(cena); cena.setdefault("entrada", "fundir"); cena.setdefault("duracao_entrada", 0.8)
    C(i, cap, (cena, em))
    pausa(i, 5.2)
    fx(i, None, "ep08_tinta", -18, atraso=-4.8)
    fx(i, None, "ep09_buk", -17, atraso=-3.4)


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

# ================================================================ GANCHO — sem Vigia (03:00 em Seul / 15:00 em BH)

# ================================================================ GANCHO — sem Vigia (03:00 em Busan / 15:00 em BH)
C(0, {"tipo": "relogios", "lados": [{"nome": "Busan", "hora": "03:00", "imagem": I + "H03_C.jpg", "brilho": 0.6},
                                     {"nome": "Belo Horizonte", "hora": "15:00", "imagem": IV2 + "F01_A.jpg", "brilho": 0.75}]})
chat(1, {"de": "Rafa", "tipo": "audio", "duracao": "0:06", "hora": "15:00", "em": "áudio", "digitando": 0.6})
C(2, c3("H03_A", "entrar", (0.48, 0.45), 0.8, 0.3))                      # o Rafa de costas no elevador, celular aceso
# os 4 s só de motor subindo + o sino: o painel com o 4 aceso, a câmera chegando devagar
C(3, c3("H04_B", "entrar", (0.55, 0.38), 0.7, 0.0))
T(3, "fundir", 2.0)
C(4, c3("M06_C", "entrar", (0.3, 0.45), 0.8, 0.2, atmos={"neblina": 0.4}))   # a irmã no degrau, de costas
C(5, c3("M03_B", "entrar", (0.5, 0.5), 1.0, 0.3))                        # a mata escura
amb(0, "ep09_motor_elevador", -24)
batidas[3]["ambiente"] = {"som": "ep09_motor_elevador", "volume_db": -14}   # o motor SOZINHO nos 4 s
fx(3, None, "ep09_elevador", -20, atraso=-0.9)                             # o sino de andar no fim do silêncio
amb(4, "ep09_mata_noite", -26)
pausa(5, 0.4)

# ================================================================ TEMA — Vigia (título ao lado dele, sem corte)
C(6, vigia((1.0, 1.04)))
saida_lenta(6, 5.4, dur=2.2)
batidas[6]["cena"].update({"antecipar": 7.2, "antecipar_fixo": True})   # o título nunca aparece em cima da mata
fx(6, None, "ep09_jing", -17, atraso=-6.2)
C(7, vigia((1.0, 1.05)))
C(8, c3("M01_B", "lado", (0.45, 0.45), 0.8, 0.0))                       # Busan, o mar e a montanha
C(9, vigia((1.0, 1.06)))
C(10, img("J01_A", (1.0, 1.06), ((0.4, 0.55), (0.42, 0.55))),
      (img("M07_B", (1.0, 1.06), ((0.45, 0.4), (0.47, 0.4))), "criatura"),
      (vid("V02_A", (1.0, 1.03)), "ritual"),
      (c3("H01_A", "entrar", (0.55, 0.45), 0.7, 0.0), "hospital"))
C(11, vigia((1.04, 1.1), ((0.45, 0.48), (0.43, 0.46))))
amb(6, "nenhum")
musica(6, "02_han", -30)
pausa(8, 0.6); pausa(10, 0.6); pausa(11, 0.6)

# ================================================================ O RAFA — 1: a montanha
C(12, img("M01_A", (1.0, 1.06), ((0.5, 0.5), (0.45, 0.5))))
C(13, img("M02_C", (1.0, 1.06), ((0.55, 0.5), (0.65, 0.45))))           # a Lívia filmando, de costas
C(14, c3("M01_C", "lado", (0.6, 0.4), 0.8, 0.0))                         # os prédios e a montanha atrás
C(15, c3("M02_B", "entrar", (0.6, 0.45), 0.9, 0.2))                      # ela na frente, na trilha
C(16, c3("M03_C", "entrar", (0.55, 0.55), 0.9, 0.2))                     # a curva vazia
C(17, img("M03_A", (1.0, 1.05), ((0.5, 0.5), (0.5, 0.5))))
C(18, c3("M03_B", "lado", (0.25, 0.5), 0.9, 0.3))                        # a mata do lado esquerdo
C(19, vid("V01_B", (1.0, 1.03)))
C(20, img("M02_A", (1.0, 1.06), ((0.55, 0.5), (0.58, 0.45))))           # o caminho por onde ela foi
C(21, c3("M03_C", "lado", (0.75, 0.5), 0.8, 0.0))                        # o lado direito da trilha
C(22, c3("M03_B", "entrar", (0.3, 0.5), 1.0, 0.3))
C(24, img("M03_B", (1.0, 1.04), ((0.5, 0.55), (0.5, 0.55))))             # "O Rafa não foi." — câmera quase parada
C(25, vid("V01_A", (1.0, 1.03)), (img("M03_C", (1.0, 1.05), ((0.5, 0.55), (0.5, 0.52))), "Do"))
C(26, img("M03_A", (1.05, 1.1), ((0.3, 0.5), (0.3, 0.5))))
amb(12, "ep09_mata_noite", -30); amb(16, "ep09_mata_noite", -24)
batidas[23]["ambiente"] = {"som": "ep09_mata_noite", "volume_db": -20}
musica(12, "11_a_montanha", -31)
fx(19, None, "respiracao_nuca", -30, atraso=-0.6)
pausa(17, 0.8); pausa(22, 0.6); pausa(25, 0.8); pausa(26, 1.6)

# ================================================================ PARTE 1 — o que mora no monte Jangsan
capitulo(27, 1, "O que mora no monte Jangsan", "장산범 · Busan", I + "M07_A.jpg",
         img("M01_C", (1.0, 1.06), ((0.6, 0.45), (0.62, 0.42))), "Em")
C(28, img("M07_B", (1.0, 1.08), ((0.45, 0.4), (0.48, 0.38))))             # o bicho branco entre as árvores (foto borrada)
C(29, vid("V01_B", (1.0, 1.03)))
C(30, ficha("장산범 · Jangsan-beom\n\"o tigre do Jangsan\"", "\"o tigre do Jangsan\""))
C(31, c3("M02_A", "entrar", (0.45, 0.5), 0.9, 0.3))
C(32, img("M07_A", (1.0, 1.06), ((0.55, 0.45), (0.57, 0.42))))
C(33, img("M07_C", (1.16, 1.2), ((0.55, 0.45), (0.56, 0.44)), kanji=K("장산범", 0.2, 0.5, "luz", "Jangsan-beom", em="Jangsan")))
pincel(33, "Jangsan")
C(34, img("M01_A", (1.0, 1.06), ((0.6, 0.45), (0.62, 0.45))))
C(35, img("M07_A", (1.0, 1.05), ((0.55, 0.45), (0.56, 0.43))), (filme("mimic_menina"), "mulher"),
      (c3("M07_B", "entrar", (0.47, 0.4), 0.7, 0.0), "caverna"))
C(36, img("M02_B", (1.0, 1.06), ((0.5, 0.5), (0.55, 0.45))))
C(37, img("M03_A", (1.0, 1.06), ((0.5, 0.5), (0.5, 0.5)), kanji=K("목소리", 0.8, 0.5, "luz", "moksori · a voz", em="voz")))
pincel(37, "voz")
amb(27, "nenhum"); amb(29, "ep09_mata_noite", -26); amb(35, "nenhum"); amb(36, "ep09_mata_noite", -26)
musica(27, "12_jangsan", -30, atraso=-5.4)            # entra com o cartão do capítulo
pausa(28, 0.6); pausa(32, 1.0); pausa(34, 0.6); pausa(37, 1.2)

# ================================================================ O RAFA — 2: os tênis
C(38, c3("M05_A", "entrar", (0.5, 0.55), 0.8, 0.2))
C(39, c3("M05_B", "entrar", (0.6, 0.5), 0.8, 0.0))                       # voluntários de colete, lanternas
C(40, c3("M04_A", "entrar", (0.5, 0.75), 0.9, 0.3, atmos={"neblina": 0.4}))   # os tênis lado a lado
C(41, img("M04_D", (1.05, 1.12), ((0.5, 0.7), (0.5, 0.72)), atmos={"neblina": 0.3}))
chat(42, {"de": "eu", "tipo": "audio", "duracao": "0:09", "hora": "08:14", "apos": 0.2})
chat(43, {"de": "eu", "tipo": "audio", "duracao": "0:04", "hora": "09:02", "apos": 0.1})
C(44, c3("M06_B", "entrar", (0.6, 0.6), 0.8, 0.2, atmos={"neblina": 0.4}))
# 45 "Era a Lívia." continua o degrau (44)
C(46, vid("V06_A", (1.0, 1.03)))                                         # (o sol na neblina cresce depois de ~4 s)
C(47, vid("V06_B", (1.0, 1.03)))
chat(48, {"de": "eu", "texto": "❤️" * 30, "hora": "06:31", "apos": 0.2},
     {"de": "Pai", "texto": "graças a Deus 🙏", "hora": "06:32", "apos": 0.9})
C(49, c3("C05_B", "entrar", (0.45, 0.6), 0.8, 0.3))                       # o Rafa no escuro, o celular na mão
C(50, img("M06_C", (1.0, 1.06), ((0.3, 0.45), (0.3, 0.4))))
C(51, img("M06_B", (1.12, 1.18), ((0.62, 0.45), (0.62, 0.42)), kanji=K("오빠", 0.22, 0.5, "sangue", "oppa", tam=0.3, atraso=0.05)))
pincel(51, None, atraso=-0.2)
C(52, img("M06_A", (1.0, 1.05), ((0.5, 0.5), (0.5, 0.45))))
C(53, img("M06_C", (1.08, 1.14), ((0.35, 0.4), (0.35, 0.38))))
amb(38, "ep09_mata_noite", -26); amb(42, "ep09_sala_bh", -30); amb(44, "ep09_mata_noite", -30)
musica(38, "13_os_tenis", -31)
pausa(41, 0.8); pausa(45, 0.6); pausa(49, 0.8); pausa(51, 0.6); pausa(53, 1.6)

# ================================================================ PARTE 2 — a irmã raposa (era Joseon)
capitulo(54, 2, "A irmã raposa", "여우누이 · Yeou Nui", I + "J01_A.jpg",
         img("J01_A", (1.0, 1.06), ((0.4, 0.55), (0.42, 0.55))), "Existe")
C(55, ficha("여우누이 · A Irmã Raposa\nmais de 75 versões", "75 versões"))
C(56, img("J01_B", (1.0, 1.06), ((0.4, 0.55), (0.42, 0.5))))
C(57, c3("J02_A", "entrar", (0.55, 0.55), 0.8, 0.0))                     # a menina de hanbok, de costas
C(58, c3("J01_C", "entrar", (0.45, 0.6), 0.9, 0.3, atmos={"neblina": 0.4}))   # o estábulo à noite
C(59, img("J01_A", (1.0, 1.08), ((0.3, 0.6), (0.25, 0.6))))
C(60, c3("J02_B", "entrar", (0.5, 0.5), 1.0, 0.3, atmos={"poeira": 0.3}))
C(61, img("J01_B", (1.1, 1.18), ((0.3, 0.75), (0.28, 0.78))))
C(62, img("J04_B", (1.0, 1.06), ((0.45, 0.55), (0.5, 0.55))))
C(63, img("J03_C", (1.0, 1.06), ((0.5, 0.55), (0.5, 0.5))))
C(64, img("J02_C", (1.0, 1.06), ((0.4, 0.55), (0.42, 0.5)), kanji=K("간", 0.82, 0.5, "sangue", "gan · fígado", tam=0.3, atraso=1.0)))
pincel(64, None, atraso=1.0)
C(65, img("J04_B", (1.0, 1.06), ((0.7, 0.5), (0.75, 0.55))))           # os dois irmãos com as trouxas
C(66, c3("J03_A", "entrar", (0.5, 0.55), 0.9, 0.0, atmos={"neblina": 0.5}))   # a vila vazia
C(67, c3("J04_A", "entrar", (0.3, 0.5), 0.8, 0.2))                       # ela na porta, de costas
C(68, img("J04_A", (1.12, 1.18), ((0.32, 0.5), (0.32, 0.48)), kanji=K("오빠", 0.8, 0.45, "sangue", "oppa", tam=0.26, atraso=0.05)))
C(69, img("J03_B", (1.0, 1.06), ((0.5, 0.5), (0.55, 0.5)), atmos={"neblina": 0.5}))
C(70, img("J04_B", (1.05, 1.1), ((0.72, 0.55), (0.72, 0.55))))             # os dois que faltavam
C(71, c3("J02_C", "entrar", (0.45, 0.45), 0.9, 0.3))
C(72, img("J03_C", (1.0, 1.06), ((0.5, 0.5), (0.5, 0.45)), atmos={"neblina": 0.5}))
amb(54, "nenhum"); amb(58, "ep09_lago", -30); amb(66, "nenhum")
musica(54, "04_joseon_irmas", -30, atraso=-5.4)
fx(61, None, "ep09_buk", -20, atraso=-0.4)
pausa(57, 0.8); pausa(61, 1.0); pausa(64, 0.8); pausa(67, 0.6); pausa(69, 0.8); pausa(70, 0.8); pausa(72, 1.6)

# ================================================================ O RAFA — 3: o óleo (SUSTO 1)
chat(73, {"de": "Lívia", "tipo": "foto", "imagem": I + "M01_B.jpg", "hora": "21:10", "apos": 0.3},
     {"de": "Lívia", "texto": "busan à noite 😍", "hora": "21:10", "apos": 1.0})
C(74, c3("C02_C", "entrar", (0.4, 0.5), 0.8, 0.2))                        # a mesa da cozinha, à noite
C(75, c3("C04_B", "entrar", (0.6, 0.65), 0.9, 0.2))                       # a coleira e a tigela na calçada
chat(76, {"de": "Rafa", "tipo": "foto", "imagem": I + "C04_A.jpg", "hora": "07:40", "apos": 0.2},
     {"de": "Rafa", "texto": "dois cachorros mortos no prédio da frente. sem marca nenhuma", "hora": "07:41", "apos": 0.9})
chat(77, {"de": "Pai", "tipo": "audio", "duracao": "0:05", "hora": "07:52", "apos": 0.1})
C(78, c3("C05_A", "entrar", (0.6, 0.55), 0.8, 0.2))                       # o Rafa sentado na cama de madrugada
C(79, c3("C03_B", "entrar", (0.75, 0.45), 0.9, 0.3))                      # do corredor: a luz da cozinha acesa
C(80, vid("V05_A", (1.0, 1.03)))                                          # ela de costas na pia (carimbo refeito)
C(81, img("C01_A", (1.05, 1.12), ((0.55, 0.45), (0.56, 0.42))))
C(82, c3("C02_B", "entrar", (0.3, 0.6), 0.9, 0.4))                        # o vidro de óleo
C(83, img("C01_C", (1.05, 1.15), ((0.55, 0.45), (0.56, 0.4))))
C(84, img("C01_B", (1.0, 1.03), ((0.5, 0.5), (0.5, 0.5))))                # o passo para trás: câmera parada
C(85, c3("C03_B", "sair", (0.4, 0.5), 0.7, 0.0))                          # o corredor, o quarto dela atrás dele
# SUSTO 1: a voz vem do quarto (atrás) — corte seco para a porta do quarto entreaberta, escura; a cozinha não se mexe
C(86, img("C03_A", (1.28, 1.3), ((0.33, 0.5), (0.33, 0.5))))                # a porta do quarto, entreaberta, escura
T(86, "corte")
C(87, img("C01_A_apagada", (1.0, 1.04), ((0.55, 0.45), (0.55, 0.45))))
C(88, {"imagem": IV2 + "F01_B.jpg", "zoom": [1.0, 1.06], "foco": [[0.6, 0.6], [0.62, 0.62]]})       # a mãe no sofá em BH
amb(74, "ep09_corredor", -28); amb(78, "geladeira", -30); amb(87, "geladeira", -32); amb(88, "ep09_sala_bh", -28)
musica(73, "05_a_parede", -31)
batidas[83]["musica"] = {"som": "nenhum", "em": "ombro"}                  # silêncio total ANTES do susto
fx(84, "trás", "ep07_respiracao_nuca", -26)
fx(86, None, "stinger_cordas", -10, atraso=-0.05)
fx(87, "apagada", "ep09_jing", -24)
batidas[87]["musica"] = {"som": "ep09_m05_a_parede", "volume_db": -32}   # volta logo depois do susto 1
pausa(80, 0.8); pausa(82, 0.8); pausa(85, 0.6); pausa(87, 1.6); pausa(88, 2.4)

# ================================================================ PARTE 3 — o elevador
capitulo(89, 3, "O elevador", "엘리베이터 게임 · o jogo", I + "H04_A.jpg",
         img("H04_A", (1.0, 1.06), ((0.5, 0.5), (0.52, 0.45))), "Existe")
C(90, ficha("엘리베이터 게임\no Jogo do Elevador", "o Jogo do Elevador"))
C(91, img("H03_B", (1.0, 1.06), ((0.45, 0.5), (0.45, 0.45))))
C(92, c3("H03_C", "entrar", (0.45, 0.45), 0.8, 0.0))
C(93, img("H03_B", (1.0, 1.05), ((0.45, 0.5), (0.45, 0.47))), (vid("V02_B", (1.4, 1.42), foco=[[0.62, 0.5], [0.62, 0.5]]), "nesta"))                       # 4 → 2 → 6 → 2 → 10 (a placa de hangul inventado fica fora)
C(94, img("H04_C", (1.0, 1.06), ((0.45, 0.45), (0.47, 0.42))))
C(95, c3("H05_C", "entrar", (0.5, 0.65), 0.8, 0.2))                       # os pés descalços entrando
C(96, img("H05_A", (1.0, 1.06), ((0.5, 0.5), (0.55, 0.55))))
C(97, img("H04_B", (1.0, 1.08), ((0.55, 0.45), (0.55, 0.5))))
C(98, c3("H03_A", "entrar", (0.45, 0.4), 0.8, 0.2))
C(99, texto("Você chegou.", "chegou.", "impacto", cps=10, tamanho=130))
C(100, c3("H06_B", "entrar", (0.5, 0.45), 1.0, 0.3))                      # o outro lado: o corredor igual, vazio
C(101, img("H05_B", (1.0, 1.06), ((0.6, 0.45), (0.6, 0.5))))
C(102, c3("C05_C", "entrar", (0.4, 0.55), 0.8, 0.3))                      # o Rafa às 4h, a tela do celular
C(103, img("C05_A", (1.05, 1.12), ((0.62, 0.5), (0.64, 0.5))))
C(104, texto("\"Quem volta da montanha nunca é quem subiu.\nO de verdade fica do outro lado.\"",
             "nunca é quem subiu.\"", cps=22, tamanho=64))   # o texto fica a frase inteira (tempo de leitura)
amb(89, "nenhum"); amb(91, "ep09_motor_elevador", -28); amb(102, "geladeira", -32)
musica(89, "03_as_regras", -30, atraso=-5.4)
fx(93, None, "ep09_elevador", -26, atraso=0.4)
pausa(93, 0.6); pausa(96, 0.8); pausa(98, 0.6); pausa(99, 0.8); pausa(101, 1.0); pausa(103, 0.6); pausa(104, 0.8)

# ================================================================ PARTE 4 — o hospital (Gonjiam)
capitulo(105, 4, "O hospital", "사 · 4 · morte", I + "H01_B.jpg",
         img("H04_A", (1.0, 1.08), ((0.45, 0.5), (0.48, 0.48)),
             kanji=[K("사", 0.2, 0.45, "sangue", "sa · quatro", tam=0.26, em="sa"),
                    K("死", 0.8, 0.45, "sangue", "sa · morte", tam=0.26, em="morte", glitch=True)]), "Na")
pincel(105, "sa"); pincel(105, "morte")
C(106, c3("H01_A", "entrar", (0.5, 0.45), 0.8, 0.0))
C(107, ficha("곤지암 · Gonjiam\nabandonado nos anos 90", "abandonado"))
C(108, c3("H01_B", "entrar", (0.45, 0.45), 0.9, 0.2))
C(109, img("H02_A", (1.0, 1.06), ((0.5, 0.5), (0.55, 0.45))))
C(110, c3("H01_C", "lado", (0.4, 0.45), 0.8, 0.0))
C(111, c3("H01_A", "entrar", (0.45, 0.6), 0.8, 0.0))
C(112, filme("gonjiam_mato"), (c3("H02_B", "entrar", (0.5, 0.4), 0.8, 0.2), "grupo"),   # a lanterna ficou quase preta na moldura
      (c3("H07_B", "entrar", (0.5, 0.5), 0.9, 0.3), "porta"))
C(113, img("H07_C", (1.0, 1.08), ((0.5, 0.45), (0.5, 0.42)), kanji=K("402", 0.82, 0.45, "luz", None, tam=0.24, em="402")))
C(114, c3("C05_B", "entrar", (0.45, 0.55), 0.8, 0.2))
C(115, img("H01_C", (1.0, 1.05), ((0.5, 0.5), (0.5, 0.48))))
amb(105, "nenhum"); amb(106, "ep09_hospital", -28); amb(112, "nenhum"); amb(113, "ep09_hospital", -28)
musica(105, "06_moca_de_branco", -30, atraso=-5.4)
pausa(106, 0.6); pausa(109, 0.6); pausa(110, 0.6); pausa(113, 0.8); pausa(115, 1.4)

# ================================================================ O RAFA — 4: o ritual
C(116, c3("H01_B", "entrar", (0.5, 0.5), 0.9, 0.3))
C(117, c3("H02_C", "entrar", (0.6, 0.45), 0.9, 0.3))
C(118, c3("H03_B", "entrar", (0.45, 0.45), 0.8, 0.3))
C(119, vid("V03_A", (1.3, 1.32), foco=[[0.58, 0.5], [0.58, 0.5]]))                                        # a luz acende, o botão (placa fora do quadro)
C(120, img("H04_A", (1.0, 1.06), ((0.5, 0.45), (0.5, 0.42))))
C(121, img("H04_C", (1.0, 1.08), ((0.45, 0.4), (0.45, 0.38))))
C(122, c3("H03_C", "entrar", (0.45, 0.45), 0.9, 0.3))                     # o áudio do gancho, agora no lugar certo
C(123, vid("V02_B", (1.4, 1.42), foco=[[0.62, 0.5], [0.62, 0.5]], video_inicio=0.5))
C(124, img("H03_A", (1.0, 1.04), ((0.45, 0.5), (0.45, 0.5))))
C(125, img("H04_C", (1.1, 1.18), ((0.4, 0.4), (0.4, 0.4))))
C(126, vid("V03_B", (1.35, 1.37), foco=[[0.62, 0.5], [0.62, 0.5]]))
C(127, c3("H05_A", "entrar", (0.62, 0.55), 0.9, 0.3))                     # os pés descalços, oleosos, do lado dos tênis
C(128, img("H03_B", (1.0, 1.03), ((0.45, 0.5), (0.45, 0.5))))
C(129, img("H05_B", (1.05, 1.12), ((0.6, 0.4), (0.62, 0.38))))
C(131, img("H03_A", (1.08, 1.12), ((0.45, 0.45), (0.45, 0.45))))
C(133, img("H04_B", (1.1, 1.18), ((0.4, 0.75), (0.4, 0.78))))
C(134, c3("H03_C", "sair", (0.45, 0.45), 0.8, 0.0))
amb(116, "ep09_hospital", -26); amb(119, "ep09_motor_elevador", -26)
musica(116, "08_gut_mudang", -31)
fx(119, "acendeu", "ep07_luz_volta", -24)
fx(121, None, "ep09_elevador", -26, atraso=-0.3)
fx(126, "abriu", "ep09_elevador", -22)
fx(127, "passos", "passos_atrasados", -24)
fx(129, "orelha", "ep07_respiracao_nuca", -20)
fx(133, "um", "tecla", -22)
pausa(117, 0.6); pausa(118, 1.2); pausa(124, 1.2); pausa(125, 0.8); pausa(128, 1.0); pausa(131, 1.0); pausa(134, 1.2)

# ================================================================ O RAFA — 5: o outro lado (SUSTO 2)
C(135, vid("V04_A", (1.0, 1.03)))
C(136, c3("H06_A", "entrar", (0.5, 0.45), 1.0, 0.2))
C(137, c3("H06_C", "entrar", (0.5, 0.45), 0.9, 0.0))
C(138, vid("V04_B", (1.0, 1.03)), (img("H07_A", (1.0, 1.08), ((0.5, 0.45), (0.5, 0.4)),
                                       kanji=K("402", 0.8, 0.45, "sangue", None, tam=0.24, em="quatrocentos")), "quatrocentos"))
C(139, c3("H07_A", "entrar", (0.5, 0.7), 1.0, 0.3))                       # as pegadas oleosas até a porta
C(140, img("H07_B", (1.15, 1.22), ((0.5, 0.45), (0.5, 0.45))))
C(141, img("H07_C", (1.1, 1.16), ((0.5, 0.45), (0.5, 0.45))))
C(143, img("H07_B", (1.22, 1.28), ((0.5, 0.45), (0.5, 0.45))))
# SUSTO 2: 3 s de silêncio (só a porta rangendo); a sala vazia (a cama, à esquerda) → CORTE para ela no canto
# 144: a sala vazia = só a cama (ela começa em x 0,65 da H08_A)
C(144, img("H08_A", (1.7, 1.72), ((0.29, 0.5), (0.29, 0.5))), (img("H08_B", (1.0, 1.04), ((0.6, 0.6), (0.6, 0.6))), "canto"))
batidas[144]["cenas"][1]["entrada"] = "corte"
batidas[144]["cenas"][0].update({"entrada": "corte", "antecipar": 1.4})   # a sala aparece no fim do silêncio, depois do rangido
C(145, img("H08_C", (1.0, 1.05), ((0.6, 0.5), (0.6, 0.5))))
C(147, img("H09_A", (1.15, 1.2), ((0.62, 0.72), (0.62, 0.72))))           # as mãos
C(148, vid("V04_A", (1.0, 1.03)), (img("H03_C", (1.0, 1.05), ((0.45, 0.45), (0.45, 0.42))), "elevador"))
C(149, img("H04_B", (1.1, 1.16), ((0.4, 0.75), (0.4, 0.78))))
C(150, img("H06_C", (1.0, 1.05), ((0.5, 0.45), (0.5, 0.45))))
C(151, c3("H06_B", "sair", (0.5, 0.45), 0.9, 0.3))
amb(135, "ep09_fluorescente", -24); amb(149, "ep09_motor_elevador", -28); amb(151, "ep09_fluorescente", -26)
musica(135, "07_o_chamado", -30)
batidas[143]["musica"] = {"som": "nenhum"}
batidas[145]["musica"] = {"som": "ep09_m07_o_chamado", "volume_db": -31}   # volta logo depois do susto 2
batidas[143]["ambiente"] = {"som": "ep09_fluorescente", "volume_db": -30}
pausa(144, 3.0)                                                           # os 3 s de silêncio antes da sala
fx(144, None, "ep06_porta_range", -22, atraso=-2.8)
fx(144, "canto", "stinger_cordas", -12)
fx(140, "ouvido", "ep09_choro_parede", -26)
fx(151, "Lívia", "ep09_elevador", -26, depois=True)
pausa(139, 0.6); pausa(141, 0.8); pausa(145, 0.6); pausa(147, 0.8); pausa(149, 0.6)

# ================================================================ O RAFA — 6: a ligação (SUSTO 3)
C(152, c3("H02_B", "entrar", (0.5, 0.4), 0.9, 0.3))
C(153, c3("H09_A", "entrar", (0.6, 0.55), 0.8, 0.2))
C(154, img("H09_B", (1.0, 1.06), ((0.5, 0.55), (0.45, 0.55))))
C(156, {"imagem": IV2 + "F01_A.jpg", "zoom": [1.0, 1.06], "foco": [[0.6, 0.6], [0.62, 0.6]]})
C(158, img("H10_C", (1.0, 1.08), ((0.5, 0.5), (0.52, 0.45))))
C(159, img("H10_C", (1.1, 1.6), ((0.5, 0.5), (0.5, 0.5))))            # entra na tela do celular: ela de costas no sofá
C(160, img("H10_C", (1.6, 1.85), ((0.5, 0.5), (0.5, 0.49))))   # a tela inteira no quadro (0,43–0,58 × 0,27–0,74)
# SUSTO 3: corta NO movimento (o rosto nunca aparece): tela preta, 2 s, a voz no escuro
C(161, texto("", None, cps=40))
T(161, "corte")
C(162, img("H09_B", (1.0, 1.04), ((0.7, 0.5), (0.72, 0.5))))
C(163, img("H09_B", (1.05, 1.1), ((0.72, 0.55), (0.72, 0.55))))
C(164, img("H09_A", (1.2, 1.3), ((0.62, 0.72), (0.62, 0.74))))
amb(152, "ep09_mata_noite", -30); amb(156, "ep09_sala_bh", -28); amb(161, "nenhum"); amb(162, "ep09_mata_noite", -32)
musica(152, "09_o_quarto", -31)
batidas[160]["musica"] = {"som": "nenhum", "em": "rosto"}
fx(161, None, "stinger_cordas", -12, atraso=-0.05)
batidas[162]["musica"] = {"som": "ep09_m07_o_chamado", "volume_db": -32}   # volta depois do susto 3 (o óleo na mão)
fx(164, "escorregadia", "ep09_jing", -24)
pausa(158, 0.6); pausa(160, 0.6); pausa(162, 2.0); pausa(163, 0.8); pausa(164, 0.6)

# ================================================================ FECHO — Vigia (corte seco do silêncio)
C(165, vigia((1.0, 1.04)))
T(165, "corte")
C(166, c3("M01_C", "lado", (0.6, 0.4), 0.8, 0.0))
C(167, vigia((1.0, 1.05)))
C(168, img("C01_B", (1.0, 1.06), ((0.55, 0.45), (0.56, 0.42))))
C(169, img("J04_A", (1.0, 1.06), ((0.4, 0.5), (0.42, 0.5)), kanji=K("오빠", 0.82, 0.45, "sangue", "oppa", tam=0.3, atraso=0.8)))
C(170, vigia((1.04, 1.1), ((0.42, 0.45), (0.4, 0.43))))
C(171, vigia((1.05, 1.12), ((0.4, 0.45), (0.36, 0.42))))
C(173, vigia((1.0, 1.05)))
C(174, c3("H08_C", "entrar", (0.75, 0.5), 0.9, 0.4))
amb(165, "nenhum"); amb(174, "ep09_mata_noite", -28)
musica(165, "10_fecho", -31)
pausa(166, 0.6); pausa(168, 0.8); pausa(169, 0.8); pausa(171, 0.6); pausa(173, 0.6); pausa(174, 0.8)



# ================================================================ DESENHO DE SOM (15/11)
# Pedido do usuário: "áudio é extremamente importante em terror, música e efeitos fazem grande diferença".
# - ambientes em CAMADAS (desenho_som.py): o lugar + um grave de tensão por baixo — nunca fica "vazio";
# - som no ESPAÇO (fone de ouvido): o que vem da esquerda/de trás/de perto é posicionado (pan);
# - efeitos no tempo da palavra; gongo AO CONTRÁRIO crescendo até o momento ruim; sub grave dando peso aos sustos.
LIVIA1 = str(AQUI / "vozes" / "limpas_escolhidas" / "livia1_Despina.wav")
for i, som, db in [(4, "ep09_amanhecer_tenso", -26), (5, "ep09_mata_tensa", -22), (12, "ep09_mata_tensa", -32),
                   (15, "ep09_mata_tensa", -25), (29, "ep09_mata_tensa", -25), (36, "ep09_mata_tensa", -25),
                   (38, "ep09_mata_tensa", -24), (44, "ep09_amanhecer_tenso", -26), (74, "ep09_cozinha", -28),
                   (78, "ep09_cozinha", -25), (87, "ep09_cozinha", -28), (91, "ep09_elevador_tenso", -28),
                   (102, "ep09_cozinha", -30), (106, "ep09_hospital_tenso", -26), (113, "ep09_hospital_tenso", -26),
                   (116, "ep09_hospital_tenso", -24), (119, "ep09_elevador_tenso", -22), (135, "ep09_fluorescente_tenso", -24),
                   (143, "ep09_fluorescente_tenso", -30), (149, "ep09_elevador_tenso", -26), (151, "ep09_fluorescente_tenso", -26),
                   (152, "ep09_amanhecer_tenso", -28), (162, "ep09_amanhecer_tenso", -30), (174, "ep09_mata_tensa", -28)]:
    batidas[i]["ambiente"] = {"som": som, "volume_db": db}
batidas[23]["ambiente"] = {"som": "ep09_mata_tensa", "volume_db": -19}          # a segunda chamada: a mata "chega perto"
# capítulos: um sopro quando o cartão entra (a música nova já entra junto)
for i in (27, 54, 89, 105):
    fx(i, None, "whoosh", -24, atraso=-4.9)
# O RAFA — 1: um galho estala do lado da voz; a voz dela repete longe enquanto ele espera; e PARA no meio da palavra
fx(18, "voz", "ep06_estalo", -27, pan=-0.6)
fx(25, "chamar", "voz_livia_longe", -31, arquivo=LIVIA1, pan=-0.8, eco=2.0, saida=0.6)
fx(25, "minutos", "voz_livia_longe", -33, arquivo=LIVIA1, pan=-0.85, eco=2.5, saida=0.6)
fx(26, None, "voz_cortada", -25, arquivo=LIVIA1, pan=-0.7, eco=1.5, ate=0.55, atraso=-1.3)   # "no meio de uma palavra"
# PARTE 1
fx(32, "não", "sub_drop", -24)
# O RAFA — 2: o gongo ao contrário cresce até o "Oppa" (ela, calma demais); o grave quando cai a ficha
fx(40, "tênis", "ep09_buk", -24)
fx(51, None, "ep09_jing", -24, reverso=True, atraso=-6.0)
fx(53, "coreano", "sub_drop", -23)
# PARTE 2: o fígado; a vila vazia; "mais dois"
fx(60, "puxou", "ep05_raspar", -26, tom=-3)
fx(66, None, "ep06_vento_capacete", -27, saida=2.0)
fx(70, "dois", "sub_drop", -23)
# O RAFA — 3: a cozinha (luz, mão molhada, o vidro, o assoalho) e o SUSTO 1 com peso grave
fx(79, "acesa", "tecla", -26)
fx(81, "molhado", "ep05_raspar", -31, tom=4, saida=1.0)
fx(82, "vidro", "ep08_bate_vidro", -28)
fx(84, "passo", "ep06_estalo", -25)
fx(86, None, "sub_drop", -15, atraso=-0.05)
fx(87, "apagada", "tecla", -22)
# PARTE 3: cada botão apertado no tempo do número
for w in ("quatro", "Dois", "Seis", "Dez"):
    fx(93, w, "tecla", -22)
fx(93, "Seis", "tecla", -22, atraso=0.62)                               # o segundo "dois"
fx(95, "entrar", "ep09_elevador", -26)
fx(96, "olha", "ep07_respiracao_nuca", -29, pan=-0.8)
fx(99, None, "braam_horror", -20)
# PARTE 4
fx(110, "CNN", "estatica_cctv", -30, saida=1.5)
# O RAFA — 4: o ritual — o muro, o elevador morto, cada botão, a porta, os passos e a respiração À ESQUERDA dele
fx(116, "muro", "metal_parada", -26)
fx(117, "parado", "ep07_corrente_longe", -29, saida=2.0)
for w in ("Quatro", "Dois", "Seis", "Dez"):
    fx(123, w, "tecla", -20)
fx(123, "Seis", "tecla", -20, atraso=0.62)
fx(125, None, "tecla", -18)
batidas[127]["sons"] = [s_ for s_ in batidas[127].get("sons", []) if s_["som"] != "passos_atrasados"]
fx(127, "passos", "passos_atrasados", -24, pan=-0.5)
batidas[129]["sons"] = [s_ for s_ in batidas[129].get("sons", []) if s_["som"] != "ep07_respiracao_nuca"]
fx(129, "orelha", "ep07_respiracao_nuca", -20, pan=-0.85)
fx(134, None, "riser_tensao", -22)
# O RAFA — 5: a porta abre no outro lado; os passos dele; SUSTO 2 com o grave
fx(135, None, "ep09_elevador", -24, atraso=-0.4)
fx(139, "andando", "passos_atrasados", -28)
fx(144, "canto", "sub_drop", -16)
fx(148, "Voltaram", "passos_atrasados", -25)
fx(149, "um", "tecla", -22)
# O RAFA — 6: a câmera virando; o gongo ao contrário cresce até ela virar o rosto → corte, cordas e o grave
fx(158, "virou", "whoosh", -26)
fx(161, None, "ep09_jing", -23, reverso=True, atraso=-6.0)
fx(161, None, "sub_drop", -15, atraso=-0.05)
fx(164, "escorregadia", "sub_drop", -22)
# FECHO: a última frase com uma respiração colada no ouvido
fx(174, None, "ep07_respiracao_nuca", -27, pan=-0.85, atraso=0.3)


# ---------------------------------------------------------------- SONNISS (15/11): efeitos profissionais no lugar dos fracos
def tira(i, som):
    batidas[i]["sons"] = [s_ for s_ in batidas[i].get("sons", []) if s_["som"] != som]


SN = "ep09_sn_"
for i in (27, 54, 89, 105):                                              # o sopro do cartão de capítulo
    tira(i, "whoosh"); fx(i, None, SN + "horror_whoosh", -25, atraso=-5.0, ate=3.5, saida=1.5)
fx(3, None, SN + "elevador_shepard", -27, atraso=-4.0, ate=4.5, saida=1.0)   # "ele tá subindo": o som que nunca para de subir
fx(28, None, SN + "respiracao_pulsante", -27, ate=24, saida=4.0)          # a criatura: uma respiração grande, pulsando, na mata
tira(86, "stinger_cordas"); fx(86, None, SN + "stinger_cello", -9, atraso=-0.05, ate=4.0, saida=2.0)
tira(79, "tecla"); fx(79, "acesa", SN + "interruptor", -22)
tira(87, "tecla"); fx(87, "apagada", SN + "interruptor", -20)
tira(99, "braam_horror"); fx(99, None, SN + "horror_momento", -19, ate=6.0, saida=2.5)
fx(123, None, SN + "coracao_panico", -27, ate=14, saida=3.0)              # o coração dele acelera nos botões
tira(126, "ep09_elevador"); fx(126, "abriu", SN + "elevador_porta_sobe", -24, ate=3.5, saida=0.8)
tira(127, "passos_atrasados")
for k, d in enumerate((0.0, 0.62, 1.25, 1.9)):                          # pés descalços na chapa de metal, à esquerda
    fx(127, "passos", SN + f"descalco_metal_{k % 3 + 1}", -24 + k * 1.5, atraso=d, pan=-0.55 + k * 0.08)
tira(129, "ep07_respiracao_nuca"); fx(129, "orelha", SN + "sussurro_fantasma", -21, pan=-0.9)
tira(134, "riser_tensao"); fx(134, None, SN + "elevador_shepard", -21, ate=9.0, saida=2.5)
fx(135, None, SN + "elevador_mecanismo", -26, atraso=-1.0)
tira(144, "ep06_porta_range"); fx(144, None, SN + "porta_rangido_lento", -21, atraso=-2.9, ate=3.2, saida=0.4)
tira(144, "stinger_cordas"); fx(144, "canto", SN + "horror_boom", -9, ate=4.0, saida=1.5)
fx(150, "fechava", SN + "elevador_porta_fecha", -24)
tira(161, "stinger_cordas"); fx(161, None, SN + "stinger_swell", -9, atraso=-0.05, ate=5.0, saida=2.5)
fx(161, None, SN + "piano_horror_reverso", -24, atraso=-11.0)              # o piano ao contrário cresce até ela virar o rosto
fx(84, "passo", SN + "respiracao_medo", -26)


# ---------------------------------------------------------------- TERROR ASIÁTICO (15/11)
# O loop ambiente (montar_loop.py) é a cama das LENDAS; a paleta de ataques (gayageum, haegeum, piri, janggu, buk+jing)
# fica para os momentos marcados: revelação, susto e ritual. Nada foi descartado (pedido do usuário).
AH = "ep09_ah_"
for i, som, db in [(27, "ep09_lenda_mata", -27), (29, "ep09_lenda_mata", -26), (36, "ep09_lenda_mata", -26),
                   (54, "ep09_lenda_joseon", -27), (58, "ep09_lenda_joseon", -26), (66, "ep09_lenda_joseon", -26),
                   (89, "ep09_lenda_elevador", -27), (91, "ep09_lenda_elevador", -26),
                   (105, "ep09_lenda_hospital", -27), (106, "ep09_lenda_hospital", -26), (113, "ep09_lenda_hospital", -26)]:
    batidas[i]["ambiente"] = {"som": som, "volume_db": db}
for i in (27, 54, 89, 105):                                   # o cartão de capítulo: buk + jing no lugar do sopro
    tira(i, SN + "horror_whoosh"); fx(i, None, AH + "buk_jing_1", -22, atraso=-4.9, ate=5.0, saida=2.0)
# revelações: o golpe dissonante do gayageum
fx(53, "coreano", AH + "gayageum_golpe_1", -17, ate=4.5, saida=2.0)
fx(69, "pais", AH + "gayageum_golpe_2", -18, ate=4.5, saida=2.0)
fx(126, "quatro", AH + "gayageum_golpe_1", -17, ate=4.5, saida=2.0)
fx(105, "morte", AH + "geomungo_grave_1", -19, ate=4.0, saida=1.5)
# o ritual: o janggu acelerando enquanto ele aperta os botões; o piri chorando quando a porta abre no 5º andar
fx(123, None, AH + "janggu_ritual_1", -21, atraso=-0.8, ate=9.0, saida=2.5)
fx(93, "nesta", AH + "janggu_ritual_2", -25, ate=8.0, saida=2.5)
fx(127, None, AH + "piri_lamento_1", -27, ate=6.0, saida=2.5)
# sustos: o grito do haegeum junto do impacto; a flauta soprando depois (a saída lenta)
fx(144, "canto", AH + "haegeum_grito_1", -20, ate=4.0, saida=1.5)
fx(87, "apagada", AH + "daegeum_sopro_1", -26, ate=6.0, saida=2.5)
fx(162, None, AH + "daegeum_sopro_2", -27, ate=6.0, saida=2.5)
fx(34, None, AH + "ajaeng_drone_1", -27, ate=9.0, saida=3.0)            # "Ninguém nunca provou que ele existe."

# ================================================================ VINHETA FIXA DE INSCRIÇÃO
batidas.append({"fala": F.VINHETA, "cta_inicio": True, "sem_legenda": True, "ambiente": {"som": "nenhum"},
                "musica": {"som": "vinheta_ultimo_abrigo", "volume_db": -20}})

voz = "audio/voz_personagens.wav" if (AQUI / "audio" / "voz_personagens.wav").exists() else "audio/voz_com_vinheta_limpa.wav"
roteiro = {
    "modo": "cenas", "formato": "16:9", "tema": "vigia", "avatar": "vigia_hd",
    "voz_arquivo": voz,
    "transcrever_pedacos": 75,                # no arquivo inteiro o Whisper pulava o fecho
    "cintilar": 0.03, "apertar_pausas": False,   # REGRA: nunca encurtar as pausas da narração
    "vigia_padrao": False,
    "cauda": 1.6, "chuva": 0, "grao": 0.14,
    # 13/11: trilha mais presente que no Ep. 08 (+4 dB), mas o rascunho 1 abafava a voz: -3 dB nas faixas e -9 sob a voz
    "mix": {"musica_ganho_db": 10.5, "fundo_sob_voz": -9, "efeitos_sob_voz": -4, "voz_pro": True, "fundo_bolso": True,
            "efeitos_pico_max": -3},
    "legendas": {"destaques": ["Coreia", "Jangsan", "Oppa", "óleo", "gergelim", "quatro", "402", "Gonjiam", "não olha"]},
    "ambiente_inicial": [{"som": "ep09_motor_elevador", "volume_db": -24}],
    "musica": {"som": "ep09_m01_tres_da_tarde", "volume_db": -28},
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
batidas[161].pop("sem_legenda", None)
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

    PROTEGE = {3, 5, 24, 26, 53, 72, 84, 86, 87, 143, 144, 158, 159, 160, 161, 162, 164, 174}   # sustos e silêncios: nunca continuar a anterior
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
        if c.get("tipo") == "capitulo" or c.get("entrada") == "corte" or c.pop("antecipar_fixo", False):
            continue
        ant = next((cenas_de(batidas[j]) for j in range(i - 1, -1, -1) if cenas_de(batidas[j])), [{}])[-1]
        if c.get("tipo") == "chat" and ant.get("tipo") == "chat":
            c["entrada"] = "corte"; continue          # conversa → conversa: a tela é a mesma
        padrao = {"nanquim": 1.3, "shoji": 0.9, "vela": 1.6}.get(c.get("entrada"), 0.6)
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
