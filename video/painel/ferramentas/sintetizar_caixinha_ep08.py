"""Trilha do Ep. 08 (terror japonês): a mesma linguagem aprovada (caixinha de música + cello + sino, baixa, sem
pancadas), em escala IN japonesa (ré–mi♭–sol–lá–si♭), com koto beliscado raro e taça de templo (rin) distante.
Uso: python3 sintetizar_caixinha_ep08.py tensao saida.mp3 [segundos]"""
import subprocess, sys
import numpy as np
from sintetizar_trilha import SR, cordas, hz, reverb
from sintetizar_caixinha_ep06 import caixinha, cello, Mesa

rng = np.random.default_rng(808)
ESCALA = ["D5", "Eb5", "G5", "A5", "Bb5", "D6", "Eb6", "G6"]


def koto(f, vel=0.18, dur=4.0):
    """Corda beliscada (Karplus-Strong) com a "dobra" de tom do koto no ataque."""
    n = int(dur * SR); p = max(2, int(SR / f)); buf = rng.uniform(-1, 1, p); out = np.zeros(n)
    for i in range(n):
        out[i] = buf[i % p]; buf[i % p] = 0.996 * 0.5 * (buf[i % p] + buf[(i + 1) % p])
    t = np.arange(n) / SR
    return out * np.exp(-t * 0.9) * vel


def rin(f, vel=0.08, dur=10.0):
    """Taça de templo: parciais inarmônicos longos, batimento lento."""
    n = int(dur * SR); t = np.arange(n) / SR; s = np.zeros(n)
    for r, a, d in ((1.0, 1.0, 0.18), (2.71, 0.5, 0.3), (5.12, 0.25, 0.5), (8.2, 0.1, 0.8)):
        s += a * np.sin(2 * np.pi * f * r * t + rng.random() * 6) * np.exp(-t * d) * (1 + 0.2 * np.sin(2 * np.pi * 0.9 * t))
    return s * np.minimum(1, t / 0.005) * vel


def tensao(dur=600.0, tempo=1.0):
    M = Mesa(dur); t = 0.5; k = 0
    while t < dur:
        M.por(cello(hz("D2"), 15.5, vel=0.19), t)
        if k % 2: M.por(cordas([hz("Eb3")], 11.0, vel=0.06, ataque=4.5), t + 3.0)      # meio-tom: inquietação
        tv = t + 1.2
        for j in range(5):
            nota = ESCALA[int(rng.integers(0, len(ESCALA)))]
            if rng.random() < 0.8:
                M.por(caixinha(hz(nota), vel=0.19, dur=3.8, desafina=rng.uniform(-30, 30)), tv)
            tv += tempo * (1.0 + 0.7 * rng.random()) * (1 + 0.12 * j)
        if k % 3 == 1: M.por(koto(hz(["D4", "G4", "A4"][k % 3]), vel=0.16), t + 6.5)
        if k % 3 == 2: M.por(rin(hz("A4"), vel=0.07), t + 8.0)
        t += 14.0; k += 1
    return M.sair(0.55)


if __name__ == "__main__":
    modo, saida = sys.argv[1], sys.argv[2]
    dur = float(sys.argv[3]) if len(sys.argv) > 3 else 600.0
    m = tensao(dur).astype(np.float32)
    est = np.stack([m, np.roll(m, int(0.011 * SR))], 1)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-af",
                    "highpass=f=55,treble=g=7:f=3500:t=s,acompressor=threshold=-30dB:ratio=2.5:attack=300:release=2500:makeup=2,loudnorm=I=-20:TP=-3:LRA=7",
                    "-ar", "44100", "-b:a", "192k", saida], input=est.tobytes(), check=True)
    print("ok", saida, f"{dur:.0f}s")
