"""Monta roteiro.json do Ep. 09 "O quarto do andar F" (falas.py: cada frase do ROTEIRO.md = 1 batida).
Regras da casa: Vigia só no tema/fecho; música o episódio inteiro, uma faixa composta para cada parte (trilha
aprovada 13/11, painel/sons/ep09_m*.mp3); sem susto; saída lenta das cenas tensas; ninguém de frente (a moça de
branco sempre com o cabelo no rosto, pequena); vozes da Bia (Leda) e da mãe (Sulafat) só pelo celular.
13/11 (pedido do usuário): "se atente bem às iluminações, jogo de câmera e foco".
 - foco/zoom de cada imagem conferidos na grade (o ponto de interesse de verdade: a porta, o ventilador, o celular);
 - "câmera 3D" (painel/ferramentas/camera3d.py): a câmera anda dentro da foto com profundidade real e foco de lente;
 - efeitos de luz só onde a imagem tem aquela luz (vela onde tem vela, neblina no lago, celular no escuro).
Uso: python3 montar_roteiro.py  → roteiro.json (+ camera3d/*.mp4 na primeira vez)
"""
import hashlib
import json
import sys
from pathlib import Path

import falas as F

AQUI = Path(__file__).parent
falas, PERS, SEC, PAUSAS, _ = F.ler()
assert len(falas) == 154 and falas[142] == "Bia." and PERS == {6: "mae", 30: "bia", 87: "bia", 91: "mae", 107: "bia", 111: "voz"}, \
    "o ROTEIRO.md mudou: rever os índices"
batidas = [{"fala": f} for f in falas]
for i, s in PAUSAS.items():
    batidas[i]["pausa_antes_s"] = s

I, CL, FP = "imagens/", "clipes/", "filmes_prontos/"
VIGIA = {"imagem": "../../painel/cenarios/abrigo_16x9.png", "vigia": True}
C3D = AQUI / "camera3d"; C3D.mkdir(exist_ok=True)


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
    return texto(t, vermelho, cps=26)


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


def fx(i, em, som, db, depois=False, atraso=0.0):
    batidas[i].setdefault("sons", []).append({"em": em, "som": som, "volume_db": db, "depois": depois, "atraso": atraso})


def musica(i, faixa, db, em=None):
    batidas[i]["musica"] = {"som": f"ep09_m{faixa}", "volume_db": db, **({"em": em} if em else {})}


def capitulo(i, n, titulo, sub, imagem, cena, em):
    """Cartão de capítulo (제N장) na pausa antes da fala, com o buk (tambor coreano) longe; depois a cena entra."""
    cap = {"tipo": "capitulo", "numero": f"제{n}장", "numero_pt": f"Capítulo {n}", "titulo": titulo, "ano": sub,
           "imagem": imagem, "antecipar": 4.8, "entrada": "nanquim", "atmos": {"poeira": 0.5}}
    cena = dict(cena); cena.setdefault("entrada", "fundir"); cena.setdefault("duracao_entrada", 0.8)
    C(i, cap, (cena, em))
    pausa(i, 5.2)
    fx(i, None, "ep08_tinta", -18, atraso=-4.8)
    fx(i, None, "ep09_buk", -17, atraso=-3.4)


HIST = []                          # grupo "Família BH 💛" visto do celular da MÃE ("eu")


def chat(i, *novas, sons=True):
    msgs = [dict(m, apos=-30) for m in HIST[-6:]]
    for m in novas:
        m = dict(m); m.setdefault("apos", 0.3)
        msgs.append(m); HIST.append({k: v for k, v in m.items() if k not in ("apos", "em", "digitando")})
        if sons and "em" not in m:
            fx(i, None, "ep08_msg", -19, atraso=m["apos"])
        elif sons:
            fx(i, m["em"], "ep08_msg", -19)
    C(i, {"tipo": "chat", "grupo": "Família BH 💛", "membros": "Bia, Mãe, Pai, Tia Nena", "mensagens": msgs})
    batidas[i]["sem_legenda"] = True


def pincel(i, em, db=-16, atraso=0.0):
    fx(i, em, "ep08_kanji", db, atraso=atraso)


def HAN(tam, x=0.5, **kw):                                                  # o elemento-marca: cada vez maior
    return K("한", x, 0.5, "tinta", "han", tam=tam, **kw)

# ================================================================ GANCHO — sem Vigia (03:00 em Seul / 15:00 em BH)
C(0, {"tipo": "relogios", "lados": [{"nome": "Seul", "hora": "03:00", "imagem": I + "S01_B.jpg", "brilho": 0.55},
                                     {"nome": "Belo Horizonte", "hora": "15:00", "imagem": I + "F01_A.jpg", "brilho": 0.75}]})
chat(1, {"de": "Bia", "tipo": "audio", "duracao": "0:05", "hora": "15:00", "em": "áudio", "digitando": 0.6})
C(2, img("F02_A", (1.0, 1.12), ((0.6, 0.35), (0.62, 0.32)), dof={"x": 0.62, "y": 0.32, "r": 0.24, "atraso": 0.2}))
# os 5 s só de ventilador: o quarto escuro, a câmera entrando devagar no ventilador
C(3, c3("B06_B", "entrar", (0.8, 0.42), 0.8, 0.45, atmos={"poeira": 0.3}))
T(3, "fundir", 2.0)
C(4, vid("V06_celular_cama", (1.0, 1.04)))
C(5, img("F01_B", (1.0, 1.1), ((0.6, 0.6), (0.65, 0.65)), dof={"x": 0.66, "y": 0.62, "r": 0.2, "atraso": 0.3}))
chat(6, {"de": "eu", "tipo": "audio", "duracao": "0:02", "hora": "15:01", "apos": 0.1})
C(7, img("B14_B", (1.0, 1.1), ((0.55, 0.55), (0.58, 0.6)), atmos={"chuva": 0.4}))
C(8, c3("B01_B", "entrar", (0.49, 0.4), 1.0, 0.3))
C(9, c3("B10_B", "entrar", (0.47, 0.38), 1.2, 0.6))
amb(0, "ep09_ventilador", -22); amb(7, "ep09_seul_chuva", -24); amb(8, "ep09_corredor", -22)
fx(2, "play", "ep08_vibra", -30)
batidas[3]["ambiente"] = {"som": "ep09_ventilador", "volume_db": -12}       # o ventilador SOZINHO nos 5 s
amb(4, "ep09_ventilador", -20)
pausa(9, 0.4)

# ================================================================ TEMA — Vigia
C(10, vigia((1.0, 1.04)))
saida_lenta(10, 1.4)
C(11, vigia((1.0, 1.05)))
C(12, img("B14_A", (1.0, 1.08), ((0.5, 0.5), (0.62, 0.45)), atmos={"chuva": 0.3}))
C(13, img("S01_A", (1.0, 1.12), ((0.5, 0.5), (0.58, 0.18)), dof={"x": 0.58, "y": 0.18, "r": 0.2, "atraso": 0.4}))
C(14, vigia((1.0, 1.06)))
C(15, img("S04_B", (1.0, 1.06), ((0.5, 0.5), (0.65, 0.5)), atmos={"vela": 0.5}, kanji=HAN(0.18, em="han", atraso=0.1)))
pincel(15, "han")
C(16, vigia((1.04, 1.08), ((0.45, 0.48), (0.43, 0.46))))
C(17, img("S04_A", (1.04, 1.12), ((0.67, 0.5), (0.67, 0.45)), atmos={"vela": 0.6}))
C(18, img("S03_A", (1.0, 1.1), ((0.6, 0.5), (0.62, 0.48)), atmos={"neblina": 0.5}))
C(19, c3("B02_A", "entrar", (0.8, 0.35), 1.0, 0.3))
amb(10, "nenhum")
musica(10, "02_han", -30)
pausa(13, 0.6); pausa(15, 0.8); pausa(17, 0.6); pausa(19, 0.6)

# ================================================================ A BIA — 1: as regras
C(20, cel(img("B14_A", (1.0, 1.06), ((0.55, 0.55), (0.6, 0.6)), atmos={"chuva": 0.3}), "21:14"))
C(21, img("B14_B", (1.0, 1.1), ((0.2, 0.2), (0.22, 0.18)), kanji=K("고시원", 0.78, 0.5, "placa", "goshiwon", fundo="vermelho", em="goshiwon")))
pincel(21, "goshiwon")
C(22, c3("B02_B", "entrar", (0.5, 0.45), 0.9, 0.0))
C(23, img("B03_A", (1.0, 1.35), ((0.5, 0.5), (0.59, 0.5)), dof={"x": 0.59, "y": 0.5, "r": 0.16, "atraso": 1.2}))
fx(23, "F", "ep09_elevador", -24)
C(24, c3("B01_A", "entrar", (0.49, 0.42), 0.9, 0.2))
C(25, cel(img("B04_A_regras", (1.0, 1.06), ((0.5, 0.45), (0.52, 0.32))), "21:40"),
  ({"tipo": "chat", "grupo": "Família BH 💛", "membros": "Bia, Mãe, Pai, Tia Nena",
    "mensagens": [{"de": "Bia", "tipo": "foto", "imagem": I + "B04_A_regras.jpg", "hora": "09:41", "apos": 0.1},
                  {"de": "Bia", "texto": "olha as regras do meu andar kkkkk", "hora": "09:41", "apos": 0.9}]}, "mandou"))
HIST += [{"de": "Bia", "tipo": "foto", "imagem": I + "B04_A_regras.jpg", "hora": "09:41"},
         {"de": "Bia", "texto": "olha as regras do meu andar kkkkk", "hora": "09:41"}]
fx(25, "mandou", "ep08_msg", -19)
# cada regra: a câmera vai até a linha dela na folha (Regra 1 no alto … Regra 4 embaixo)
C(26, img("B04_A_regras", (1.35, 1.4), ((0.53, 0.1), (0.53, 0.11)), dof={"x": 0.5, "y": 0.5, "r": 0.34}))
C(27, img("B04_A_regras", (1.35, 1.4), ((0.53, 0.2), (0.53, 0.21)), dof={"x": 0.5, "y": 0.5, "r": 0.34}))
C(28, img("B04_A_regras", (1.3, 1.36), ((0.53, 0.33), (0.53, 0.34)), dof={"x": 0.5, "y": 0.5, "r": 0.34}))
C(29, img("B04_A_regras", (1.3, 1.36), ((0.53, 0.47), (0.53, 0.48)), dof={"x": 0.5, "y": 0.5, "r": 0.34}))
chat(30, {"de": "Bia", "tipo": "audio", "duracao": "0:03", "hora": "09:42", "apos": 0.1})
C(31, img("B04_A_regras", (1.0, 1.04), ((0.5, 0.4), (0.5, 0.4)), atmos={"poeira": 0.3}))
amb(20, "ep09_seul_chuva", -26); amb(22, "ep09_corredor", -28)
musica(20, "03_as_regras", -30)
pausa(23, 0.6); pausa(26, 0.4); pausa(27, 0.4); pausa(28, 0.4); pausa(29, 0.4); pausa(31, 0.8)

# ================================================================ PARTE 1 — o andar F
capitulo(32, 1, "O andar que não existe", "사 · 4 · morte", I + "B03_B.jpg",
         img("B03_B", (1.0, 1.1), ((0.5, 0.5), (0.6, 0.52)),
             kanji=[K("사", 0.2, 0.45, "sangue", "sa · quatro", tam=0.26, em="sa"),
                    K("死", 0.8, 0.45, "sangue", "sa · morte", tam=0.26, em="morte", glitch=True)]), "Na")
pincel(32, "sa"); pincel(32, "morte")
C(33, img("B03_A", (1.1, 1.5), ((0.45, 0.5), (0.59, 0.5)), dof={"x": 0.59, "y": 0.5, "r": 0.14, "atraso": 1.5}))
C(34, c3("B01_B", "entrar", (0.49, 0.4), 1.2, 0.3, atmos={"poeira": 0.3}))
C(35, c3("B01_A", "lado", (0.5, 0.45), 0.8, 0.0))
C(36, img("S01_B", (1.0, 1.15), ((0.5, 0.4), (0.6, 0.2)), dof={"x": 0.6, "y": 0.18, "r": 0.18, "atraso": 0.4}))
C(37, img("B11_B", (1.0, 1.14), ((0.5, 0.5), (0.5, 0.25))))
amb(32, "nenhum"); amb(34, "ep09_corredor", -24)
pausa(33, 0.6); pausa(36, 0.6); pausa(37, 1.0)

# ================================================================ PARTE 2 — o ventilador
C(38, c3("B02_A", "entrar", (0.8, 0.33), 1.0, 0.5))
C(39, ficha("2006 · agência de defesa do consumidor\n\"asfixia por ventilador\"\nentre os acidentes de verão", "\"asfixia por ventilador\""))
C(40, img("B02_B", (1.2, 1.5), ((0.8, 0.35), (0.82, 0.36)), dof={"x": 0.82, "y": 0.36, "r": 0.2, "atraso": 0.6}))
C(41, img("B06_A", (1.0, 1.08), ((0.5, 0.5), (0.3, 0.6)), dof={"x": 0.29, "y": 0.62, "r": 0.18}))
C(42, c3("B06_A", "entrar", (0.29, 0.62), 0.9, 0.5))
C(43, vid("V02_ventilador", (1.0, 1.04)))
C(44, vid("V02b_ventilador", (1.0, 1.06)))
C(45, img("B07_A", (1.0, 1.12), ((0.5, 0.5), (0.3, 0.45)), dof={"x": 0.28, "y": 0.45, "r": 0.2, "atraso": 0.4}))
amb(38, "ep09_ventilador", -22); fx(42, "três", "ep09_ventilador_liga", -22)
pausa(39, 0.6); pausa(41, 0.6); pausa(43, 0.8); pausa(44, 0.6); pausa(45, 1.2)

# ================================================================ PARTE 3 — as irmãs (Joseon)
capitulo(46, 2, "As duas irmãs", "era Joseon · séc. XVII", I + "S03_B.jpg",
         img("S03_A", (1.0, 1.08), ((0.6, 0.5), (0.62, 0.48)), atmos={"neblina": 0.6}), "Para")
C(47, c3("S03_A", "entrar", (0.62, 0.5), 0.8, 0.0, atmos={"neblina": 0.6},
         kanji=K("장화홍련", 0.2, 0.5, "tinta", "Janghwa e Hongryeon", em="Janghwa")))
pincel(47, "Janghwa")
C(48, img("S04_B", (1.0, 1.08), ((0.6, 0.5), (0.6, 0.45)), atmos={"vela": 0.6}))
C(49, img("S04_A", (1.1, 1.3), ((0.15, 0.85), (0.17, 0.82)), atmos={"vela": 0.8}, dof={"x": 0.16, "y": 0.8, "r": 0.15}))
C(50, img("S04_A", (1.0, 1.1), ((0.67, 0.5), (0.67, 0.4)), atmos={"vela": 0.6}))
C(51, texto("O pai acreditou.", "acreditou.", "impacto", cps=10, tamanho=130))
C(52, c3("S03_B", "lado", (0.55, 0.55), 0.8, 0.0, atmos={"neblina": 0.7}))
C(54, filme("irmas_deque"))
C(55, img("S03_A", (1.1, 1.3), ((0.6, 0.75), (0.55, 0.8)), atmos={"neblina": 0.8}))
C(56, ficha("Conto da era Joseon · autor desconhecido\nbaseado num caso julgado em Cheolsan", "Cheolsan"))
C(57, img("S04_B", (1.05, 1.2), ((0.66, 0.5), (0.66, 0.45)), atmos={"vela": 0.4, "neblina": 0.3}))
C(58, img("S04_A", (1.0, 1.08), ((0.3, 0.6), (0.2, 0.75)), atmos={"vela": 0.7}))
C(60, filme("irmas_casa"))
C(61, img("S03_B", (1.0, 1.1), ((0.55, 0.5), (0.58, 0.45)), atmos={"neblina": 0.6}, kanji=HAN(0.26, atraso=1.5)))
amb(46, "nenhum"); amb(47, "ep09_lago", -24); amb(54, "nenhum"); amb(55, "ep09_lago", -24); amb(60, "nenhum")
musica(46, "04_joseon_irmas", -30)
pausa(51, 0.8); pausa(53, 0.6); pausa(54, 0.6); pausa(55, 0.8); pausa(56, 0.4); pausa(57, 0.8); pausa(59, 0.6)
pausa(61, 0.6); pausa(62, 0.4)

# ================================================================ A BIA — 2: a parede
C(63, c3(CL + "base_V03.jpg", "entrar", (0.3, 0.5), 0.9, 0.3))         # a parede, de perto
C(64, vid("V03_batidas_parede", (1.0, 1.04)))
C(65, img("B07_B", (1.0, 1.06), ((0.5, 0.5), (0.5, 0.5))))
C(66, vid("V03b_batidas_parede", (1.0, 1.06)))
C(67, c3("B12_B", "entrar", (0.48, 0.4), 0.9, 0.3))
C(68, img("B12_A", (1.0, 1.1), ((0.5, 0.45), (0.5, 0.4)), dof={"x": 0.5, "y": 0.4, "r": 0.2}))
C(69, img("B11_A", (1.0, 1.12), ((0.5, 0.4), (0.51, 0.12)), dof={"x": 0.51, "y": 0.1, "r": 0.18, "atraso": 0.5}))
C(70, c3("B12_A", "sair", (0.5, 0.42), 0.8, 0.0))
amb(63, "ep09_ventilador", -26)
fx(63, "choro", "ep09_choro_parede", -26)
fx(64, "bateu", "ep09_batidas", -18, atraso=0.1)
batidas[67].setdefault("sons", []).append({"em": None, "som": "ep09_batidas", "volume_db": -14, "depois": False, "atraso": -3.0})
amb(67, "ep09_corredor", -24)
musica(63, "05_a_parede", -31)
pausa(65, 0.8); pausa(68, 0.8); pausa(69, 0.6); pausa(70, 1.4)

# ================================================================ PARTE 4 — quem morre sozinho
capitulo(71, 3, "Quem morre sozinho", "고독사 · godoksa", I + "B13_B.jpg",
         img("B13_A", (1.0, 1.1), ((0.5, 0.5), (0.6, 0.72)), kanji=K("고독사", 0.2, 0.45, "sangue", "godoksa · morte solitária", em="godoksa")), "Existe")
pincel(71, "godoksa")
C(73, c3("B13_B", "entrar", (0.55, 0.75), 0.9, 0.4))
C(74, ficha("2024 · 3.924 mortes solitárias\nMinistério da Saúde e Bem-Estar da Coreia", "3.924"))
C(75, img("S01_A", (1.0, 1.1), ((0.5, 0.5), (0.4, 0.6))))
C(76, img("B13_A", (1.1, 1.3), ((0.3, 0.6), (0.65, 0.8)), dof={"x": 0.7, "y": 0.8, "r": 0.2}))
C(77, c3("B01_B", "entrar", (0.49, 0.42), 0.8, 0.2))
C(78, img("B07_A", (1.0, 1.1), ((0.5, 0.5), (0.3, 0.45))))
C(79, c3("S02_A", "entrar", (0.62, 0.5), 0.9, 0.35))
C(80, img("B11_B", (1.0, 1.1), ((0.5, 0.5), (0.5, 0.3))))
C(81, img("S02_B", (1.0, 1.1), ((0.6, 0.6), (0.6, 0.5))))
C(82, c3(CL + "base_V02.jpg", "entrar", (0.82, 0.4), 1.1, 0.5))       # o ventilador no escuro
amb(71, "nenhum"); amb(73, "ep09_corredor", -26); amb(82, "ep09_ventilador", -22)
pausa(72, 0.6); pausa(74, 0.6); pausa(76, 0.6); pausa(78, 1.0); pausa(81, 0.6)

# ================================================================ A BIA — 3: o nome em vermelho
C(83, img("B05_B", (1.0, 1.06), ((0.4, 0.5), (0.5, 0.5))))
C(84, img("B05_A", (1.2, 1.4), ((0.67, 0.45), (0.67, 0.45)), kanji=K("빨간색", 0.22, 0.5, "sangue", "vermelho", em="Vermelha")))
pincel(84, "Vermelha")
C(85, vid("V04_plaquinha", (1.0, 1.04)))
chat(86, {"de": "Bia", "tipo": "foto", "imagem": I + "B05_A.jpg", "hora": "10:12", "apos": 0.1},
     {"de": "Bia", "texto": "alguém riscou meu nome 😶", "hora": "10:12", "apos": 0.9})
chat(87, {"de": "Bia", "tipo": "audio", "duracao": "0:05", "hora": "10:20", "apos": 0.1})
C(88, img("B05_A", (1.0, 1.1), ((0.6, 0.45), (0.67, 0.45)), dof={"x": 0.68, "y": 0.45, "r": 0.2}))
C(89, img("B05_B", (1.3, 1.45), ((0.67, 0.45), (0.67, 0.45))))
C(90, img("F01_A", (1.0, 1.08), ((0.6, 0.6), (0.65, 0.62))))
chat(91, {"de": "eu", "tipo": "audio", "duracao": "0:04", "hora": "15:22", "apos": 0.1})
C(92, img("B14_B", (1.0, 1.08), ((0.5, 0.5), (0.6, 0.6)), atmos={"chuva": 0.3}))
amb(83, "ep09_corredor", -26); amb(90, "ep09_sala_bh", -26); amb(92, "ep09_seul_chuva", -26)
musica(83, "06_moca_de_branco", -31)
pausa(85, 0.6); pausa(88, 0.4); pausa(89, 0.8); pausa(92, 1.0)

# ================================================================ PARTE 5 — a moça de branco
capitulo(93, 4, "A moça de branco", "처녀귀신 · cheonyeo gwishin", I + "S04_B.jpg",
         c3("S04_A", "entrar", (0.66, 0.5), 0.9, 0.4, atmos={"vela": 0.6}), "Se")
C(94, img("B10_A", (1.2, 1.6), ((0.48, 0.38), (0.48, 0.36)), dof={"x": 0.48, "y": 0.36, "r": 0.12, "atraso": 0.8},
          kanji=K("처녀귀신", 0.8, 0.5, "sangue", "cheonyeo gwishin · a virgem fantasma", glitch=True, em="Cheonyeo")))
pincel(94, "Cheonyeo")
C(95, img("S04_B", (1.0, 1.12), ((0.66, 0.5), (0.66, 0.42)), atmos={"vela": 0.5}))
C(96, img("S05_B", (1.0, 1.08), ((0.5, 0.5), (0.45, 0.55)), atmos={"vela": 0.7}))
C(97, vid("V05_figura_corredor", (1.0, 1.03)))
C(98, c3("S06_A", "entrar", (0.4, 0.4), 0.9, 0.0, kanji=K("아랑", 0.8, 0.45, "tinta", "Arang · Miryang", em="Arang")))
pincel(98, "Arang")
C(99, ficha("Arang · Miryang\nprimeira versão escrita em 1810\nritual Arangje até hoje", "Arangje"))
C(100, texto("Casando elas.", "Casando", "impacto", cps=10, tamanho=130))
C(101, c3("S05_A", "entrar", (0.55, 0.45), 1.0, 0.5, atmos={"vela": 0.8},
          kanji=K("영혼결혼식", 0.14, 0.5, "tinta", "casamento de almas", em="casamento")))
pincel(101, "casamento")
C(102, img("S05_B", (1.15, 1.35), ((0.5, 0.45), (0.5, 0.42)), atmos={"vela": 0.8}))
C(103, img("B11_A", (1.0, 1.1), ((0.5, 0.5), (0.43, 0.8)), kanji=HAN(0.34, x=0.8, atraso=1.0)))
C(104, c3("B01_B", "entrar", (0.49, 0.4), 1.0, 0.3))
C(105, c3("B10_B", "entrar", (0.47, 0.38), 1.4, 0.7))
amb(93, "nenhum"); amb(97, "ep09_corredor", -26); amb(98, "nenhum"); amb(103, "ep09_corredor", -26)
pausa(94, 0.6); pausa(97, 0.8); pausa(99, 0.6); pausa(100, 0.8); pausa(102, 1.0); pausa(103, 0.6); pausa(105, 1.4)

# ================================================================ A BIA — 4: o chamado (o clímax; tudo devagar)
C(106, {"tipo": "relogios", "lados": [{"nome": "Seul", "hora": "03:00", "imagem": I + "B06_B.jpg", "brilho": 0.6},
                                       {"nome": "Belo Horizonte", "hora": "15:00", "imagem": I + "F01_B.jpg", "brilho": 0.8}]})
chat(107, {"de": "Bia", "tipo": "audio", "duracao": "0:05", "hora": "15:00", "apos": 0.1})
C(108, img("F01_B", (1.0, 1.1), ((0.5, 0.55), (0.65, 0.65)), dof={"x": 0.66, "y": 0.62, "r": 0.22}))
chat(109, {"de": "Bia", "tipo": "audio", "duracao": "0:11", "hora": "15:02", "apos": 0.2})
C(110, vid("V01_corredor", (1.0, 1.05)))
C(111, vid("V05b_figura_corredor", (1.0, 1.03)))
C(112, img("B04_A_regras", (1.3, 1.36), ((0.53, 0.31), (0.53, 0.33)), dof={"x": 0.53, "y": 0.32, "r": 0.2}))
chat(113, {"de": "eu", "texto": "NÃO SOU EU. NÃO ABRE.", "hora": "15:03", "check": "✓", "em": "maiúsculas", "digitando": 1.0})
C(114, img("F02_B", (1.0, 1.12), ((0.5, 0.45), (0.55, 0.35)), dof={"x": 0.55, "y": 0.35, "r": 0.22}))
amb(106, "ep09_ventilador", -24); amb(108, "ep09_sala_bh", -28); amb(110, "ep09_corredor", -22)
amb(112, "ep09_corredor", -26); amb(113, "ep09_sala_bh", -30)
batidas[111]["ambiente"] = {"som": "ep09_ventilador", "volume_db": -20}
musica(106, "07_o_chamado", -29)
pausa(108, 0.6); pausa(110, 0.8); pausa(112, 1.2); pausa(114, 0.8)

# ================================================================ PARTE 6 — a mudang
capitulo(115, 5, "A mudang", "무당 · o ritual gut", I + "S05_B.jpg",
         img("S05_B", (1.0, 1.08), ((0.5, 0.5), (0.5, 0.45)), atmos={"vela": 0.6},
             kanji=K("무당", 0.82, 0.45, "sangue", "mudang · a xamã", em="mudang")), "Quando")
pincel(115, "mudang")
C(116, img("S01_A", (1.0, 1.12), ((0.5, 0.5), (0.85, 0.35)), dof={"x": 0.85, "y": 0.35, "r": 0.2, "atraso": 0.8}))
C(117, filme("exhuma_tambor", kanji=K("굿", 0.12, 0.45, "sangue", "gut · o ritual", em="gut")))
pincel(117, "gut")
C(118, img("S05_A", (1.05, 1.2), ((0.5, 0.5), (0.4, 0.4)), atmos={"vela": 0.8}))
C(119, filme("exhuma_danca"))
C(120, filme("exhuma_cova"))
C(121, filme("exhuma_caixao"), (filme("exhuma_montanha"), "estacas"))
C(122, ficha("Exhuma (2024) · dir. Jang Jae-hyun · Showbox\n11,9 milhões de ingressos", "11,9 milhões"))
C(123, img("S06_B", (1.0, 1.1), ((0.5, 0.5), (0.4, 0.45))))
C(124, img("S05_B", (1.0, 1.06), ((0.5, 0.5), (0.5, 0.5)), atmos={"vela": 0.5}, kanji=HAN(0.42, atraso=0.6)))
amb(115, "nenhum")
musica(115, "08_gut_mudang", -29)
pausa(117, 0.6); pausa(119, 0.6); pausa(120, 0.6); pausa(122, 0.8); pausa(124, 1.6)

# ================================================================ A BIA — 5: o quarto
C(125, c3("B12_A", "entrar", (0.5, 0.42), 0.9, 0.3))
fx(125, "chave", "ep09_chave", -20)
C(126, c3("B02_B", "entrar", (0.3, 0.55), 0.8, 0.0))
C(127, c3("B06_B", "entrar", (0.29, 0.62), 1.0, 0.5), (img("B06_A", (1.1, 1.2), ((0.8, 0.4), (0.82, 0.4))), "ventilador"))
C(128, img("B07_A", (1.0, 1.15), ((0.4, 0.45), (0.3, 0.45)), dof={"x": 0.27, "y": 0.45, "r": 0.2}))
fx(128, "papel", "ep09_papel", -22)
C(129, c3("B07_B", "entrar", (0.2, 0.5), 1.0, 0.4))
C(130, c3("B08_A", "entrar", (0.5, 0.5), 0.8, 0.45))
C(131, img("B08_B", (1.1, 1.25), ((0.5, 0.5), (0.4, 0.4)), kanji=K("합격", 0.78, 0.5, "sangue", "hapgyeok · aprovada", tam=0.3, em="Hapgyeok")))
pincel(131, "Hapgyeok")
C(132, img("B02_A", (1.0, 1.08), ((0.5, 0.5), (0.4, 0.55))))
C(133, img("B08_A", (1.2, 1.4), ((0.35, 0.4), (0.4, 0.45)), dof={"x": 0.4, "y": 0.45, "r": 0.2}))
C(134, img("B09_B", (1.0, 1.06), ((0.5, 0.5), (0.45, 0.45))))
C(135, c3("B09_A", "entrar", (0.53, 0.5), 0.9, 0.4))
C(136, texto("\"Ela não queria\nir sozinha.\"", "ir sozinha.\"", cps=14, tamanho=120))
amb(125, "ep09_corredor", -26); amb(126, "ep09_ventilador", -22)
musica(125, "09_o_quarto", -30)
pausa(126, 0.6); pausa(128, 0.6); pausa(129, 0.6); pausa(131, 1.0); pausa(133, 0.8); pausa(135, 0.4); pausa(136, 0.6)

# ================================================================ A BIA — 6: até hoje
C(137, img("B13_B", (1.0, 1.08), ((0.5, 0.5), (0.55, 0.7))))
C(138, c3("B01_B", "entrar", (0.49, 0.4), 1.0, 0.3))
C(139, img("B11_B", (1.0, 1.08), ((0.4, 0.5), (0.4, 0.4))))
C(140, img("S05_B", (1.0, 1.1), ((0.5, 0.5), (0.5, 0.45)), atmos={"vela": 0.6}))
C(141, vid("V04b_plaquinha", (1.0, 1.04)))
C(142, img("B11_A", (1.3, 1.6), ((0.51, 0.12), (0.51, 0.1)),
           kanji=K("비아", 0.22, 0.5, "sangue", "Bia", tam=0.3, atraso=0.1, escrever=1.2)))
batidas[142]["cena"].update({"entrada": "fundir", "duracao_entrada": 1.8})     # entra no silêncio antes do "Bia"
pincel(142, None, -14, atraso=-1.6)
C(143, img("F02_A", (1.0, 1.1), ((0.6, 0.4), (0.62, 0.35)), dof={"x": 0.62, "y": 0.35, "r": 0.22}))
fx(143, "vibra", "ep08_vibra", -24)
chat(144, {"de": "Bia", "tipo": "audio", "duracao": "0:05", "hora": "15:00", "apos": 0.2})
C(145, img("F01_A", (1.0, 1.06), ((0.6, 0.6), (0.62, 0.62))))
amb(137, "nenhum"); amb(138, "ep09_corredor", -26); amb(143, "ep09_sala_bh", -28)
pausa(140, 0.6); pausa(141, 0.6); pausa(142, 1.6); pausa(144, 0.6)
batidas[145]["ambiente"] = {"som": "ep09_ventilador", "volume_db": -20}

# ================================================================ FECHO — Vigia (corte seco do silêncio)
C(146, vigia((1.0, 1.04)))
T(146, "corte")
C(147, vigia((1.0, 1.05)))
C(148, img("B13_A", (1.0, 1.1), ((0.5, 0.5), (0.65, 0.75))))
C(149, img("S04_B", (1.0, 1.08), ((0.66, 0.5), (0.66, 0.45)), atmos={"vela": 0.5}, kanji=HAN(0.5, atraso=0.8)))
C(150, vigia((1.04, 1.1), ((0.42, 0.45), (0.4, 0.43))))
C(151, vigia((1.05, 1.12), ((0.4, 0.45), (0.36, 0.42))))
C(152, vigia((1.0, 1.05)))
C(153, c3("B06_B", "entrar", (0.8, 0.42), 1.0, 0.5))
amb(146, "nenhum"); amb(153, "ep09_ventilador", -24)
musica(146, "10_fecho", -31)
pausa(149, 0.8); pausa(151, 0.8); pausa(152, 0.6); pausa(153, 0.6)

# ================================================================ VINHETA FIXA DE INSCRIÇÃO
batidas.append({"fala": F.VINHETA, "cta_inicio": True, "sem_legenda": True, "ambiente": {"som": "nenhum"},
                "musica": {"som": "vinheta_ultimo_abrigo", "volume_db": -20}})

voz = "audio/voz_personagens.wav" if (AQUI / "audio" / "voz_personagens.wav").exists() else "audio/voz_com_vinheta_limpa.wav"
roteiro = {
    "modo": "cenas", "formato": "16:9", "tema": "vigia", "avatar": "vigia_hd",
    "voz_arquivo": voz,
    "cintilar": 0.03, "apertar_pausas": False,   # REGRA: nunca encurtar as pausas da narração
    "vigia_padrao": False,
    "cauda": 1.6, "chuva": 0, "grao": 0.14,
    # 13/11: trilha mais presente que no Ep. 08 (+4 dB), mas o rascunho 1 abafava a voz: -3 dB nas faixas e -9 sob a voz
    "mix": {"musica_ganho_db": 12, "fundo_sob_voz": -9, "efeitos_sob_voz": -4, "voz_pro": True, "fundo_bolso": True,
            "efeitos_pico_max": -3},
    "legendas": {"destaques": ["Coreia", "han", "regra", "F-zero-quatro", "sozinha", "sozinhos", "vermelho", "ventilador",
                               "mudang", "godoksa"]},
    "ambiente_inicial": [{"som": "ep09_ventilador", "volume_db": -22}],
    "musica": {"som": "ep09_m01_tres_da_tarde", "volume_db": -28},
    "abertura": {"texto": "O VIGIA\nEP. 09 · O QUARTO DO ANDAR F", "vermelho": "ANDAR F", "duracao": 6.0, "segurar": 4.0,
                 "antes_da_batida": 10, "sons": [{"som": "ep09_jing", "t": 0.2, "volume_db": -16}]},
    "cta": {"titulo": "Liga pra alguém hoje.", "canal": "Último Abrigo",
            "subtitulo": "Inscreva-se para mais casos do Vigia",
            "fundo": "../../painel/cenarios/abrigo_16x9.png", "pose": "c_cafe_convite",
            "antes": 0.6, "clique_em": "Inscreva-se", "duracao": 2.5},
    "batidas": batidas,
}

_ali = json.load(open(AQUI / "audio" / "alinhamento.json"))
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
sons = {s["som"] for b in batidas for s in b.get("sons", [])} | {b[k]["som"] for b in batidas for k in ("ambiente", "musica") if b.get(k)}
sem_som = sorted(s for s in sons if s != "nenhum" and not list(sons_dir.glob(s + ".*")))
if sem_som:
    raise SystemExit("sons faltando: " + ", ".join(sem_som))


def garantir_leitura():
    """Tela de texto: depois de digitada fica >= 1,5 s + 0,3 s por palavra. O que faltar entra como pausa na fala seguinte."""
    sys.path.insert(0, str(AQUI.parents[1] / "painel"))
    from gerar import tokens
    tempos = json.load(open(AQUI / "audio" / "alinhamento.json"))
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
        if falta > -0.45:
            prox["pausa_antes_s"] = round(prox.get("pausa_antes_s", 0) + falta + 0.6, 2); mudou.append((i, round(falta, 1)))
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
                n = max(n, off + (6.5 if K.get("legenda") or len(K.get("texto", "")) > 1 else 3.5))
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

    PROTEGE = {3, 9, 31, 62, 105, 136, 142, 145, 153}
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
            extra = round(min(2.5, falta - acc), 2); b["pausa_antes_s"] = round(b.get("pausa_antes_s", 0) + extra, 2); alongadas.append((i, extra))
        acc, falta = dur(i), precisa(b, i)
    # fusões que terminam antes da voz
    for i, b in enumerate(batidas[1:len(falas)], 1):
        cs = cenas_de(b)
        if not cs:
            continue
        c = cs[0]
        if c.get("tipo") == "capitulo" or c.get("entrada") == "corte":
            continue
        ant = next((cenas_de(batidas[j]) for j in range(i - 1, -1, -1) if cenas_de(batidas[j])), [{}])[-1]
        if c.get("tipo") == "chat" and ant.get("tipo") == "chat":
            c["entrada"] = "corte"; continue          # conversa → conversa: a tela é a mesma
        padrao = {"nanquim": 1.3, "shoji": 0.9, "vela": 1.6}.get(c.get("entrada"), 0.6)
        c.setdefault("entrada", "fundir"); c.setdefault("duracao_entrada", padrao)
        c["antecipar"] = round(min(c["duracao_entrada"], b.get("pausa_antes_s", 0) + 0.25), 2)
    print("frases que continuam a imagem anterior:", continuadas)
    print("pausas alongadas para o kanji/cena respirar (fala, s):", alongadas)


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
        fim = inicios[k + 1][0] if k + 1 < len(inicios) else t + 6
        dur = round(max(4.0, fim - t) + 2.5, 1)
        chave = hashlib.md5(json.dumps([c["imagem"], p, dur], sort_keys=True).encode()).hexdigest()[:12]
        arq = C3D / f"{Path(c['imagem']).stem}_{chave}.mp4"
        if not arq.exists():
            camera3d.gerar(AQUI / c["imagem"], arq, dur, p["mov"], tuple(p["foco"]), p["forca"], p["desfoque"]); feitos += 1
        c["video"] = str(arq.relative_to(AQUI)); c.pop("imagem", None)
        c.pop("dof", None)                             # o foco de lente já está no próprio vídeo
    print("câmera 3D:", sum(1 for _, c in inicios if str(c.get("video", "")).startswith("camera3d")), "cenas,", feitos, "geradas agora")


camera_3d()
sem = [i for i, b in enumerate(batidas) if not cenas_de(b)]
(AQUI / "roteiro.json").write_text(json.dumps(roteiro, ensure_ascii=False, indent=1), encoding="utf-8")
n_cenas = sum(len(cenas_de(b)) for b in batidas)
print(f"{len(batidas)} falas, {n_cenas} cenas, falas sem cena (continuam a anterior): {sem}")
print("pausa total:", round(sum(b.get("pausa_antes_s", 0) for b in batidas), 1), "s")
