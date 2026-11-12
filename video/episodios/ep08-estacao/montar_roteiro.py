"""Monta roteiro.json do Ep. 08 "A estação que não existe" (falas.py: cada frase do ROTEIRO.md = 1 batida).
Regras da casa: Vigia só no tema/aparte/fecho; música o episódio inteiro (trilha estilo japonês, aprovada 12/11);
saída lenta das cenas tensas; ninguém de frente (clipes da cabine cortados antes do rosto); som de kanji = ep08_kanji
(NUNCA o pincel "chocalho"); sons-chave altos e sozinhos (pausa depois); vozes da Dani (Aoede) e da mãe (Gacrux) só
com som de lugar. Uso: python3 montar_roteiro.py
"""
import json
import sys
from pathlib import Path

import falas as F

AQUI = Path(__file__).parent
falas, PERS, SEC, PAUSAS, _ = F.ler()
assert len(falas) == 202 and falas[146] == "Uma perna." and PERS == {2: "dani1", 121: "dani1", 141: "dani2", 177: "mae"}, \
    "o ROTEIRO.md mudou: rever os índices"
batidas = [{"fala": f} for f in falas]
for i, s in PAUSAS.items():
    batidas[i]["pausa_antes_s"] = s

I, R, CL = "imagens/", "imagens_reais/", "clipes/"
VIGIA = {"imagem": "../../painel/cenarios/abrigo_16x9.png", "vigia": True}
LINHA = [1666, 1677, 1741, 1750, 1825, 1979, 1991, 1998, 2004]


# ------------------------------------------------------------------ ajudantes
def vigia(z=(1.0, 1.04), foco=((0.55, 0.5), (0.57, 0.48))):
    return dict(VIGIA, zoom=list(z), foco=[list(foco[0]), list(foco[1])])


def img(nome, z=(1.0, 1.08), foco=None, pasta=I, **kw):
    c = {"imagem": pasta + nome + ".jpg", "zoom": list(z), **kw}
    if foco:
        c["foco"] = [list(foco[0]), list(foco[1])]
    return c


def real(nome, z=(1.0, 1.06), foco=None, **kw):
    return img(nome, z, foco, pasta=R, **kw)


def grav(nome, z=(1.0, 1.08), foco=None, **kw):
    """Gravura/pintura em pé: inteira no quadro (fundo desfocado dela mesma), poeira de papel velho."""
    return real(nome, z, foco, encaixe="conter", atmos=kw.pop("atmos", {"poeira": 0.5}), **kw)


def vid(nome, z=(1.0, 1.04), **kw):
    return {"video": CL + nome + ".mp4", "zoom": list(z), **kw}


def cel(c, hora, sinal=None, vertical=False):
    """Vídeo/foto de celular: interface de gravação, foco caçando e mão."""
    c = dict(c); c["celular"] = {"hora": hora, **({"sinal": sinal} if sinal else {}), **({"vertical": True} if vertical else {})}
    c.setdefault("mao", 0.6)
    return c


def texto(t, vermelho=None, estilo="maquina", **kw):
    return {"tipo": "texto", "texto": t, "estilo": estilo, **({"vermelho": vermelho} if vermelho else {}), **kw}


def K(texto_k, x=0.82, y=0.5, modo="luz", legenda=None, **kw):
    return {"texto": texto_k, "x": x, "y": y, "modo": modo, **({"legenda": legenda} if legenda else {}), **kw}


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


def T(i, entrada, dur=None):
    c = batidas[i].get("cena") or batidas[i]["cenas"][0]
    c["entrada"] = entrada
    if dur:
        c["duracao_entrada"] = dur


def saida_lenta(i_seguinte, segurar, transicao="fundir", dur=1.6):
    b = batidas[i_seguinte]
    b["pausa_antes_s"] = segurar + dur
    (b.get("cena") or b["cenas"][0]).update({"entrada": transicao, "duracao_entrada": dur, "antecipar": dur})


def pausa(i, s):
    batidas[i]["pausa_antes_s"] = round(batidas[i].get("pausa_antes_s", 0) + s, 2)


def amb(i, som, db=-20, em=None):
    batidas[i]["ambiente"] = {"som": som, "volume_db": db, **({"em": em} if em else {})}


def fx(i, em, som, db, depois=False, atraso=0.0):
    batidas[i].setdefault("sons", []).append({"em": em, "som": som, "volume_db": db, "depois": depois, "atraso": atraso})


def capitulo(i, n, titulo, ano, imagem, cena, em, atual=None):
    """Cartão de capítulo na pausa antes da fala (com taiko longe), depois a primeira cena entra na palavra `em`."""
    nums = "一二三四五六七"
    cap = {"tipo": "capitulo", "numero": f"第{nums[n - 1]}章" if n else "最終章", "numero_pt": f"Capítulo {n}" if n else "A história",
           "titulo": titulo, "ano": ano, "imagem": imagem, "antecipar": 3.2, "entrada": "nanquim", "atmos": {"poeira": 0.6}}
    if atual:
        cap["linha"] = {"anos": LINHA, "de": LINHA[0], "atual": atual, "dur": 3.0}
    C(i, cap, (cena, em))
    pausa(i, 3.6)
    fx(i, None, "ep08_tinta", -12, atraso=-3.2)
    fx(i, None, "ep08_taiko", -12, atraso=-2.0)


HIST = []                         # conversa do grupo "Família 🏠" (cada tela mostra o histórico + o que chega)


def chat(i, *novas, sons=True):
    msgs = [dict(m, apos=-30) for m in HIST[-6:]]
    for m in novas:
        m = dict(m); m.setdefault("apos", 0.3)
        msgs.append(m); HIST.append({k: v for k, v in m.items() if k not in ("apos", "em", "digitando")})
        if sons and "em" not in m:
            fx(i, None, "ep08_vibra" if m["de"] == "Dani" else "ep08_msg", -12 if m["de"] == "Dani" else -14, atraso=m["apos"])
        elif sons:
            fx(i, m["em"], "ep08_vibra" if m["de"] == "Dani" else "ep08_msg", -12)
    C(i, {"tipo": "chat", "grupo": "Família 🏠", "membros": "Dani, Lucas, Mãe, Pai", "mensagens": msgs})
    batidas[i]["sem_legenda"] = True


def kanji_som(i, em, db=-13, atraso=0.0):
    fx(i, em, "ep08_kanji", db, atraso=atraso)


V = dict(com_vigia=True)

# ================================================================ GANCHO — sem Vigia
C(0, {"tipo": "relogios", "lados": [{"nome": "Hamamatsu", "hora": "23:40", "imagem": I + "H01_fabrica_noite.jpg", "brilho": 0.5},
                                     {"nome": "Londrina", "hora": "11:40"}]})
chat(1, {"de": "Dani", "tipo": "foto", "imagem": I + "D01_vagao_vazio.jpg", "hora": "23:20", "apos": 0.1},
     {"de": "Dani", "texto": "Só eu hoje 😅", "hora": "23:20", "apos": 0.6},
     {"de": "Lucas", "texto": "kkkk dormiu de novo?", "hora": "11:21", "apos": 1.2},
     {"de": "Dani", "tipo": "audio", "duracao": "0:09", "hora": "23:40", "em": "áudio", "digitando": 0.8})
C(2, cel(vid("V02_janela_trem"), "23:40"))
C(3, cel(img("D03_placa_kisaragi", (1.0, 1.25), ((0.5, 0.5), (0.86, 0.33))), "23:47"))
pausa(3, 2.0)                                                                       # a voz da Dani cresce 1,4 s (ajuste)
chat(4, {"de": "Pai", "texto": "Filha??", "hora": "11:48", "apos": 0.4},
     {"de": "Mãe", "texto": "Dani responde a mãe", "hora": "11:48", "apos": 1.2},
     {"de": "Lucas", "texto": "que lugar é esse", "hora": "11:49", "apos": 2.0})
C(5, vid("V04_sem_relogio", (1.0, 1.06)))
C(6, img("J08_tv_chiado", (1.0, 1.1), ((0.5, 0.5), (0.62, 0.45)),
         kanji=K("呪い", 0.2, 0.5, "sangue", "maldição", atraso=0.8, glitch=True, selo="呪")))
kanji_som(6, "participar", atraso=-0.6)
amb(0, "ep08_trem_dentro", -16); amb(5, "ep08_campo_noite", -20); amb(6, "ep08_tv_chiado", -24)
pausa(6, 0.6)

# ================================================================ TEMA — Vigia
C(7, vigia((1.0, 1.04)))
saida_lenta(7, 1.2)
C(8, vigia((1.0, 1.05)), (img("J07_palco_kabuki", (1.0, 1.08)), "país"), **V)
C(9, vigia((1.04, 1.1), ((0.4, 0.45), (0.38, 0.43))))
C(10, real("R17_hannya_hokusai", (1.0, 1.1), ((0.6, 0.45), (0.6, 0.42)), encaixe="conter",
           kanji=K("日本", 0.2, 0.5, "luz", "Japão", atraso=0.1, selo="怖")))
kanji_som(10, "Japão", atraso=-0.2)
C(11, img("J08_tv_chiado", (1.0, 1.06)), (img("J06_fantasma_corredor", (1.0, 1.08)), "casa"), (img("D01_vagao_vazio", (1.0, 1.06)), "trem"))
C(12, vigia((1.0, 1.05)))
C(13, img("J02_vela_sombra", (1.0, 1.12), ((0.5, 0.6), (0.75, 0.45)), atmos={"vela": 0.7},
          kanji=K("掟", 0.22, 0.5, "sangue", "a regra", tam=0.3, atraso=0.4)))
kanji_som(13, "regra")
C(14, grav("R18_oyuki_okyo", (1.0, 1.06), linha={"anos": LINHA, "de": 1666, "atual": 2004, "dur": 5.0}),
  (img("N09_estacao_noite", (1.0, 1.08), atmos={"neblina": 0.5}), "fórum"), **V)
C(15, vigia((1.0, 1.05)), (img("H02_dani_plataforma", (1.0, 1.08)), "brasileira"), **V)
amb(7, "nenhum")
pausa(10, 0.6); pausa(13, 0.6); pausa(14, 0.6)

# ================================================================ PARTE 1 — cem velas (1677)
capitulo(16, 1, "Cem velas", "1677", R + "R08_cem_contos_reuniao.jpg",
         img("L07_cem_velas", (1.0, 1.08), atmos={"vela": 0.8}, kanji=K("百", 0.86, 0.45, "luz", "cem", tam=0.26, atraso=1.4)), "sala", 1677)
kanji_som(16, "Cem")
C(17, img("L07b_cem_velas", (1.0, 1.1), ((0.5, 0.6), (0.5, 0.55)), atmos={"vela": 0.8}))
C(18, vid("V06_cem_velas_apagando", (1.0, 1.05)))
fx(18, "apagada", "ep08_vela", -10, depois=True)
C(19, img("J01_cem_velas_vazio", (1.0, 1.12), ((0.5, 0.6), (0.45, 0.65)), atmos={"vela": 0.6, "fumaca": 0.4}))
C(20, real("R08_cem_contos_reuniao", (1.0, 1.1), ((0.5, 0.55), (0.6, 0.6)), atmos={"poeira": 0.5},
           kanji=K("百物語", 0.12, 0.5, "tinta", "Hyakumonogatari Kaidankai", selo="百", atraso=0.6)))
kanji_som(20, "Hyakumonogatari")
C(21, img("J02_vela_sombra", (1.0, 1.06), ((0.4, 0.75), (0.4, 0.72)), atmos={"vela": 0.8}, dof={"x": 0.27, "y": 0.8, "r": 0.18, "atraso": 0.4}))
C(22, img("J02_vela_sombra", (1.15, 1.45), ((0.45, 0.6), (0.78, 0.42)), atmos={"vela": 1.0}))
fx(22, "apagasse", "ep08_vela", -10, depois=True)
C(23, real("R08_cem_contos_reuniao", (1.05, 1.12), ((0.6, 0.6), (0.62, 0.58)), linha={"anos": LINHA, "de": 1666, "atual": 1677, "dur": 3.0}))
C(24, img("J06b_fantasma_corredor", (1.0, 1.15), ((0.5, 0.5), (0.47, 0.45)), atmos={"neblina": 0.5}))
amb(16, "nenhum")
pausa(18, 1.0); pausa(22, 1.2); pausa(24, 0.4)

# ================================================================ PARTE 2 — o fantasma sem pés (1750)
capitulo(25, 2, "O fantasma que não tem pés", "1750", R + "R18_oyuki_okyo.jpg",
         grav("R18_oyuki_okyo", (1.0, 1.06), kanji=K("幽霊図", 0.8, 0.5, "tinta", "Maruyama Ōkyo · c. 1750", selo="応挙", atraso=1.2)),
         "pintor", 1750)
kanji_som(25, "Ōkyo")
C(26, img("L01_oyuki_pergaminho", (1.0, 1.1), ((0.5, 0.45), (0.5, 0.4)), atmos={"vela": 0.5}))
C(27, grav("R18_oyuki_okyo", (1.15, 1.6), ((0.5, 0.5), (0.5, 0.2))))
C(28, grav("R18_oyuki_okyo", (1.6, 1.8), ((0.5, 0.55), (0.5, 0.85)), atmos={"neblina": 0.5, "poeira": 0.4}))
C(29, img("J06_fantasma_corredor", (1.0, 1.12), ((0.4, 0.45), (0.33, 0.35)), atmos={"neblina": 0.4},
          kanji=K("幽霊", 0.8, 0.5, "luz", "yūrei · fantasma", em="yūrei")))
kanji_som(29, "yūrei")
C(30, img("J06_fantasma_corredor", (1.4, 1.6), ((0.33, 0.35), (0.32, 0.4))))
C(31, img("L01b_oyuki_pergaminho", (1.0, 1.12), ((0.5, 0.45), (0.5, 0.3))))
C(32, img("J06b_fantasma_corredor", (1.2, 1.5), ((0.5, 0.5), (0.48, 0.55)), atmos={"neblina": 0.5}))
C(33, grav("R06_oiwa_fantasma_kuniyoshi", (1.1, 1.4), ((0.4, 0.3), (0.4, 0.45))))
C(34, real("R17_hannya_hokusai", (1.0, 1.12), ((0.6, 0.45), (0.6, 0.42)), encaixe="conter", atmos={"poeira": 0.5},
           kanji=K("怨霊", 0.2, 0.5, "sangue", "onryō · espírito vingativo", selo="怨", glitch=True, em="onryō")))
kanji_som(34, "onryō")
C(35, grav("R06_oiwa_fantasma_kuniyoshi", (1.0, 1.1), ((0.4, 0.4), (0.38, 0.3))))
C(36, img("J05_lanterna", (1.0, 1.1), atmos={"vela": 0.6}, kanji=K("三", 0.2, 0.5, "sangue", "três", tam=0.32, em="três")))
kanji_som(36, "três")
pausa(28, 0.8); pausa(34, 0.4); pausa(36, 0.4)

# ================================================================ PARTE 3 — as três mulheres
capitulo(37, 3, "As três mulheres", "1666 · 1741 · 1825", R + "R06_oiwa_fantasma_kuniyoshi.jpg",
         grav("R06_oiwa_fantasma_kuniyoshi", (1.0, 1.08), kanji=K("お岩", 0.8, 0.5, "luz", "Oiwa", selo="怨", atraso=0.3)), "Oiwa", 1825)
kanji_som(37, "Oiwa")
C(38, img("J07_palco_kabuki", (1.0, 1.1), atmos={"fumaca": 0.4}, kanji=K("四谷怪談", 0.84, 0.5, "luz", "Yotsuya Kaidan · 1825", selo="怨", em="kabuki")))
kanji_som(38, "kabuki")
C(39, img("J07_palco_kabuki", (1.15, 1.3), ((0.5, 0.6), (0.6, 0.65))))
C(40, img("J07_palco_kabuki", (1.4, 1.6), ((0.62, 0.68), (0.66, 0.7)), dof={"x": 0.6, "y": 0.68, "r": 0.2}))
C(41, grav("R06_oiwa_fantasma_kuniyoshi", (1.0, 1.06), dof={"x": 0.45, "y": 0.4, "r": 0.25},
           kanji=K("毒", 0.2, 0.5, "sangue", "veneno", tam=0.3, glitch=True, em="veneno")))
kanji_som(41, "veneno")
C(42, grav("R01_oiwa_lanterna_hokusai", (1.2, 1.6), ((0.5, 0.4), (0.55, 0.48))))
C(43, texto("Ela morre.\nE volta.", "E volta.", "impacto", cps=10, tamanho=140))
C(44, img("J05_lanterna", (1.0, 1.1)), (grav("R01_oiwa_lanterna_hokusai", (1.0, 1.08)), "lanterna"))
C(45, grav("R01_oiwa_lanterna_hokusai", (1.0, 1.15), ((0.5, 0.5), (0.55, 0.47)), dof={"x": 0.55, "y": 0.47, "r": 0.25, "atraso": 1.5},
           kanji=K("北斎", 0.84, 0.5, "tinta", "Katsushika Hokusai · 1831", selo="北斎", atraso=0.8)))
kanji_som(45, "Hokusai")
C(46, img("J05b_lanterna", (1.0, 1.1), kanji=K("於岩稲荷", 0.2, 0.5, "placa", "santuário Oiwa Inari · Tóquio", fundo="vermelho", em="santuário")))
kanji_som(46, "santuário")
C(47, img("J07_palco_kabuki", (1.0, 1.15), ((0.5, 0.5), (0.3, 0.55)), atmos={"fumaca": 0.6}))
C(48, grav("R03_okiku_poco_hokusai", (1.0, 1.06), kanji=K("お菊", 0.2, 0.5, "luz", "Okiku", atraso=0.3)))
T(48, "shoji", 0.9); fx(48, None, "ep08_shoji", -11, atraso=-0.6); kanji_som(48, "Okiku")
C(49, img("J03_poco_jardim", (1.0, 1.12), ((0.5, 0.5), (0.5, 0.45)), atmos={"neblina": 0.5}))
C(50, grav("R03_okiku_poco_hokusai", (1.05, 1.12), ((0.5, 0.4), (0.5, 0.3)),
           kanji=K("皿屋敷", 0.18, 0.5, "sangue", "Bancho Sarayashiki · a mansão dos pratos", selo="呪", glitch=True, em="voz")))
kanji_som(50, "voz")
C(51, grav("R03_okiku_poco_hokusai", (1.12, 1.22), ((0.5, 0.25), (0.5, 0.22)), atmos={"neblina": 0.5},
           kanji=[{"texto": "一", "em": "Um", "x": 0.16, "y": 0.5, "tam": 0.3, "modo": "sangue", "escrever": 0.5},
                  {"texto": "二", "em": "Dois", "x": 0.84, "y": 0.42, "tam": 0.3, "modo": "sangue", "escrever": 0.5},
                  {"texto": "三", "em": "Três", "x": 0.5, "y": 0.72, "tam": 0.3, "modo": "sangue", "escrever": 0.6}]))
kanji_som(51, "Um", -14); kanji_som(51, "Dois", -14); kanji_som(51, "Três", -13)
C(52, img("N08_poco_noite", (1.05, 1.15), ((0.5, 0.6), (0.5, 0.65)), atmos={"neblina": 0.7},
          kanji=K("九", 0.8, 0.45, "sangue", "nove", tam=0.34, selo="呪", em="nove")))
kanji_som(52, "nove"); fx(52, "grito", "ep08_taiko", -12, depois=True)
C(53, real("R10_poco_okiku_himeji", (1.0, 1.06), kanji=K("実在", 0.86, 0.42, "placa", "Foto real · castelo de Himeji", tam=0.14, fundo="vermelho", em="real")),
  (real("R11_poco_okiku_himeji_2", (1.0, 1.08)), "grade"))
C(54, img("N08_poco_noite", (1.02, 1.12), ((0.5, 0.6), (0.5, 0.66)), atmos={"neblina": 0.8},
          kanji=K("お菊井戸", 0.82, 0.5, "recorte", "O poço da Okiku", fundo="nanquim", atraso=0.4)))
kanji_som(54, "poço")
C(55, img("L06b_peonia", (1.0, 1.08), atmos={"vela": 0.5},
          kanji=K("牡丹燈籠", 0.84, 0.5, "luz", "Botan Dōrō · a lanterna de peônia", em="lanterna"),
          linha={"anos": LINHA, "de": 1825, "atual": 1666, "dur": 3.0}))
T(55, "vela", 1.6); fx(55, None, "ep08_vela", -10, atraso=-1.0); kanji_som(55, "lanterna")
C(56, img("L06c_peonia", (1.0, 1.1)))
C(57, img("J05_lanterna", (1.0, 1.15), ((0.5, 0.55), (0.5, 0.5)), atmos={"vela": 0.7}))
C(58, img("L06_peonia_esqueleto", (1.0, 1.1)), (grav("R05_esqueleto_detalhe", (1.0, 1.1), ((0.45, 0.3), (0.45, 0.2))), "esqueleto"))
T(58, "shoji", 0.9); fx(58, None, "ep08_shoji", -11, atraso=-0.5)
C(59, real("R04_esqueleto_kuniyoshi", (1.0, 1.08), ((0.4, 0.45), (0.55, 0.35)), atmos={"poeira": 0.6},
           kanji=K("相馬の古内裏", 0.1, 0.5, "tinta", "Utagawa Kuniyoshi · c. 1844", selo="国芳", em="Kuniyoshi")))
kanji_som(59, "Kuniyoshi")
C(60, real("R04_esqueleto_kuniyoshi", (1.5, 1.9), ((0.55, 0.35), (0.6, 0.3)), dof={"x": 0.6, "y": 0.35, "r": 0.22}))
pausa(41, 0.6); pausa(42, 0.8); pausa(43, 0.6); pausa(47, 0.8); pausa(51, 0.6); pausa(52, 0.4); pausa(53, 1.6)
pausa(54, 0.6); pausa(58, 0.6); pausa(60, 1.0)

# ================================================================ PARTE 4 — do poço para a televisão
capitulo(61, 4, "Do poço para a televisão", "1991 · 1998", I + "J08_tv_chiado.jpg",
         img("J08_tv_chiado", (1.0, 1.08), atmos={"pelicula": 0.6}, kanji=K("リング", 0.2, 0.5, "luz", "Ring · Koji Suzuki · 1991", em="livro")),
         "escritor", 1991)
kanji_som(61, "livro")
C(62, img("J08_tv_chiado", (1.1, 1.25), ((0.6, 0.45), (0.8, 0.38)), atmos={"pelicula": 0.6},
          linha={"anos": LINHA, "de": 1991, "atual": 1998, "dur": 2.5}))
C(63, img("J08_tv_chiado", (1.2, 1.4), ((0.6, 0.75), (0.62, 0.82))), (img("J09_telefone", (1.0, 1.1)), "telefonema"),
  (img("J09_telefone", (1.1, 1.25), kanji=K("七日", 0.2, 0.5, "sangue", "sete dias", glitch=True, em="sete")), "sete"))
kanji_som(63, "sete")
C(64, img("J08_tv_chiado", (1.3, 1.9), ((0.7, 0.42), (0.8, 0.38)), atmos={"pelicula": 0.8}))
C(65, img("J04_poco_cabelo", (1.0, 1.2), ((0.5, 0.5), (0.6, 0.65)), atmos={"neblina": 0.4}), (grav("R03_okiku_poco_hokusai", (1.0, 1.06)), "Okiku"))
C(66, img("J06_fantasma_corredor", (1.2, 1.4), ((0.33, 0.4), (0.33, 0.35))), (grav("R01_oiwa_lanterna_hokusai", (1.0, 1.06)), "Oiwa"))
C(67, grav("R18_oyuki_okyo", (1.0, 1.08)), (img("J08_tv_chiado", (1.0, 1.1), atmos={"pelicula": 0.6}), "televisão"))
C(68, texto("O Chamado (2002)\nquase US$ 250 milhões", "US$ 250 milhões", cps=30))
C(69, img("J06b_fantasma_corredor", (1.0, 1.15), atmos={"neblina": 0.4},
          kanji=K("呪怨", 0.18, 0.5, "sangue", "Ju-On · O Grito", selo="怨", glitch=True, em="Ju-On")))
kanji_som(69, "Ju-On")
C(70, img("J02_vela_sombra", (1.0, 1.15), ((0.5, 0.5), (0.78, 0.42)), atmos={"vela": 0.8}))
C(71, texto("É a regra.", "regra.", "impacto", cps=8, tamanho=150))
amb(61, "ep08_tv_chiado", -24); amb(65, "nenhum")
pausa(64, 0.8); pausa(67, 0.6); pausa(70, 0.6); pausa(71, 0.8)

# ================================================================ APARTE — Vigia
C(72, vigia((1.0, 1.05)))
saida_lenta(72, 1.6)
C(73, img("J08_tv_chiado", (1.0, 1.1)), **V)
C(74, img("J06_fantasma_corredor", (1.0, 1.1)), **V)
C(75, vigia((1.04, 1.1), ((0.4, 0.45), (0.38, 0.43))))
C(76, vigia((1.0, 1.06)))
C(77, img("J03_poco_jardim", (1.0, 1.06)), (img("J08_tv_chiado", (1.0, 1.06)), "televisão"), (img("J11b_banheiro", (1.0, 1.06)), "banheiro"),
  (img("D01_vagao_vazio", (1.0, 1.06)), "trem"))
C(78, vigia((1.05, 1.12), ((0.4, 0.45), (0.37, 0.42))))
amb(72, "nenhum")
pausa(76, 0.6); pausa(78, 0.6)

# ================================================================ PARTE 5 — as lendas que saíram da tela
capitulo(79, 5, "As lendas que saíram da tela", "1950 → 1979", I + "L02c_kuchisake_longe.jpg",
         img("J10_kuchisake_costas", (1.0, 1.08), atmos={"pelicula": 1.0}, linha={"anos": LINHA, "de": 1825, "atual": 1979, "dur": 3.0}),
         "história", 1979)
C(80, img("J10b_kuchisake_costas", (1.0, 1.1), ((0.5, 0.5), (0.62, 0.5)), atmos={"pelicula": 1.0}))
C(81, img("L02c_kuchisake_longe", (1.0, 1.15), ((0.5, 0.5), (0.58, 0.5)), atmos={"pelicula": 0.8}))
C(82, img("L02b_kuchisake_poste", (1.0, 1.15), ((0.5, 0.5), (0.5, 0.45)), atmos={"pelicula": 0.8}))
C(83, img("L02_kuchisake", (1.0, 1.12), ((0.5, 0.5), (0.5, 0.42)), atmos={"pelicula": 0.8}))
C(84, img("L02_kuchisake", (1.12, 1.2), ((0.5, 0.42), (0.5, 0.42)), atmos={"pelicula": 0.6},
          kanji=K("口裂け女", 0.16, 0.5, "sangue", "Kuchisake-onna · a mulher da boca cortada", glitch=True, selo="口", atraso=0.3)))
kanji_som(84, "Kuchisake-onna")
C(85, grav("R19_kuchisake_ehon_sayoshigure", (1.0, 1.15), ((0.5, 0.5), (0.42, 0.22)),
           kanji=K("絵本小夜時雨", 0.86, 0.5, "tinta", "Ehon Sayoshigure · 1801", em="livro")))
kanji_som(85, "livro")
C(86, img("J10_kuchisake_costas", (1.1, 1.25), ((0.5, 0.55), (0.5, 0.55)), atmos={"pelicula": 0.8}))
C(87, img("J10b_kuchisake_costas", (1.0, 1.12), ((0.3, 0.7), (0.32, 0.75)), atmos={"pelicula": 0.8}))
C(88, texto("A maldição só vive\nenquanto passa adiante.", "passa adiante.", cps=30))
C(89, img("J11_banheiro_escuro", (1.0, 1.1), ((0.5, 0.5), (0.68, 0.5)),
          kanji=K("花子さん", 0.16, 0.48, "luz", "Hanako-san", fundo="nanquim", em="Hanako-san")))
kanji_som(89, "Hanako-san"); fx(89, "pergunta", "ep08_bate_cabine", -6, depois=True)
pausa(90, 2.4)                                                                        # as três batidas soam SOZINHAS
C(90, img("L04b_hanako_sombra", (1.04, 1.12), ((0.6, 0.6), (0.65, 0.65)), mao=0.5))
C(91, img("L04_hanako_pes", (1.04, 1.12), ((0.55, 0.6), (0.58, 0.7)), mao=0.5, dof={"x": 0.58, "y": 0.78, "r": 0.2, "atraso": 1.0}))
C(92, img("J12_passagem_neve", (1.0, 1.08)), (img("L05_teketeke", (1.0, 1.12), ((0.5, 0.5), (0.58, 0.4)),
                                                  kanji=K("テケテケ", 0.18, 0.5, "sangue", "Teke Teke", glitch=True, em="som")), "cotovelos"))
kanji_som(92, "som")
C(93, img("J13b_boneca_cabelo", (1.0, 1.08), atmos={"vela": 0.5}))
C(94, img("L03b_boneca_okiku", (1.0, 1.1), ((0.5, 0.5), (0.5, 0.45)), atmos={"vela": 0.5},
          kanji=K("萬念寺", 0.84, 0.5, "placa", "templo Mannenji · Hokkaido", fundo="vermelho", em="Mannenji")))
kanji_som(94, "Mannenji")
C(95, img("J13_boneca_cabelo", (1.0, 1.25), ((0.35, 0.45), (0.37, 0.6)), atmos={"vela": 0.6},
          kanji=K("髪", 0.84, 0.45, "sangue", "o cabelo", tam=0.26, em="cresceu")))
kanji_som(95, "cresceu")
C(96, img("J08_tv_chiado", (1.2, 1.0), ((0.75, 0.4), (0.5, 0.5)), linha={"anos": LINHA, "de": 1979, "atual": 2004, "dur": 3.0}))
C(97, texto("Ele entrou\nna internet.", "na internet.", cps=18))
amb(79, "nenhum"); amb(89, "nenhum"); amb(92, "ep08_campo_noite", -24); amb(93, "nenhum")
pausa(84, 0.6); pausa(88, 0.4); pausa(91, 1.2); pausa(93, 0.4); pausa(95, 1.0); pausa(97, 0.6)

# ================================================================ PARTE 6 — a estação que não existe (2004)
capitulo(98, 6, "A estação que não existe", "2004", I + "N09_estacao_noite.jpg",
         texto("2channel · 8 de janeiro de 2004 · madrugada\n\n> Hasumi: estou num trem que não para", "não para", cps=26), "fórum", 2004)
C(99, real("R13_trem_enshu_2", (1.0, 1.08), kanji=K("遠州鉄道", 0.86, 0.45, "placa", "Foto real · linha Enshū", tam=0.11, fundo="vermelho", em="Enshū")),
  (vid("V02b_janela_trem", (1.0, 1.04)), "parava"))
kanji_som(99, "Enshū"); batidas[98]["sem_legenda"] = True
C(100, img("N09_estacao_noite", (1.0, 1.12), atmos={"neblina": 0.7},
           kanji=K("きさらぎ駅", 0.5, 0.4, "luz", "Kisaragi · estação", vertical=False, fonte="mincho", tam=0.15, glitch=True, selo="駅", em="desceu")))
T(100, "nanquim"); fx(100, None, "ep08_tinta", -11, atraso=-0.6); fx(100, "desceu", "ep08_freio", -16); fx(100, "Kisaragi", "ep08_sino_estacao", -12, depois=True)
C(101, img("N09b_estacao_noite", (1.0, 1.1), atmos={"neblina": 0.7}))
C(102, img("N09c_estacao_noite", (1.0, 1.1), mao=0.4))
C(103, img("N09c_estacao_noite", (1.1, 1.25), ((0.5, 0.5), (0.4, 0.45)), atmos={"neblina": 0.6}))
fx(103, "tambor", "ep08_tambor_longe", -14); fx(103, "sino", "ep08_sino_estacao", -14, depois=True)
C(104, img("D04b_plataforma_trilho", (1.0, 1.12), ((0.5, 0.5), (0.8, 0.5))))
C(105, img("D06_carro_estrada", (1.0, 1.12), ((0.5, 0.5), (0.35, 0.6))))
C(106, img("D06_carro_estrada", (1.12, 1.2), ((0.35, 0.6), (0.33, 0.62))))
C(107, real("R13_trem_enshu_2", (1.0, 1.05)), (real("R14_saginomiya_plataforma", (1.0, 1.08),
   kanji=K("実在", 0.86, 0.42, "placa", "Foto real · estação Saginomiya", tam=0.14, fundo="vermelho", atraso=0.2)), "Saginomiya"))
C(108, real("R14_saginomiya_plataforma", (1.1, 1.4), ((0.4, 0.5), (0.25, 0.45)),
            kanji=K("さぎの宮", 0.82, 0.45, "placa", "Saginomiya", tam=0.12, fundo="nenhum", em="placa")))
C(109, img("D03b_placa_kisaragi", (1.0, 1.12), ((0.5, 0.5), (0.3, 0.45)),
           kanji=K("きさらぎ", 0.78, 0.45, "luz", "Kisaragi", vertical=False, fonte="mincho", tam=0.13, em="Kisaragi")))
kanji_som(109, "Kisaragi")
C(110, real("R13_trem_enshu_2", (1.05, 1.2), ((0.6, 0.5), (0.65, 0.48))))
C(111, img("H01_fabrica_noite", (1.0, 1.08), kanji=K("浜松", 0.2, 0.5, "luz", "Hamamatsu", tam=0.28, selo="浜", atraso=0.1)))
kanji_som(111, "Hamamatsu", atraso=-0.1)
C(112, img("H01_fabrica_noite", (1.08, 1.25), ((0.5, 0.5), (0.85, 0.6))), (img("H02b_dani_plataforma", (1.0, 1.08)), "duzentos"))
C(113, img("H02_dani_plataforma", (1.0, 1.08), kanji=K("出稼ぎ", 0.8, 0.5, "tinta", "dekasegi · trabalhar longe de casa", atraso=0.1)))
kanji_som(113, "dekasseguis", atraso=-0.1)
C(114, img("H02_dani_plataforma", (1.08, 1.2), ((0.3, 0.5), (0.28, 0.5))))
amb(98, "nenhum"); amb(100, "ep08_campo_noite", -20); amb(103, "ep08_tambor_longe", -22); amb(107, "nenhum")
pausa(99, 0.4); pausa(101, 1.0); pausa(103, 1.0); pausa(106, 1.4); pausa(109, 0.6); pausa(111, 0.8); pausa(113, 0.8)

# ================================================================ A HISTÓRIA — a Dani
capitulo(115, 0, "A Dani", "Londrina → Hamamatsu", I + "H02b_dani_plataforma.jpg",
         img("H01_fabrica_noite", (1.0, 1.08)), "Fazia")
C(116, {"tipo": "relogios", "lados": [{"nome": "Hamamatsu", "hora": "23:52", "imagem": I + "H02_dani_plataforma.jpg", "brilho": 0.5},
                                       {"nome": "Londrina", "hora": "11:52"}]})
chat(117, {"de": "Dani", "texto": "Saindo da fábrica 🏭", "hora": "23:05", "apos": 0.2},
     {"de": "Mãe", "texto": "Vai com Deus filha ❤️", "hora": "11:06", "apos": 1.0},
     {"de": "Pai", "texto": "almoçando aqui, a comida tá sem graça sem você 😂", "hora": "11:06", "apos": 1.8})
C(118, img("H02_dani_plataforma", (1.0, 1.1)), (img("N10_trem_noite", (1.0, 1.08)), "trem"))
chat(119, {"de": "Dani", "tipo": "foto", "imagem": I + "D01_vagao_vazio.jpg", "hora": "23:20", "em": "foto"},
     {"de": "Dani", "texto": "Só eu hoje 😅", "hora": "23:20", "em": "hoje"})
chat(120, {"de": "Dani", "tipo": "audio", "duracao": "0:09", "hora": "23:40", "em": "áudio", "digitando": 0.6})
C(121, cel(vid("V02_janela_trem"), "23:40"))
chat(122, {"de": "Lucas", "texto": "Dormiu e passou do ponto de novo 😂", "hora": "11:41", "em": "Dormiu", "digitando": 0.8})
pausa(122, 2.0)
chat(123, {"de": "Dani", "texto": "Não dormi. O trem não parou em nenhuma estação.", "hora": "23:41", "em": "Não", "digitando": 0.6})
chat(124, {"de": "Mãe", "tipo": "audio", "duracao": "0:14", "hora": "11:42", "em": "áudio"})
chat(125, {"de": "Dani", "tipo": "video", "imagem": I + "D02_cabine_silhueta.jpg", "hora": "23:44", "em": "vídeo"})
C(126, cel(vid("V01_cabine_ate45", (1.0, 1.03)), "23:44"))
C(127, cel(img("D02_cabine_silhueta", (1.0, 1.12), ((0.5, 0.5), (0.56, 0.42))), "23:44"))
C(128, cel(img("D02_cabine_silhueta", (1.3, 1.6), ((0.56, 0.42), (0.55, 0.45))), "23:44"))
C(129, cel(img("D02b_cabine_silhueta", (1.2, 1.4), ((0.6, 0.45), (0.62, 0.45))), "23:45"))
fx(129, "vidro", "ep08_bate_vidro", -6, depois=True)
pausa(130, 1.4)                                                                     # as batidas no vidro soam sozinhas
C(130, cel(vid("V01b_cabine_ate45", (1.0, 1.04)), "23:45"))
fx(130, "freando", "ep08_freio", -14)
C(131, img("D04_plataforma_trilho", (1.0, 1.08)))
fx(131, None, "ep08_sino_estacao", -12, atraso=-1.4)
C(132, cel(img("D03_placa_kisaragi", (1.0, 1.3), ((0.5, 0.5), (0.86, 0.33))), "23:51",),)
batidas[132]["cena"]["kanji"] = K("きさらぎ", 0.3, 0.38, "luz", "Kisaragi", vertical=False, fonte="mincho", tam=0.13, em="Kisaragi")
kanji_som(132, "Kisaragi")
chat(133, {"de": "Pai", "texto": "Que estação é essa?", "hora": "11:52", "em": "estação", "digitando": 0.6})
chat(134, {"de": "Lucas", "texto": "…", "hora": "11:53", "em": "Procurou", "digitando": 2.0})
chat(135, {"de": "Lucas", "texto": "Dani, não existe estação com esse nome.", "hora": "11:54", "em": "Dani", "digitando": 0.6})
chat(136, {"de": "Dani", "texto": "Eu tô em cima dela.", "hora": "23:54", "em": "Eu", "digitando": 0.5})
C(137, img("D04_plataforma_trilho", (1.0, 1.15), ((0.5, 0.5), (0.22, 0.6)), atmos={"neblina": 0.5}))
C(138, cel(img("D03b_placa_kisaragi", (1.0, 1.1)), "23:58", "fraco"))
chat(139, {"de": "Dani", "texto": "o celular tá sem serviço mas o grupo funciona??", "hora": "00:02", "em": "Só"})
chat(140, {"de": "Dani", "tipo": "audio", "duracao": "0:09", "hora": "00:10", "em": "áudio"})
C(141, cel(img("D04b_plataforma_trilho", (1.0, 1.1), ((0.5, 0.5), (0.7, 0.5))), "00:10", "fraco"))
pausa(142, 3.8)
C(142, img("N09c_estacao_noite", (1.0, 1.12), ((0.5, 0.5), (0.4, 0.45)), atmos={"neblina": 0.7}))
fx(142, "tambor", "ep08_taiko", -16, depois=True); fx(142, "sino", "ep08_sino_estacao", -13, depois=True)
C(143, vid("V04_sem_relogio", (1.0, 1.06)))
C(144, cel(vid("V03_trilho_lanterna"), "00:21", "fraco"))
C(145, cel(vid("V03_trilho_lanterna", (1.05, 1.15), video_inicio=3.0), "00:21", "fraco"))
C(146, cel(img("D05_perna_trilho", (1.0, 1.0), zoom_digital={"x": 0.53, "y": 0.4, "ate": 2.0, "atraso": 0.2, "dur": 1.6}), "00:22", "fraco"))
C(147, cel(img("D05_perna_trilho", (1.0, 1.0), zoom_digital={"x": 0.53, "y": 0.4, "ate": 2.6, "atraso": 0.0, "dur": 2.0}), "00:22", "fraco"))
C(148, cel(img("D05_perna_trilho", (1.6, 2.0), ((0.53, 0.4), (0.53, 0.12))), "00:22", "fraco"))
C(149, cel(img("D05_perna_trilho", (2.0, 2.1), ((0.53, 0.12), (0.53, 0.1))), "00:22", "fraco"))
fx(149, "Ei", "ep08_ei", -5, depois=True)
pausa(150, 1.8)                                                                     # o "Ei!" soa sozinho
C(150, cel(vid("V03_trilho_lanterna", (1.1, 1.2), velocidade=2.0, mao=1.0), "00:22", "fraco"))
chat(151, {"de": "Dani", "tipo": "foto", "imagem": I + "D06_carro_estrada.jpg", "hora": "00:35", "em": "Saí"},
     {"de": "Dani", "texto": "Saí numa estrada. Tem um carro parado. O motorista falou que me leva até a cidade.", "hora": "00:35", "em": "carro"})
chat(152, {"de": "Pai", "texto": "Não entra, filha.", "hora": "12:36", "em": "Não", "digitando": 0.5})
chat(153, {"de": "Dani", "texto": "Pai, eu tô sozinha no meio do mato. Ele parece normal.", "hora": "00:36", "em": "Pai", "digitando": 0.6})
C(154, img("D06_carro_estrada", (1.1, 1.3), ((0.35, 0.6), (0.33, 0.62))))
fx(154, "entrou", "ep08_porta_carro", -9, depois=True)
pausa(155, 1.4)
C(155, {"tipo": "mapa", "hora_inicio": "00:41", "hora_fim": "00:58", "progresso": [0.0, 0.5]})
fx(155, None, "ep08_vibra", -12, atraso=0.1)
chat(158, {"de": "Lucas", "texto": "Dani, ele tá indo pro lado errado.", "hora": "12:47", "em": "Dani"})
C(159, vid("V05_carro_montanha", (1.0, 1.04)))
chat(160, {"de": "Pai", "texto": "DANI", "hora": "12:49", "em": "DANI"})
C(161, {"tipo": "mapa", "hora_inicio": "00:41", "hora_fim": "00:58", "progresso": [0.5, 0.7]})
C(162, vid("V05b_carro_montanha", (1.0, 1.04)))
chat(163, {"de": "Dani", "texto": "…", "hora": "00:53", "em": "mensagem", "digitando": 1.4}, sons=False)
chat(164, {"de": "Dani", "texto": "ele não fala japonês", "hora": "00:53", "em": "fala", "digitando": 0.6})
chat(165, {"de": "Dani", "texto": "…", "hora": "00:54", "em": "depois", "digitando": 1.0}, sons=False)
chat(166, {"de": "Dani", "texto": "ele tá falando com alguém. em português. com a voz do pai.", "hora": "00:54", "em": "falando", "digitando": 0.6})
C(167, {"tipo": "mapa", "hora_inicio": "00:41", "hora_fim": "00:58", "progresso": [0.7, 1.0], "some_em": "sumiu"})
amb(115, "nenhum"); amb(118, "ep08_trem_dentro", -18); amb(131, "ep08_campo_noite", -18); amb(141, "ep08_tambor_longe", -16)
amb(143, "ep08_campo_noite", -18); amb(155, "ep08_trem_dentro", -40); amb(159, "ep08_tambor_longe", -26)
HIST.clear()
pausa(123, 0.4); pausa(126, 0.4); pausa(128, 1.2); pausa(131, 0.6); pausa(135, 0.8); pausa(136, 1.2); pausa(137, 1.0)
pausa(147, 1.0); pausa(148, 1.2); pausa(154, 0.6); pausa(157, 1.2); pausa(160, 0.8); pausa(161, 0.6); pausa(162, 1.2)
pausa(164, 1.4); pausa(166, 1.6); pausa(168, 1.6)

# ================================================================ A VIRADA — o vídeo da vigília
C(169, img("N10b_trem_noite", (1.0, 1.08)), (vid("V04_sem_relogio", (1.0, 1.06), video_inicio=4.0), "câmeras"))
saida_lenta(169, 3.6, dur=2.2)
HIST.extend([{"de": "Lucas", "texto": "alguma notícia?", "hora": "09:02"}])
chat(170, {"de": "Mãe", "texto": "Liguei no consulado de novo", "hora": "15:20", "em": "consulado"},
     {"de": "Lucas", "texto": "A fábrica disse que ela saiu 23h05", "hora": "15:31", "em": "fábrica"},
     {"de": "Pai", "texto": "Ninguém sabe de nada", "hora": "15:40", "em": "todo"})
C(171, texto("Nada.", "Nada.", "impacto", cps=8, tamanho=150))
C(172, cel(img("D09_vigilia", (1.0, 1.06)), "16:10", vertical=True))
C(173, cel(img("D09_vigilia", (1.06, 1.12), ((0.5, 0.6), (0.5, 0.7))), "16:10", vertical=True))
C(174, cel(img("D09_vigilia", (1.15, 1.35), ((0.5, 0.75), (0.42, 0.85))), "16:11", vertical=True))
C(175, cel(img("D10_vigilia_janela", (1.0, 1.04)), "16:12", vertical=True))
C(176, cel(img("D10_vigilia_janela", (1.04, 1.08), ((0.5, 0.6), (0.5, 0.62))), "16:12", vertical=True))
C(177, cel(img("D10_vigilia_janela", (1.08, 1.1), ((0.5, 0.62), (0.5, 0.62))), "16:12", vertical=True))
pausa(178, 2.0)
C(178, cel(img("D10b_vigilia_janela", (1.0, 1.06)), "16:13", vertical=True))
C(179, cel(img("D10_vigilia_janela", (1.0, 1.04), ((0.5, 0.6), (0.6, 0.4))), "16:13", vertical=True))
C(180, cel(img("D10_vigilia_janela", (1.04, 1.06), ((0.6, 0.4), (0.6, 0.38))), "16:13", vertical=True))
batidas[181]["pausa_antes_s"] = 0
C(181, {"tipo": "chat", "grupo": "Oração pela Dani 🙏", "membros": "1.248 participantes", "mensagens": [
    {"de": "Rose", "texto": "Compartilhado 🙏", "hora": "21:02", "apos": 0.3},
    {"de": "Igreja Batista Vila Nova", "texto": "Estamos orando pela família", "hora": "21:10", "apos": 1.2},
    {"de": "Desaparecidos PR", "tipo": "video", "imagem": I + "D10_vigilia_janela.jpg", "texto": "Compartilhem", "hora": "21:40", "apos": 2.2},
    {"de": "Marcos", "texto": "Força família 🙏🙏", "hora": "22:15", "apos": 3.4}]})
batidas[181]["cena"]["entrada"] = "fundir"; batidas[181]["sem_legenda"] = True
saida_lenta(181, 1.6)
C(182, cel(img("D10_vigilia_janela", (1.0, 1.03)), "16:12", vertical=True))
C(183, {"tipo": "chat", "grupo": "Oração pela Dani 🙏", "membros": "1.248 participantes", "mensagens": [
    {"de": "Marcos", "texto": "Força família 🙏🙏", "hora": "22:15", "apos": -30},
    {"de": "desconhecido_1987", "texto": "…", "hora": "03:12", "em": "comentou", "digitando": 1.6}]})
batidas[183]["sem_legenda"] = True
C(184, {"tipo": "chat", "grupo": "Oração pela Dani 🙏", "membros": "1.248 participantes", "mensagens": [
    {"de": "Marcos", "texto": "Força família 🙏🙏", "hora": "22:15", "apos": -30},
    {"de": "desconhecido_1987", "texto": "Quem é a moça na janela de cima?", "hora": "03:12", "apos": 0.1}]})
batidas[184]["sem_legenda"] = True
fx(184, None, "ep08_msg", -12, atraso=0.1)
pausa(185, 1.6)
C(185, cel(vid("V07_vigilia_zoom_janela", (1.0, 1.0)), "16:12", vertical=True))
C(187, cel(img("D10_vigilia_janela", (1.0, 1.0), zoom_digital={"x": 0.623, "y": 0.245, "ate": 3.2, "atraso": 0.2, "dur": 3.0}), "16:12", vertical=True))
C(188, cel(img("D11_janela_close", (1.0, 1.06), ((0.45, 0.5), (0.45, 0.48))), "16:12", vertical=True))
C(189, cel(img("D11_janela_close", (1.1, 1.3), ((0.45, 0.45), (0.45, 0.42))), "16:12", vertical=True))
C(190, cel(img("D11_janela_close", (1.3, 1.4), ((0.45, 0.5), (0.45, 0.62))), "16:12", vertical=True))
C(191, grav("R18_oyuki_okyo", (1.2, 1.5), ((0.5, 0.35), (0.5, 0.2))))
T(191, "fundir", 1.8)
amb(169, "nenhum"); amb(172, "ep08_quintal", -18); amb(177, "ep08_quintal", -14); amb(178, "ep08_reza", -18)
amb(181, "nenhum"); amb(182, "ep08_quintal", -20); amb(183, "nenhum"); amb(185, "ep08_reza", -20); amb(191, "nenhum")
pausa(171, 0.6); pausa(174, 0.6); pausa(180, 1.0); pausa(184, 1.4); pausa(186, 0.8); pausa(187, 1.4); pausa(188, 1.0)
pausa(189, 1.0); pausa(190, 1.2); pausa(191, 1.4)

# ================================================================ FECHO — Vigia (corte seco, sem transição)
C(192, vigia((1.0, 1.04)))
pausa(192, 2.4)
C(193, vigia((1.04, 1.1), ((0.4, 0.45), (0.38, 0.43))))
C(194, grav("R03_okiku_poco_hokusai", (1.0, 1.06)), (grav("R01_oiwa_lanterna_hokusai", (1.0, 1.06)), "Oiwa"),
  (img("N09_estacao_noite", (1.0, 1.08), atmos={"neblina": 0.6}), "estação"), **V)
C(195, cel(img("D10_vigilia_janela", (1.0, 1.0), zoom_digital={"x": 0.623, "y": 0.245, "ate": 2.6, "atraso": 0.0, "dur": 2.0}), "16:12", vertical=True))
C(196, cel(img("D11_janela_close", (1.2, 1.3), ((0.45, 0.45), (0.45, 0.43))), "16:12", vertical=True))
C(197, vigia((1.0, 1.05)))
saida_lenta(197, 1.6)
C(198, vigia((1.05, 1.12), ((0.4, 0.45), (0.36, 0.42))))
C(199, vigia((1.0, 1.05)), (vid("V02b_janela_trem", (1.0, 1.04)), "ônibus"), **V)
C(200, texto("Não manda mensagem\npra ninguém.", "pra ninguém.", cps=26))
C(201, vigia((1.0, 1.05)))
amb(192, "nenhum")
pausa(194, 0.6); pausa(196, 1.0); pausa(198, 0.8); pausa(200, 0.6); pausa(201, 0.6)

# ================================================================ VINHETA FIXA DE INSCRIÇÃO
batidas.append({"fala": F.VINHETA, "cta_inicio": True, "sem_legenda": True, "ambiente": {"som": "nenhum"},
                "musica": {"som": "vinheta_ultimo_abrigo", "volume_db": -20}})

voz = "audio/voz_personagens.wav" if (AQUI / "audio" / "voz_personagens.wav").exists() else "audio/voz_com_vinheta_limpa.wav"
T_DB = -35
roteiro = {
    "modo": "cenas", "formato": "16:9", "tema": "vigia", "avatar": "vigia_hd",
    "voz_arquivo": voz,
    "cintilar": 0.03, "apertar_pausas": False,   # REGRA: nunca encurtar as pausas da narração
    "vigia_padrao": False,
    "preencher_pausas": {"min": 1.3},
    "cauda": 1.6, "chuva": 0, "grao": 0.16,
    "mix": {"musica_ganho_db": 12, "fundo_sob_voz": -9, "efeitos_sob_voz": -4, "voz_pro": True, "fundo_bolso": True,
            "efeitos_pico_max": -3},
    "legendas": {"destaques": ["Japão", "regra", "poço", "real", "estação", "existe", "Kisaragi", "janela", "olhar"]},
    "ambiente_inicial": [{"som": "ep08_trem_dentro", "volume_db": -16}],
    "musica": {"som": "ep08_japones_longa", "volume_db": T_DB},
    "abertura": {"texto": "O VIGIA\nEP. 08 · A ESTAÇÃO QUE NÃO EXISTE", "vermelho": "QUE NÃO EXISTE", "duracao": 3.2, "segurar": 1.6,
                 "antes_da_batida": 7, "sons": [{"som": "ep08_taiko", "t": 0.2, "volume_db": -10}]},
    "cta": {"titulo": "Você acabou de olhar.", "canal": "Último Abrigo",
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


garantir_leitura()
aplicar_ajuste_pausas()
sem = [i for i, b in enumerate(batidas) if not cenas_de(b)]
(AQUI / "roteiro.json").write_text(json.dumps(roteiro, ensure_ascii=False, indent=1), encoding="utf-8")
n_cenas = sum(len(cenas_de(b)) for b in batidas)
print(f"{len(batidas)} falas, {n_cenas} cenas, falas sem cena (continuam a anterior): {sem}")
print("pausa total:", round(sum(b.get("pausa_antes_s", 0) for b in batidas), 1), "s")
