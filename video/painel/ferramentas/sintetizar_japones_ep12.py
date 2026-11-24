"""Trilha do Ep. 12 (Demônios do Japão, 24/11) — irmã mais escura da trilha japonesa do Ep. 08 (a do episódio que
mais deu resultado): koto uma oitava abaixo, shakuhachi com frases longas e "ma" (silêncio) entre elas, um taiko grave
e lento como um coração, batida seca de hyoshigi (as duas madeiras) de vez em quando e um cello grave com trítono
(ré–lá♭) segurando o medo. Escala IN em ré (ré–mi♭–sol–lá–si♭).
Uso: python3 sintetizar_japones_ep12.py saida.mp3 [segundos]"""
import subprocess, sys
import numpy as np
from sintetizar_trilha import SR, cordas, hz
from sintetizar_caixinha_ep06 import cello, Mesa
from sintetizar_caixinha_ep08 import koto, rin
import sintetizar_japones_ep08 as J

rng = np.random.default_rng(1212); J.rng = rng
KOTO = ["D3", "Eb3", "G3", "A3", "Bb3", "D4", "Eb4", "G4"]
FLAUTA = ["D4", "Eb4", "G4", "A4", "Bb4"]


def taiko(vel=0.35, dur=2.4):
    n = int(dur * SR); t = np.arange(n) / SR
    f = 46 + 40 * np.exp(-t / 0.05)
    corpo = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.55)
    pele = rng.standard_normal(n) * np.exp(-t / 0.025) * 0.25
    s = corpo + pele
    return s / (np.abs(s).max() + 1e-9) * vel


def hyoshigi(vel=0.18):
    n = int(0.5 * SR); t = np.arange(n) / SR
    s = (np.sin(2 * np.pi * 1850 * t) + 0.6 * np.sin(2 * np.pi * 2790 * t)) * np.exp(-t / 0.03)
    s += rng.standard_normal(n) * np.exp(-t / 0.006) * 0.5
    return s / (np.abs(s).max() + 1e-9) * vel


def compor(dur):
    M = Mesa(dur); t = 0.5; k = 0
    while t < dur:
        M.por(cello(hz("D2"), 18.5, vel=0.16), t)
        M.por(cordas([hz("D2"), hz("Ab2")], 14.0, vel=0.04, ataque=6.0), t + 2.0)
        # coração: duas batidas graves, longe, a cada ciclo par
        if k % 2 == 0:
            for j in range(4):
                M.por(taiko(0.30), t + 4.0 + j * 1.9); M.por(taiko(0.16), t + 4.45 + j * 1.9)
        tk = t + 1.0
        if k % 4 == 3:
            for j, nt in enumerate(reversed(KOTO)):
                M.por(koto(hz(nt), vel=0.09, dur=3.5), tk + j * 0.09)
            tk += 2.8
        for j in range(int(rng.integers(3, 5))):
            nt = KOTO[int(rng.integers(0, 6))]
            M.por(koto(hz(nt), vel=0.16, dur=5.0), tk)
            if rng.random() < 0.25: M.por(koto(hz(nt), vel=0.09, dur=4.0), tk + 0.2)
            tk += 0.9 + 1.1 * rng.random()
        if k % 2 == 1:
            tf = t + 6.5
            for j in range(int(rng.integers(2, 4))):
                d = 3.2 + 2.6 * rng.random()
                M.por(J.shakuhachi(hz(FLAUTA[int(rng.integers(0, len(FLAUTA)))]), d, vel=0.10), tf)
                tf += d + 0.6 + 1.0 * rng.random()
        if k % 5 == 4:
            M.por(hyoshigi(0.16), t + 15.0); M.por(hyoshigi(0.12), t + 15.35)
        if k % 3 == 2: M.por(rin(hz("A4"), vel=0.05), t + 13.0)
        t += 18.0; k += 1
    return M.sair(0.5)


if __name__ == "__main__":
    saida = sys.argv[1]; dur = float(sys.argv[2]) if len(sys.argv) > 2 else 600.0
    m = compor(dur).astype(np.float32)
    est = np.stack([m, np.roll(m, int(0.013 * SR))], 1)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-af",
                    "highpass=f=38,acompressor=threshold=-30dB:ratio=2.5:attack=300:release=2500:makeup=2,loudnorm=I=-20:TP=-3:LRA=7",
                    "-ar", "44100", "-b:a", "192k", saida], input=est.tobytes(), check=True)
    print("ok", saida, f"{dur:.0f}s")
