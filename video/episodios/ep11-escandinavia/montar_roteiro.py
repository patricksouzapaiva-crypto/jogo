"""Monta roteiro.json do Ep. 11 — Escandinávia: "Por que você nunca deve entrar na floresta escandinava?" (16/11).
Molde do Ep. 10 (gancho sem Vigia; TEMA, APARTE e FECHO com o Vigia; 4 capítulos; a história do Lucas e do Rafael; o fecho).
Identidade: os cartões em XILOGRAVURA VIVA (cartoes.py: a pedra rúnica com a serpente e a gravura do capítulo), a trilha de
ORQUESTRA gravada (trilha/compor_orquestra.py: a polska em ré menor, feita sob medida para os tempos desta montagem), a câmera
de segurança no celeiro (cctv), o obturador nos cortes secos e o material REAL com crédito (reais_prontos/: Tollund,
Grauballe, Olaus Magnus, Midvinterblot, Rök).
Regras: Vigia só no TEMA/APARTE/FECHO; nenhum rosto de IA; cena >= 3 s; legenda só em português; nórdico só nas fichas.
Uso: python3 montar_roteiro.py → roteiro.json"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import falas as F

AQUI = Path(__file__).parent
falas, PERS, SEC, PAUSAS, _ = F.ler()
assert len(falas) == 136 and PERS.get(96) == "lucas" and PERS.get(110) == "lucas", "o ROTEIRO.md mudou: rever os índices"
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




# ================================================================ Ep. 11 — material
RP = "reais_prontos/"
CL = "clipes/flow/"
DATA = "21-11-2025"


def IA(cod, v=1):
    pasta = AQUI / "imagens" / "cenas" / cod
    f = next(iter(sorted(pasta.glob(f"{cod}_0{v}.*"))), None)
    assert f, f"imagem faltando: {cod} v{v}"
    return str(f.relative_to(AQUI))


def real(nome, z=(1.0, 1.035), **kw):
    """Foto real do Commons já no papel de dossiê com o crédito (preparar_midia.py): zoom mínimo, o crédito não sai."""
    return {"imagem": RP + nome + ".jpg", "zoom": list(z), **kw}


def clipe(nome, ate=None, inicio=0.0, cam=None, hora=None, queda=None, z=(1.0, 1.03), **kw):
    """Clipe do Flow (clipes/flow/V0x_<tomada>_*.mp4). ate: corta antes de erro da IA. cam/hora: câmera de segurança."""
    arq = next(iter(sorted((AQUI / CL).glob(nome + "_*.mp4"))))
    arq = CL + arq.name
    if ate:
        saida = AQUI / CL / f"{Path(arq).stem}_ate{ate}.mp4"
        if not saida.exists():
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(AQUI / arq), "-t", str(ate), "-an", "-c:v", "libx264",
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
    c = dict(c); c["entrada"] = "obturador"; c["duracao_entrada"] = dur
    return c


def obt_som(i, em=None, db=-15):
    fx(i, em, "ep10_obturador", db, atraso=-0.3 if em is None else -0.15)


def seco(c):
    c = dict(c); c["entrada"] = "corte"
    return c


def zoom(nome, z=(1.0, 1.08), foco=((0.5, 0.5), (0.5, 0.48)), **kw):
    return img(nome, z, foco, **kw)


TRILHA_SOM = "ep11_trilha"
TRILHA = {"som": TRILHA_SOM, "volume_db": -27}
CARTAO = 7.6
CARTOES_T = []


def capitulo(i, n, cena, em):
    """Cartão do capítulo = a XILOGRAVURA VIVA (cartoes.py): vídeo pronto de 7,6 s com a música do capítulo (orquestra).
    A trilha do episódio já tem um buraco no lugar do cartão (compor_orquestra.episodio)."""
    cap = {"video": f"cartoes/cap{n}.mp4", "zoom": [1.0, 1.0], "antecipar": CARTAO, "antecipar_fixo": True,
           "entrada": "corte", "tipo_cartao": True, "congelar": True, "sem_look": True}
    cena = dict(cena); cena["entrada"] = "fundir"; cena["duracao_entrada"] = 0.9
    C(i, cap, (cena, em))
    pausa(i, CARTAO - 0.2)
    som = AQUI / "cartoes" / f"cap{n}_som.wav"
    if not som.exists():
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(AQUI / "cartoes" / f"cap{n}.mp4"), "-vn", "-ac", "2",
                        "-ar", "48000", str(som)], check=True)
    fx(i, None, f"cartao{n}", -13, atraso=-CARTAO + 0.05, arquivo=str(som))
    CARTOES_T.append(i)


HIST = []


def chat(i, *novas, sons=True, legenda=True):
    msgs = [dict(m, apos=-30) for m in HIST[-6:]]
    for m in novas:
        m = dict(m); m.setdefault("apos", 0.3)
        msgs.append(m); HIST.append({k: v for k, v in m.items() if k not in ("apos", "em", "digitando")})
        if sons and "em" not in m:
            fx(i, None, "ep08_msg", -19, atraso=m["apos"])
        elif sons:
            fx(i, m["em"], "ep08_msg", -19)
    C(i, {"tipo": "chat", "grupo": "Expedição Norte ❄️", "membros": "Lucas, Rafael, Thiago, Bruna", "mensagens": msgs})
    if not legenda:
        batidas[i]["sem_legenda"] = True


# ================================================================ GANCHO — sem Vigia
C(0, clipe("V01_b"))
C(1, seco(real("C1_01_real")))
C(2, seco(zoom(IA("G02a", 2), (1.0, 1.06), ((0.4, 0.5), (0.38, 0.48)))))
C(3, obt(zoom(IA("G02b", 2), (1.0, 1.06))), (obt(zoom(IA("G02c", 1), (1.0, 1.08), ((0.55, 0.45), (0.55, 0.38)))), "correr"))
obt_som(3); obt_som(3, "correr")
amb(0, "ep11_vento_pinheiros", -22)
fx(0, None, "ep11_passos_neve", -24, atraso=0.2, ate=6.0, saida=1.5)
fx(2, None, "ep11_kulning_longe", -24, atraso=-0.6, ate=7.0, saida=2.5)
fx(3, "correr", "ep11_impacto_grave", -16)
pausa(1, 0.4); pausa(3, 0.6); pausa(4, 1.0)

# ================================================================ TEMA — Vigia
C(4, vigia((1.0, 1.04)))
saida_lenta(4, 5.4, dur=2.2)
batidas[4]["cena"].update({"antecipar": 7.2, "antecipar_fixo": True})   # o título aparece sobre o Vigia, com a polska
C(7, c3(IA("T01", 3), "entrar", (0.5, 0.55), 0.9, 0.2, atmos={"neblina": 0.3}))
C(8, zoom(IA("T01", 7), (1.0, 1.07), ((0.4, 0.55), (0.42, 0.55))))
C(9, real("C2_blot_01"))
C(10, ficha("BLÓT\nRituais nórdicos antigos de sacrifício de sangue", "BLÓT"))
amb(4, "nenhum"); amb(7, "ep11_vento_pinheiros", -28); amb(9, "nenhum")
pausa(9, 0.4); pausa(11, 0.8)

# ================================================================ CAPÍTULO 1 — os corpos do pântano e a árvore de Uppsala
capitulo(11, 1, real("C1_tollund_01"), "Em")
C(16, obt(real("C1_01_real")))
obt_som(16)
C(17, real("C1_tollund_04"))
C(18, c3(IA("C1_01", 1), "entrar", (0.5, 0.55), 0.9, 0.2, atmos={"neblina": 0.4}))
C(19, obt(real("C1_02_real")))
obt_som(19)
C(20, ficha("CORPOS DO PÂNTANO\nVítimas de sacrifícios pagãos preservadas na turfa gelada", "CORPOS DO PÂNTANO"))
C(21, real("C1_04_real"))
C(22, ficha("TEMPLO DE UPPSALA · SÉCULO XI\nRelato de Adam de Bremen", "TEMPLO DE UPPSALA"))
C(23, c3(IA("C1_02", 2), "entrar", (0.5, 0.45), 0.9, 0.2, atmos={"neblina": 0.3}))
C(24, zoom(IA("C1_02", 1), (1.0, 1.07), ((0.5, 0.55), (0.5, 0.5))))
C(31, zoom(IA("C1_02", 2), (1.08, 1.2), ((0.25, 0.35), (0.22, 0.3))))
amb(16, "nenhum"); amb(18, "ep11_vento_pinheiros", -28); amb(21, "nenhum"); amb(23, "ep11_mata_inverno_noite", -28)
fx(31, "árvores", "sub_drop", -21)
pausa(18, 0.4); pausa(20, 0.6); pausa(22, 0.6); pausa(31, 0.4); pausa(32, 0.8)

# ================================================================ CAPÍTULO 2 — a Águia de Sangue e o inverno sem fim
capitulo(32, 2, zoom(IA("C2_01", 2), (1.0, 1.08), ((0.5, 0.5), (0.5, 0.45))), "Quando")
C(33, ficha("FIMBULVETR\nO inverno de três anos seguidos sem verão", "FIMBULVETR"))
C(34, c3(IA("T01", 5), "entrar", (0.5, 0.5), 0.9, 0.2, atmos={"neblina": 0.4}))
C(40, clipe("V02_a"))
C(41, clipe("V02_b"), (c3(IA("C2_02", 1), "entrar", (0.4, 0.55), 0.9, 0.3, atmos={"neblina": 0.5}), "atiravam"))
C(44, zoom(IA("C2_01", 1), (1.0, 1.08), ((0.3, 0.5), (0.45, 0.5))))
C(45, ficha("BLÓÐÖRN · A ÁGUIA DE SANGUE\nExecução ritual das sagas nórdicas", "BLÓÐÖRN"))
C(46, zoom(IA("C2_01", 1), (1.15, 1.3), ((0.5, 0.55), (0.5, 0.58))))
C(47, zoom(IA("C2_01", 3), (1.0, 1.08), ((0.5, 0.5), (0.5, 0.58))))
C(48, zoom(IA("C2_01", 3), (1.1, 1.22), ((0.5, 0.35), (0.5, 0.3))))
amb(33, "nenhum"); amb(34, "ep11_nevasca", -28); amb(44, "nenhum")
fx(40, None, "ep11_vento_pinheiros", -24, ate=12.0, saida=3.0)
fx(47, "machado", "ep11_impacto_grave", -18)
pausa(40, 0.4); pausa(45, 0.6); pausa(46, 0.8); pausa(48, 0.6); pausa(53, 0.8)

# ================================================================ CAPÍTULO 3 — as criaturas da mata e o filho bastardo
capitulo(53, 3, real("C3_01_real"), "Mas")
C(54, real("C3_rok_03"))
C(55, c3(IA("G01", 1), "entrar", (0.5, 0.5), 0.9, 0.2, atmos={"neblina": 0.3}))
C(56, c3(IA("C3_01", 1), "entrar", (0.5, 0.45), 0.9, 0.2, atmos={"neblina": 0.4}))
C(59, c3(IA("C3_02", 1), "entrar", (0.55, 0.45), 0.9, 0.2), (zoom(IA("C3_02", 2), (1.0, 1.08), ((0.4, 0.6), (0.38, 0.62))), "guardam"))
C(63, c3(IA("C3_03", 2), "entrar", (0.55, 0.4), 0.9, 0.2))
C(64, zoom(IA("C3_03", 1), (1.0, 1.08), ((0.5, 0.35), (0.5, 0.3))))
C(65, ficha("JÖTNAR\nOs gigantes primordiais e divindades sombrias da natureza", "JÖTNAR"))
C(67, zoom(IA("T01", 1), (1.0, 1.07), ((0.4, 0.55), (0.38, 0.55))))
C(68, c3(IA("G02b", 1), "entrar", (0.5, 0.5), 0.9, 0.3))
amb(54, "nenhum"); amb(55, "ep11_mata_inverno_noite", -27); amb(65, "nenhum"); amb(67, "ep11_vento_pinheiros", -28)
fx(63, None, "ep11_rosnado", -26, atraso=0.6, ate=4.0, saida=1.5)
fx(68, "oferecido", "ep11_impacto_grave", -17)
pausa(56, 0.4); pausa(63, 0.6); pausa(65, 0.6); pausa(68, 0.6); pausa(69, 0.8)

# ================================================================ CAPÍTULO 4 — quando o culto voltou para a tela
capitulo(69, 4, c3(IA("C4_01", 1), "entrar", (0.5, 0.45), 0.9, 0.3, atmos={"neblina": 0.4}), "Nos")
C(70, ficha("THE RITUAL (O RITUAL)\n2017 · Dir. David Bruckner", "THE RITUAL"))
C(73, c3(IA("C4_01", 2), "entrar", (0.5, 0.4), 0.8, 0.1))
C(77, ficha("MIDSOMMAR\n2019 · Dir. Ari Aster", "MIDSOMMAR"))
C(78, zoom(IA("C4_01", 2), (1.08, 1.2), ((0.5, 0.45), (0.5, 0.4))))
amb(70, "nenhum"); amb(73, "ep11_vento_pinheiros", -30); amb(77, "nenhum")
pausa(73, 0.4); pausa(78, 0.6); pausa(79, 1.0)

# ================================================================ APARTE — Vigia: o tributo
C(79, vigia((1.0, 1.04)))
C(83, c3(IA("G02b", 2), "entrar", (0.5, 0.5), 0.9, 0.2))
C(84, zoom(IA("H03", 1), (1.0, 1.06), ((0.5, 0.55), (0.52, 0.5))))
C(85, vigia((1.04, 1.1), ((0.45, 0.48), (0.43, 0.46))))
amb(79, "nenhum"); amb(83, "ep11_vento_pinheiros", -30); amb(85, "nenhum")
fx(86, "sacrifício", "ep11_impacto_grave", -18)
pausa(83, 0.6); pausa(85, 0.4)
pausa(87, 3.2)   # respiro: a polska sobe sozinha antes da história (pedido do usuário: a trilha em destaque)

# ================================================================ LUCAS E RAFAEL — 1: a nevasca em Hälsingland
C(87, zoom(IA("H01", 2), (1.0, 1.06), ((0.5, 0.55), (0.5, 0.5))))
C(88, c3(IA("T01", 4), "entrar", (0.5, 0.5), 0.9, 0.2, atmos={"neblina": 0.3}))
chat(89, {"de": "Lucas", "tipo": "foto", "imagem": IA("H01", 7), "hora": "15:02", "apos": 0.4},
     {"de": "Lucas", "texto": "nevasca do nada aqui, a trilha sumiu 😬", "hora": "15:03", "apos": 1.6},
     {"de": "Lucas", "texto": "sem GPS. vamos andando até achar abrigo", "hora": "15:41", "apos": 3.2})
C(90, zoom(IA("H01", 5), (1.0, 1.06), ((0.5, 0.5), (0.5, 0.45))), (c3(IA("H03", 3), "entrar", (0.5, 0.5), 0.8, 0.2), "avistarem"))
C(91, c3(IA("H03", 2), "entrar", (0.55, 0.5), 0.9, 0.2))
C(92, zoom(IA("H04", 2), (1.0, 1.06), ((0.5, 0.5), (0.5, 0.48))))
chat(96, {"de": "Lucas", "tipo": "foto", "imagem": IA("H04", 1), "hora": "19:20", "apos": 0.3},
     {"de": "Lucas", "tipo": "audio", "duracao": "0:13", "hora": "19:21", "apos": 1.2})
C(97, zoom(IA("H04", 1), (1.0, 1.08), ((0.5, 0.6), (0.5, 0.62))))
C(98, zoom(IA("H04", 1), (1.1, 1.2), ((0.35, 0.55), (0.32, 0.55))))
C(99, zoom(IA("H03", 4), (1.0, 1.06), ((0.55, 0.5), (0.55, 0.48))))
amb(87, "ep11_vento_pinheiros", -26); amb(89, "ep11_nevasca", -28); amb(91, "ep11_vento_pinheiros", -28); amb(96, "nenhum"); amb(97, "nenhum")
fx(87, None, "ep11_passos_neve", -24, ate=8.0, saida=2.0)
pausa(88, 0.4); pausa(91, 0.6); pausa(97, 0.6); pausa(99, 0.4); pausa(100, 1.6)

# ================================================================ LUCAS E RAFAEL — 2: o celeiro
C(100, c3(IA("H03", 4), "entrar", (0.6, 0.5), 0.9, 0.2, atmos={"neblina": 0.3}))
C(104, zoom(IA("H03", 1), (1.06, 1.14), ((0.55, 0.5), (0.58, 0.48))))
C(105, zoom(IA("H02_H07", 1), (1.0, 1.04)), (obt(zoom(IA("H05", 1), (1.0, 1.06), ((0.4, 0.45), (0.4, 0.42)))), "runa"))
obt_som(105, "runa")
C(106, c3(IA("H09", 1), "entrar", (0.5, 0.6), 0.8, 0.2))
C(107, clipe("V04_c", cam="CAM 02 - CELEIRO // -18°C", hora="02:24:51"), (clipe("V04_d", cam="CAM 02 - CELEIRO // -18°C", hora="02:24:58"), "ajoelhados"))
C(108, obt(zoom(IA("H08", 2), (1.0, 1.06), ((0.5, 0.45), (0.5, 0.4)))), (obt(zoom(IA("H08", 6), (1.0, 1.06))), "Rafael"))
obt_som(108); obt_som(108, "Rafael")
chat(110, {"de": "Lucas", "tipo": "video", "imagem": IA("H08", 3), "hora": "02:27", "apos": 0.2},
     {"de": "Lucas", "tipo": "audio", "duracao": "0:08", "hora": "02:27", "apos": 1.0})
amb(100, "ep11_mata_inverno_noite", -26); amb(107, "nenhum"); amb(108, "nenhum"); amb(110, "ep11_vento_pinheiros", -30)
fx(100, None, "ep11_kulning_longe", -22, atraso=1.5, ate=9.0, saida=3.0)
fx(104, None, "ep11_coracao", -26, ate=7.0, saida=2.0)
fx(106, None, "ep11_passos_neve", -22, ate=6.0, saida=1.5)
fx(107, None, "ep10_cctv_estatica", -27, ate=0.8, saida=0.3)
pausa(105, 0.6); pausa(107, 0.6); pausa(110, 0.6); pausa(111, 1.2)

# ================================================================ LUCAS E RAFAEL — 3: o que espera entre os pinheiros
C(111, zoom(IA("H08", 5), (1.0, 1.05)))
C(112, seco(cctv(zoom(IA("H06", 2), (1.0, 1.02)), "CAM 02 - CELEIRO // -18°C", "02:28:03")))
C(113, clipe("V05_c"))
C(114, clipe("V05_d"))
C(115, seco(zoom(IA("H10", 2), (1.0, 1.04))))
C(116, zoom(IA("H10", 1), (1.0, 1.08), ((0.45, 0.6), (0.4, 0.62))))
C(117, clipe("V05_a"))
C(118, zoom(IA("H09", 2), (1.0, 1.04)))
C(119, c3(IA("H11", 1), "entrar", (0.5, 0.5), 0.6, 0.2))
C(120, obt(zoom(IA("H11", 2), (1.0, 1.05))), (clipe("V06_c"), "coisa"))
obt_som(120)
C(121, clipe("V06_b"))
C(122, clipe("V06_a"), (c3(IA("H11", 2), "entrar", (0.5, 0.4), 0.7, 0.2), "altar"))   # 17/11: V06_d saiu (lanterna presa na criatura)
amb(111, "nenhum"); amb(113, "ep11_nevasca", -24); amb(115, "nenhum"); amb(116, "ep11_vento_pinheiros", -28); amb(118, "nenhum")
fx(111, "galho", "ep11_galho_quebra", -14)
fx(112, None, "ep10_cctv_estatica", -25, ate=0.6, saida=0.2)
fx(113, None, "ep11_passos_neve_correndo", -18, ate=10.0, saida=2.0)
fx(119, None, "ep11_lanterna_clique", -16, atraso=1.0)
fx(120, "coisa", "ep11_rosnado", -20)
pausa(112, 1.0); pausa(115, 0.6); pausa(117, 0.6); pausa(118, 1.6); pausa(120, 0.8); pausa(122, 0.4)
pausa(123, 4.4)   # o golpe do clímax, o silêncio de 1,8 s e o grave voltando antes do resgate

# ================================================================ FECHO — Vigia
C(123, c3(IA("H09", 2), "sair", (0.5, 0.6), 0.8, 0.2, atmos={"neblina": 0.3}))
C(124, c3(IA("T01", 6), "entrar", (0.5, 0.5), 0.8, 0.2, atmos={"neblina": 0.4}))
C(125, zoom(IA("H02_H07", 2), (1.0, 1.06), ((0.55, 0.55), (0.6, 0.55))))
C(128, vigia((1.0, 1.04)))
C(130, zoom(IA("F01", 1), (1.0, 1.06), ((0.5, 0.5), (0.5, 0.45))))
C(131, zoom(IA("H03", 4), (1.06, 1.14), ((0.7, 0.5), (0.72, 0.5))))
C(132, zoom(IA("F03", 1), (1.0, 1.07), ((0.5, 0.5), (0.5, 0.45))))
C(133, vigia((1.02, 1.07)))
C(135, vigia((1.08, 1.14), ((0.42, 0.45), (0.4, 0.43))))
amb(123, "ep11_vento_pinheiros", -28); amb(128, "nenhum"); amb(130, "ep11_mata_inverno_noite", -30); amb(133, "nenhum")
fx(135, "cantar", "ep11_kulning_longe", -26, ate=8.0, saida=3.0)
pausa(125, 0.6); pausa(128, 0.8); pausa(132, 0.6); pausa(135, 0.4)


# ================================================================ v2 (17/11) — os trechos novos (ROTEIRO_v2_NOVOS.md)
def TENT(rel):
    return "imagens/tentativas/" + rel


C(12, real("C1_tollund_03"))
C(13, real("C1_tollund_03", z=(1.05, 1.12)))
C(14, ficha("A ÚLTIMA REFEIÇÃO\nMingau de cevada e sementes, horas antes da morte", "A ÚLTIMA REFEIÇÃO"))
C(15, c3(IA("C1_01", 1), "entrar", (0.45, 0.55), 0.8, 0.2, atmos={"neblina": 0.5}))
C(25, zoom(IA("C1_02", 2), (1.0, 1.08), ((0.5, 0.6), (0.5, 0.65))))
C(26, c3(TENT("C2_02_pantano_ou_museu/C2_02_pantano_ou_museu_04.png"), "entrar", (0.5, 0.6), 0.9, 0.2, atmos={"neblina": 0.5}))
C(27, zoom(IA("G01", 2), (1.0, 1.08), ((0.5, 0.45), (0.5, 0.4))))
C(28, ficha("HÁVAMÁL\nO poema de Odin · estrofes 138 e 139", "HÁVAMÁL"))
C(29, c3(IA("C2_01", 2), "entrar", (0.5, 0.35), 0.8, 0.2))
C(30, zoom(IA("G01", 1), (1.0, 1.08), ((0.5, 0.5), (0.5, 0.45))))
C(35, c3(IA("T01", 8), "entrar", (0.5, 0.55), 0.8, 0.2, atmos={"neblina": 0.4}))
C(36, ficha("ANO 536\nO inverno vulcânico que escureceu o hemisfério norte", "ANO 536"))
C(37, zoom(IA("T01", 2), (1.0, 1.08), ((0.5, 0.4), (0.5, 0.35))))
C(38, zoom(IA("T01", 7), (1.05, 1.14), ((0.6, 0.55), (0.62, 0.55))))
C(39, real("C3_rok_02"))
C(42, zoom(IA("C2_02", 1), (1.0, 1.08), ((0.4, 0.5), (0.35, 0.55))))
C(43, zoom(IA("C2_02", 2), (1.06, 1.14), ((0.3, 0.5), (0.3, 0.48))))
C(49, zoom(IA("C2_01", 1), (1.0, 1.08), ((0.25, 0.5), (0.3, 0.5))))
C(50, zoom(TENT("C2_01_composites/C2_01_composites_01.png"), (1.0, 1.08), ((0.35, 0.5), (0.3, 0.5))))
C(51, ficha("A ÁGUIA DE SANGUE · 2022\nEstudo anatômico na revista Speculum: o ritual era possível", "2022"))
C(52, zoom(IA("C2_01", 3), (1.12, 1.24), ((0.5, 0.55), (0.5, 0.6))))
C(57, zoom(TENT("C3_02_repeticoes_da_Skogsra/C3_02_repeticoes_da_Skogsra_01.png"), (1.0, 1.08), ((0.5, 0.45), (0.5, 0.4))))
C(58, zoom(TENT("C3_02_repeticoes_da_Skogsra/C3_02_repeticoes_da_Skogsra_02.png"), (1.0, 1.08), ((0.55, 0.45), (0.55, 0.4))))
C(60, zoom(IA("C3_02", 2), (1.0, 1.08), ((0.4, 0.6), (0.38, 0.62))))
C(61, c3(IA("F03", 2), "entrar", (0.6, 0.45), 0.8, 0.2))
C(62, zoom(IA("C3_02", 1), (1.1, 1.22), ((0.5, 0.4), (0.5, 0.35))))
C(71, zoom(IA("C4_01", 1), (1.06, 1.16), ((0.45, 0.45), (0.45, 0.4))))
C(72, zoom(IA("C3_03", 2), (1.0, 1.1), ((0.55, 0.4), (0.55, 0.35))))
C(74, zoom(TENT("F01_erros/F01_Erro_1_Mastro.png"), (1.0, 1.08)))
C(75, zoom(IA("F01", 2), (1.0, 1.08), ((0.45, 0.5), (0.4, 0.5))))
C(76, zoom(TENT("F01_erros/F01_Erro_3_Mastro.png"), (1.0, 1.1), ((0.5, 0.5), (0.5, 0.45))))
C(93, zoom(IA("H04", 2), (1.06, 1.14), ((0.5, 0.5), (0.5, 0.45))))
C(94, c3(IA("H03", 3), "entrar", (0.5, 0.55), 0.8, 0.2))
C(95, obt(zoom(TENT("H08_repeticoes_da_porta_H05/H08_repeticoes_da_porta_H05_08.png"), (1.0, 1.08), ((0.45, 0.4), (0.45, 0.6)))))
obt_som(95)
C(101, zoom(IA("H03", 1), (1.1, 1.2), ((0.5, 0.5), (0.52, 0.48))))
C(102, ficha("KULNING\nO canto das pastoras suecas para chamar o gado", "KULNING"))
C(103, zoom(IA("H03", 4), (1.08, 1.18), ((0.4, 0.5), (0.38, 0.5))))
C(109, obt(zoom(IA("H08", 4), (1.0, 1.08), ((0.5, 0.35), (0.5, 0.25)))))
obt_som(109)
chat(126, {"de": "Lucas", "tipo": "audio", "duracao": "0:09", "hora": "04:51", "apos": 0.6})
fx(127, "cantando", "ep11_kulning_longe", -22, ate=8.0, saida=3.0)
amb(26, "ep11_vento_pinheiros", -30); amb(28, "nenhum"); amb(36, "nenhum"); amb(37, "ep11_nevasca", -30); amb(51, "nenhum")
amb(52, "ep11_vento_pinheiros", -32); amb(102, "nenhum"); amb(103, "ep11_mata_inverno_noite", -28)
fx(95, "oito", "ep11_gelo_estalo", -20); fx(109, "nona", "ep11_impacto_grave", -15)

# 17/11 (usuário: "está muito rápido" / "pode respirar, mas não pode ficar em silêncio"): respiro entre as frases e
# no fim de cada capítulo; a TRILHA e o AMBIENTE continuam por baixo de toda pausa (nunca "nenhum" num respiro).
for _i in range(1, len(falas)):
    if _i not in (96, 110):          # as falas do Lucas já têm o respiro delas
        pausa(_i, 0.45)
for _i in (SEC["CAPÍTULO 2"], SEC["CAPÍTULO 3"], SEC["CAPÍTULO 4"], SEC["APARTE"], SEC["LUCAS E RAFAEL — 2"], SEC["LUCAS E RAFAEL — 3"]):
    pausa(_i, 2.0)
for _b in batidas:                   # ambiente "nenhum" vira um vento bem baixo: nunca silêncio morto
    if _b.get("ambiente", {}).get("som") == "nenhum":
        _b["ambiente"] = {"som": "ep11_vento_pinheiros", "volume_db": -36}

# ================================================================ VINHETA FIXA DE INSCRIÇÃO
batidas.append({"fala": F.VINHETA, "cta_inicio": True, "sem_legenda": True, "ambiente": {"som": "nenhum"},
                "musica": {"som": "vinheta_ultimo_abrigo", "volume_db": -20}})

voz = "audio/voz_personagens.wav" if (AQUI / "audio" / "voz_personagens.wav").exists() else "audio/voz_com_vinheta_limpa.wav"
roteiro = {
    "modo": "cenas", "formato": "16:9", "tema": "vigia", "avatar": "vigia_hd",
    "voz_arquivo": voz,
    "transcrever_pedacos": 75,
    "alinhamento_forcado": True,
    "look": {"preset": "noite_fria", "forca": 0.8, "halacao": 0.25},
    "cintilar": 0.03, "apertar_pausas": False,
    "cena_minima": 3.0,
    "vigia_padrao": False,
    "cauda": 1.6, "chuva": 0, "grao": 0.14,
    "mix": {"musica_ganho_db": 12, "fundo_sob_voz": -8, "efeitos_sob_voz": -4, "voz_pro": True, "fundo_bolso": True,
            "efeitos_pico_max": -3},
    "legendas": {"destaques": ["Escandinávia", "Blót", "Uppsala", "Tollund", "Fimbulvetr", "Ättestupa", "Águia de Sangue", "Odin",
                               "Skogsrå", "Draugr", "Jötnar", "Midsommar", "O Ritual", "Hälsingland", "Lucas", "Rafael", "Nøkken", "Mare",
                               "pagamento", "sacrifício"]},
    "ambiente_inicial": [{"som": "ep11_vento_pinheiros", "volume_db": -24}],
    "musica": TRILHA,
    "titulo_ep": {"antes_da_batida": 4, "linhas": ["O VIGIA · EPISÓDIO 11", "POR QUE VOCÊ NUNCA DEVE", "ENTRAR NA FLORESTA", "ESCANDINAVA?"],
                  "vermelho": "ESCANDINAVA?", "duracao": 5.6, "folga": 1.0, "centro": True},
    "cta": {"titulo": "Não siga o canto.", "canal": "Último Abrigo",
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

    PROTEGE = {1, 2, 3, 4, 11, 32, 53, 69, 111, 112, 115, 118, 119, 120, 121, 122, 123}   # sustos e silêncios: nunca continuar a anterior
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
    """16/11: a trilha de ORQUESTRA (trilha/compor_orquestra.py episodio) composta sobre os tempos desta montagem: cada
    seção tem sua parte, o golpe do clímax cai na palavra "coisa" (o feixe acerta a criatura) e a trilha abre buraco nos
    cartões. Só recompõe quando o plano muda (painel/sons/ep11_trilha.plano)."""
    from gerar import tokens as tk, norm
    cum, T0 = 0.0, []
    for i in range(len(falas)):
        cum += batidas[i].get("pausa_antes_s", 0); T0.append(_ali[_ini[i]][0] + cum)
    fim = _ali[-1][1] + cum + 8
    ws = [norm(w) for w in tk(falas[120])]; k = next(j for j, w in enumerate(ws) if w.startswith("coisa"))
    climax = round(T0[120] + _ali[_ini[120] + k][0] - _ali[_ini[120]][0], 2)
    cartoes = [[round(T0[i] - CARTAO, 2), round(T0[i] - 0.15, 2)] for i in CARTOES_T]
    marcos = [("gancho", 0), ("tema", SEC["TEMA"]), ("cap1", SEC["CAPÍTULO 1"]), ("cap2", SEC["CAPÍTULO 2"]), ("cap3", SEC["CAPÍTULO 3"]),
              ("cap4", SEC["CAPÍTULO 4"]), ("aparte", SEC["APARTE"]), ("hist1", SEC["LUCAS E RAFAEL — 1"]),
              ("hist2", SEC["LUCAS E RAFAEL — 2"]), ("hist3", SEC["LUCAS E RAFAEL — 3"]), ("fecho", SEC["FECHO"])]
    ini = [0.0] + [T0[i] - (CARTAO if nome.startswith("cap") else 7.2 if nome == "tema" else 4.0 if nome == "hist1" else 4.6 if nome == "fecho" else 0) for nome, i in marcos[1:]]
    secoes = [[nome, round(ini[k], 2), round(ini[k + 1] if k + 1 < len(ini) else fim, 2)] for k, (nome, _) in enumerate(marcos)]
    secoes = [[n, a + (CARTAO if n.startswith("cap") else 0), b] for n, a, b in secoes]   # a parte do capítulo começa depois do cartão
    plano = {"secoes": secoes, "climax": climax, "fim": round(fim, 2), "cartoes": cartoes}
    sons = AQUI.parents[1] / "painel" / "sons"
    marca = sons / f"{TRILHA_SOM}.plano"; txt = json.dumps(plano)
    if (sons / f"{TRILHA_SOM}.mp3").exists() and marca.exists() and marca.read_text() == txt:
        return
    print("trilha:", txt, flush=True)
    (AQUI / "trilha" / "plano.json").write_text(txt)
    subprocess.run([sys.executable, str(AQUI / "trilha" / "compor_orquestra.py"), "episodio", str(AQUI / "trilha" / "plano.json"),
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
print(f"{len(batidas)} falas, {n_cenas} cenas, falas sem cena (continuam a anterior): {sem}")
print("pausa total:", round(sum(b.get("pausa_antes_s", 0) for b in batidas), 1), "s")
