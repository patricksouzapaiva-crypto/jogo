"""Junta as 10 faixas na ordem do episódio (para ouvir a trilha inteira): volume igualado (-18 LUFS), a volta do
silêncio do 08 (150 s) entra em fade (regra: sem pancada) e cada faixa emenda na seguinte com 4 s de crossfade.
Saída: Trilha_O_Vigia_Ep09.mp3 (e faixas_prontas/*.wav para a montagem)."""
import glob, subprocess
from pathlib import Path
AQUI = Path(__file__).parent; (AQUI / "faixas_prontas").mkdir(exist_ok=True)
CORRECAO = {"08_gut_mudang": "volume='if(between(t,149.9,153.5),(t-149.9)/3.6,1)':eval=frame,",
            # 14/11: o 12 entra com um tambor 14 dB acima a cada 4 s (pancada sob a voz): compressor achata as batidas
            "12_jangsan": "acompressor=threshold=0.03:ratio=20:attack=1:release=600:makeup=1,"}
fs = sorted(glob.glob(str(AQUI / "faixas" / "*.mp3")))
prontas = []
for f in fs:
    n = Path(f).stem; out = AQUI / "faixas_prontas" / f"{n}.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f, "-af", CORRECAO.get(n, "") + "loudnorm=I=-18:TP=-2:LRA=14",
                    "-ar", "44100", str(out)], check=True)
    prontas.append(out)
args = []; [args.extend(["-i", str(p)]) for p in prontas]
filt, ant = "", "[0]"
for k in range(1, len(prontas)):
    filt += f"{ant}[{k}]acrossfade=d=4:c1=tri:c2=tri[x{k}];"; ant = f"[x{k}]"
subprocess.run(["ffmpeg", "-v", "error", "-y", *args, "-filter_complex", filt.rstrip(";"), "-map", ant,
                "-b:a", "192k", str(AQUI / "Trilha_O_Vigia_Ep09.mp3")], check=True)
print("ok")
# instala as faixas no motor: painel/sons/ep09_m<nome>.mp3 (já com o volume igualado e a correção do 08)
SONS = AQUI.parents[2] / "painel" / "sons"
for p in prontas:
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(p), "-b:a", "192k", str(SONS / f"ep09_m{p.stem}.mp3")], check=True)
print("instaladas no motor:", len(prontas))
