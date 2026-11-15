"""Vitrine da identidade do Ep. 10 (Tailândia, 16/11): os 4 cartões de capítulo com o pano Pha Yant, cada um com a
SUA música (ep10_cap1..4), a câmera de segurança do Mateus (CCTV) e a transição de obturador do dossiê.
Imagens de fundo provisórias (as do Ep. 10 ainda estão sendo feitas).
Uso: python3 vitrine_tailandia.py [--rascunho]  → episodios/ep10-tailandia/previas/vitrine_tailandia.mp4"""
import json, subprocess, sys, tempfile
from pathlib import Path
AQUI = Path(__file__).resolve().parents[1]; EP = AQUI.parent / "episodios" / "ep10-tailandia"
PROV = AQUI.parent / "episodios" / "ep09-coreia" / "imagens_v4" / "escolhidas"
SONS = AQUI / "sons"
im = lambda n: str(PROV / f"{n}.jpg")
av_dir = AQUI / "avatares" / "vigia_hd"; av = json.load(open(av_dir / "poses.json"))
C, SOM = [], []
def cena(dur, **c):
    t0 = C[-1]["t1"] if C else 0.0
    C.append({"t0": t0, "t1": t0 + dur, **c}); return t0
def som(t, nome, db): SOM.append((t, nome, db))

CAPS = [(1, "O aluguel da terra e os famintos", "Século XIX → hoje", "vermelho", "M03"),
        (2, "As criaturas da noite", "Folclore rural de Isan", "vermelho", "M08"),
        (3, "Os corpos emprestados e a magia proibida", "A tradição Rang Song", "branco", "H01"),
        (4, "Quando a câmera entrou na floresta", "Loei · 2021", "vermelho", "H03")]
for n, tit, ano, cor, fundo in CAPS:
    t = cena(7.6, tipo="pha_yant", numero=n, numero_pt=f"Capítulo {n}", titulo=tit, ano=ano, cor=cor, imagem=im(fundo),
             entrada="obturador" if n > 1 else None, duracao_entrada=0.5)
    som(t, f"ep10_cap{n}", 0); som(t + 0.05, "ep10_pano", -8); som(t + 1.6, "ep10_tambor_ritual_1", -12)
    if n == 2:   # entre o 2 e o 3: a câmera de segurança, com o obturador e a queda do Wi-Fi
        t = cena(4.5, imagem=im("H03"), zoom=[1.0, 1.03], entrada="obturador", duracao_entrada=0.5,
                 efeitos={"cctv": {"cam": "CAM 01 - CORREDOR", "hora": "02:40:18", "data": "18-09-2025"}})
        som(t, "ep10_obturador", -4); som(t, "ep10_cctv_estatica", -6)
        t = cena(4.5, imagem=im("H06"), zoom=[1.0, 1.02], entrada="obturador", duracao_entrada=0.5,
                 efeitos={"cctv": {"cam": "CAM 02 - QUARTO", "hora": "03:17:09", "data": "18-09-2025", "queda": 2.6}})
        som(t, "ep10_obturador", -4); som(t, "ep10_cctv_estatica", -6); som(t + 2.6, "ep10_queda_wifi", -4)
    else:
        som(t - 0.25 if n > 1 else 0, "ep10_obturador", -6)
dur = C[-1]["t1"] + 0.6
tema = json.load(open(AQUI / "temas" / "vigia.json"))
D = {"modo": "cenas", "W": 1920, "H": 1080, "fps": 30, "duracao": dur, "tema": tema,
     "avatar": {"base": str(av_dir) + "/", "tipo": av.get("tipo", "busto"), "mediana": av.get("largura_cabeca_mediana"), "poses": av["poses"]},
     "canto": {"x": 40, "w": 250, "base": 1070}, "canto_destaque": {"x": 60, "w": 560, "base": 1120}, "legenda_y": 988, "legenda_tam": 50,
     "chuva": 0, "grao": 0.12, "cintilar": 0.02, "vigia_padrao": False, "cenas": C, "poses": [], "legendas": [], "escuros": []}
tmp = Path(tempfile.mkdtemp(prefix="vitrine_")); (tmp / "linha.json").write_text(json.dumps(D, ensure_ascii=False))
cmd = ["node", str(AQUI / "render.js"), str(tmp / "linha.json"), str(tmp / "v.mp4")] + (["--rascunho"] if "--rascunho" in sys.argv else [])
REUSO = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--video=")), None)   # só refaz o som
if REUSO:
    (tmp / "v.mp4").symlink_to(REUSO)
else:
    subprocess.run(cmd, check=True)
# som: a trilha da 1ª metade por baixo (baixa: o cartão é da música do capítulo) + música de cada cartão + efeitos
leito = EP / "trilha" / "previa_cordas.mp3"
ins, flt = ["-stream_loop", "-1", "-i", str(leito)], [f"[1]atrim=0:{dur},afade=t=out:st={dur - 1.5}:d=1.5,volume=-16dB[m]"]
for k, (ts, nome, db) in enumerate(SOM, 1):
    ins += ["-i", str(SONS / f"{nome}.mp3")]
    flt.append(f"[{k + 1}]aformat=channel_layouts=stereo,volume={db}dB,adelay={int(ts * 1000)}|{int(ts * 1000)}[s{k}]")
flt.append("[m]" + "".join(f"[s{k}]" for k in range(1, len(SOM) + 1)) + f"amix=inputs={len(SOM) + 1}:normalize=0,alimiter=limit=0.9[a]")
(EP / "previas").mkdir(exist_ok=True)
saida = EP / "previas" / "vitrine_tailandia.mp4"
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(tmp / "v.mp4"), *ins, "-filter_complex", ";".join(flt), "-map", "0:v", "-map", "[a]",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(saida)], check=True)
print("ok", saida, f"{dur:.1f}s")
