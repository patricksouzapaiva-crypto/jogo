"""Vitrine da identidade coreana (Ep. 09 v4, 15/11): ~50 s com o cartão-talismã, as transições novas e as cenas
exclusivas de cada história, com som, para aprovação ANTES das imagens novas chegarem (imagens provisórias do v3).
Uso: python3 vitrine_coreia.py [--rascunho]  → episodios/ep09-coreia/previas/vitrine_coreia.mp4"""
import json, subprocess, sys, tempfile
from pathlib import Path
AQUI = Path(__file__).resolve().parents[1]; EP = AQUI.parent / "episodios" / "ep09-coreia"; IM = EP / "imagens_v3"
SONS = AQUI / "sons"
im = lambda n: str(IM / f"{n}.jpg")
av_dir = AQUI / "avatares" / "vigia_hd"; av = json.load(open(av_dir / "poses.json"))
C = []
def cena(dur, **c):
    t0 = C[-1]["t1"] if C else 0.0
    C.append({"t0": t0, "t1": t0 + dur, **c}); return t0
SOM = []
def som(t, nome, db, **kw): SOM.append((t, nome, db, kw))

t = cena(5.4, tipo="talisma", numero="제1장", numero_pt="Capítulo 1", titulo="O quarto do magistrado", ano="Miryang · séc. XVI", selo="恨", imagem=im("J01_A"))
som(t + 0.05, "ep09_papel", -14); som(t + 0.55, "ep08_pincel", -12); som(t + 1.9, "ep09_gut_jing_1", -9); som(t + 2.3, "ep08_tinta", -16)
t = cena(7.0, tipo="sombra", entrada="queimar", chega=[1.2, 5.0], vela=[0.09, 0.78])
som(t - 0.2, "ep08_vela", -12); som(t + 1.0, "ep09_sn_horror_whoosh", -16)
t = cena(5.4, tipo="talisma", entrada="hanji", numero="제2장", numero_pt="Capítulo 2", titulo="As irmãs do lago", ano="Cheolsan · séc. XVII", selo="怨", imagem=im("M03_A"))
som(t + 0.05, "ep09_papel", -14); som(t + 0.55, "ep08_pincel", -12); som(t + 1.9, "ep09_gut_jing_2", -9)
t = cena(6.5, tipo="agua", entrada="queimar", imagem=im("M01_A"), horizonte=0.6, afunda=[0.52, 0.8, 2.6])
t = cena(6.5, tipo="crt", entrada="rasgo", imagem=im("J03_A"), liga=0.25, rolar=[3.2], desliga=0.7)
som(t, "ep08_tv_chiado", -18)
t = cena(6.5, tipo="sumuk", entrada="hanji", imagem=im("J02_A"), pintar=4.2, vermelho=[[0.47, 0.42]])
som(t + 0.3, "ep08_pincel", -13); som(t + 2.2, "ep08_pincel", -15)
t = cena(5.0, imagem=im("M04_A"), zoom=[1.0, 1.04], efeitos={"flash": {"em": 1.4, "imagem": im("M07_A")}})
som(t + 1.4, "impacto", -10, grave=True)
t = cena(6.0, tipo="elevador", entrada="fundir", sequencia=[[4, 0.5], [2, 1.1], [6, 1.7], [2, 2.3], [10, 2.9], [5, 4.3]])
som(t, "ep09_elevador_tenso", -20)
t = cena(6.0, entrada="rasgo", imagem=im("H02_A"), zoom=[1.0, 1.1], efeitos={"aovivo": {"espectadores": [1203, 4870], "travar": [3.4]}})
som(t, "estatica_cctv", -22)
dur = C[-1]["t1"] + 0.6
tema = json.load(open(AQUI / "temas" / "vigia.json"))
D = {"modo": "cenas", "W": 1920, "H": 1080, "fps": 30, "duracao": dur, "tema": tema,
     "avatar": {"base": str(av_dir) + "/", "tipo": av.get("tipo", "busto"), "mediana": av.get("largura_cabeca_mediana"), "poses": av["poses"]},
     "canto": {"x": 40, "w": 250, "base": 1070}, "canto_destaque": {"x": 60, "w": 560, "base": 1120}, "legenda_y": 988, "legenda_tam": 50,
     "chuva": 0, "grao": 0.14, "cintilar": 0.02, "vigia_padrao": False, "cenas": C, "poses": [], "legendas": [], "escuros": []}
tmp = Path(tempfile.mkdtemp(prefix="vitrine_")); (tmp / "linha.json").write_text(json.dumps(D, ensure_ascii=False))
cmd = ["node", str(AQUI / "render.js"), str(tmp / "linha.json"), str(tmp / "v.mp4")] + (["--rascunho"] if "--rascunho" in sys.argv else [])
REUSO = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--video=")), None)   # só refaz o som
if REUSO:
    (tmp / "v.mp4").symlink_to(REUSO)
else:
    subprocess.run(cmd, check=True)
# som: trilha do Ep. 08 por baixo + os efeitos nos instantes certos
ins, flt = ["-i", str(SONS / "ep08_japones_longa.mp3")], [f"[1]atrim=0:{dur},afade=t=out:st={dur - 1.5}:d=1.5,volume=-12dB[m]"]
for k, (ts, nome, db, kw) in enumerate(SOM, 1):
    ins += ["-i", str(SONS / f"{nome}.mp3")]
    flt.append(f"[{k + 1}]{'lowpass=f=900,' if kw.get('grave') else ''}volume={db}dB,adelay={int(ts * 1000)}|{int(ts * 1000)}[s{k}]")
flt.append("[m]" + "".join(f"[s{k}]" for k in range(1, len(SOM) + 1)) + f"amix=inputs={len(SOM) + 1}:normalize=0,alimiter=limit=0.9[a]")
saida = EP / "previas" / "vitrine_coreia.mp4"
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(tmp / "v.mp4"), *ins, "-filter_complex", ";".join(flt), "-map", "0:v", "-map", "[a]",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(saida)], check=True)
print("ok", saida, f"{dur:.1f}s")
