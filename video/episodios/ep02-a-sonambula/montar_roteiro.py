"""Gera roteiro.json do Ep. 02 a partir do ROTEIRO.md (falas) + a decupagem abaixo (imagem, enquadramento,
pose, som). Rodar de novo sempre que o texto ou a decupagem mudar:
    python video/episodios/ep02-a-sonambula/montar_roteiro.py
Enquadramentos: zoom [inicial, final] e foco [[x,y] inicial, [x,y] final] em fração da imagem.
Os focos são palpites até as imagens reais chegarem — ajustar depois de ver cada uma.
"""
import json
import re
from pathlib import Path

AQUI = Path(__file__).parent
md = (AQUI / "ROTEIRO.md").read_text(encoding="utf-8")
rot = md.split("## ROTEIRO")[1].split("## LISTA DE IMAGENS")[0]
falas = []
for l in rot.splitlines():
    m = re.match(r"^(\*\(Vigia[^)]*\)\*\s*)?\*\*\[([^\]]+)\]\*\*\s*(.+)$", l.strip())
    if m and m.group(2) not in ("ABERTURA", "CTA"):
        falas.append(m.group(3).strip())


def img(n):
    return f"imagens/{n}.png"


def cena(n, z=(1.0, 1.05), f0=(0.5, 0.5), f1=None, em=None, **kw):
    c = {"imagem": img(n), "zoom": list(z), "foco": [list(f0), list(f1 or f0)]}
    if em:
        c["em"] = em
    c.update(kw)
    return c


ABERTO = (1.0, 1.06)
FECHA = (1.0, 1.35)           # aproxima bastante (aberto -> detalhe)
CLOSE = (1.25, 1.32)
VIGIA = {"imagem": img("V1"), "zoom": [1.0, 1.04], "foco": [[0.5, 0.5], [0.52, 0.5]], "vigia": True}
CCTV = lambda n, hora, z=(1.0, 1.04), f0=(0.5, 0.5), f1=None, vel=1, em=None: cena(
    n, z, f0, f1, em=em, cctv={"inicio": hora, "velocidade": vel, "data": "14/03", "cam": "CAM 01"})

# decupagem por fala (índice = ordem das falas no ROTEIRO.md)
d = {
 0: {"cena": {"tipo": "relogio", "hora": "03:12"}, "sons": [{"em": "Três", "som": "impacto", "volume_db": -20, "grave": True}]},
 1: {"cena": cena("I01", (1.45, 1.5), (0.2, 0.75), (0.22, 0.72))},                     # só o travesseiro/escuro
 2: {},
 3: {"cena": cena("I01", (1.15, 1.25), (0.35, 0.6), (0.55, 0.45))},                    # câmera "vira" para ela
 4: {"cena": cena("I01", (1.0, 1.08), (0.6, 0.45), em="Helena"), "sons": [{"em": "Helena", "som": "impacto", "volume_db": -14, "grave": True}]},
 5: {"cena": cena("I02", (1.0, 1.08), (0.5, 0.45))},
 6: {"cena": cena("I02c", (1.0, 1.08), (0.55, 0.5), (0.55, 0.55), em="sussurro")},
 7: {"queda": {"forca": 0.7, "mais": 0.4}},
 8: {"pausa_antes_s": 3.2, "cena": VIGIA, "enfase": [{"em": "Boa", "pose": "s_convidando", "segurar": 2.2}]},
 9: {}, 10: {"enfase": [{"em": "Apaga", "pose": "s_silencio", "segurar": 1.8}]},
 11: {"cena": cena("I03", ABERTO, (0.5, 0.55), (0.55, 0.5)), "musica": {"som": "drone_terror", "volume_db": -14},
      "ambiente": {"som": "casa_noite", "volume_db": -3}},
 12: {"cena": cena("I04", ABERTO, (0.5, 0.5), (0.5, 0.45))},
 13: {"cena": cena("I04", FECHA, (0.5, 0.45), (0.52, 0.22), em="dobrando")},
 14: {"cena": cena("I06", ABERTO, (0.5, 0.5), (0.5, 0.45))},
 15: {"cena": cena("I05", ABERTO, (0.5, 0.5), (0.48, 0.45)), "ambiente": {"em": "jardim", "som": "chuva_externa", "volume_db": -6}},
 16: {"cena": cena("I08", ABERTO, (0.5, 0.5), (0.5, 0.45)), "ambiente": {"som": "casa_noite", "volume_db": -3}},
 17: {"cena": cena("I09", ABERTO, (0.5, 0.5), (0.5, 0.48))},
 18: {"cena": cena("I10", (1.3, 1.3), (0.42, 0.28), (0.4, 0.78))},
 19: {"cena": cena("I11", ABERTO, (0.55, 0.45), (0.62, 0.4))},
 20: {"cena": cena("I11", CLOSE, (0.67, 0.36), (0.67, 0.34))},
 21: {"cena": cena("I09", (1.3, 1.4), (0.37, 0.3), (0.37, 0.28))},
 22: {"cena": VIGIA, "enfase": [{"em": "Guarde", "pose": "c_dedo_explicando", "segurar": 2.0}]},
 23: {"cena": {"tipo": "relogio", "hora": "02:47"}, "musica": {"som": "drone_tensao", "volume_db": -15}},
 24: {},
 25: {"cena": cena("I06", (1.0, 1.1), (0.5, 0.5), (0.5, 0.48)), "ambiente": {"em": "corredor", "som": "geladeira", "volume_db": -6}},
 26: {"cena": cena("I06", (1.2, 1.32), (0.6, 0.45), (0.62, 0.42))},
 27: {},
 28: {"cena": cena("I07", (1.0, 1.06), (0.6, 0.4), em="cabeça")},
 29: {"cena": cena("I07", CLOSE, (0.68, 0.26), (0.68, 0.25), em="sorria"),
      "sons": [{"em": "sorria", "som": "impacto", "volume_db": -15, "grave": True}], "enfase": [{"em": "sorria", "pose": "e_medo_gola"}]},
 30: {"cena": cena("I14", ABERTO, (0.45, 0.5), (0.45, 0.48), lado="dir"), "ambiente": {"som": "casa_noite", "volume_db": -3}},
 31: {"cena": cena("I12", FECHA, (0.55, 0.45), (0.68, 0.42)), "sons": [{"em": "trancada", "som": "porta_tranca", "volume_db": -4}],
      "enfase": [{"em": "trancada", "pose": "e_maos_na_boca"}]},
 32: {"cena": cena("I03", (1.15, 1.25), (0.62, 0.5), (0.64, 0.48))},
 33: {"cena": cena("I13", ABERTO, (0.5, 0.5), (0.55, 0.48))},
 34: {"cena": cena("I13", FECHA, (0.6, 0.45), (0.67, 0.3))},
 35: {"cena": cena("I02b", (1.05, 1.15), (0.55, 0.45), (0.55, 0.5)), "enfase": [{"em": "sussurrava", "pose": "s_sussurro"}]},
 36: {"cena": cena("I14", ABERTO, (0.45, 0.5), (0.45, 0.48), lado="dir"), "ambiente": {"em": "coração", "som": "batimento", "volume_db": -6}},
 37: {"cena": cena("I13", (1.0, 1.04), (0.5, 0.5)), "ambiente": {"em": "despertador", "som": "casa_noite", "volume_db": -3}},
 38: {"cena": cena("I15", ABERTO, (0.5, 0.5), (0.5, 0.45))},
 39: {"cena": cena("I15", FECHA, (0.5, 0.45), (0.5, 0.4), em="bota"), "enfase": [{"em": "bota", "pose": "e_bracos_cruzados_cetico"}]},
 40: {},
 41: {"cena": VIGIA, "enfase": [{"em": "Agora", "pose": "e_sussurro_malicioso", "segurar": 2.4}]},
 42: {"cena": cena("I16", (1.35, 1.4), (0.45, 0.85), (0.6, 0.85)), "sons": [{"em": "gás", "som": "gas_vazando", "volume_db": -6}],
      "enfase": [{"em": "cheiro", "pose": "e_recuo_maos"}]},
 43: {"cena": cena("I16", ABERTO, (0.5, 0.6), (0.52, 0.45))},
 44: {"cena": cena("I16", (1.5, 1.55), (0.52, 0.24), (0.52, 0.22))},
 45: {"cena": cena("X1", (1.0, 1.06), (0.3, 0.35), (0.3, 0.3))},
 46: {"cena": cena("I17", ABERTO, (0.5, 0.5), (0.5, 0.45))},
 47: {"cena": cena("I17", CLOSE, (0.43, 0.22), (0.43, 0.2), em="Sonâmbula"), "enfase": [{"em": "nunca", "pose": "e_indignado"}]},
 48: {"cena": cena("I18", ABERTO, (0.5, 0.5), (0.4, 0.5))},
 49: {"cena": cena("I18", FECHA, (0.3, 0.45), (0.22, 0.45))},
 50: {"cena": cena("I18", (1.0, 1.04), (0.5, 0.5)), "tom": "sombrio"},
 51: {"cena": CCTV("I19", "23:00:00", vel=40), "ambiente": {"som": "estatica_cctv", "volume_db": -4}},
 52: {"cena": CCTV("I19", "01:00:00", vel=40)},
 53: {"cena": CCTV("I19", "02:50:00", (1.0, 1.3), (0.5, 0.45), (0.48, 0.28))},
 54: {"cena": CCTV("I19", "03:12:00", (1.3, 1.35), (0.48, 0.28))},
 55: {"cena": CCTV("I20", "03:12:04"), "sons": [{"em": "Alguém", "som": "impacto", "volume_db": -18, "grave": True}]},
 56: {},
 57: {"cena": CCTV("I20", "03:12:09", (1.4, 1.5), (0.27, 0.28), (0.27, 0.26)), "queda": {"forca": 0.8, "mais": 0.6},
      "sons": [{"em": "ele", "som": "impacto", "volume_db": -8, "grave": True}], "enfase": [{"em": "ele", "pose": "e_aterrorizado_maos", "segurar": 2.2}]},
 58: {"cena": CCTV("I20", "03:12:15", (1.0, 1.06), (0.5, 0.5))},
 59: {"cena": CCTV("I21", "03:13:02")},
 60: {"cena": CCTV("I22", "03:15:11", (1.0, 1.06), (0.6, 0.5), (0.68, 0.5)), "sons": [{"em": "faca", "som": "impacto", "volume_db": -10, "grave": True}],
      "enfase": [{"em": "faca", "pose": "e_maos_na_boca", "segurar": 2.2}], "ambiente": {"em": "faca", "som": "batimento", "volume_db": -5}},
 61: {"cena": CCTV("I22", "03:15:20", (1.3, 1.4), (0.82, 0.3), (0.82, 0.28))},
 62: {"cena": CCTV("I22", "03:15:41", (1.35, 1.45), (0.45, 0.35), (0.45, 0.33))},
 63: {"cena": CCTV("I23", "03:16:30"), "ambiente": {"som": "estatica_cctv", "volume_db": -4}},
 64: {"cena": CCTV("I23", "03:17:05", (1.2, 1.3), (0.8, 0.4), (0.85, 0.4)), "sons": [{"em": "Trancar", "som": "porta_tranca", "volume_db": -6}]},
 65: {"cena": cena("I24", ABERTO, (0.5, 0.5), (0.4, 0.4)), "ambiente": {"som": "casa_noite", "volume_db": -5}},
 66: {"cena": cena("I25", (1.3, 1.35), (0.5, 0.82), (0.5, 0.84)), "tom": "sombrio"},
 67: {"cena": cena("I25", ABERTO, (0.5, 0.5), (0.6, 0.45), em="Helena")},
 68: {"cena": cena("I25", FECHA, (0.6, 0.4), (0.68, 0.22))},
 69: {"cena": cena("I25", (1.45, 1.5), (0.68, 0.18), (0.68, 0.16)), "queda": {"forca": 0.6, "mais": 0.8}},
 70: {"pausa_antes_s": 0.8, "cena": cena("I06", (1.0, 1.05), (0.5, 0.5), em="Helena", desaturar=True),
      "cenas": [cena("I15", (1.1, 1.15), (0.5, 0.45), em="Escondendo", desaturar=True),
                cena("I16", (1.2, 1.25), (0.5, 0.8), em="Fechando", desaturar=True),
                cena("I24", (1.0, 1.05), (0.5, 0.5), em="Esperando", desaturar=True)], "tom": "sombrio"},
 71: {"cena": cena("X1", (1.0, 1.06), (0.3, 0.35), desaturar=True), "tom": "sombrio"},
 72: {"cena": cena("I01", (1.0, 1.08), (0.6, 0.35), desaturar=True), "enfase": [{"em": "vigia", "pose": "s_encarando", "segurar": 2.5}],
      "sons": [{"em": "vigia", "som": "impacto", "volume_db": -12, "grave": True}]},
 73: {"cena": CCTV("I22", "03:15:20", (1.0, 1.05), (0.5, 0.5)), "tom": "sombrio"},
 74: {"cena": VIGIA, "tom": "sombrio", "enfase": [{"em": "Agora", "pose": "e_apontando", "segurar": 1.8}]},
 75: {"enfase": [{"em": "Boa", "pose": "s_sorriso_sombrio", "segurar": 9}]},
}

batidas = []
for i, f in enumerate(falas):
    b = {"fala": f}
    b.update(d.get(i, {}))
    batidas.append(b)

roteiro = {
    "modo": "cenas", "formato": "16:9", "tema": "vigia", "avatar": "vigia_meio",
    "voz": {"modelo": "gemini-3.8-flash-tts", "nome": "Algenib", "so_texto": True},
    "voz_max_chars": 1400,
    "pausas": {"ponto": 0.75, "reticencias": 1.0, "virgula": 0.32, "comum": 0.14},
    "cauda": 1.4, "chuva": 0, "grao": 0.14,
    "legendas": {"destaques": ["sonâmbula", "faca", "facas", "vigia", "câmera"]},
    "ambiente_inicial": [{"som": "casa_noite", "volume_db": -3}],
    "musica": {"som": "drone_terror", "volume_db": -15},
    "abertura": {"imagem": "imagens/A1.png", "duracao": 2.8, "antes_da_batida": 8, "zoom": [1.04, 1.0]},
    "cta": {"titulo": "Gostou dessa história?", "canal": "Último Abrigo", "fundo": "imagens/V1.png",
            "subtitulo": "Inscreva-se para mais casos do Vigia", "pose": "e_apontando", "duracao": 3.6},
    "batidas": batidas,
}
(AQUI / "roteiro.json").write_text(json.dumps(roteiro, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"roteiro.json: {len(batidas)} batidas, "
      f"{sum(1 for b in batidas if 'cena' in b) + sum(len(b.get('cenas', [])) for b in batidas)} cortes de cena")
