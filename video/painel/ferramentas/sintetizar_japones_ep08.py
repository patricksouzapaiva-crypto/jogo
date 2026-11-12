"""Trilha do Ep. 08 — versão "estilo japonês" (pedido do usuário em 12/11): no lugar da caixinha de música, o koto
toca a melodia e a flauta shakuhachi sopra frases longas (meri: começa abaixo do tom e sobe; sopro audível; vibrato só
no fim da nota); entre as frases, silêncio de verdade ("ma"), com o cello grave e a taça de templo segurando o fundo.
Escala IN (ré–mi♭–sol–lá–si♭). Sem pancadas.
Uso: python3 sintetizar_japones_ep08.py saida.mp3 [segundos]"""
import subprocess, sys
import numpy as np
from sintetizar_trilha import SR, cordas, hz
from sintetizar_caixinha_ep06 import cello, Mesa
from sintetizar_caixinha_ep08 import koto, rin

rng = np.random.default_rng(1308)
KOTO = ["D4", "Eb4", "G4", "A4", "Bb4", "D5", "Eb5", "G5"]
FLAUTA = ["D4", "Eb4", "G4", "A4", "Bb4", "D5"]


def shakuhachi(f, dur, vel=0.12):
    n = int(dur * SR); t = np.arange(n) / SR
    meri = -75 * np.exp(-t / 0.45) * (1 if rng.random() < 0.7 else 0)            # entra abaixo e sobe
    vib = 18 * np.sin(2 * np.pi * 5.0 * t) * np.clip((t - dur * 0.55) / (dur * 0.3), 0, 1)
    fi = f * 2 ** ((meri + vib) / 1200)
    ph = 2 * np.pi * np.cumsum(fi) / SR
    tom = np.sin(ph) + 0.30 * np.sin(2 * ph) + 0.10 * np.sin(3 * ph) + 0.04 * np.sin(4 * ph)
    # sopro: ruído filtrado em faixas nos harmônicos (FFT) + um pouco de ar largo
    N = 1 << (n - 1).bit_length(); fr = np.fft.rfftfreq(N, 1 / SR)
    R = np.fft.rfft(rng.standard_normal(N))
    g = sum(a * np.exp(-((fr - f * k) / (f * 0.09)) ** 2) for k, a in ((1, 1.0), (2, 0.5), (3, 0.25)))
    g += 0.06 * np.exp(-((fr - 2500) / 1800) ** 2)
    ar = np.fft.irfft(R * g, N)[:n]; ar /= np.abs(ar).max() + 1e-9
    # envelope de sopro: entra com ar ("chiff"), cresce e some devagar
    env = np.minimum(1, t / 0.35) * np.minimum(1, (dur - t) / 0.9).clip(0) * (0.75 + 0.25 * np.sin(np.pi * t / dur))
    chiff = np.exp(-t / 0.12)
    s = tom * 0.8 * env + ar * (0.28 * env + 0.9 * chiff * np.minimum(1, t / 0.02))
    return s / (np.abs(s).max() + 1e-9) * vel


def compor(dur):
    M = Mesa(dur); t = 0.5; k = 0
    while t < dur:
        M.por(cello(hz("D2"), 17.5, vel=0.15), t)
        if k % 2: M.por(cordas([hz("A2"), hz("Eb3")], 12.0, vel=0.045, ataque=5.0), t + 3.5)
        # koto: frase curta, rubato; às vezes nota repetida (sukui) ou glissando descendente
        tk = t + 0.8
        if k % 4 == 3:
            for j, nt in enumerate(reversed(KOTO)):
                M.por(koto(hz(nt), vel=0.10, dur=3.0), tk + j * 0.07)
            tk += 2.5
        for j in range(int(rng.integers(3, 6))):
            nt = KOTO[int(rng.integers(0, 6))]
            M.por(koto(hz(nt), vel=0.17), tk)
            if rng.random() < 0.2: M.por(koto(hz(nt), vel=0.10), tk + 0.18)
            tk += 0.7 + 0.9 * rng.random()
        # shakuhachi: 2–3 notas longas em ciclos alternados, começando depois do koto
        if k % 2 == 0:
            tf = t + 7.5
            for j in range(int(rng.integers(2, 4))):
                d = 2.8 + 2.4 * rng.random()
                M.por(shakuhachi(hz(FLAUTA[int(rng.integers(0, len(FLAUTA)))]), d, vel=0.11), tf)
                tf += d + 0.4 + 0.8 * rng.random()
        if k % 3 == 2: M.por(rin(hz("A4"), vel=0.06), t + 12.0)
        t += 17.0; k += 1
    return M.sair(0.5)


if __name__ == "__main__":
    saida = sys.argv[1]; dur = float(sys.argv[2]) if len(sys.argv) > 2 else 600.0
    m = compor(dur).astype(np.float32)
    est = np.stack([m, np.roll(m, int(0.013 * SR))], 1)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-af",
                    "highpass=f=55,acompressor=threshold=-30dB:ratio=2.5:attack=300:release=2500:makeup=2,loudnorm=I=-20:TP=-3:LRA=7",
                    "-ar", "44100", "-b:a", "192k", saida], input=est.tobytes(), check=True)
    print("ok", saida, f"{dur:.0f}s")
