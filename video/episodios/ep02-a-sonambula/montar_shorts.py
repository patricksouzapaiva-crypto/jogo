"""Monta os Shorts de divulgação (9:16) a partir do episódio longo, reaproveitando a narração dele.
Uso: python montar_shorts.py <video_longo.mp4.tempos.json> <voz_pausas.wav do mesmo render>"""
import copy, json, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "painel"))
from gerar import tokens  # noqa: E402

AQUI = Path(__file__).parent
longo = json.load(open(AQUI / "roteiro.json"))
tempos = json.load(open(sys.argv[1]))["palavras"]
voz = sys.argv[2]
VOZ0 = 0.4  # início da voz no vídeo longo

# índice da 1ª palavra de cada batida
ini, k = [], 0
for b in longo["batidas"]:
    ini.append(k); k += len(tokens(b["fala"]))

SHORTS = [
    {"nome": "s1_voce_nao_devia", "de": 0, "ate": 7, "titulo": "Quer saber o que ela fazia?",
     "musica": [(2, "trilha_tensa_1", "silencioso", -22), (7, "silencio", "Você", -40)], "ambiente": []},
    {"nome": "s2_a_gravacao", "de": 53, "ate": 62, "titulo": "Quer ver o resto da gravação?",
     "musica": [(53, "trilha_tensa_2", None, -21), (55, "silencio", "Sentou", -40)], "ambiente": [(56, "estatica_cctv", None, -4)]},
    {"nome": "s3_a_poltrona", "de": 36, "ate": 42, "titulo": "Quer saber por que ela disse isso?",
     "musica": [(36, "trilha_tensa_2", None, -21), (41, "silencio", "disse", -40)], "ambiente": [(36, "batimento", "coração", -9), (37, "nenhum", "despertador", -40)]},
]

FOCO_SHORT = {"I20": (0.28, 0.35), "I13": (0.66, 0.4), "I19": (0.45, 0.4)}

(AQUI / "shorts").mkdir(exist_ok=True)
for S in SHORTS:
    a, b = S["de"], S["ate"]
    p0 = ini[a]; p1 = ini[b + 1] - 1 if b + 1 < len(ini) else len(tempos) - 1
    t0 = max(0.0, tempos[p0][1] - VOZ0 - 0.25)
    t1 = tempos[p1][2] - VOZ0 + 0.6
    arq = AQUI / "shorts" / f"{S['nome']}_voz.wav"
    if not arq.exists():  # reaproveita o recorte de voz já feito
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t0:.3f}", "-to", f"{t1:.3f}", "-i", voz, str(arq)], check=True)
    bat = copy.deepcopy(longo["batidas"][a:b + 1])
    for x in bat:
        for ch in ("musica", "ambiente", "pausa_antes_s"):
            x.pop(ch, None)
        for c in ([x["cena"]] if x.get("cena") else []) + x.get("cenas", []):
            if c.get("imagem"):
                c["imagem"] = "../" + c["imagem"]
            c.pop("lado", None)
            c["encaixe"] = "cobrir"   # Short: imagem ocupa a tela toda, recortada no foco
            nome = Path(c.get("imagem", "")).stem
            if nome in FOCO_SHORT:     # no vertical, o recorte precisa achar o personagem
                fx, fy = FOCO_SHORT[nome]
                c["foco"] = [[fx, c["foco"][0][1]], [fx, fy]]
    if not bat[0].get("cena"):
        raise SystemExit(f"{S['nome']}: a 1ª batida precisa de imagem")
    bat[0]["cena"].pop("em", None)
    for (i, som, em, db) in S["musica"]:
        bat[i - a]["musica"] = {"som": som, "volume_db": db, **({"em": em} if em else {})}
    for (i, som, em, db) in S["ambiente"]:
        bat[i - a]["ambiente"] = {"som": som, "volume_db": db, **({"em": em} if em else {})}
    r = {k: v for k, v in longo.items() if k not in ("batidas", "abertura", "formato", "voz_max_chars", "canto", "canto_destaque")}
    # Vigia em alta resolução (poses equivalentes) e cenário da torre
    MAPA = {"e_recuo_maos": "e_pare", "e_indignado": "e_bracos_cruzados_cetico", "e_susto_recuando": "e_aterrorizado_maos",
            "e_sussurro_malicioso": "c_sussurrando", "e_desespero_cabeca": "e_aterrorizado_maos", "e_serio_ameaçador": "s_encarando",
            "e_plano_sinistro": "s_sorriso_sombrio", "e_sorriso_insano": "s_sorriso_sombrio", "e_encarando": "s_encarando",
            "s_olhar_lado": "c_desconfiado_lado", "s_pensativo_queixo": "c_pensativo_queixo", "s_sussurro": "c_sussurrando",
            "s_pare": "e_pare", "s_serio": "c_serio_frontal", "s_desconfiado_ombro": "c_desconfiado_lado"}
    for x in bat:
        for en in x.get("enfase", []):
            en["pose"] = MAPA.get(en["pose"], en["pose"])
        if x.get("tom") == "sombrio":
            x.pop("tom")
    for x in bat:
        for c in ([x["cena"]] if x.get("cena") else []) + x.get("cenas", []):
            if c.get("vigia"):
                c["imagem"] = "../../../painel/cenarios/abrigo_vertical.png"
    r.update({"avatar": "vigia_hd",
              "mix": {"musica_ganho_db": 12, "fundo_sob_voz": -8, "efeitos_sob_voz": -3}})
    r.update({"formato": "9:16", "voz_arquivo": arq.name, "batidas": bat, "cauda": 1.0,
              "musica": {"som": "silencio", "volume_db": -40}, "ambiente_inicial": [],
              "legendas": dict(longo["legendas"]),
              "cta": {"titulo": S["titulo"], "canal": "Último Abrigo", "subtitulo": "História completa no canal",
                      "fundo": "../../../painel/cenarios/abrigo_vertical.png", "pose": "c_cafe_convite", "duracao": 3.4}})
    (AQUI / "shorts" / f"{S['nome']}.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    print(S["nome"], f"{t1 - t0:.1f}s de narração")
