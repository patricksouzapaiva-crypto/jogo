"""Monta roteiro.json do Ep. 06 "A porta na mata" a partir do ROTEIRO.md (falas.py: cada linha = 1 batida).
Regras da casa: Vigia só no tema/inserções/fecho; música o episódio inteiro (nunca silêncio total); saída lenta
das cenas tensas; clímax fica na imagem; ninguém de frente; ferimento é CONTADO, nunca mostrado.
Som: a mata tem som o tempo todo — os passarinhos SOMEM quando batem na porta (39) e só voltam na descida (156).
Uso: python3 montar_roteiro.py   (o tempo de leitura das telas de texto é garantido sozinho)
"""
import json
import sys
from pathlib import Path

import falas as F

AQUI = Path(__file__).parent
falas, CAIO, SEC = F.ler()
assert len(falas) == 190 and falas[142] == "Seis." and falas[104] == "Era o Caio.", "o ROTEIRO.md mudou: rever os índices"
batidas = [{"fala": f} for f in falas]

VIGIA = {"imagem": "../../painel/cenarios/abrigo_16x9.png", "vigia": True}


def vigia(z=(1.0, 1.04), foco=((0.55, 0.5), (0.57, 0.48))):
    return dict(VIGIA, zoom=list(z), foco=[list(foco[0]), list(foco[1])])


def img(nome, z=(1.0, 1.06), foco=None, **kw):
    c = {"imagem": f"grade/{nome}.jpg", "zoom": list(z), **kw}
    if foco:
        c["foco"] = [list(foco[0]), list(foco[1])]
    return c


def real(nome, reserva, z=(1.0, 1.06), foco=None, **kw):
    """Foto real (imagens_reais/, já passada pelo gradar.py); se não existir, usa a imagem de reserva."""
    return img(nome if (AQUI / "grade" / f"{nome}.jpg").exists() else reserva, z, foco, **kw)


def vid(nome, z=(1.0, 1.04), **kw):
    return {"video": f"grade/{nome}.mp4", "zoom": list(z), **kw}


def texto(t, vermelho=None, estilo="maquina", **kw):
    return {"tipo": "texto", "texto": t, "estilo": estilo, **({"vermelho": vermelho} if vermelho else {}), **kw}


def cartao(c, legenda, giro=-1.5):
    c = dict(c); c.update({"tipo": "cartao", "legenda_cartao": legenda, "giro": giro})
    return c


def C(i, *cenas, com_vigia=False):
    """Cenas da fala i. Cenas extras: (cena, "palavra onde entra")."""
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


def T(i, entrada, dur=0.8):
    b = batidas[i]
    (b.get("cena") or b["cenas"][0]).update({"entrada": entrada, "duracao_entrada": dur})


def saida_lenta(i_seguinte, segurar, transicao="fundir", dur=1.6):
    """Cena de tensão não termina com corte seco: fica `segurar` s depois da última palavra e funde devagar."""
    b = batidas[i_seguinte]
    b["pausa_antes_s"] = segurar + dur
    (b.get("cena") or b["cenas"][0]).update({"entrada": transicao, "duracao_entrada": dur, "antecipar": dur})


def pausa(i, s):
    batidas[i]["pausa_antes_s"] = batidas[i].get("pausa_antes_s", 0) + s


def mus(i, som, db, em=None):
    batidas[i]["musica"] = {"som": som, "volume_db": db, **({"em": em} if em else {})}


def amb(i, som, db=-14, em=None):
    batidas[i]["ambiente"] = {"som": som, "volume_db": db, **({"em": em} if em else {})}


def fx(i, em, som, db, depois=True, atraso=0.0):
    batidas[i].setdefault("sons", []).append({"em": em, "som": som, "volume_db": db, "depois": depois, "atraso": atraso})


def aplicar_ajuste_pausas():
    arq = AQUI / "audio" / "ajuste_pausas.json"
    for k, d in (json.load(open(arq)) if arq.exists() else {}).items():
        b = batidas[int(k)]
        if b.get("pausa_antes_s"):
            b["pausa_antes_s"] = round(max(0.3, b["pausa_antes_s"] + d), 2)


V = dict(com_vigia=True)
# pontos de interesse medidos nas imagens
SEXTA_B = ((0.72, 0.36), (0.725, 0.35))      # a 6ª lanterna em P09_B
LUZES_B = ((0.58, 0.42), (0.80, 0.42))       # varredura pelas lanternas em P08_B/P09_B
PORTA1B = ((0.50, 0.42), (0.50, 0.40))       # a porta em P01_B
RIO_A = ((0.63, 0.36), (0.63, 0.34))         # as duas silhuetas em P10_A
RIO_B = ((0.51, 0.43), (0.51, 0.42))         # idem em P10_B
JANELA = ((0.55, 0.37), (0.56, 0.38))        # a janela acesa em P17_B
TELA18 = ((0.45, 0.72), (0.45, 0.72))        # a tela do celular em P18_A

# ================================================================ GANCHO — sem Vigia
C(0, img("P08_B", (1.0, 1.08), ((0.6, 0.5), (0.65, 0.45))))
C(1, img("P08_B", (1.45, 1.45), LUZES_B))
C(2, img("P09_B", (1.6, 1.75), SEXTA_B))
C(3, texto("Eles eram cinco.", "cinco.", cps=30))
C(4, img("P09_B", (1.0, 1.08), ((0.6, 0.45), (0.65, 0.42))))
C(5, img("P09_B", (1.45, 1.7), ((0.62, 0.42), SEXTA_B[0])))
C(6, img("P09_B", (1.9, 2.1), SEXTA_B))
C(7, img("P09_B", (2.1, 2.2), SEXTA_B))
C(8, img("P09_A", (1.0, 1.12), ((0.45, 0.5), (0.5, 0.48))))
C(9, texto("Quem era o sexto?", "sexto?", cps=30))
C(10, img("P07_A", (1.0, 1.08), ((0.5, 0.55), (0.5, 0.5))), (img("P01_B", (1.0, 1.2), PORTA1B), "melhor"))
pausa(2, 1.4); pausa(3, 1.0); pausa(5, 0.6); pausa(6, 0.8); pausa(8, 1.2); pausa(9, 0.6)
fx(6, "rindo", "ep06_risada", -17)

# ================================================================ TEMA — Vigia apresenta
C(11, vigia((1.0, 1.05)), (real("floresta_eua_2", "P06_A", (1.0, 1.08)), "guarda"), **V)
C(12, real("floresta_escura_11", "P06_B", (1.0, 1.1)), (real("floresta_escura_3", "P06_A", (1.0, 1.1)), "achada"), **V)
C(13, real("escada_wald_1", "P06_B", (1.0, 1.15), ((0.5, 0.5), (0.5, 0.45))), **V)
C(14, real("escada_wald_1", "P06_B", (1.15, 1.35), ((0.5, 0.45), (0.5, 0.42))), (real("escada_wald_0", "P06_A", (1.0, 1.12)), "Sem"), **V)
C(15, texto("Não chegue perto.\nE não pergunte.", "não pergunte.", cps=40))
C(16, vigia((1.0, 1.05)), (real("mata_atlantica_1", "P06_B", (1.0, 1.1)), "mata"), **V)
C(17, vigia((1.04, 1.1), ((0.4, 0.45), (0.38, 0.43))))
C(18, img("P06_B", (1.0, 1.3), ((0.5, 0.5), (0.52, 0.48))), **V)
C(19, img("P01_B", (1.0, 1.12), PORTA1B), **V)
C(20, img("P02_A", (1.0, 1.12), ((0.5, 0.5), (0.5, 0.45))), **V)
C(21, vigia((1.0, 1.05)))
C(22, cartao(real("shackleton_5", "P06_A"), "Ernest Shackleton · 1916"), (real("south_georgia_3", "P06_A", (1.0, 1.1)), "atravessou"), **V)
C(23, real("shackleton_exp_1", "P06_A", (1.0, 1.1)), **V)
C(24, texto("Eles eram três.\nOs três contaram quatro.", "quatro.", cps=30))
pausa(13, 0.8); pausa(15, 0.5); pausa(17, 0.6); pausa(18, 1.0); pausa(21, 1.4)

# ================================================================ PARTE 1 — a clareira
C(25, real("serra_neblina_3", "P06_A", (1.0, 1.08)), (real("trilha_mata_5", "P06_B", (1.0, 1.1)), "Dois"))
T(25, "preto", 1.2); pausa(25, 1.4)
C(26, vid("V05_trilha_capacete", (1.0, 1.04)))
C(27, img("P07_B", (1.35, 1.35), ((0.3, 0.6), (0.72, 0.6))))                 # passa pelos cinco, de costas
C(28, img("P07_A", (1.5, 1.6), ((0.2, 0.62), (0.22, 0.6))))
C(29, vid("V03_mata", (1.0, 1.04)), (img("P06_B", (1.0, 1.06), ((0.5, 0.5), (0.52, 0.5))), "clareira"))
C(30, img("P06_B", (1.1, 1.5), ((0.52, 0.5), (0.775, 0.38))))                # o olhar acha a porta
C(31, img("P01_B", (1.0, 1.1), PORTA1B), (img("P01_A", (2.0, 2.3), ((0.56, 0.45), (0.565, 0.45))), "Maçaneta"))
C(32, img("P02_B", (1.0, 1.1), ((0.5, 0.5), (0.52, 0.48))))
C(33, img("P02_A", (1.2, 1.3), ((0.5, 0.5), (0.48, 0.5))))
C(34, img("P07_A", (1.0, 1.1), ((0.5, 0.6), (0.45, 0.6))))
C(35, real("trilha_mata_6", "P06_A", (1.0, 1.1)))
C(36, texto("Porta na mata\nnão se abre.", "não se abre.", cps=30))
C(37, texto("Se abrir,\nnão se atravessa.", "não se atravessa.", cps=30))
C(38, vid("V03_mata", (1.0, 1.05), video_inicio=3.0))
C(39, img("P07_B", (1.0, 1.05)), (img("P01_B", (1.2, 1.35), PORTA1B), "bateram"))
pausa(30, 1.0); pausa(31, 1.2); pausa(34, 0.8); pausa(36, 1.0); pausa(37, 0.8); pausa(38, 1.2)

# ================================================================ PARTE 2 — as batidas
C(40, vid("V01_aproxima_porta", (1.0, 1.03)))
C(41, img("P07_A", (1.0, 1.12), ((0.5, 0.55), (0.52, 0.45))))
C(42, img("P02_B", (1.0, 1.15), ((0.5, 0.5), (0.5, 0.48))))
C(43, img("P01_B", (1.35, 1.6), PORTA1B))
C(44, img("P07_B", (1.5, 1.6), ((0.45, 0.6), (0.4, 0.6))))
C(45, img("P07_A", (1.6, 1.75), ((0.28, 0.6), (0.3, 0.58))))
C(46, img("P01_A", (1.0, 1.1), ((0.5, 0.45), (0.5, 0.43))))
C(47, img("P04_A", (1.0, 1.12), ((0.55, 0.6), (0.6, 0.62))))
C(48, img("P03_A", (1.0, 1.15), ((0.5, 0.55), (0.48, 0.55))))
C(49, img("P05_A", (1.0, 1.15), ((0.5, 0.5), (0.47, 0.5))))
C(50, img("P05_B", (1.0, 1.1), ((0.5, 0.5), (0.52, 0.5))), (img("P03_B", (1.0, 1.08)), "contornou"))
C(51, img("P03_B", (1.1, 1.2), ((0.55, 0.55), (0.57, 0.55))))
C(52, img("P04_B", (1.0, 1.12), ((0.6, 0.5), (0.65, 0.5))))
C(53, img("P04_B", (1.2, 1.35), ((0.75, 0.5), (0.78, 0.5))))
C(54, vid("V02_porta_abre", (1.0, 1.04), video_inicio=2.6))
C(55, img("P01_B", (1.5, 1.8), PORTA1B))
saida_lenta(41, 2.6)
pausa(43, 1.4); pausa(44, 2.0); pausa(46, 0.9); pausa(47, 1.6); pausa(48, 1.6); pausa(51, 0.8); pausa(52, 1.2)
pausa(54, 1.2); pausa(55, 1.6)
fx(39, "bateram", "ep05_batidas", -13)
fx(43, "novo", "ep05_batidas_lentas", -19)
fx(47, "abriu", "ep06_porta_range", -17)
fx(52, "Devagar", "ep06_porta_range", -21)

# ================================================================ PARTE 3 — a primeira noite
C(56, img("P08_A", (1.0, 1.08), ((0.45, 0.5), (0.4, 0.5))))
T(56, "preto", 1.2); pausa(56, 2.6)
C(57, img("P08_A", (1.5, 1.6), ((0.3, 0.5), (0.28, 0.5))))
C(58, img("P08_B", (1.2, 1.3), ((0.75, 0.45), (0.78, 0.45))))
C(59, vid("V03_mata", (1.0, 1.05), video_inicio=1.0))
T(59, "fundir", 1.2); pausa(59, 1.6)
C(60, real("serra_neblina_6", "P06_A", (1.0, 1.12)), (real("gps_0", "P06_B", (1.0, 1.1)), "GPS"))
C(61, img("P06_B", (1.0, 1.25), ((0.5, 0.5), (0.775, 0.38))))
C(62, vid("V05_trilha_capacete", (1.0, 1.04), video_inicio=3.0))
C(63, img("P01_A", (1.0, 1.25), ((0.5, 0.45), (0.5, 0.43))))
C(64, real("riacho_mata", "P10_B", (1.0, 1.1)))
C(65, img("P10_B", (1.0, 1.25), ((0.5, 0.5), RIO_B[0])))
C(66, img("P10_B", (1.7, 1.9), RIO_B))
C(67, img("P10_A", (1.0, 1.4), ((0.55, 0.45), RIO_A[0])))
C(68, img("P10_A", (2.0, 2.3), RIO_A))                                        # a outra acena — fica nesta imagem
C(69, img("P10_A", (2.3, 2.45), RIO_A))
C(70, img("P07_B", (1.0, 1.1), ((0.5, 0.6), (0.52, 0.58))))
saida_lenta(70, 2.4)
pausa(61, 1.4); pausa(63, 1.6); pausa(65, 1.2); pausa(66, 0.8); pausa(68, 1.2); pausa(69, 1.0)

# ---------------------------------------------------------------- inserção 1 — "eu vi" (Vigia)
C(71, vigia((1.0, 1.05)))
saida_lenta(71, 2.2)
C(72, vigia((1.05, 1.1), ((0.4, 0.45), (0.38, 0.42))))
C(73, real("prisao_3", "P06_A", (1.0, 1.1)), (real("dna_1", "P06_B", (1.0, 1.1)), "soltas"), **V)
C(74, real("testemunha_5", "P06_A", (1.0, 1.1)), (real("olho_escuro_0", "P06_B", (1.0, 1.2), ((0.5, 0.5), (0.5, 0.5))), "olhou"), **V)
C(75, texto("O seu cérebro não grava rosto.\nEle reconhece.", "reconhece.", cps=45))
C(76, vigia((1.05, 1.12), ((0.4, 0.45), (0.37, 0.42))))
pausa(72, 0.6); pausa(76, 0.8)

# ================================================================ PARTE 4 — a segunda noite
C(77, img("P08_B", (1.0, 1.1), ((0.6, 0.5), (0.65, 0.45))), (img("P09_B", (1.5, 1.7), SEXTA_B), "Seis"))
T(77, "preto", 1.2); pausa(77, 2.2)
C(78, img("P09_B", (1.0, 1.06), ((0.6, 0.45), (0.62, 0.45))))
C(79, img("P09_B", (1.9, 2.1), SEXTA_B))
C(80, vid("V04_fogueira", (1.0, 1.05)))
C(81, vid("V04_fogueira", (1.1, 1.15), video_inicio=2.5), (img("P09_A", (1.3, 1.5), ((0.45, 0.45), (0.5, 0.42))), "O passo"))
C(82, texto("O Remedo não mata.", "não mata.", cps=28))
C(83, texto("Ele brinca.", "brinca.", "impacto", cps=8, tamanho=150))
C(84, img("P09_A", (1.0, 1.15), ((0.5, 0.5), (0.25, 0.4))))                  # o olhar sai do fogo para o escuro
C(85, img("P08_A", (1.9, 2.0), ((0.2, 0.25), (0.18, 0.25))))
C(86, img("P08_A", (2.0, 2.15), ((0.18, 0.25), (0.16, 0.25))))
C(87, img("P08_B", (1.5, 1.6), ((0.55, 0.55), (0.6, 0.55))))
C(88, img("P09_B", (1.7, 1.85), ((0.6, 0.5), (0.62, 0.5))))
C(89, vid("V04_fogueira", (1.0, 1.06), video_inicio=1.0))
C(90, img("P08_B", (1.3, 1.4), ((0.7, 0.5), (0.72, 0.5))))
C(91, texto("“Me amarra.\nSe acontecer de novo,\nvocês sabem que não sou eu.”", "não sou eu.”", cps=22))
C(92, img("P12_A", (1.1, 1.2), ((0.52, 0.55), (0.55, 0.55))))
C(93, img("P12_B", (1.0, 1.15), ((0.6, 0.55), (0.7, 0.6))))
C(94, img("P11_A", (1.0, 1.12), ((0.4, 0.55), (0.45, 0.55))))
C(95, img("P09_A", (1.6, 1.75), ((0.3, 0.5), (0.28, 0.5))))
C(96, img("P09_A", (1.75, 1.9), ((0.28, 0.5), (0.26, 0.5))))
C(97, texto("O subtenente.", "subtenente.", cps=20))
C(98, img("P11_B", (1.0, 1.15), ((0.55, 0.55), (0.6, 0.55))))
C(99, img("P12_A", (1.0, 1.08), ((0.4, 0.5), (0.35, 0.45))))
C(100, img("P12_B", (1.0, 1.2), ((0.5, 0.5), (0.6, 0.6))))
C(101, img("P12_A", (1.5, 1.8), ((0.6, 0.8), (0.63, 0.88))))                 # a mão já enfaixada — o ferimento não aparece
C(102, img("P12_B", (1.5, 1.6), ((0.75, 0.6), (0.78, 0.6))))
C(103, img("P12_B", (1.6, 1.8), ((0.4, 0.3), (0.3, 0.2))))                   # sobe para o escuro
C(104, texto("Era o Caio.", "Caio.", "impacto", cps=8, tamanho=150))
pausa(79, 1.2); pausa(80, 2.2); pausa(82, 1.2); pausa(83, 1.0); pausa(84, 2.2); pausa(85, 1.6); pausa(86, 2.0)
pausa(89, 0.8); pausa(90, 1.4); pausa(92, 0.9); pausa(94, 1.6); pausa(96, 0.9); pausa(97, 1.2); pausa(98, 0.8)
pausa(99, 1.6); pausa(100, 1.2); pausa(101, 1.0); pausa(103, 1.4); pausa(104, 1.4)
fx(79, "risada", "ep06_risada", -17)
fx(85, "estalo", "ep06_estalo", -15)

# ================================================================ PARTE 5 — os testes
C(105, texto("03:00", "03:00", "impacto", cps=10, tamanho=170))
saida_lenta(105, 3.0, dur=2.0)
C(106, img("P08_B", (1.0, 1.1), ((0.6, 0.5), (0.62, 0.48))))
C(107, img("P09_B", (1.2, 1.35), ((0.6, 0.45), (0.65, 0.42))))
C(108, img("P08_A", (1.0, 1.1), ((0.45, 0.5), (0.48, 0.5))))
C(109, img("P07_A", (1.4, 1.4), ((0.2, 0.6), (0.8, 0.6))))
C(110, img("P08_B", (1.3, 1.4), ((0.62, 0.5), (0.64, 0.5))))
C(111, img("P09_A", (1.2, 1.4), ((0.5, 0.48), (0.52, 0.45))))
C(112, img("P13_B", (1.3, 1.3), ((0.38, 0.5), (0.41, 0.5))))                 # só os cinco numerados no quadro
C(113, img("P13_B", (1.3, 1.3), ((0.41, 0.5), (0.6, 0.5))))                  # a contagem anda… e aparece o sexto
C(114, img("P13_B", (2.0, 2.3), ((0.82, 0.47), (0.84, 0.47))))
C(115, img("P08_A", (1.3, 1.4), ((0.55, 0.5), (0.57, 0.5))))
C(116, texto("E se um de nós\nnão for de verdade?", "de verdade?", cps=30))
C(117, texto("E se for eu…\ne eu não souber?", "não souber?", cps=28))
C(118, vid("V04_fogueira", (1.1, 1.16), video_inicio=0.5))
C(119, img("P09_B", (1.0, 1.15), ((0.6, 0.5), (0.62, 0.48))))
C(120, img("P08_A", (1.0, 1.1), ((0.5, 0.5), (0.5, 0.48))))
C(121, img("P11_A", (1.1, 1.2), ((0.4, 0.55), (0.42, 0.55))), (img("P12_A", (1.6, 1.7), ((0.62, 0.86), (0.63, 0.88))), "três"))
C(122, img("P08_B", (1.1, 1.0), ((0.6, 0.5), (0.6, 0.5))))
pausa(107, 1.0); pausa(111, 0.8); pausa(113, 1.4); pausa(114, 1.4); pausa(115, 2.0); pausa(116, 0.8); pausa(117, 1.2)
pausa(118, 1.8); pausa(120, 1.4); pausa(121, 1.2)

# ---------------------------------------------------------------- inserção 2 — o que ele quer (Vigia)
C(123, vigia((1.0, 1.05)))
saida_lenta(123, 2.6)
C(124, vigia((1.05, 1.1), ((0.4, 0.45), (0.38, 0.42))))
C(125, vigia((1.0, 1.05)), (img("P11_B", (1.0, 1.12)), "suficiente"), **V)
C(126, img("P09_A", (1.0, 1.15), ((0.45, 0.5), (0.5, 0.45))), **V)
C(127, real("bombeiros_fogo_1", "P07_B", (1.0, 1.1)), (img("P07_A", (1.0, 1.12), ((0.5, 0.6), (0.5, 0.55))), "não"), **V)
C(128, real("shackleton_5", "P06_A", (1.0, 1.12)), **V)
C(129, real("south_georgia_1", "P06_A", (1.0, 1.12)), **V)
C(130, texto("Ninguém perguntou\no que ele queria.", "queria.", cps=40))
pausa(124, 0.6); pausa(126, 0.8); pausa(130, 0.8)

# ================================================================ PARTE 6 — a câmera
C(131, vid("V03_mata", (1.0, 1.05), video_inicio=0.5))
T(131, "preto", 1.2); pausa(131, 2.0)
C(132, img("P11_B", (1.0, 1.1)), (vid("V05_trilha_capacete", (1.0, 1.04), video_inicio=1.0), "capacete"))
C(133, img("P14_B", (1.0, 1.1), ((0.6, 0.5), (0.62, 0.5))))
C(134, img("P15_B", (1.0, 1.1), ((0.6, 0.6), (0.62, 0.6))))
C(135, img("P15_B", (1.4, 1.55), ((0.72, 0.62), (0.73, 0.6))))
C(136, img("P15_B", (1.5, 1.6), ((0.35, 0.5), (0.3, 0.5))))                  # na frente dele: nada
C(137, img("P15_A", (1.3, 1.7), ((0.4, 0.6), (0.42, 0.45))))                 # o braço — fica nesta imagem
C(138, img("P15_A", (1.7, 1.8), ((0.42, 0.45), (0.42, 0.44))))
C(139, img("P14_B", (1.0, 1.12), ((0.6, 0.5), (0.62, 0.5))))
C(140, img("P14_A", (1.15, 1.3), ((0.5, 0.52), (0.5, 0.52))))
C(141, img("P09_A", (1.0, 1.1), ((0.45, 0.48), (0.47, 0.46))))
C(142, img("P09_B", (1.8, 2.0), SEXTA_B))
C(143, img("P14_A", (1.4, 1.5), ((0.5, 0.52), (0.5, 0.52))))
C(144, texto("Ele não era um deles.\nNunca foi.", "Nunca foi.", cps=30))
C(145, img("P14_A", (1.0, 1.1)), (real("olho_escuro_0", "P09_B", (1.0, 1.25), ((0.5, 0.5), (0.5, 0.5))), "só"))
C(146, texto("A câmera não tem olho\npra enganar.", "enganar.", cps=34))
C(147, img("P07_B", (1.0, 1.1), ((0.5, 0.6), (0.52, 0.58))))
C(148, img("P07_A", (1.2, 1.3), ((0.5, 0.6), (0.5, 0.58))))
C(149, img("P11_A", (1.2, 1.3), ((0.4, 0.55), (0.42, 0.55))))
C(150, vid("V05_trilha_capacete", (1.0, 1.04), video_inicio=2.0))
C(151, img("P16_A", (1.0, 1.15), ((0.45, 0.5), (0.35, 0.5))))
C(152, img("P16_B", (1.0, 1.12), ((0.5, 0.5), (0.45, 0.5))))
C(153, real("rua_vazia_madrugada_3", "P06_A", (1.0, 1.12)))
C(154, img("P06_A", (1.0, 1.2), ((0.5, 0.5), (0.53, 0.72 * 0.75))))
C(155, real("rua_bairro_noite_3", "P06_B", (1.0, 1.1)))
C(156, vid("V03_mata", (1.0, 1.05), video_inicio=2.0))
C(157, vid("V05_trilha_capacete", (1.0, 1.04), video_inicio=0.0))
C(158, img("P06_B", (1.0, 1.15), ((0.5, 0.5), (0.6, 0.45))))
C(159, img("P03_A", (1.0, 1.2), ((0.5, 0.55), (0.5, 0.55))))
C(160, img("P04_B", (1.0, 1.12), ((0.6, 0.5), (0.65, 0.5))))
C(161, img("P01_A", (1.0, 1.15), ((0.5, 0.45), (0.5, 0.43))))
C(162, texto("Se já abriu…\nnão adianta fechar.", "não adianta fechar.", cps=26))
pausa(134, 1.0); pausa(136, 1.4); pausa(137, 1.6); pausa(138, 2.6); pausa(139, 2.0); pausa(141, 1.2); pausa(142, 1.6)
pausa(143, 1.2); pausa(144, 1.4); pausa(147, 1.0); pausa(148, 1.2); pausa(150, 1.4); pausa(152, 1.0); pausa(153, 0.8)
pausa(156, 1.6); pausa(158, 1.4); pausa(159, 1.6); pausa(160, 1.6); pausa(162, 1.4)

# ================================================================ EPÍLOGO
C(163, real("hospital_quarto_2", "P19_B", (1.0, 1.1)))
saida_lenta(163, 3.2, dur=2.0)
C(164, texto("RELATÓRIO DE OCORRÊNCIA\nCausa: queda e desorientação.", "queda e desorientação.", cps=34))
C(165, img("P19_B", (1.0, 1.15), ((0.5, 0.5), (0.52, 0.5))))
C(166, img("P19_A", (1.0, 1.12), ((0.45, 0.5), (0.43, 0.5))))
C(167, real("rua_vazia_madrugada_3", "P17_B", (1.0, 1.08)), (img("P17_B", (1.0, 1.1), ((0.5, 0.5), (0.52, 0.45))), "A luz"))
C(168, img("P17_B", (1.3, 1.7), ((0.52, 0.45), JANELA[0])))
C(169, img("P17_B", (1.9, 2.3), JANELA))                                      # CLÍMAX — fica nesta imagem
C(170, img("P17_B", (2.3, 2.5), JANELA))
C(171, img("P18_A", (1.0, 1.08), ((0.5, 0.55), (0.48, 0.6))))
C(172, img("P18_A", (1.3, 1.7), ((0.48, 0.6), TELA18[0])))
C(173, img("P18_A", (1.7, 1.85), TELA18))
C(174, img("P18_A", (1.85, 2.05), TELA18))
C(175, img("P18_A", (1.2, 1.3), ((0.55, 0.3), (0.58, 0.25))))
C(176, img("P17_B", (2.3, 2.6), JANELA))
C(177, img("P17_B", (2.6, 2.75), JANELA))
C(178, img("P17_B", (2.75, 2.85), JANELA))
pausa(165, 1.0); pausa(167, 1.6); pausa(168, 1.2); pausa(169, 1.6); pausa(170, 1.4); pausa(171, 2.0); pausa(172, 1.4)
pausa(173, 1.0); pausa(174, 1.0); pausa(175, 2.2); pausa(176, 1.4); pausa(177, 2.0); pausa(178, 1.4)
fx(167, "carro", "ep06_motor", -20, depois=False)
fx(168, "Rindo", "ep06_riso_menina", -18)
fx(173, "ninguém", "ep06_riso_menina", -20)

# ================================================================ FECHO — Vigia
C(179, vigia((1.0, 1.05)))
saida_lenta(179, 4.4, dur=2.0)                                                # sai devagar do clímax
C(180, vigia((1.05, 1.1), ((0.4, 0.45), (0.38, 0.42))))
C(181, vigia((1.0, 1.05)), (img("P09_B", (1.3, 1.5), SEXTA_B), "ser"), **V)
C(182, img("P17_B", (1.0, 1.15), ((0.5, 0.5), (0.52, 0.45))), **V)
C(183, texto("Porta na mata\nnão se abre.", "não se abre.", cps=30))
C(184, texto("Se abrir,\nnão se atravessa.", "não se atravessa.", cps=30))
C(185, texto("E se já abriu…\nconta de novo.", "conta de novo.", cps=26))
C(186, vigia((1.0, 1.05)))
C(187, vigia((1.05, 1.1), ((0.4, 0.45), (0.38, 0.42))))
C(188, vigia((1.1, 1.16), ((0.35, 0.45), (0.33, 0.42))))
C(189, texto("Aponta a câmera.", "câmera.", "impacto", cps=8, tamanho=140))
pausa(180, 1.0); pausa(183, 1.2); pausa(184, 0.8); pausa(185, 1.0); pausa(186, 1.2); pausa(188, 1.2); pausa(189, 1.4)

# ================================================================ VOZ DO CAIO (as duas únicas falas com outra voz)
# trocar_vozes.py monta audio/voz_personagens.wav; a pausa seguinte encolhe o que a fala nova crescer.

# ================================================================ SOM DE LUGAR (canal "ambiente")
A_DB = -15
amb(11, "nenhum")                                    # o Vigia fala do abrigo: só a música
amb(25, "ep06_mata_dia", A_DB)                       # a mata viva
amb(39, "ep06_mata_muda", A_DB, em="bateram")        # bateram: os passarinhos somem
amb(56, "ep06_mata_noite", A_DB + 3)
amb(59, "ep06_mata_muda", A_DB)
amb(64, "ep06_riacho", A_DB - 3)
amb(70, "ep06_mata_muda", A_DB)
amb(71, "nenhum")
amb(77, "ep06_mata_noite", A_DB + 3)
amb(123, "nenhum")
amb(131, "ep06_mata_muda", A_DB)
amb(134, "ep06_vento_capacete", A_DB - 4)            # a gravação do capacete
amb(139, "ep06_mata_muda", A_DB)
amb(156, "ep06_mata_dia", A_DB)                      # na descida, os passarinhos voltam
amb(158, "ep06_mata_muda", A_DB)                     # …menos na clareira
amb(163, "nenhum")
amb(165, "ep06_rua_noite", A_DB + 4)
amb(179, "nenhum")

# ================================================================ MÚSICA (canal "trilhas"): fundo ↔ tensão, nunca silêncio
F_DB, T_DB = -21, -24
mus(0, "ep06_tensao_longa", T_DB)                    # gancho
mus(11, "ep06_fundo_longa", F_DB)
mus(39, "ep06_tensao_longa", T_DB, em="bateram"); mus(56, "ep06_fundo_longa", F_DB)
mus(64, "ep06_tensao_longa", T_DB); mus(71, "ep06_fundo_longa", F_DB)
mus(77, "ep06_tensao_longa", T_DB); mus(105, "ep06_fundo_longa", F_DB)
mus(112, "ep06_tensao_longa", T_DB); mus(123, "ep06_fundo_longa", F_DB)
mus(133, "ep06_tensao_longa", T_DB); mus(147, "ep06_fundo_longa", F_DB)
mus(158, "ep06_tensao_longa", T_DB); mus(163, "ep06_fundo_longa", F_DB)
mus(167, "ep06_tensao_longa", T_DB); mus(179, "ep06_fundo_longa", F_DB)

# ================================================================ VINHETA FIXA DE INSCRIÇÃO
batidas.append({"fala": F.VINHETA, "cta_inicio": True, "sem_legenda": True, "ambiente": {"som": "nenhum"},
                "musica": {"som": "vinheta_ultimo_abrigo", "volume_db": -20}})

voz = "audio/voz_personagens.wav" if (AQUI / "audio" / "voz_personagens.wav").exists() else "audio/voz_com_vinheta_limpa.wav"
roteiro = {
    "modo": "cenas", "formato": "16:9", "tema": "vigia", "avatar": "vigia_hd",
    "voz_arquivo": voz,
    "cintilar": 0.045, "apertar_pausas": False,   # REGRA: nunca encurtar as pausas da narração
    "vigia_padrao": False,
    "preencher_pausas": {"min": 1.3},
    "cauda": 1.6, "chuva": 0, "grao": 0.20,
    "mix": {"musica_ganho_db": 12, "fundo_sob_voz": -9, "efeitos_sob_voz": -4, "voz_pro": True, "fundo_bolso": True},
    "legendas": {"destaques": ["porta", "seis", "cinco", "Remedo", "câmera", "Caio", "conta"]},
    "ambiente_inicial": [{"som": "ep06_mata_noite", "volume_db": A_DB + 3}],
    "musica": {"som": "ep06_tensao_longa", "volume_db": T_DB},
    "abertura": {"texto": "O VIGIA\nEP. 06 · A PORTA NA MATA", "vermelho": "PORTA NA MATA", "duracao": 3.2, "segurar": 1.6,
                 "antes_da_batida": 11, "sons": [{"som": "sub_drop", "t": 0.2, "volume_db": -12}]},
    "cta": {"titulo": "Conta de novo.", "canal": "Último Abrigo",
            "subtitulo": "Inscreva-se para mais casos do Vigia",
            "fundo": "../../painel/cenarios/abrigo_16x9.png", "pose": "c_cafe_convite",
            "antes": 0.6, "clique_em": "Inscreva-se", "duracao": 2.5},
    "batidas": batidas,
}


def cenas_de(b):
    return ([b["cena"]] if b.get("cena") else []) + b.get("cenas", [])


for b in batidas:  # tela de texto não leva legenda (o texto já está na tela)
    for c in cenas_de(b):
        if c.get("tipo") == "texto" and "em" not in c:
            b["sem_legenda"] = True
faltando = sorted({c[k] for b in batidas for c in cenas_de(b) for k in ("imagem", "video") if c.get(k) and not (AQUI / c[k]).exists()})
if faltando:
    raise SystemExit("arquivos faltando: " + ", ".join(faltando))
def garantir_leitura():
    """Tela de texto: depois de digitada fica >= 1,5 s + 0,3 s por palavra. O que faltar entra como pausa na fala seguinte."""
    sys.path.insert(0, str(AQUI.parents[1] / "painel"))
    from gerar import tokens
    tempos = json.load(open(AQUI / "audio" / "alinhamento.json"))
    k, ini, fim = 0, [], []
    for b in batidas:
        n = len(tokens(b["fala"])); ini.append(tempos[k][0]); fim.append(tempos[k + n - 1][1]); k += n
    mudou = []
    for i, b in enumerate(batidas[:-1]):
        cs = cenas_de(b)
        if len(cs) != 1 or cs[0].get("tipo") != "texto":
            continue
        c, prox = cs[0], batidas[i + 1]
        t1 = ini[i + 1] + prox.get("pausa_antes_s", 0) - (cenas_de(prox)[0].get("antecipar", 0) if cenas_de(prox) else 0)
        sobra = (t1 - ini[i]) - len(c["texto"]) / c.get("cps", 40)
        falta = 1.5 + 0.3 * len(c["texto"].split()) - sobra
        if falta > -0.45:
            prox["pausa_antes_s"] = round(prox.get("pausa_antes_s", 0) + falta + 0.6, 2); mudou.append((i, round(falta, 1)))
    print("pausas aumentadas para dar tempo de leitura (fala, s):", mudou)


garantir_leitura()
sem = [i for i, b in enumerate(batidas) if not cenas_de(b)]
aplicar_ajuste_pausas()
(AQUI / "roteiro.json").write_text(json.dumps(roteiro, ensure_ascii=False, indent=1), encoding="utf-8")
n_cenas = sum(len(cenas_de(b)) for b in batidas)
reservas = sorted({c["imagem"] for b in batidas for c in cenas_de(b) if c.get("imagem", "").startswith("grade/P")})
print(f"{len(batidas)} falas, {n_cenas} cenas, falas sem cena: {sem}")

