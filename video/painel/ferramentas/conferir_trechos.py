"""28/11 (Cinema #2, rascunhos 1 e 2: o som do filme tocava 15 s antes da cena): confere, num vídeo pronto, se o som de
cada trecho de filme (filmes_prontos/<nome>.wav) cai junto da imagem dele. Usa o <vídeo>.tempos.json do gerar.py.
Uso: python3 conferir_trechos.py <pasta do episódio> <vídeo.mp4>   → sai com código 1 se algum trecho estiver fora."""
import json, subprocess, sys, tempfile
from pathlib import Path
import numpy as np, soundfile as sf
from scipy.signal import fftconvolve

ep, video = Path(sys.argv[1]), Path(sys.argv[2])
tmp = Path(tempfile.mkdtemp())
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-ac", "1", "-ar", "8000", str(tmp / "v.wav")], check=True)
x, sr = sf.read(tmp / "v.wav")
cenas = {}
for c in json.load(open(str(video) + ".tempos.json"))["cenas"]:
    cenas.setdefault(Path(c["arquivo"]).stem, []).append(c["t0"])
ruins = 0
for wav in sorted((ep / "filmes_prontos").glob("*.wav")):
    n = wav.stem
    if n not in cenas:
        continue
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(wav), "-ac", "1", "-ar", "8000", str(tmp / "c.wav")], check=True)
    c, _ = sf.read(tmp / "c.wav"); c = c / (np.linalg.norm(c) + 1e-9)
    for t_img in cenas[n]:   # procura perto de cada aparição (± 30 s)
        i0, i1 = max(0, int((t_img - 30) * sr)), min(len(x), int((t_img + 30) * sr) + len(c))
        seg = x[i0:i1]
        cc = fftconvolve(seg, c[::-1], "valid"); j = int(np.argmax(np.abs(cc)))
        w = seg[j:j + len(c)]; q = abs(np.dot(w, c)) / (np.linalg.norm(w) + 1e-9); t = (i0 + j) / sr
        ok = abs(t - t_img) < 1.2 and q > 0.5
        ruins += not ok
        print(f"{'ok ' if ok else '!! '} {n:14s} imagem {t_img:8.2f}  som {t:8.2f}  dif {t - t_img:+6.2f}  semelhança {q:.2f}")
print("FORA DO LUGAR:", ruins)
sys.exit(1 if ruins else 0)
