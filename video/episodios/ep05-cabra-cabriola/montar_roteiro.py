"""Monta roteiro.json do Ep. 05 "Abre, filha." (Cabra Cabriola) a partir do ROTEIRO.md (cada fala "> ..." = 1 batida).
As falas são endereçadas pelo ÍNDICE (a frase "Abre, filha. É a mãe." se repete 6 vezes) — se o ROTEIRO.md mudar,
conferir os índices com: python3 montar_roteiro.py --falas
Regras da casa: Vigia só nas inserções; música de fundo o episódio inteiro (silêncio = só de narração); a cantiga
entra SOZINHA (o fundo sai); saída lenta das cenas tensas; clímax fica na imagem; ninguém com cara de IA; a criatura
nunca aparece (só as quatro sombras na fresta B11c).
Uso: python3 montar_roteiro.py
"""
import json
import re
import sys
from pathlib import Path

AQUI = Path(__file__).parent
md = (AQUI / "ROTEIRO.md").read_text(encoding="utf-8")
md = md[:md.index("## Fatos reais")]
falas = [re.sub(r"\*\(.*?\)\*", "", l[2:]).replace("**", "").strip() for l in md.splitlines() if l.startswith("> ")]
falas = [f for f in falas if f]
if "--falas" in sys.argv:
    for i, f in enumerate(falas):
        print(i, f[:100])
    raise SystemExit
assert len(falas) == 148 and falas[122].startswith("Na fresta da porta"), "o ROTEIRO.md mudou: rever os índices"
batidas = [{"fala": f} for f in falas]

VIGIA = {"imagem": "../../painel/cenarios/abrigo_16x9.png", "vigia": True}


def vigia(z=(1.0, 1.04), foco=((0.55, 0.5), (0.57, 0.48))):
    return dict(VIGIA, zoom=list(z), foco=[list(foco[0]), list(foco[1])])


def img(nome, z=(1.0, 1.06), foco=None, **kw):
    arq = f"grade/{nome}.jpg"   # IA e fotos reais passam pela mesma correção de cor (gradar.py)
    c = {"imagem": arq, "zoom": list(z), **kw}
    if foco:
        c["foco"] = [list(foco[0]), list(foco[1])]
    return c


def vid(nome, z=(1.0, 1.04), **kw):
    return {"video": f"videos/{nome}.mp4", "zoom": list(z), **kw}


def texto(t, vermelho=None, estilo="maquina", **kw):
    return {"tipo": "texto", "texto": t, "estilo": estilo, **({"vermelho": vermelho} if vermelho else {}), **kw}


def cartao(nome, legenda, giro=-1.5, video=False):
    c = vid(nome) if video else img(nome)
    c.update({"tipo": "cartao", "legenda_cartao": legenda, "giro": giro})
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


def mus(i, som, db=-24, em=None):
    batidas[i]["musica"] = {"som": som, "volume_db": db, **({"em": em} if em else {})}


def amb(i, som, db=-9):
    batidas[i]["ambiente"] = {"som": som, "volume_db": db}


def fx(i, em, som, db, depois=True, atraso=0.0):
    batidas[i].setdefault("sons", []).append({"em": em, "som": som, "volume_db": db, "depois": depois, "atraso": atraso})


V = dict(com_vigia=True)
PORTA = ((0.5, 0.45), (0.5, 0.42))      # a porta no fim do corredor (B01)
FRESTA = ((0.5, 0.47), (0.5, 0.46))     # a fresta com as quatro sombras (B11c) — zoom >= 1.3 tira a data do canto

# ================================================================ SOM DE LUGAR NAS FALAS (11/11)
# A voz atrás da porta soa ATRÁS DA PORTA; a mãe de verdade soa NO TELEFONE. O público distingue as duas
# "mães" pelo ouvido. E a voz da coisa evolui como na história: 1ª noite grossa (tom 0,80), 2ª quase (0,92),
# depois perfeita — só a madeira no meio. O áudio do epílogo volta a ser grosso: outra voz, ainda aprendendo.
def vfx(i, tipo, tom=None, de=None):
    batidas[i]["voz_fx"] = {"tipo": tipo, **({"tom": tom} if tom else {}), **({"de": de} if de else {})}


for i, tom in ((1, None), (36, 0.80), (54, 0.92), (80, None), (84, None), (105, None), (113, None), (117, None), (132, None)):
    vfx(i, "porta", tom)
for i in (6, 108, 116):
    vfx(i, "telefone")
vfx(139, "telefone", 0.80)

# ================================================================ VOZES DOS PERSONAGENS (11/11)
# A mãe (voz Gacrux) fala as falas-chave; a Marina (Leda) só no áudio do epílogo. trocar_vozes.py monta
# audio/voz_personagens.wav e diz quanto cada fala nova cresceu: a pausa seguinte diminui o mesmo tanto.
def aplicar_ajuste_pausas():
    arq = AQUI / "audio" / "ajuste_pausas.json"
    for k, d in (json.load(open(arq)) if arq.exists() else {}).items():
        b = batidas[int(k)]
        if b.get("pausa_antes_s"):
            b["pausa_antes_s"] = round(max(0.3, b["pausa_antes_s"] + d), 2)


# ================================================================ GANCHO (0:00–0:40) — sem Vigia
C(0, img("B01_porta_corredor", (1.0, 1.1), PORTA))
C(1, img("B01_porta_corredor", (1.3, 1.42), PORTA))
C(2, img("B02_mao_chave", (1.0, 1.08), ((0.45, 0.55), (0.42, 0.55))))
C(3, img("B02_mao_chave", (1.2, 1.3), ((0.35, 0.6), (0.33, 0.6))))
C(4, img("B03_celular_ligacao", (1.0, 1.08), ((0.6, 0.45), (0.62, 0.43))))
C(5, texto("EM LIGAÇÃO\nMÃE · 01:12:40", "MÃE", cps=30))
C(6, img("B03_celular_ligacao", (1.3, 1.42), ((0.64, 0.42), (0.65, 0.4))))
C(7, texto("O que estava do outro lado\ndaquela porta?", "porta?", cps=40))
C(8, img("B01_porta_corredor", (1.5, 1.75), PORTA))
pausa(6, 1.3)
pausa(8, 1.2)

# ================================================================ TEMA — Vigia apresenta
C(9, vigia((1.0, 1.05)))
C(10, cartao("bebe_mao_0", "Carolina do Norte · 1980"), **V)
C(11, img("bebe_mao_3", (1.0, 1.1), ((0.5, 0.5), (0.5, 0.45))), **V)
C(12, img("maos_idosa_0", (1.0, 1.1), ((0.5, 0.55), (0.45, 0.5))), **V)
C(13, texto("Você aprendeu essa voz\nantes de nascer.", "antes de nascer.", cps=45))
C(14, vigia((1.04, 1.1), ((0.4, 0.45), (0.38, 0.43))))
C(15, vigia((1.0, 1.05)), (img("fechadura_antiga_2", (1.0, 1.2), ((0.5, 0.45), (0.5, 0.42))), "aprendesse"), **V)
C(16, img("sabbath_goya_5", (1.0, 1.1), ((0.3, 0.5), (0.2, 0.5))), (img("bode_preto_3", (1.0, 1.12), ((0.45, 0.45), (0.42, 0.4))), "Cabra"), **V)
C(17, cartao("pereira_4", "F. A. Pereira da Costa · Pernambuco, 1908", giro=1.2), (img("livro_antigo_3", (1.0, 1.08)), "registrou"), **V)
C(18, img("recife_rua_noite_1", (1.0, 1.08)), (img("porta_madeira_0", (1.0, 1.1), ((0.7, 0.5), (0.75, 0.5))), "Os"), **V)
C(19, img("fechadura_antiga_5", (1.0, 1.1)), (img("bode_preto_1", (1.0, 1.12), ((0.45, 0.45), (0.42, 0.42))), "Grossa"), **V)
C(20, img("cabra_escuro_0", (1.0, 1.15), ((0.5, 0.5), (0.5, 0.42))), **V)
C(21, img("janela_noite_3", (1.0, 1.1), ((0.6, 0.5), (0.7, 0.5))), (img("olho_cabra_0", (1.0, 1.15), ((0.5, 0.5), (0.5, 0.5))), "Noite"), **V)
C(22, vid("ferreiro_v_0", (1.0, 1.04)), (vid("ferreiro_v_3", (1.0, 1.05)), "bigorna"), **V)
C(23, texto("Na noite seguinte…\na porta se abriu.", "abriu.", cps=35))
C(24, vigia((1.0, 1.05)), (texto("Ela não arromba.\nEla aprende.", "aprende.", cps=45), "Ela"))
C(25, vigia((1.06, 1.14), ((0.35, 0.45), (0.33, 0.42))))
fx(22, "bigorna", "ep05_bigorna", -20)

# ================================================================ PARTE 1 — o combinado (sem Vigia até a inserção)
C(26, img("sobrado_recife_3", (1.0, 1.08)), (img("recife_rua_noite_0", (1.0, 1.08), ((0.5, 0.5), (0.55, 0.5))), "sobrado"))
T(26, "preto", 1.2); pausa(26, 1.2)
C(27, img("casa_antiga_noite_1", (1.0, 1.1), ((0.55, 0.5), (0.6, 0.5))))
C(28, img("maos_idosa_0", (1.1, 1.2), ((0.5, 0.55), (0.5, 0.5))), (img("predio_moderno_noite_9", (1.0, 1.06)), "Três"))
C(29, img("predio_moderno_noite_10", (1.0, 1.08)))
C(30, img("B01_porta_corredor", (1.0, 1.08), PORTA))
C(31, img("porta_madeira_0", (1.0, 1.1), ((0.7, 0.5), (0.75, 0.5))))
C(32, texto("“Abre, filha. É a mãe.”", "mãe.”", cps=40))
C(33, img("fechadura_antiga_1", (1.0, 1.1), ((0.45, 0.45), (0.5, 0.45))))
C(34, img("rua_vazia_madrugada_3", (1.0, 1.08)), (img("B01_porta_corredor", (1.0, 1.06), PORTA), "bateram"))
C(35, img("B01_porta_corredor", (1.15, 1.3), PORTA))
C(36, texto("“Abre, filha.\nÉ a mãe.”", "mãe.”", cps=14))            # a voz errada: digitação arrastada
C(37, img("B01_porta_corredor", (1.5, 1.65), PORTA))
C(38, img("corredor_abandonado_2", (1.0, 1.12), ((0.5, 0.5), (0.5, 0.45))))
C(39, img("fechadura_antiga_2", (1.1, 1.4), ((0.5, 0.42), (0.5, 0.4))))
C(40, img("B04_olho_magico_escuro", (1.0, 1.1), ((0.5, 0.5), (0.5, 0.5))))
C(41, img("B04_olho_magico_escuro", (1.2, 1.3), ((0.55, 0.55), (0.55, 0.55))))
C(42, texto("Marina: mãe, a senhora tá em casa?", "em casa?", cps=40))
C(43, texto("Mãe: Tô aqui, filha. Que foi?", "Que foi?", cps=40))
C(44, vid("escada_v_0", (1.0, 1.05)))
C(45, img("escada_sinistra_2", (1.0, 1.06), ((0.5, 0.5), (0.5, 0.52))), (img("escada_sinistra_2", (1.3, 1.5), ((0.5, 0.6), (0.5, 0.72))), "saltos"))  # desce os degraus
pausa(36, 1.3); pausa(41, 0.8)
pausa(14, 1.8); pausa(24, 0.8); pausa(25, 0.5); pausa(33, 1.6); pausa(37, 2.1); pausa(44, 2.0)
fx(34, "bateram", "ep05_batidas", -13)
fx(35, "Três", "ep05_batidas_lentas", -13, depois=False)
fx(45, "saltos", "ep05_saltos", -15)

# ---------------------------------------------------------------- inserção 1 — o mesmo pesadelo (Vigia)
C(46, vigia((1.0, 1.05)))
saida_lenta(46, 2.2)
C(47, cartao("grimm_retrato_0", "Irmãos Grimm · Alemanha, 1812"), (img("livro_antigo_0", (1.0, 1.08)), "publicaram"), **V)
C(48, img("grimm_lobo_2", (1.0, 1.12), ((0.5, 0.45), (0.5, 0.4))), (img("porta_arranhada_1", (1.0, 1.1)), "Então"), **V)
C(49, vid("mapa_v_5", (1.0, 1.05)), (img("mapa_antigo_1", (1.0, 1.12), ((0.4, 0.5), (0.3, 0.45))), "Portugal"), **V)
C(50, img("mapa_antigo_6", (1.0, 1.1)), (vigia((1.0, 1.04)), "tiveram"), **V)
C(51, texto("Em todas elas,\no monstro começa errando.", "errando.", cps=50))
C(52, vigia((1.05, 1.1), ((0.4, 0.45), (0.38, 0.42))))

# ================================================================ PARTE 2 — mais parecida
C(53, img("recife_rua_noite_1", (1.0, 1.06)), (img("B01_porta_corredor", (1.1, 1.2), PORTA), "bateram"))
T(53, "preto", 1.2); pausa(53, 1.2)
C(54, texto("“Abre, filha. É a mãe.”", "mãe.”", cps=20))
C(55, img("B01_porta_corredor", (1.4, 1.5), PORTA))
C(56, img("fechadura_antiga_2", (1.0, 1.25), ((0.5, 0.45), (0.5, 0.42))))
C(57, img("B05_celular_chao", (1.0, 1.1), ((0.55, 0.6), (0.6, 0.65))))
C(58, vid("cozinha_v_3", (1.0, 1.04)), (img("celular_escuro_0", (1.0, 1.1)), "ouviram"))
C(59, img("B05_celular_chao", (1.3, 1.4), ((0.6, 0.68), (0.62, 0.7))))
C(60, vid("corredor_v_2", (1.0, 1.06)))
C(61, img("maos_idosa_0", (1.15, 1.25), ((0.45, 0.5), (0.45, 0.5))))
C(62, img("chaveiro_0", (1.0, 1.1)), (img("fechadura_antiga_1", (1.1, 1.2), ((0.45, 0.45), (0.5, 0.45))), "trocou"))
C(63, img("beco_7", (1.0, 1.08)))
C(64, img("beco_0", (1.0, 1.1), ((0.5, 0.5), (0.5, 0.55))), (img("B06_beco_marcas", (1.0, 1.08), ((0.5, 0.55), (0.5, 0.6))), "terra"))
C(65, img("B06_beco_marcas", (1.3, 1.45), ((0.48, 0.75), (0.48, 0.77))))
C(66, img("B06_beco_marcas", (1.5, 1.65), ((0.5, 0.45), (0.55, 0.3))))      # sobe das marcas para a janela
C(67, img("janela_noite_3", (1.1, 1.3), ((0.7, 0.5), (0.75, 0.5))))
pausa(54, 1.0); pausa(60, 1.5); pausa(67, 1.6); pausa(52, 0.5); pausa(55, 1.7)
fx(53, "bateram", "ep05_batidas", -13)

# ---------------------------------------------------------------- inserção 2 — a voz de quem você ama (Vigia)
C(68, img("cinema_antigo_3", (1.0, 1.08)), **V)
saida_lenta(68, 2.0)
C(69, cartao("cinema_antigo_4", "“O Exorcista” · 1973"), (img("quarto_abandonado_1", (1.0, 1.1)), "cama"), **V)
C(70, img("cadeira_vazia_2", (1.0, 1.15), ((0.5, 0.6), (0.5, 0.62))), **V)
C(71, cartao("floresta_v_1", "“Aniquilação” · 2018", giro=1.2, video=True), (img("floresta_escura_3", (1.0, 1.12)), "Com"), **V)
C(72, vigia((1.0, 1.05)))
C(73, vigia((1.05, 1.1), ((0.4, 0.45), (0.38, 0.42))), (img("porta_entreaberta_0", (1.0, 1.15), ((0.7, 0.5), (0.72, 0.5))), "abre"), **V)
C(74, cartao("hospicio_0", "Paris · 1923"), (img("hospital_antigo_1", (1.0, 1.1)), "pacientes"), **V)
C(75, img("hospital_antigo_2", (1.0, 1.1)), (img("espelho_antigo_0", (1.0, 1.1), ((0.6, 0.4), (0.65, 0.35))), "idêntico"), **V)
C(76, img("espelho_antigo_0", (1.3, 1.5), ((0.68, 0.33), (0.7, 0.3))), **V)
C(77, texto("Às vezes, a única prova\nde que tem algo errado…\né um sentimento.", "sentimento.", cps=45))

# ================================================================ PARTE 3 — Nina
C(78, img("B07_quarto_mae", (1.0, 1.08), ((0.55, 0.5), (0.6, 0.5))))
T(78, "preto", 1.2); pausa(78, 2.0)
C(79, img("B01_porta_corredor", (1.0, 1.1), PORTA))
C(80, texto("“Abre, filha.\nA mãe esqueceu a chave\nna fruteira.”", "fruteira.”", cps=26))
C(81, img("fruteira_0", (1.0, 1.15), ((0.5, 0.5), (0.5, 0.48))))
C(82, img("B07b_quarto_mae", (1.0, 1.1), ((0.6, 0.5), (0.65, 0.5))))
C(83, img("B01_porta_corredor", (1.2, 1.3), PORTA))
C(84, texto("“Tá frio aqui fora, Nina.”", "Nina.”", cps=24))
C(85, img("B01_porta_corredor", (1.45, 1.6), PORTA))
C(86, img("B08_duas_corredor", (1.0, 1.08), ((0.5, 0.5), (0.5, 0.48))))
C(87, img("B08b_duas_corredor", (1.0, 1.1), ((0.55, 0.5), (0.55, 0.45))))
C(88, img("B08_duas_corredor", (1.3, 1.4), ((0.5, 0.35), (0.5, 0.32))))     # a bandeira da porta, acima delas
C(89, img("B09_maos_dadas", (1.0, 1.1), ((0.5, 0.5), (0.52, 0.48))))
C(90, img("B09c_maos_dadas", (1.1, 1.25), ((0.5, 0.45), (0.5, 0.45))))
C(91, img("B08c_duas_corredor", (1.0, 1.08)), (img("escada_sinistra_1", (1.0, 1.1)), "Quando"))
C(92, img("escada_sinistra_0", (1.1, 1.3), ((0.5, 0.55), (0.5, 0.7))), (img("parede_mofo_1", (1.0, 1.2), ((0.3, 0.5), (0.5, 0.5))), "raspando"))
pausa(81, 2.9); pausa(84, 0.8); pausa(85, 3.4); pausa(90, 1.0)
fx(79, "bateram", "ep05_batidas", -13)
fx(92, "escada", "ep05_saltos", -16)
fx(92, "raspando", "ep05_raspar", -18)

# ---------------------------------------------------------------- aparte do Vigia
C(93, vigia((1.0, 1.05)))
saida_lenta(93, 2.2)
C(94, vid("ferreiro_v_5", (1.0, 1.05)), (img("bigorna_fogo_2", (1.0, 1.15)), "voltava"), **V)
C(95, vigia((1.04, 1.1), ((0.4, 0.45), (0.38, 0.42))))
C(96, texto("Ela ainda não sabe…\nconversar.", "conversar.", cps=20))
fx(93, "ferreiro", "ep05_bigorna", -20)

# ================================================================ PARTE 4 — a pergunta
C(97, img("predio_moderno_noite_9", (1.0, 1.08)), (img("B13_celular_cabeceira", (1.0, 1.08), ((0.5, 0.4), (0.45, 0.35))), "Honório"))
T(97, "preto", 1.2); pausa(97, 2.4)
C(98, img("B09b_maos_dadas", (1.0, 1.1)))
C(99, img("celular_escuro_0", (1.0, 1.12)))
C(100, img("B03_celular_ligacao", (1.0, 1.08), ((0.6, 0.45), (0.62, 0.43))))
C(101, img("cadeira_vazia_7", (1.0, 1.15), ((0.3, 0.6), (0.25, 0.6))), (img("porta_entreaberta_0", (1.0, 1.12), ((0.7, 0.5), (0.72, 0.5))), "noite"))
C(102, texto("TERÇA-FEIRA\nEM LIGAÇÃO · MÃE · 01:04:12", "MÃE", cps=34), (img("B03_celular_ligacao", (1.1, 1.2), ((0.62, 0.43), (0.63, 0.42))), "contava"))
C(103, texto("02:10", "02:10", "impacto", cps=10, tamanho=170))
C(104, img("B01_porta_corredor", (1.0, 1.08), PORTA))
C(105, img("B01_porta_corredor", (1.25, 1.4), PORTA))
C(106, img("B02_mao_chave", (1.0, 1.1), ((0.45, 0.55), (0.4, 0.58))))
C(107, img("B03_celular_ligacao", (1.0, 1.08), ((0.6, 0.45), (0.62, 0.43))))
C(108, img("B03_celular_ligacao", (1.3, 1.42), ((0.64, 0.42), (0.65, 0.4))))
C(109, img("B01_porta_corredor", (1.5, 1.6), PORTA))
C(110, img("B01_porta_corredor", (1.6, 1.8), PORTA))
C(111, img("B03_celular_ligacao", (1.4, 1.5), ((0.64, 0.42), (0.65, 0.4))))
C(112, img("fechadura_antiga_2", (1.0, 1.35), ((0.5, 0.45), (0.5, 0.42))))
C(113, texto("“Eu disse que, enquanto\neu tivesse voz…\nvocê nunca ia ficar sozinha.”", "sozinha.”", cps=28))
C(114, img("B02_mao_chave", (1.25, 1.35), ((0.35, 0.6), (0.33, 0.6))))
C(115, img("B03_celular_ligacao", (1.5, 1.6), ((0.64, 0.42), (0.65, 0.4))))
C(116, texto("“Marina… eu nunca contei isso\npra ninguém.”", "ninguém.”", cps=36))
C(117, img("B01_porta_corredor", (1.8, 2.0), PORTA))
C(118, img("B10_olho_magico_luz", (1.0, 1.08), ((0.5, 0.5), (0.5, 0.5))))
C(119, img("B10_olho_magico_luz", (1.25, 1.35), ((0.5, 0.48), (0.5, 0.48))))
C(120, img("B10b_olho_magico_luz", (1.2, 1.4), ((0.5, 0.5), (0.5, 0.68))))    # desce: ninguém da altura dela
C(121, img("B01_porta_corredor", (1.6, 1.8), ((0.5, 0.5), (0.5, 0.78))))      # o olhar desce pela porta
C(122, img("B11c_fresta_quatro", (1.3, 1.6), FRESTA))                           # CLÍMAX — fica nesta imagem
C(123, img("B11c_fresta_quatro", (1.6, 2.0), FRESTA))
C(124, img("B11c_fresta_quatro", (2.0, 2.15), FRESTA))
pausa(104, 0.9); pausa(105, 2.6); pausa(108, 1.2); pausa(111, 1.5); pausa(112, 2.6); pausa(114, 2.8); pausa(117, 2.1)
pausa(119, 1.2); pausa(120, 1.6); pausa(122, 1.0); pausa(124, 2.5)
fx(104, "batidas", "ep05_batidas", -13)
fx(122, "lugares", "sub_drop", -14)

# ================================================================ PARTE 5 — até clarear
C(125, img("B12_marina_chao", (1.0, 1.08), ((0.6, 0.5), (0.62, 0.5))))
saida_lenta(125, 3.0, dur=2.0)                                                   # sai devagar do clímax
C(126, img("B11c_fresta_quatro", (1.35, 1.45), FRESTA))
C(127, img("B12_marina_chao", (1.2, 1.3), ((0.62, 0.45), (0.64, 0.45))))
C(128, img("quarto_abandonado_5", (1.0, 1.12), ((0.45, 0.55), (0.4, 0.55))), (img("B12_marina_chao", (1.3, 1.4), ((0.64, 0.45), (0.65, 0.45))), "música"))
C(129, img("B03_celular_ligacao", (1.2, 1.3), ((0.62, 0.43), (0.63, 0.42))))
C(130, img("amanhecer_rua_2", (1.0, 1.08)), (img("B11b_fresta_vazia", (1.3, 1.4), FRESTA), "casa"))
saida_lenta(130, 2.0)
C(131, img("B11d_fresta_dia", (1.3, 1.4), ((0.5, 0.4), (0.5, 0.38))))
C(132, texto("“Abre, filha. É a mãe.”", "mãe.”", cps=32))
C(133, img("B02_mao_chave", (1.0, 1.1), ((0.45, 0.55), (0.4, 0.58))))
C(134, img("B02_mao_chave", (1.2, 1.35), ((0.35, 0.6), (0.33, 0.6))))
pausa(133, 1.6)
fx(131, "vezes", "ep05_batidas", -13)

# ================================================================ EPÍLOGO
C(135, vigia((1.0, 1.05)), (img("predio_moderno_noite_10", (1.0, 1.08)), "apartamento"), **V)
saida_lenta(135, 2.2)
C(136, vigia((1.04, 1.1), ((0.4, 0.45), (0.38, 0.42))))
C(137, img("B13_celular_cabeceira", (1.0, 1.08), ((0.5, 0.5), (0.48, 0.5))))
T(137, "preto", 1.0); pausa(137, 1.2)
C(138, texto("ÁUDIO · MARINA · 0:04", "MARINA", cps=30))
C(139, texto("“Mãe…\nabre a porta.”", "porta.”", cps=10))
C(140, img("B13_celular_cabeceira", (1.3, 1.45), ((0.48, 0.52), (0.47, 0.52))))
C(141, texto("Ainda.", "Ainda.", "impacto", cps=8, tamanho=170))
pausa(139, 1.4); pausa(140, 1.9); pausa(141, 1.6)
fx(137, "vibrou", "ep05_vibrar", -16)
fx(141, "Ainda", "ep05_batidas_lentas", -12, atraso=1.4)                        # as três batidas, na porta do paciente

C(142, vigia((1.0, 1.05)), (img("pereira_4", (1.0, 1.08)), "mil"), **V)
saida_lenta(142, 4.2, dur=2.0)
C(143, vigia((1.04, 1.08)))
C(144, vigia((1.0, 1.05)), (img("cabra_escuro_0", (1.0, 1.3), ((0.4, 0.4), (0.38, 0.33))), "troca"), **V)
C(145, vigia((1.0, 1.05)), (img("B01_porta_corredor", (1.0, 1.15), PORTA), "outro"), **V)
C(146, vigia((1.05, 1.1), ((0.4, 0.45), (0.38, 0.42))))
C(147, vigia((1.08, 1.16), ((0.35, 0.45), (0.33, 0.42))))

# ================================================================ MÚSICA
# Base: ep05_fundo_longa (ambiente_inicial) toca o episódio inteiro. Por cima, a trilha de tensão nas noites.
# A cantiga entra SOZINHA: o fundo sai ("ambiente": nenhum) e volta depois (variantes b/c = outros trechos da mesma música).
T_DB = -25
mus(0, "ep05_tensao_longa", T_DB)                      # gancho
amb(9, "nenhum"); mus(9, "ep05_cantiga", -19)          # tema: a voz da mãe → só a cantiga
amb(15, "ep05_fundo_b"); mus(15, "silencio", -40)      # "E se alguma coisa aprendesse…" → o fundo volta
mus(34, "ep05_tensao_longa", T_DB); mus(46, "silencio", -40)       # 1ª noite
mus(53, "ep05_tensao_longa", T_DB); mus(58, "silencio", -40)       # 2ª noite
mus(64, "ep05_tensao_longa", T_DB - 2); mus(68, "silencio", -40)   # as marcas no beco
mus(79, "ep05_tensao_longa", T_DB); mus(93, "silencio", -40)       # 3ª noite
mus(102, "ep05_tensao_longa", T_DB)                                 # a pergunta → clímax
amb(128, "nenhum"); mus(128, "ep05_cantiga", -19)      # "a música da hora de dormir" → só a cantiga
amb(130, "ep05_fundo_c"); mus(130, "silencio", -40)    # amanhece → o fundo volta
mus(137, "ep05_tensao_longa", T_DB); mus(142, "silencio", -40)     # o áudio

# ================================================================ VINHETA FIXA DE INSCRIÇÃO
VINHETA = ("Se você ficou até aqui… então já é um dos meus. Inscreva-se no Último Abrigo e ative o sininho, "
           "pra não perder o próximo caso. Eu vou estar aqui. Esperando.")
batidas.append({"fala": VINHETA, "cta_inicio": True, "sem_legenda": True, "ambiente": {"som": "nenhum"},
                "musica": {"som": "vinheta_ultimo_abrigo", "volume_db": -20}})

roteiro = {
    "modo": "cenas", "formato": "16:9", "tema": "vigia", "avatar": "vigia_hd",
    "voz_arquivo": "audio/voz_personagens.wav",
    "cintilar": 0.045,  # acabamento de película: luz que respira + grão um pouco mais presente
    "apertar_pausas": False,   # REGRA: nunca encurtar as pausas da narração
    "vigia_padrao": False,
    "preencher_pausas": {"min": 1.3},
    "cauda": 1.6, "chuva": 0, "grao": 0.20,
    "mix": {"musica_ganho_db": 12, "fundo_sob_voz": -9, "efeitos_sob_voz": -4, "voz_pro": True, "fundo_bolso": True},
    "legendas": {"destaques": ["voz", "porta", "mãe", "abre", "Nina", "chave", "batidas"]},
    "ambiente_inicial": [{"som": "ep05_fundo_longa", "volume_db": -9}],
    "musica": {"som": "silencio", "volume_db": -40},
    "abertura": {"texto": "O VIGIA\nEP. 05 · ABRE, FILHA.", "vermelho": "FILHA.", "duracao": 3.2, "segurar": 1.6,
                 "antes_da_batida": 9, "sons": [{"som": "sub_drop", "t": 0.2, "volume_db": -12}]},
    "cta": {"titulo": "Qual voz faria você abrir?", "canal": "Último Abrigo",
            "subtitulo": "Inscreva-se para mais casos do Vigia",
            "fundo": "../../painel/cenarios/abrigo_16x9.png", "pose": "c_cafe_convite",
            "antes": 0.6, "clique_em": "Inscreva-se", "duracao": 2.5},
    "batidas": batidas,
}
for b in batidas:  # tela de texto não leva legenda (o texto já está na tela)
    for c in ([b["cena"]] if b.get("cena") else []) + b.get("cenas", []):
        if c.get("tipo") == "texto" and "em" not in c:
            b["sem_legenda"] = True
faltando = []
for b in batidas:
    for c in ([b["cena"]] if b.get("cena") else []) + b.get("cenas", []):
        for k in ("imagem", "video"):
            if c.get(k) and not (AQUI / c[k]).exists():
                faltando.append(c[k])
if faltando:
    raise SystemExit("arquivos faltando: " + ", ".join(sorted(set(faltando))))
sem = [i for i, b in enumerate(batidas) if not (b.get("cena") or b.get("cenas"))]
aplicar_ajuste_pausas()
(AQUI / "roteiro.json").write_text(json.dumps(roteiro, ensure_ascii=False, indent=1), encoding="utf-8")
n_cenas = sum(len(b.get("cenas", [])) or 1 for b in batidas if b.get("cena") or b.get("cenas"))
print(f"{len(batidas)} falas, {n_cenas} cenas, falas sem cena: {sem}")
