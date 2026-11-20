"""Fim do Ep. 11 (20/11, usuário: "no fim do vídeo, quando a tela escurecer, use o fundo nórdico com essa voz e os
tambores"): depois do convite do Vigia a tela escurece e fica só o som. Por baixo, o bordão ré–lá da trilha (o fundo
nórdico). Por cima, um tambor de ritual lento no compasso da polska (TUM . tum), que incha e depois some. O tema
volta bem baixo nas violas. Em cima de tudo, o kulning (a voz da mata), afinado de dó menor para ré menor e com o
reverb do salão de pedra.
Uso: python3 compor_fim.py kulning.mp3 saida.wav [duracao=32]"""
import subprocess, sys
from pathlib import Path
import numpy as np
import soundfile as sf
from compor_orquestra import Orquestra, TEMA, Q, BAR, bordao

voz, saida = sys.argv[1], Path(sys.argv[2]); D = float(sys.argv[3]) if len(sys.argv) > 3 else 32.0
o = Orquestra(D + 2)
bordao(o, 0.0, D, 0.6); o.cresc("cb", "D2", 0.0, D, 0.5, 0.35)
o.cresc("vla_trem", "A3", 8.0, D - 12, 0.02, 0.18, pan=0.3)
# o tambor: 1º tempo forte, 3º fraco; entra devagar, incha até ~70% e se desfaz
t, k = 2.0, 0
while t < D - 4:
    x = t / (D - 4); env = min(1.0, x / 0.7) if x < 0.7 else max(0.25, 1 - (x - 0.7) / 0.3 * 0.75)
    o.golpe("bumbo", t, 0.25 + 0.55 * env, k); o.golpe("bumbo", t + 2 * Q, 0.12 + 0.25 * env, k + 5)
    if k % 2 == 0: o.golpe("timp", t, 0.2 + 0.45 * env, k)
    t += BAR; k += 1
o.golpe("timp", D - 3.6, 1.0, 5); o.golpe("bumbo", D - 3.6, 1.1, 13)
# o tema, longe e lento, nas violas (uma oitava abaixo)
t = 6.0
for nt, q in TEMA[:18]:
    if t > D - 6: break
    o.nota("vla", nt[:-1] + str(int(nt[-1]) - 1), t, q * Q * 1.4, 0.32, ataque=0.15, solta=0.6, pan=-0.25); t += q * Q * 1.35
orq = saida.with_suffix(".orq.wav"); o.salvar(orq, rev=0.36, corte=D)

# a voz: +2 semitons (dó menor → ré menor), sem o grave, com o salão de pedra (ecos longos) e entrando aos 3 s
kul = saida.with_suffix(".voz.wav")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", voz, "-af",
                f"rubberband=pitch={2 ** (2 / 12):.5f}:formant=preserved,highpass=f=220,"
                "aecho=0.8:0.55:620|1340|2210:0.3|0.18|0.1,adelay=3000|3000,"
                f"atrim=0:{D},afade=t=out:st={D - 7}:d=6", "-ar", "44100", "-ac", "2", str(kul)], check=True)
a, _ = sf.read(orq, dtype="float32"); b, _ = sf.read(kul, dtype="float32")
n = int(D * 44100); a = np.pad(a, ((0, max(0, n - len(a))), (0, 0)))[:n]; b = np.pad(b, ((0, max(0, n - len(b))), (0, 0)))[:n]
y = a * 0.85 + b * 0.62
f = int(3.0 * 44100); y[-f:] *= np.linspace(1, 0, f)[:, None] ** 1.5
y /= np.abs(y).max() / 0.89
sf.write(saida, y, 44100); orq.unlink(); kul.unlink()
print("ok", saida)
