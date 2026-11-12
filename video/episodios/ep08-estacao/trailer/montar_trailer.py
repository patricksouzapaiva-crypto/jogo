"""Trailer de 60 s do Ep. 08 — vitrine dos recursos novos do motor (12/11). Uso: python3 montar_trailer.py"""
import json
from pathlib import Path
AQUI = Path(__file__).parent
falas = [l.strip() for l in (AQUI / "falas.txt").read_text().splitlines() if l.strip()]
I, R = "../imagens/", "../imagens_reais/"
LINHA = [1666, 1677, 1750, 1825, 1979, 1998, 2004]
def fx(som, db, em=None, depois=False, atraso=0.0): return {"som": som, "volume_db": db, "em": em, "depois": depois, "atraso": atraso}
B = []
# 0 — o grupo da família (gancho)
B.append({"fala": falas[0], "sem_legenda": True, "cenas": [{"tipo": "chat", "grupo": "Família 🏠", "membros": "Dani, Lucas, Mãe, Pai",
  "mensagens": [{"de": "Dani", "tipo": "foto", "imagem": I + "N10b_trem_noite.jpg", "hora": "23:20", "apos": 0.2},
                {"de": "Dani", "texto": "Só eu hoje 😅", "hora": "23:20", "apos": 1.0},
                {"de": "Lucas", "texto": "kkkk dormiu de novo?", "hora": "11:21", "apos": 2.0},
                {"de": "Mãe", "texto": "Fala com o maquinista, filha", "hora": "11:22", "apos": 3.0},
                {"de": "Dani", "texto": "Gente… esse trem não para faz vinte minutos.", "hora": "23:40", "em": "mensagem", "digitando": 1.4}]}],
  "sons": [fx("ep08_msg", -12, None, False, 0.2), fx("ep08_msg", -12, None, False, 1.0), fx("ep08_msg", -14, None, False, 2.0), fx("ep08_msg", -14, None, False, 3.0),
           fx("ep08_vibra", -12, "mensagem", True), fx("ep08_taiko", -6, "mensagem", True, 1.6)],
  "ambiente": {"som": "ep08_trem_dentro", "volume_db": -12}})
# 1 — capítulo + Oiwa (paralaxe, foco no olho, kanji com hanko, linha do tempo, poeira)
B.append({"fala": falas[1], "pausa_antes_s": 3.4, "cenas": [
  {"tipo": "capitulo", "numero": "第一章", "numero_pt": "Capítulo 1", "titulo": "As três mulheres", "ano": "1666 · 1741 · 1825",
   "imagem": R + "R06_oiwa_fantasma_kuniyoshi.jpg", "antecipar": 3.0, "entrada": "nanquim", "atmos": {"poeira": 0.7}},
  {"imagem": R + "R01_oiwa_lanterna_hokusai.jpg", "em": "uma", "encaixe": "conter", "zoom": [1.0, 1.1], "entrada": "nanquim",
   "dof": {"x": 0.53, "y": 0.5, "r": 0.2, "atraso": 1.6}, "atmos": {"poeira": 0.6, "vela": 0.5},
   "kanji": {"texto": "四谷怪談", "x": 0.82, "y": 0.5, "modo": "luz", "legenda": "Yotsuya Kaidan · 1825", "selo": "怨", "atraso": 0.5},
   "linha": {"anos": LINHA, "de": 1666, "atual": 1825, "dur": 3.5}}],
  "sons": [fx("ep08_tinta", -10, "uma"), fx("ep08_pincel", -10, "uma", False, 0.5), fx("ep08_carimbo", -9, "voltou")],
  "ambiente": {"som": "ep08_campo_noite", "volume_db": -24}})
# 2 — Okiku (porta de correr, kanji vermelho com glitch)
B.append({"fala": falas[2], "cenas": [{"imagem": R + "R03_okiku_poco_hokusai.jpg", "encaixe": "conter", "zoom": [1.0, 1.08], "entrada": "shoji",
   "atmos": {"poeira": 0.5}, "kanji": {"texto": "皿屋敷", "x": 0.17, "y": 0.5, "modo": "sangue", "legenda": "A mansão dos pratos", "selo": "呪", "glitch": True, "atraso": 0.6}}],
  "sons": [fx("ep08_shoji", -10), fx("ep08_pincel", -12, "pratos")]})
# 3 — a contagem: um kanji por número, no ritmo da voz
B.append({"fala": falas[3], "pausa_antes_s": 0.6, "cenas": [{"imagem": R + "R03_okiku_poco_hokusai.jpg", "encaixe": "conter", "zoom": [1.12, 1.22],
   "foco": [[0.5, 0.25], [0.5, 0.22]], "atmos": {"neblina": 0.5},
   "kanji": [{"texto": "一", "em": "Um", "x": 0.16, "y": 0.5, "tam": 0.3, "modo": "sangue", "escrever": 0.5},
             {"texto": "二", "em": "Dois", "x": 0.84, "y": 0.42, "tam": 0.3, "modo": "sangue", "escrever": 0.5},
             {"texto": "三", "em": "Três", "x": 0.5, "y": 0.72, "tam": 0.3, "modo": "sangue", "escrever": 0.6, "selo": "九"}]}],
  "sons": [fx("ep08_pincel", -9, "Um"), fx("ep08_pincel", -9, "Dois"), fx("ep08_pincel", -8, "Três")]})
# 4 — o poço real: foto de dia (prova) → a mesma de noite, com neblina e kanji recortado
B.append({"fala": falas[4], "pausa_antes_s": 0.8, "cenas": [
  {"imagem": R + "R11_poco_okiku_himeji_2.jpg", "zoom": [1.0, 1.04], "entrada": "shoji", "kanji": {"texto": "実在", "x": 0.85, "y": 0.42, "tam": 0.14, "modo": "placa", "fundo": "vermelho", "legenda": "Foto real · Himeji", "atraso": 0.2, "escrever": 0.6}},
  {"imagem": I + "N08_poco_noite.jpg", "em": "real", "zoom": [1.02, 1.1], "foco": [[0.5, 0.6], [0.5, 0.65]], "entrada": "fundir", "duracao_entrada": 1.2,
   "atmos": {"neblina": 0.8}, "kanji": {"texto": "お菊井戸", "x": 0.82, "y": 0.5, "modo": "recorte", "legenda": "O poço da Okiku", "atraso": 0.6}}],
  "sons": [fx("ep08_shoji", -10), fx("ep08_taiko", -10, "real")]})
# 5 — 1979: película (vazamento de luz, riscos), vela que apaga, linha do tempo
B.append({"fala": falas[5], "pausa_antes_s": 1.2, "cenas": [{"imagem": I + "L02_kuchisake.jpg", "zoom": [1.0, 1.12], "foco": [[0.5, 0.5], [0.5, 0.42]], "entrada": "vela",
   "atmos": {"pelicula": 1.0}, "kanji": {"texto": "口裂け女", "x": 0.16, "y": 0.5, "modo": "sangue", "legenda": "A mulher da boca cortada", "glitch": True, "atraso": 1.6},
   "linha": {"anos": LINHA, "de": 1825, "atual": 1979, "dur": 3.5}}],
  "sons": [fx("ep08_vela", -8, None, False, -0.6), fx("ep08_pincel", -12, "máscara")]})
# 6 — Hanako: celular na mão, foco nos pés
B.append({"fala": falas[6], "cenas": [{"imagem": I + "L04_hanako_pes.jpg", "zoom": [1.04, 1.1], "foco": [[0.55, 0.6], [0.58, 0.7]], "mao": 0.6,
   "dof": {"x": 0.58, "y": 0.78, "r": 0.2, "atraso": 1.0}, "kanji": {"texto": "花子さん", "x": 0.16, "y": 0.48, "modo": "luz", "fundo": "nanquim", "legenda": "Hanako-san", "atraso": 0.4}}]})
# 7 — Kisaragi: mancha de tinta, freio e sino, kanji horizontal com glitch e hanko
B.append({"fala": falas[7], "pausa_antes_s": 0.9, "cenas": [{"imagem": I + "N09_estacao_noite.jpg", "zoom": [1.0, 1.12], "entrada": "nanquim", "atmos": {"neblina": 0.7},
   "kanji": {"texto": "きさらぎ駅", "x": 0.5, "y": 0.4, "vertical": False, "fonte": "mincho", "tam": 0.15, "modo": "luz", "legenda": "Kisaragi · estação", "glitch": True, "selo": "駅", "em": "desceu"},
   "linha": {"anos": LINHA, "de": 1979, "atual": 2004, "dur": 3.0}}],
  "sons": [fx("ep08_tinta", -10), fx("ep08_freio", -16, "desceu"), fx("ep08_sino_estacao", -12, "existe", True)],
  "ambiente": {"som": "ep08_tambor_longe", "volume_db": -20}})
# 8 — o mapa com o ponto azul indo pra montanha
B.append({"fala": falas[8], "sem_legenda": True, "cenas": [{"tipo": "mapa", "hora_inicio": "23:43", "hora_fim": "23:58", "some_em": "cidade"}],
  "sons": [fx("ep08_porta_carro", -12, None, False, -0.4)]})
# 9 — o grupo de novo: as últimas mensagens
B.append({"fala": falas[9], "sem_legenda": True, "cenas": [{"tipo": "chat", "grupo": "Família 🏠", "membros": "Dani, Lucas, Mãe, Pai", "mensagens": [
  {"de": "Pai", "texto": "DANI", "hora": "11:52", "apos": 0.1},
  {"de": "Mãe", "texto": "filha responde a mãe", "hora": "11:52", "apos": 0.7},
  {"de": "Dani", "texto": "ele não fala japonês", "hora": "23:53", "em": "grupo", "digitando": 1.0},
  {"de": "Dani", "texto": "ele tá falando com alguém. em português. com a voz do pai.", "hora": "23:54", "em": "vivo", "digitando": 0.8}]}],
  "sons": [fx("ep08_vibra", -12, "grupo"), fx("ep08_vibra", -12, "vivo")]})
# 10 — título final (sem susto: tudo some e sobra o tambor longe)
B.append({"fala": falas[10], "pausa_antes_s": 0.8, "cenas": [{"tipo": "capitulo", "numero": "きさらぎ", "numero_pt": "O Vigia · Episódio 08", "titulo": "A estação que não existe",
   "ano": "Em breve no Último Abrigo", "imagem": I + "N09b_estacao_noite.jpg", "entrada": "vela", "selo": "終", "atmos": {"neblina": 0.6}}],
  "sons": [fx("ep08_taiko", -6, "Japão", True)]})
r = {"modo": "cenas", "formato": "16:9", "tema": "vigia", "avatar": "vigia_hd", "voz_arquivo": "audio/voz_limpa.wav",
     "cintilar": 0.03, "apertar_pausas": False, "vigia_padrao": False, "cauda": 3.0, "chuva": 0, "grao": 0.16,
     "mix": {"musica_ganho_db": 12, "fundo_sob_voz": -9, "efeitos_sob_voz": -4, "voz_pro": True, "fundo_bolso": True, "efeitos_pico_max": -3},
     "legendas": {"destaques": ["Japão", "poço", "real", "estação", "existe", "participar"]},
     "musica": {"som": "ep08_cx_tensao", "volume_db": -33}, "batidas": B}
(AQUI / "roteiro.json").write_text(json.dumps(r, ensure_ascii=False, indent=1))
print(len(B), "batidas")
