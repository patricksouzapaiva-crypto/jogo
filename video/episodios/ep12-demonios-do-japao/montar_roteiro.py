"""Monta roteiro.json do Ep. 12 — "Os demônios do Japão não querem a sua alma" (24/11).
Molde do Ep. 08 (o episódio japonês que mais deu resultado): gancho sem Vigia; cartões de capítulo japoneses (第一章…)
com tinta e taiko; kanji na tela; trilha japonesa (sintetizar_japones_ep12.py, irmã mais escura da do Ep. 08).
Pedido do usuário: O MÁXIMO DE IMAGENS REAIS. Quase tudo é gravura, rolo ou foto real:
- real(n): a obra INTEIRA no papel com o crédito (reais_prontos/, preparar_midia.py);
- det(n, foco): close de detalhe no original (reais/), a câmera anda dentro da obra;
- rolo(n): travelling num rolo horizontal (rolos/), lido da direita para a esquerda, como um emaki;
- IA(cod, reserva): ilustração pedida ao usuário (imagens/<cod>.jpg, SEM rosto). Enquanto não chega, entra a reserva real.
Regras: Vigia só no VIGIA e no FECHO; nenhum rosto de IA; cena >= 4 s; legenda só em português; nunca silêncio.
Uso: python3 montar_roteiro.py → roteiro.json"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import falas as F

AQUI = Path(__file__).parent
falas, PERS, SEC, PAUSAS, _ = F.ler()
assert len(falas) == 203 and falas[202] == "Eu sou o Vigia. Boa noite." and SEC["A HISTÓRIA"] == 160, "o ROTEIRO.md mudou: rever os índices"
batidas = [{"fala": f} for f in falas]
for i, s in PAUSAS.items():
    batidas[i]["pausa_antes_s"] = s

VIGIA = {"imagem": "../../painel/cenarios/abrigo_16x9.png", "vigia": True}
C3D = AQUI / "camera3d"; C3D.mkdir(exist_ok=True)
ALI = Path(__import__("os").environ.get("ALINHAMENTO") or AQUI / "audio" / "alinhamento.json")


# ------------------------------------------------------------------ ajudantes
def vigia(z=(1.0, 1.04), foco=((0.55, 0.5), (0.57, 0.48))):
    return dict(VIGIA, zoom=list(z), foco=[list(foco[0]), list(foco[1])])


def _arq(pasta, nome):
    for ext in (".jpg", ".png"):
        if (AQUI / pasta / (nome + ext)).exists():
            return pasta + nome + ext
    raise SystemExit(f"imagem faltando: {pasta}{nome}")


def real(nome, z=(1.0, 1.05), foco=None, **kw):
    """A obra inteira, no papel, com o crédito embaixo (zoom pequeno: o crédito não pode sair do quadro)."""
    c = {"imagem": _arq("reais_prontos/", nome), "zoom": list(z), "atmos": kw.pop("atmos", {"poeira": 0.4}), **kw}
    if foco:
        c["foco"] = [list(foco[0]), list(foco[1])]
    return c


def det(nome, foco=((0.5, 0.5), (0.5, 0.45)), z=(1.0, 1.1), **kw):
    """Close de detalhe: o original cobrindo a tela; a câmera vai de foco[0] a foco[1]."""
    return {"imagem": _arq("reais/", nome), "zoom": list(z), "foco": [list(foco[0]), list(foco[1])],
            "atmos": kw.pop("atmos", {"poeira": 0.3}), **kw}


def conter(nome, z=(1.0, 1.06), foco=None, **kw):
    """Obra inteira sem papel (fundo desfocado dela mesma): para as fotos dos rolos do casamento das assombrações."""
    c = {"imagem": _arq("reais/", nome), "zoom": list(z), "encaixe": "conter", "atmos": kw.pop("atmos", {"poeira": 0.4}), **kw}
    if foco:
        c["foco"] = [list(foco[0]), list(foco[1])]
    return c


def rolo(nome, **kw):
    return {"video": f"rolos/{nome}.mp4", "zoom": [1.0, 1.0], **kw}


def casamento(n, foco=((0.3, 0.5), (0.7, 0.5)), z=(1.15, 1.2)):
    """Rolo 'Casamento ilustrado de assombrações' (Cleveland, CC0): trecho n, a câmera anda pelo desfile."""
    return {"imagem": f"reais/ROLO_casamento/alt{n:02d}.jpg", "zoom": list(z), "foco": [list(foco[0]), list(foco[1])],
            "atmos": {"poeira": 0.4}}


PEDIDOS = []


def IA(cod, reserva, z=(1.0, 1.08), foco=((0.5, 0.5), (0.5, 0.46)), **kw):
    """Ilustração pedida ao usuário (imagens/<cod>.jpg). Sem ela, a reserva (imagem real) segura o lugar."""
    for ext in (".jpg", ".png"):
        if (AQUI / "imagens" / (cod + ext)).exists():
            return {"imagem": f"imagens/{cod}{ext}", "zoom": list(z), "foco": [list(foco[0]), list(foco[1])], **kw}
    PEDIDOS.append(cod)
    return reserva


def IAk(cod, reserva, k, leg):
    """Ilustração com o nome do yokai em kanji (substitui a ficha quando a imagem chega)."""
    c = IA(cod, None)
    return kj(c, k, 0.16, 0.5, "luz", leg, atraso=0.6) if c else reserva


def texto(t, vermelho=None, estilo="maquina", **kw):
    return {"tipo": "texto", "texto": t, "estilo": estilo, **({"vermelho": vermelho} if vermelho else {}), **kw}


def ficha(t, vermelho=None):
    """FICHA de documentário (dado real, com fonte): máquina de escrever, parada, no tempo de leitura."""
    return texto(t, vermelho, cps=40)


def K(texto_k, x=0.82, y=0.5, modo="luz", legenda=None, **kw):
    return {"texto": texto_k, "x": x, "y": y, "modo": modo, **({"legenda": legenda} if legenda else {}), **kw}


def kj(c, *a, **kw):
    """Põe um kanji (K) numa cena."""
    c = dict(c); c["kanji"] = K(*a, **kw)
    return c


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


def saida_lenta(i_seguinte, segurar, transicao="fundir", dur=1.6):
    b = batidas[i_seguinte]
    b["pausa_antes_s"] = round(b.get("pausa_antes_s", 0) + segurar + dur, 2)
    (b.get("cena") or b["cenas"][0]).update({"entrada": transicao, "duracao_entrada": dur, "antecipar": dur})


def pausa(i, s):
    batidas[i]["pausa_antes_s"] = round(batidas[i].get("pausa_antes_s", 0) + s, 2)


def amb(i, som, db=-20, em=None):
    batidas[i]["ambiente"] = {"som": som, "volume_db": db, **({"em": em} if em else {})}


def fx(i, em, som, db, depois=False, atraso=0.0, **kw):
    batidas[i].setdefault("sons", []).append({"em": em, "som": som, "volume_db": db, "depois": depois, "atraso": atraso, **kw})


def kanji_som(i, em, db=-16, atraso=0.0):
    fx(i, em, "ep08_kanji", db, atraso=atraso)


def seco(c):
    c = dict(c); c["entrada"] = "corte"
    return c


CARTAO = 7.6


def capitulo(i, n, titulo, ano, imagem, cena):
    """24/11: o cartão EMAKI VIVO (capitulos/emaki.py: o rolo desenrola, a gravura nasce no nanquim, o pincel escreve o
    número, o carimbo 鬼 bate) — vídeo pronto de 7,6 s em cartoes/cap<n>.mp4, com o som dele. Sem o vídeo (ainda não
    renderizado), cai no cartão japonês do Ep. 08."""
    primeira = falas[i].split()[0].strip(",.:;…\"")
    cena = dict(cena); cena.setdefault("entrada", "fundir"); cena.setdefault("duracao_entrada", 0.9)
    vid = AQUI / "cartoes" / f"cap{n}.mp4"
    if vid.exists():
        cap = {"video": f"cartoes/cap{n}.mp4", "zoom": [1.0, 1.0], "antecipar": CARTAO, "antecipar_fixo": True,
               "entrada": "corte", "tipo_cartao": True, "congelar": True, "sem_look": True}
        C(i, cap, (cena, primeira))
        pausa(i, CARTAO - 0.2)
        som = AQUI / "cartoes" / f"cap{n}_som.wav"
        if not som.exists() or som.stat().st_mtime < vid.stat().st_mtime:
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(vid), "-vn", "-ac", "2", "-ar", "48000", str(som)], check=True)
        fx(i, None, f"cartao{n}", -6, atraso=-CARTAO + 0.05, arquivo=str(som))
        CARTOES.append(i); return
    nums = "一二三四五六七"
    cap = {"tipo": "capitulo", "numero": f"第{nums[n - 1]}章" if n else "最終章", "numero_pt": f"Capítulo {n}" if n else "A história",
           "titulo": titulo, "ano": ano, "imagem": imagem, "antecipar": 4.8, "entrada": "nanquim", "atmos": {"poeira": 0.6}}
    C(i, cap, (cena, primeira))
    pausa(i, 5.2)
    fx(i, None, "ep08_tinta", -17, atraso=-4.8)
    fx(i, None, "ep08_taiko", -17, atraso=-3.4)
    CARTOES.append(i)
    DUR_CARTAO[i] = 5.2


DUR_CARTAO = {}
CARTOES = []
HIST = []


def chat(i, *novas, sons=True):
    msgs = [dict(m, apos=-30) for m in HIST[-6:]]
    for m in novas:
        m = dict(m); m.setdefault("apos", 0.3)
        msgs.append(m); HIST.append({k: v for k, v in m.items() if k not in ("apos", "em", "digitando")})
        if sons and "em" not in m:
            fx(i, None, "ep08_msg", -19, atraso=m["apos"])
        elif sons:
            fx(i, m["em"], "ep08_msg", -19)
    C(i, {"tipo": "chat", "grupo": "Turno da noite 🏭", "membros": "Camila, Tati, Rodrigo, Kenji", "mensagens": msgs})
    batidas[i]["sem_legenda"] = True


RP = "reais_prontos/"

# ================================================================ GANCHO — sem Vigia (o caso de Matsudo, 2022)
C(0, IA("G01_arvore_santuario_madrugada", det("kifune_2", ((0.5, 0.55), (0.5, 0.45)), (1.0, 1.08))))
C(1, IA("G02_boneco_prego_tronco", det("ritual_mulher", ((0.3, 0.5), (0.28, 0.45)), (1.3, 1.45))))
C(2, ficha('"REZO PELA ANIQUILAÇÃO"\nBilhete preso aos bonecos · Matsudo, Japão, maio de 2022', "REZO PELA ANIQUILAÇÃO"))
C(3, dict(IA("G03_camera_santuario", det("kifune_3", ((0.5, 0.5), (0.52, 0.48)), (1.0, 1.06))),
         efeitos={"cctv": {"cam": "CAM 02", "hora": "02:14:37", "data": "18-05-2022"}}))
C(4, ficha("MATSUDO · MAIO DE 2022\nHomem de 72 anos preso por danificar as árvores sagradas", "72 ANOS"))
C(5, det("m_ushinokoku", ((0.85, 0.75), (0.85, 0.6)), (1.4, 1.6)))
C(6, real("ritual_sekien"), (det("ritual_sekien", ((0.4, 0.35), (0.4, 0.3)), (1.6, 1.8)), "aro"))
C(7, kj(real("ritual_mulher", (1.0, 1.06)), "丑の刻参り", 0.12, 0.5, "sangue", "ushi no toki mairi · a visita da hora do Boi", selo="呪", atraso=0.3))
kanji_som(7, "maldição", atraso=-0.4)
C(8, real("hashihime_sekien"))
C(9, det("hashihime_sekien", ((0.45, 0.45), (0.45, 0.38)), (1.4, 1.65)))
C(10, real("kyosai_6"), (rolo("ROLO_hyakki_aic"), "pior"))
C(11, kj(real("hannya_preto", (1.0, 1.08)), "鬼", 0.15, 0.5, "sangue", "demônio", atraso=0.6))
kanji_som(11, "ninguém")
amb(0, "ep08_campo_noite", -22)
fx(1, None, "ep12_martelo_prego", -18, atraso=0.3)
fx(5, "prego", "ep12_martelo_prego", -15)
fx(6, "três", "ep08_vela", -20)
pausa(5, 0.6); pausa(7, 0.8); pausa(9, 1.0); pausa(11, 0.6)

# ================================================================ VIGIA
C(12, vigia((1.0, 1.04)))
C(14, vigia((1.04, 1.1), ((0.45, 0.48), (0.43, 0.46))))
amb(12, "nenhum")
saida_lenta(12, 5.4, dur=2.2)
batidas[12]["cena"].update({"antecipar": 7.2, "antecipar_fixo": True})   # o título aparece sobre o Vigia, com a trilha

# ================================================================ TEMA — não são demônios
C(15, real("m_satanas_durer"))   # 24/11 (usuário: imagem que não condiz): o demônio do OCIDENTE (Duvet, Apocalipse)
C(16, ficha("NO OCIDENTE, O DEMÔNIO\nÉ um anjo caído · serve ao Diabo · quer a sua alma", "QUER A SUA ALMA"))
C(17, real("m_exorcismo"))   # o padre que expulsa (Vivarini, S. Pedro Mártir exorcizando)
C(18, real("m_santo_antao"))   # ainda o Ocidente: os demônios de Schongauer
C(19, real("m_otsue_oni"))   # "Lá não existe Diabo": a virada para o Japão
C(20, kj(real("m_mascara_kobeshimi"), "鬼", 0.18, 0.5, "sangue", "oni", atraso=0.4))
kanji_som(20, "oni")
C(21, kj(real("kyosai_4"), "妖怪", 0.12, 0.5, "luz", "yōkai", atraso=0.3), )
kanji_som(21, "yōkai")
C(22, det("kyosai_5", ((0.35, 0.5), (0.6, 0.5)), (1.25, 1.3)))
C(23, real("m_kyosai_lesma"))
C(24, det("m_kyosai_luta", ((0.3, 0.45), (0.35, 0.45)), (1.3, 1.4)))
C(25, real("m_hannya_hokusai"))
C(26, real("hyakki_tsukumogami"), (real("m_raijin_momoyogusa"), "deus"))
C(27, det("m_hannya_hokusai", ((0.55, 0.45), (0.55, 0.4)), (1.4, 1.7)))
pausa(16, 0.4); pausa(24, 0.6); pausa(27, 1.0)

# ================================================================ PARTE 1 — a mulher que pediu para virar demônio
capitulo(28, 1, "A mulher que virou demônio", "séc. IX", RP + "m_kanawa.jpg", real("m_ushinokoku"))
C(29, det("m_ushinokoku", ((0.42, 0.25), (0.42, 0.2)), (1.6, 1.8)))
C(30, real("kifune_2"))
C(31, det("kifune_3", ((0.5, 0.45), (0.5, 0.4)), (1.1, 1.2)))
C(32, det("kifune_2", ((0.5, 0.35), (0.5, 0.25)), (1.15, 1.3)))
C(33, det("hashihime_sekien", ((0.45, 0.25), (0.45, 0.2)), (1.6, 1.8)))
C(34, real("m_kanawa"))
C(35, det("m_kanawa", ((0.45, 0.25), (0.45, 0.2)), (1.6, 1.8)))
C(36, det("hashihime_sekien", ((0.45, 0.4), (0.45, 0.35)), (1.8, 2.0)))
C(37, real("ritual_mulher"))
C(38, det("ritual_mulher", ((0.6, 0.5), (0.5, 0.5)), (1.2, 1.3)))
C(39, det("hashihime_sekien", ((0.5, 0.8), (0.5, 0.7)), (1.4, 1.5)))
C(40, real("hannya_preto", (1.0, 1.08)))
C(41, real("m_shirazunoyabu"))
C(42, det("m_shirazunoyabu", ((0.4, 0.3), (0.4, 0.25)), (1.4, 1.6)))
C(43, kj(real("hashihime_sekien"), "橋姫", 0.15, 0.5, "luz", "Hashihime · a princesa da ponte", selo="鬼", atraso=0.6))
kanji_som(43, "Hashihime")
C(44, real("m_rashomon_tsuna"))
C(45, det("m_rashomon_tsuna", ((0.5, 0.25), (0.5, 0.2)), (1.4, 1.6)))
C(46, real("m_rashomon_noh"))
C(47, kj(real("modoribashi"), "戻橋", 0.14, 0.5, "luz", "Modoribashi · a ponte da volta", atraso=0.8))
kanji_som(47, "Modoribashi")
C(48, real("m_kanawa"), (real("hannya_preto"), "rosto"))
C(49, det("hannya_preto", ((0.35, 0.5), (0.65, 0.5)), (1.2, 1.25)))
C(50, real("m_hannya_hokusai"))
fx(37, "correndo", "ep08_taiko", -18)
fx(46, "cortou", "ep12_espada", -16)
pausa(36, 0.4); pausa(39, 0.8); pausa(40, 1.0); pausa(42, 0.8); pausa(49, 0.6); pausa(50, 0.6)

# ================================================================ PARTE 2 — o oni e a porta do demônio
capitulo(51, 2, "A porta do demônio", "713 · hoje", RP + "m_ibaraki_esboco.jpg", real("m_ibaraki_esboco"))
C(52, kj(det("m_ibaraki_esboco", ((0.4, 0.3), (0.4, 0.25)), (1.3, 1.45)), "隠", 0.82, 0.5, "luz", "on · o que se esconde", atraso=1.0))
kanji_som(52, "on")
C(53, IA("N05_oni_um_olho_campo", real("kyosai_7")))
C(54, IA("N06_oni_chapeu_funeral", real("kyosai_3")))
C(55, real("m_jigokudayu"), (det("m_jigoku_livro", ((0.7, 0.45), (0.72, 0.42)), (1.4, 1.5)), "cabeça"))
C(56, real("m_raijin_estatua"))
C(57, kj(real("m_zodiaco"), "艮", 0.2, 0.5, "sangue", "ushitora · o nordeste", tam=0.3, atraso=0.4))
kanji_som(57, "mapa")
C(58, det("m_zodiaco", ((0.5, 0.45), (0.55, 0.45)), (1.25, 1.3)))
C(59, kj(real("enryakuji"), "鬼門", 0.14, 0.5, "sangue", "kimon · a porta do demônio", selo="鬼", atraso=0.8))
kanji_som(59, "kimon")
C(60, det("enryakuji", ((0.5, 0.6), (0.5, 0.4)), (1.1, 1.2)))
C(61, real("sarugatsuji"))
C(62, det("sarugatsuji", ((0.35, 0.5), (0.25, 0.5)), (1.2, 1.4)))
C(64, {"imagem": "imagens/O01_macaco_guardiao.jpg", "zoom": [1.0, 1.06], "foco": [[0.5, 0.55], [0.5, 0.5]]})   # o macaco guardião (o objeto que o usuário gerou)
C(65, IA("N07_casa_canto_nordeste", det("sarugatsuji", ((0.3, 0.5), (0.25, 0.5)), (1.2, 1.3))))
C(66, ficha("KYOTO · 2015\nMais de 1.100 cantos de casa protegidos contra o kimon", "1.100"))
C(67, ficha("TÓQUIO · ABRIL DE 1936\nO Ministério da Educação demole o banheiro do ministro: estava no kimon", "1936"))
C(69, det("enryakuji", ((0.5, 0.4), (0.5, 0.35)), (1.2, 1.3)))
C(70, real("shuten_sekien"))
pausa(57, 0.4); pausa(63, 0.6); pausa(69, 0.6); pausa(70, 0.6)

# ================================================================ PARTE 3 — o oni que bebia saquê
capitulo(71, 3, "O oni que bebia saquê", "990", RP + "m_raiko_cabeca.jpg", real("m_shuten_palacio"))
C(72, det("m_shuten_palacio", ((0.5, 0.6), (0.5, 0.5)), (1.3, 1.4)))
C(73, real("shuten_oeyama_1927"))
C(74, kj(real("shuten_sekien"), "酒呑童子", 0.12, 0.5, "luz", "Shuten-dōji · o menino que bebe saquê", selo="酒", atraso=0.4))
kanji_som(74, "nome")
C(75, det("shuten_sekien", ((0.4, 0.45), (0.4, 0.4)), (1.4, 1.6)))
C(76, rolo("shuten_rolo_cbl"))
C(78, real("shuten_rolo_cbl"))
C(79, det("shuten_rolo_cbl", ((0.3, 0.5), (0.45, 0.5)), (1.5, 1.6)))
C(80, det("shuten_rolo_cbl", ((0.55, 0.5), (0.65, 0.5)), (1.6, 1.7)))
C(81, real("m_raiko_cabeca"))
C(82, det("m_raiko_cabeca", ((0.6, 0.65), (0.6, 0.6)), (1.4, 1.6)))
C(83, real("kubizuka_3"))
C(84, det("kubizuka_3", ((0.5, 0.5), (0.5, 0.45)), (1.1, 1.2)))
C(86, kj(real("kubizuka_1"), "首塚", 0.84, 0.5, "luz", "Kubizuka · o túmulo da cabeça", atraso=0.8))
kanji_som(86, "Kubizuka")
C(87, real("kubizuka_2"))
C(88, det("kubizuka_2", ((0.5, 0.45), (0.5, 0.4)), (1.2, 1.3)))
C(89, real("m_setsubun"))
C(90, det("m_setsubun", ((0.35, 0.5), (0.3, 0.5)), (1.4, 1.5)))
C(91, det("m_rashomon_tsuna", ((0.5, 0.7), (0.5, 0.6)), (1.3, 1.4)))
C(92, real("setsubun_hokusai"))
C(93, real("m_otsue_oni"))
fx(80, "cortaram", "ep12_espada", -15)
fx(81, "mordeu", "ep08_taiko", -16)
pausa(80, 0.6); pausa(82, 0.8); pausa(85, 0.6); pausa(88, 0.8); pausa(93, 0.6)

# ================================================================ PARTE 4 — o demônio que virou deus
capitulo(94, 4, "O demônio que virou deus", "903", RP + "m_michizane_trovao.jpg", real("m_raijin_momoyogusa"))
C(95, kj(real("m_raijin_biombo"), "和魂 · 荒魂", 0.5, 0.18, "luz", "o lado calmo · o lado bravo", atraso=1.0))
C(96, det("m_raijin_biombo", ((0.6, 0.4), (0.55, 0.4)), (1.4, 1.5)))
C(97, det("m_raijin_momoyogusa", ((0.5, 0.4), (0.5, 0.35)), (1.3, 1.5)))
C(98, real("m_michizane_retrato"))
C(99, det("m_michizane_retrato", ((0.5, 0.35), (0.5, 0.3)), (1.3, 1.5)))
C(100, real("m_michizane_trovao"))
C(101, real("m_tenjin_engi"))
C(102, det("m_tenjin_engi", ((0.5, 0.4), (0.5, 0.6)), (1.4, 1.5)))
C(103, kj(real("m_michizane_ator"), "天神", 0.82, 0.5, "luz", "Tenjin · o deus dos estudantes", atraso=0.6))
kanji_som(103, "Tenjin")
C(104, kj(real("hyakki_tsukumogami"), "付喪神", 0.14, 0.5, "luz", "tsukumogami · o objeto que ganha alma", atraso=1.2))
C(105, det("hyakki_tsukumogami", ((0.2, 0.5), (0.4, 0.5)), (1.3, 1.35)))
C(106, det("hyakki_tsukumogami", ((0.6, 0.5), (0.8, 0.5)), (1.3, 1.35)))
C(107, real("hyakki_tsukumogami"))   # 24/11: o desfile de 500 anos é o Tsukumogami emaki (não o Casamento)
C(108, det("hyakki_tsukumogami", ((0.75, 0.5), (0.55, 0.5)), (1.35, 1.4)))
fx(100, "raio", "ep12_trovao", -14)
pausa(97, 0.8); pausa(100, 0.4); pausa(103, 0.8); pausa(108, 0.8)

# ================================================================ PARTE 5 — as regras
capitulo(109, 5, "As regras", "como sobreviver", RP + "sekien_kappa.jpg", casamento(18))
C(110, kj(casamento(24), "掟", 0.2, 0.5, "sangue", "a regra", tam=0.3, atraso=0.4))
kanji_som(110, "regra")
C(111, real("sekien_kappa"))
C(112, det("sekien_kappa", ((0.5, 0.6), (0.5, 0.55)), (1.3, 1.45)))
C(113, det("sekien_kappa", ((0.5, 0.45), (0.5, 0.4)), (1.6, 1.8)))
C(114, IAk("N01_nurikabe_estrada", ficha("NURIKABE\nA parede invisível que fecha o caminho à noite", "NURIKABE"), "塗壁", "nurikabe · a parede invisível"))
C(115, IA("N02_nurikabe_bastao", casamento(30)))
C(116, real("sekien_satori"))
C(117, det("sekien_satori", ((0.45, 0.45), (0.45, 0.4)), (1.4, 1.6)))
C(118, real("sekien_rokurokubi"))
C(119, det("sekien_rokurokubi", ((0.5, 0.35), (0.5, 0.3)), (1.5, 1.7)))
C(120, IAk("N03_jorogumo_cachoeira", ficha("JORŌGUMO\nA aranha que vira mulher · cachoeira de Jōren, Izu", "JORŌGUMO"), "絡新婦", "jorōgumo · a aranha que vira mulher"))
C(121, real("m_festa_sake"))   # a festa de saquê (Kunichika)
C(122, IA("N04_lenhador_teia_futon", det("m_tsuchigumo_noh", ((0.5, 0.5), (0.5, 0.45)), (1.1, 1.2))))
C(123, real("m_tengu_rei"))
C(124, det("m_tengu_rei", ((0.5, 0.4), (0.5, 0.35)), (1.3, 1.4)))
pausa(113, 0.6); pausa(115, 0.6); pausa(117, 0.6); pausa(119, 0.6); pausa(122, 1.2); pausa(124, 0.6)

# ================================================================ PARTE 6 — os piores
capitulo(125, 6, "Os piores", "1251 · 2022", RP + "ushioni_rolo.jpg", real("nureonna_7"))
C(126, real("nureonna_sekien"))
C(127, det("nureonna_7", ((0.5, 0.3), (0.5, 0.45)), (1.3, 1.4)))
C(128, det("nureonna_sekien", ((0.5, 0.5), (0.5, 0.45)), (1.4, 1.6)))
C(129, kj(real("ushioni_rolo"), "牛鬼", 0.84, 0.5, "sangue", "ushi-oni", atraso=0.6))
kanji_som(129, "ushi-oni")
C(130, ficha("TEMPLO SENSŌ-JI · ANO DE 1251\nCrônica Azuma Kagami: 24 monges doentes, 7 mortos", "7 MORTOS"))
C(131, real("ushioni_sekien"))
C(132, det("ushioni_rolo", ((0.5, 0.55), (0.5, 0.5)), (1.4, 1.6)))
C(133, real("tsuchigumo_rijks"))
C(134, rolo("tsuchigumo_14"))
C(135, real("tamamo_xilo"))
C(136, real("tamamo_rijks"))
C(137, det("tamamo_rijks", ((0.5, 0.3), (0.5, 0.25)), (1.3, 1.5)))
C(138, kj(det("tamamo_xilo", ((0.5, 0.4), (0.5, 0.35)), (1.3, 1.5)), "九尾", 0.16, 0.5, "sangue", "a raposa de nove caudas", atraso=1.0))
kanji_som(138, "raposa")
C(139, real("pedra_tochigi"))
C(140, kj(real("pedra_2018"), "殺生石", 0.84, 0.5, "sangue", "Sesshō-seki · a pedra que mata", selo="死", atraso=0.4))
kanji_som(140, "Sesshō-seki")
C(141, real("pedra_2022"))
C(142, real("pedra_rachada"))
C(143, det("pedra_rachada", ((0.5, 0.5), (0.5, 0.45)), (1.1, 1.2)))
C(144, det("pedra_2022", ((0.5, 0.5), (0.5, 0.45)), (1.1, 1.2)))
C(145, det("pedra_rachada", ((0.5, 0.45), (0.5, 0.4)), (1.3, 1.6)))
amb(125, "ep12_mar_noite", -24); amb(133, "nenhum")
fx(127, "pesar", "sub_drop", -20)
fx(134, "crânios", "ep08_taiko", -16)
fx(141, "rachou", "ep12_pedra_racha", -14)
pausa(128, 0.8); pausa(132, 0.8); pausa(134, 1.0); pausa(141, 0.6); pausa(145, 1.2)

# ================================================================ PARTE 7 — o desfile dos cem demônios
capitulo(146, 7, "O desfile dos cem demônios", "956", RP + "kyosai_6.jpg", casamento(36))
C(147, kj(real("kyosai_6"), "百鬼夜行", 0.12, 0.5, "luz", "Hyakki Yagyō · o desfile noturno dos cem demônios", selo="百", atraso=0.6))
kanji_som(147, "Hyakki")
C(148, det("kyosai_6", ((0.3, 0.5), (0.6, 0.5)), (1.3, 1.35)))
C(149, rolo("ROLO_hyakki_aic"))
C(150, real("kyosai_7"))
C(151, det("kyosai_7", ((0.6, 0.5), (0.4, 0.5)), (1.3, 1.35)))
C(152, real("kyosai_8"))
C(153, ficha("KATASHIHAYA, EKASENIKURINI, TAMERUSAKE…\nA reza contra o desfile dos cem demônios", "KATASHIHAYA"))
C(154, det("kyosai_8", ((0.4, 0.5), (0.6, 0.5)), (1.3, 1.35)))
C(156, kj(real("sekien_kamaitachi"), "鳥山石燕", 0.84, 0.5, "luz", "Toriyama Sekien · 1776", atraso=0.8))
C(157, real("sekien_yamauba"))
C(158, real("m_yamauba"))
C(159, real("ritual_sekien"))
pausa(148, 0.8); pausa(152, 0.6); pausa(155, 0.6); pausa(159, 2.0)

# ================================================================ A HISTÓRIA — a sétima noite (ilustrações pedidas, sem rosto)
capitulo(160, 0, "A sétima noite", "hoje", RP + "kifune_3.jpg",
         IA("H01_fabrica_noite", det("kifune_1", ((0.5, 0.5), (0.5, 0.45)), (1.0, 1.08))))
C(161, IA("H02_bosque_santuario", det("kifune_2", ((0.5, 0.6), (0.5, 0.5)), (1.05, 1.15))))
C(162, IA("H03_tres_chamas_arvores", det("ritual_sekien", ((0.4, 0.3), (0.4, 0.25)), (1.6, 1.8))))
C(164, IA("H04_tronco_escuro", det("m_ushinokoku", ((0.85, 0.6), (0.85, 0.5)), (1.4, 1.6))))
C(165, IA("H05_rua_de_cima", det("kifune_1", ((0.5, 0.4), (0.5, 0.3)), (1.1, 1.2))))
chat(166, {"de": "Tati", "texto": "gente olha isso no santuário do lado da firma 😨", "hora": "07:12", "apos": 0.3},
     {"de": "Tati", "tipo": "foto", "imagem": "reais_prontos/ritual_mulher.jpg" if not (AQUI / "imagens" / "H06_boneco_foto.jpg").exists()
      else "imagens/H06_boneco_foto.jpg", "hora": "07:12", "apos": 1.4})
C(167, IA("H07_papel_data", det("ritual_mulher", ((0.3, 0.5), (0.28, 0.45)), (1.6, 1.8))))
C(169, IA("H08_celular_pesquisa", real("ritual_sekien")))
C(170, ficha("RITUAL DA HORA DO BOI\nSete noites seguidas · a terça-feira foi a quinta", "a quinta"))
C(171, det("ritual_sekien", ((0.6, 0.3), (0.6, 0.25)), (1.4, 1.5)))
C(172, kj(real("ritual_mulher"), "見るな", 0.15, 0.5, "sangue", "não seja visto", selo="呪", atraso=0.4))
kanji_som(172, "vir")
C(173, IA("H09_muro_noite", det("kubizuka_1", ((0.5, 0.5), (0.5, 0.45)), (1.0, 1.1))))
C(175, IA("H10_celular_na_mao", det("kifune_3", ((0.5, 0.5), (0.5, 0.45)), (1.2, 1.3))))
C(177, IA("H03_tres_chamas_arvores", det("ritual_sekien", ((0.4, 0.3), (0.4, 0.25)), (1.6, 1.8))))
C(178, IA("H11_lanterna_feixe", det("ritual_sekien", ((0.4, 0.35), (0.42, 0.33)), (2.0, 2.3))))
C(179, IA("H12_coroa_velas_costas", det("hashihime_sekien", ((0.45, 0.3), (0.45, 0.28)), (1.8, 2.1))))
C(181, IA("H13_escuro", real("hannya_preto", (1.04, 1.1))))
C(182, IA("H14_martelo_no_chao", det("ritual_mulher", ((0.6, 0.5), (0.6, 0.45)), (1.4, 1.5))))
C(183, IA("H15_chamas_apagando", det("ritual_sekien", ((0.4, 0.3), (0.4, 0.3)), (1.6, 1.6))))
C(184, IA("H16_cadeira_vazia", det("kifune_1", ((0.5, 0.5), (0.5, 0.45)), (1.0, 1.1))))
C(187, IA("H02_bosque_santuario", det("kifune_2", ((0.5, 0.6), (0.5, 0.5)), (1.05, 1.15))))
C(188, IA("H17_prego_novo", det("m_ushinokoku", ((0.85, 0.75), (0.85, 0.65)), (1.4, 1.6))))
C(190, IA("H18_papel_outra_data", det("ritual_mulher", ((0.3, 0.5), (0.28, 0.45)), (1.6, 1.8))))
C(192, real("ritual_sekien", (1.0, 1.08)))
C(194, IA("H19_arvore_vazia_madrugada", det("kifune_2", ((0.5, 0.5), (0.5, 0.42)), (1.0, 1.1))))
amb(161, "ep08_campo_noite", -22); amb(166, "nenhum"); amb(169, "ep08_campo_noite", -26)
fx(164, "som", "ep12_martelo_prego", -17, atraso=0.5)
fx(177, "martelo", "ep12_martelo_prego", -15)
fx(178, "lanterna", "ep11_lanterna_clique", -14)
fx(181, None, "sub_drop", -18, atraso=0.2)
fx(188, "prego", "ep12_martelo_prego", -18)
pausa(163, 0.6); pausa(168, 1.2); pausa(176, 0.8); pausa(180, 1.4); pausa(181, 1.6); pausa(186, 1.2); pausa(191, 1.2)
pausa(192, 0.8); pausa(194, 1.6)

# ================================================================ FECHO — o Vigia
C(195, vigia((1.0, 1.04)))
C(198, real("ritual_sekien", (1.0, 1.06)))
C(199, det("m_ushinokoku", ((0.85, 0.6), (0.85, 0.55)), (1.4, 1.6)))
C(200, real("hannya_preto", (1.0, 1.08)))
C(202, vigia((1.04, 1.1), ((0.45, 0.48), (0.43, 0.46))))
amb(195, "nenhum")
pausa(195, 1.6)

# respiro entre as frases e no começo de cada parte; a trilha e o ambiente seguem por baixo (nunca silêncio)
for _i in range(1, len(falas)):
    pausa(_i, 0.45)
for _b in batidas:
    if _b.get("ambiente", {}).get("som") == "nenhum":
        _b["ambiente"] = {"som": "ep08_campo_noite", "volume_db": -36}

# ================================================================ VINHETA FIXA DE INSCRIÇÃO
batidas.append({"fala": F.VINHETA, "cta_inicio": True, "sem_legenda": True, "ambiente": {"som": "nenhum"},
                "musica": {"som": "vinheta_ultimo_abrigo", "volume_db": -20}})

TRILHA_SOM = "ep12_trilha"
voz = "audio/voz_com_vinheta_limpa.wav"
roteiro = {
    "modo": "cenas", "formato": "16:9", "tema": "vigia", "avatar": "vigia_hd",
    "voz_arquivo": voz,
    "transcrever_pedacos": 75,
    "alinhamento_forcado": True,
    "cintilar": 0.03, "apertar_pausas": False, "digitacao_db": -19,
    "cena_minima": 4.0,
    "vigia_padrao": False,
    "cauda": 1.6, "chuva": 0, "grao": 0.16,
    "mix": {"musica_ganho_db": 12, "fundo_sob_voz": -8, "efeitos_sob_voz": -4, "voz_pro": True, "fundo_bolso": True,
            "efeitos_pico_max": -3},
    "legendas": {"destaques": ["Japão", "oni", "yōkai", "demônio", "regra", "Hashihime", "Shuten-dōji", "Tenjin", "kimon",
                               "Sesshō-seki", "Hyakki Yagyō", "Camila", "sete noites", "maldição", "rosto"]},
    "ambiente_inicial": [{"som": "ep08_campo_noite", "volume_db": -22}],
    "musica": {"som": TRILHA_SOM, "volume_db": -27},   # 24/11: em destaque, mas 10 dB abaixo da voz (revisão do rascunho 1)
    "titulo_ep": {"antes_da_batida": 12, "linhas": ["O VIGIA · EPISÓDIO 12", "OS DEMÔNIOS DO JAPÃO", "NÃO QUEREM", "A SUA ALMA"],
                  "vermelho": "A SUA ALMA", "duracao": 5.6, "folga": 1.0, "centro": True},
    "cta": {"titulo": "Não deixe que te vejam.", "canal": "Último Abrigo",
            "subtitulo": "Inscreva-se para mais casos do Vigia",
            "fundo": "../../painel/cenarios/abrigo_16x9.png", "pose": "c_cafe_convite",
            "antes": 0.6, "clique_em": "Inscreva-se", "duracao": 6.0},
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
        if False:   # respiros da trilha: não são compensação
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

    PROTEGE = {1, 2, 3, 4, 5, 7, 8, 17, 18, 19, 11, 40, 46, 81, 126, 200, 128, 134, 141, 163, 168, 172, 176, 178, 179, 180, 181, 188, 191, 192, 194}   # sustos e silêncios: nunca continuar a anterior
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
    """24/11 (usuário: "uma trilha ainda mais bem feita do que a do episódio 8"): a trilha é COMPOSTA sobre os tempos desta
    montagem (trilha/compor_trilha.py): cada seção tem a sua parte e os golpes caem nas palavras. Só recompõe quando o
    plano muda (painel/sons/ep12_trilha.plano)."""
    from gerar import tokens as tk, norm
    cum, T0 = 0.0, []
    for i in range(len(falas)):
        cum += batidas[i].get("pausa_antes_s", 0); T0.append(_ali[_ini[i]][0] + cum)
    fim = _ali[len(sum([tk(f) for f in falas], [])) - 1][1] + cum + 6

    def tw(i, palavra):
        ws = [norm(w) for w in tk(falas[i])]; alvo = norm(palavra)
        k = next((j for j, w in enumerate(ws) if w == alvo or w.startswith(alvo)), 0)
        return round(T0[i] + _ali[_ini[i] + k][0] - _ali[_ini[i]][0], 2)

    M = {"maldicao": tw(7, "maldição"), "atenderam": tw(9, "atenderam"), "correndo": tw(37, "correndo"),
         "nao_mulher": tw(40, "mulher"), "hashihime": tw(43, "Hashihime"), "kimon": tw(59, "kimon"),
         "cortaram": tw(80, "cortaram"), "mordeu": tw(81, "mordeu"), "kubizuka": tw(86, "Kubizuka"),
         "raio": tw(100, "raio"), "tenjin": tw(103, "Tenjin"), "dormiu": tw(122, "Dormiu"), "pesar": tw(127, "pesar"),
         "cranios": tw(134, "crânios"), "rachou": tw(141, "rachou"), "saido": tw(145, "saído"),
         "desfile": tw(147, "Hyakki"), "morria": tw(148, "morria"), "morosuke": tw(150, "Em"), "reza": tw(153, "katashihaya"),
         "bebado": tw(155, "não"), "tres_chamas": tw(163, "Três"), "metal": tw(164, "Metal"), "a_dela": tw(168, "dela"),
         "setima": tw(173, "sétima"), "lanterna": tw(178, "lanterna"), "rosto": tw(180, "rosto"), "seis_anos": tw(181, "Todo"),
         "sumiu": tw(186, "Sumiu"), "prego_novo": tw(188, "prego"), "nao_dela": tw(191, "Não"), "ninguem_viu": tw(194, "ninguém")}
    marcos = [("gancho", 0), ("vigia", 12), ("tema", 15), ("p1", 28), ("p2", 51), ("p3", 71), ("p4", 94), ("p5", 109),
              ("p6", 125), ("p7", 146), ("hist", 160), ("fecho", 195)]
    ini = [0.0] + [T0[i] - (DUR_CARTAO.get(i, CARTAO) if i in CARTOES else 7.2 if i == 12 else 1.0) for _, i in marcos[1:]]
    secoes = [[n, round(ini[k] + (DUR_CARTAO.get(marcos[k][1], CARTAO) if marcos[k][1] in CARTOES else 0), 2), round(ini[k + 1] if k + 1 < len(ini) else fim, 2)]
              for k, (n, _) in enumerate(marcos)]
    cartoes = [[round(T0[i] - DUR_CARTAO.get(i, CARTAO), 2), round(T0[i] - 0.1, 2)] for i in CARTOES]
    fichas = [[round(T0[i] - L, 2), round(T0[i], 2)] for i, L in FICHA_L.items()]   # a voz para: a música segura
    plano = {"secoes": secoes, "marcos": M, "fim": round(fim, 2), "cartoes": cartoes, "fichas": fichas}
    sons = AQUI.parents[1] / "painel" / "sons"
    # a marca leva também o código do compositor: mudar a música (sem mudar os tempos) recompõe
    marca = sons / f"{TRILHA_SOM}.plano"
    txt = json.dumps(plano) + hashlib.md5((AQUI / "trilha" / "compor_trilha.py").read_bytes()).hexdigest()
    if (sons / f"{TRILHA_SOM}.mp3").exists() and marca.exists() and marca.read_text() == txt:
        return
    print("trilha: compondo sobre a montagem…", flush=True)
    (AQUI / "trilha" / "plano.json").write_text(json.dumps(plano))
    subprocess.run([sys.executable, str(AQUI / "trilha" / "compor_trilha.py"), str(AQUI / "trilha" / "plano.json"),
                    str(sons / f"{TRILHA_SOM}.mp3")], check=True)
    marca.write_text(txt)


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
print("ilustrações ainda pedidas (entrou a reserva real):", sorted(set(PEDIDOS)))
print(f"{len(batidas)} falas, {n_cenas} cenas, falas sem cena (continuam a anterior): {sem}")
print("pausa total:", round(sum(b.get("pausa_antes_s", 0) for b in batidas), 1), "s")
