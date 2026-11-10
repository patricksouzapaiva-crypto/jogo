"""Trilha sinistra sintetizada em código (sem ruído por construção): piano grave, cordas graves, coro "uuu" e
um motivo de celesta, em ré menor com intervalos dissonantes (2ª menor e trítono), com reverberação de sala.
Criada em 10/11 porque a `suspense_forte` (ElevenLabs) soava como ruído/chiado e os créditos acabaram.
Uso: python3 sintetizar_trilha.py saida.mp3 [segundos]
"""
import subprocess
import sys

import numpy as np

SR = 44100
rng = np.random.default_rng(13)


def hz(nota):  # "D2", "Ab3"...
    nomes = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7,
             "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}
    n, o = nota[:-1], int(nota[-1])
    return 440.0 * 2 ** ((nomes[n] + 12 * (o + 1) - 69) / 12)


def env_ad(n, ataque, decai):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(ataque, 1e-3)) * np.exp(-t / decai)


def piano(f, dur=7.0, vel=0.5):
    n = int(dur * SR); t = np.arange(n) / SR
    s = np.zeros(n)
    for k in range(1, 9):  # parciais levemente inarmônicas, as agudas morrem antes
        fk = f * k * np.sqrt(1 + 0.0004 * k * k)
        s += np.sin(2 * np.pi * fk * t + rng.random() * 6) / k ** 1.3 * np.exp(-t * (0.35 + 0.5 * k))
    return s * env_ad(n, 0.025, 6.0) * vel   # ataque macio (sem "estalo")


def celesta(f, dur=4.0, vel=0.25):
    n = int(dur * SR); t = np.arange(n) / SR
    s = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * f * 4.01 * t) * np.exp(-t * 6) \
        + 0.2 * np.sin(2 * np.pi * f * 2 * t) * np.exp(-t * 2)
    return s * env_ad(n, 0.002, 1.4) * vel


def cordas(freqs, dur, vel=0.12, ataque=3.0):
    """Pad de cordas: várias vozes levemente desafinadas, vibrato lento, só harmônicos baixos (som limpo)."""
    n = int(dur * SR); t = np.arange(n) / SR
    s = np.zeros(n)
    for f in freqs:
        for d in (-0.06, 0.0, 0.07):
            vib = 1 + 0.0025 * np.sin(2 * np.pi * (4.6 + d * 10) * t + rng.random() * 6)
            fase = 2 * np.pi * np.cumsum(f * (1 + d / 100) * vib) / SR
            for k in range(1, 7):
                s += np.sin(k * fase) / k ** 1.6
    env = np.minimum(1, t / ataque) * np.minimum(1, (dur - t) / ataque)
    return s / (len(freqs) * 3) * env * vel


def coro(freqs, dur, vel=0.07):
    """Coro "uuu": harmônicos com peso dos formantes da vogal u (~320 e ~800 Hz)."""
    n = int(dur * SR); t = np.arange(n) / SR
    s = np.zeros(n)
    for f in freqs:
        for d in (-0.1, 0.1):
            vib = 1 + 0.004 * np.sin(2 * np.pi * 5.2 * t + rng.random() * 6)
            fase = 2 * np.pi * np.cumsum(f * (1 + d / 100) * vib) / SR
            for k in range(1, 16):
                fk = f * k
                peso = np.exp(-((fk - 320) / 120) ** 2) + 0.4 * np.exp(-((fk - 800) / 200) ** 2)
                s += np.sin(k * fase) * peso
    env = np.minimum(1, t / 4) * np.minimum(1, (dur - t) / 4)
    return s / (len(freqs) * 2) * env * vel


def reverb(x, seg=3.2, mistura=0.35):
    """Sala escura: resposta ao impulso de decaimento exponencial (filtrada), aplicada por convolução."""
    n = int(seg * SR); t = np.arange(n) / SR
    ir = rng.standard_normal(n) * np.exp(-t / (seg / 6.5))
    ir = np.convolve(ir, np.ones(12) / 12, mode="same")  # tira o brilho do "ar"
    ir /= np.sqrt((ir ** 2).sum())
    m = len(x) + n - 1; N = 1 << (m - 1).bit_length()
    w = np.fft.irfft(np.fft.rfft(x, N) * np.fft.rfft(ir, N), N)[:len(x)]
    return x * (1 - mistura) + w * mistura * 2.2


def compor(dur=120.0):
    n = int(dur * SR)
    mix = np.zeros(n + SR * 8)

    def por(sinal, t0):
        i = int(t0 * SR); mix[i:i + len(sinal)] += sinal[: len(mix) - i]

    # cordas graves: acordes que mudam devagar (Dm -> cluster com 2ª menor -> trítono -> Dm(b6))
    acordes = [("D2", "A2", "F3"), ("D2", "Eb3", "A2"), ("D2", "Ab2", "F3"), ("Bb1", "F2", "D3")]
    t = 0.0; k = 0
    while t < dur:
        por(cordas([hz(x) for x in acordes[k % 4]], 17.0), t); t += 14.0; k += 1
    # coro entra e sai, bem baixo
    for t0 in np.arange(10, dur, 28):
        por(coro([hz("D4"), hz("F4")] if int(t0) % 56 < 28 else [hz("Eb4"), hz("A3")], 16.0), t0)
    # piano grave: notas isoladas, espaço entre elas (a tensão está no intervalo)
    notas = ["D2", "A1", "Eb2", "D2", "Ab1", "D2", "F2", "Eb2"]
    for i, t0 in enumerate(np.arange(1.5, dur - 4, 5.5)):
        por(piano(hz(notas[i % len(notas)]), vel=0.4 + 0.08 * rng.random()), t0 + rng.random() * 0.4)
    # motivo de celesta (4 notas, intervalo de trítono no fim), a cada ~22 s
    motivo = ["D5", "F5", "E5", "Ab4"]
    for t0 in np.arange(8, dur - 6, 22):
        for j, nt in enumerate(motivo):
            por(celesta(hz(nt)), t0 + j * 0.9)
    mix = reverb(mix[: n + SR * 4])[:n]
    mix *= np.minimum(1, np.arange(n) / (SR * 2)) * np.minimum(1, (n - np.arange(n)) / (SR * 3))
    return mix / (np.abs(mix).max() + 1e-9) * 0.8


if __name__ == "__main__":
    saida = sys.argv[1]
    dur = float(sys.argv[2]) if len(sys.argv) > 2 else 120.0
    m = compor(dur).astype(np.float32)
    est = np.stack([m, np.roll(m, int(0.011 * SR))], 1)  # leve abertura estéreo
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                    "-af", "loudnorm=I=-23:TP=-2:LRA=9", "-ar", "44100", "-b:a", "192k", saida],
                   input=est.tobytes(), check=True)
    print("ok:", saida)
