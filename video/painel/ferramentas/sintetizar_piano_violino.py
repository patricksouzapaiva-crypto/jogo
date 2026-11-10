"""Trilha clássica e sinistra para piano, violino e violoncelo, composta em código (Ep. 05, 10/11/2026).
O usuário rejeitou as faixas do Suno "consertadas" (soavam metálicas) e pediu "piano, violino, clássico mas sinistro".
Ré menor, valsa lenta (3/4, ~52 bpm): baixo do piano no 1º tempo, acorde quebrado nos outros; o violino canta notas
longas com meios-tons de tensão (dó#–ré, mi bemol napolitano). Quatro seções que se alternam para não cansar.
Uso: python3 sintetizar_piano_violino.py fundo saida.mp3 [segundos]
     python3 sintetizar_piano_violino.py tensao saida.mp3 [segundos]
"""
import subprocess
import sys

import numpy as np

from sintetizar_trilha import SR, cordas, hz, piano, reverb

rng = np.random.default_rng(5)


def violino(f, dur, vel=0.2, tremolo=False):
    """Violino solo: dente de serra por harmônicos, filtrado pelo "corpo" do instrumento, vibrato que entra aos poucos,
    ataque de arco (sem estalo). Sem ruído, sem brilho metálico (harmônicos acima de ~4 kHz ficam de fora)."""
    n = int(dur * SR); t = np.arange(n) / SR
    rampa = np.clip((t - 0.25) / 0.6, 0, 1)
    vib = 1 + 0.0055 * rampa * np.sin(2 * np.pi * (5.4 + 0.3 * rng.random()) * t + rng.random() * 6)
    fase = 2 * np.pi * np.cumsum(f * vib) / SR
    s = np.zeros(n)
    for k in range(1, 15):
        fk = f * k
        if fk > 4200:
            break
        corpo = 0.35 + np.exp(-((fk - 290) / 90) ** 2) + 0.9 * np.exp(-((fk - 520) / 160) ** 2) \
            + 0.5 * np.exp(-((fk - 1150) / 350) ** 2) + 0.35 * np.exp(-((fk - 2600) / 600) ** 2)
        s += np.sin(k * fase + rng.random() * 6) * corpo / k
    ataque, solta = (0.06, 0.25) if tremolo else (0.22, 0.5)
    env = np.minimum(1, t / ataque) * np.minimum(1, np.maximum(0, dur - t) / solta)
    env *= 1 + 0.05 * rampa * np.sin(2 * np.pi * 5.4 * t)          # o arco "respira" junto com o vibrato
    if tremolo:
        env *= 0.62 + 0.38 * np.sin(2 * np.pi * 10.5 * t + rng.random() * 6) ** 2
    return s * env * vel


class Mesa:
    def __init__(self, dur):
        self.n = int(dur * SR); self.seco = np.zeros(self.n + SR * 10)

    def por(self, sinal, t0):
        i = int(max(0, t0) * SR)
        if i < len(self.seco):
            self.seco[i:i + len(sinal)] += sinal[: len(self.seco) - i]

    def sair(self, mistura=0.42):
        m = reverb(self.seco[: self.n + SR * 4], seg=3.6, mistura=mistura)[: self.n]
        k = np.arange(self.n)
        m *= np.minimum(1, k / (SR * 3)) * np.minimum(1, (self.n - k) / (SR * 5))
        return m / (np.abs(m).max() + 1e-9) * 0.8


# 16 compassos: (baixo, notas do acorde quebrado, violino [(nota, tempos)...])
PROGRESSAO = [
    ("D2", ("A3", "F4"), [("A4", 3)]),
    ("D2", ("A3", "D4"), [("D5", 3)]),
    ("D2", ("Bb3", "G4"), [("Bb4", 3)]),
    ("D2", ("A3", "F4"), [("A4", 3)]),
    ("Bb1", ("F3", "D4"), [("F5", 3)]),
    ("G1", ("G3", "Bb3"), [("D5", 3)]),
    ("A1", ("G3", "C#4"), [("C#5", 3)]),
    ("A1", ("E3", "C#4"), [("E5", 2), ("C#5", 1)]),
    ("D2", ("A3", "F4"), [("F5", 3)]),
    ("C2", ("A3", "E4"), [("E5", 3)]),
    ("Bb1", ("F3", "D4"), [("D5", 3)]),
    ("G1", ("Eb3", "Bb3"), [("Eb5", 3)]),        # napolitano: o mi bemol que "azeda" o ré menor
    ("A1", ("F3", "D4"), [("D5", 3)]),
    ("A1", ("G3", "C#4"), [("C#5", 2), ("Bb4", 1)]),
    ("D2", ("A3", "D4"), [("D5", 3)]),
    ("D2", ("A3", "F4"), []),
]


def fundo(dur=960.0, tempo=1.16):
    """tempo = segundos por tempo do compasso (1,16 s ≈ 52 bpm)."""
    M = Mesa(dur); comp = 3 * tempo; t = 0.6; secao = 0
    while t < dur:
        tipo = secao % 4
        for baixo, acorde, mel in PROGRESSAO:
            if t >= dur:
                break
            hum = lambda: (rng.random() - 0.5) * 0.05
            # piano — sempre presente (é a espinha da música)
            M.por(piano(hz(baixo) * 2, dur=comp * 1.6, vel=0.30), t + hum())
            M.por(piano(hz(baixo), dur=comp * 1.6, vel=0.10), t + hum())
            if tipo == 0:                       # só piano, bem esparso
                M.por(piano(hz(acorde[1]), dur=5, vel=0.34), t + 2 * tempo + hum())
                M.por(piano(hz(acorde[0]) * 2, dur=5, vel=0.2), t + tempo + hum())
            else:
                M.por(piano(hz(acorde[0]), dur=5, vel=0.32), t + tempo + hum())
                M.por(piano(hz(acorde[1]), dur=5, vel=0.34), t + 2 * tempo + hum())
            # violoncelo sustentando o baixo (seções 2 e 3)
            if tipo in (2, 3):
                M.por(cordas([hz(baixo) * 4, hz(acorde[0]) * 2], comp + 2.2, vel=0.16, ataque=1.4), t - 0.4)
            # violino
            tv = t
            for nota, tempos in mel:
                d = tempos * tempo
                if tipo == 1:                   # melodia
                    M.por(violino(hz(nota), d + 0.35, vel=0.34), tv)
                elif tipo == 2:                 # melodia uma oitava acima, de longe
                    M.por(violino(hz(nota) * 2, d + 0.35, vel=0.13), tv)
                    M.por(violino(hz(nota), d + 0.35, vel=0.20), tv)
                elif tipo == 3:                 # suspense: trêmulo em meio-tom contra a melodia
                    M.por(violino(hz(nota), d + 0.2, vel=0.17, tremolo=True), tv)
                    M.por(violino(hz(nota) * 2 ** (1 / 12), d + 0.2, vel=0.10, tremolo=True), tv)
                tv += d
            t += comp
        secao += 1
    return M.sair()


def tensao(dur=480.0):
    """Sem melodia: pedal grave do violoncelo, violinos em trêmulo com meios-tons que incham e somem, piano em notas
    isoladas. Mesma tonalidade e mesmos timbres do fundo — dá para fundir uma na outra."""
    M = Mesa(dur)
    pares = [("D5", "Eb5"), ("A4", "Bb4"), ("C#5", "D5"), ("F5", "E5"), ("A4", "Ab4"), ("D5", "C#5")]
    t = 0.0; k = 0
    while t < dur:
        M.por(cordas([hz("D3"), hz("A3")], 16.0, vel=0.20, ataque=4.0), t)
        a, b = pares[k % len(pares)]
        d = 11.0
        for nota, v in ((a, 0.26), (b, 0.18)):
            s = violino(hz(nota), d, vel=v, tremolo=True)
            s *= np.sin(np.pi * np.arange(len(s)) / len(s)) ** 1.5          # incha e some
            M.por(s, t + 2.0)
        if k % 3 == 2:                                                       # nota aguda parada, sem trêmulo
            M.por(violino(hz("A5"), 9.0, vel=0.07), t + 5.0)
        t += 13.0; k += 1
    graves = ["D3", "A2", "Eb3", "D3", "Bb2", "D3", "Ab2"]
    for i, t0 in enumerate(np.arange(3.0, dur - 6, 6.5)):
        M.por(piano(hz(graves[i % len(graves)]), vel=0.30 + 0.06 * rng.random()), t0 + rng.random() * 0.5)
        if i % 4 == 3:
            M.por(piano(hz("D5"), dur=5, vel=0.20), t0 + 2.2)
            M.por(piano(hz("Eb5"), dur=5, vel=0.18), t0 + 2.9)
    return M.sair(mistura=0.48)


if __name__ == "__main__":
    qual, saida = sys.argv[1], sys.argv[2]
    dur = float(sys.argv[3]) if len(sys.argv) > 3 else None
    m = (fundo(dur or 960.0) if qual == "fundo" else tensao(dur or 480.0)).astype(np.float32)
    est = np.stack([m, np.roll(m, int(0.013 * SR))], 1)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                    "-af", "highpass=f=70,loudnorm=I=-20:TP=-3:LRA=8", "-ar", "44100", "-b:a", "192k", saida],
                   input=est.tobytes(), check=True)
    print("ok:", saida)
