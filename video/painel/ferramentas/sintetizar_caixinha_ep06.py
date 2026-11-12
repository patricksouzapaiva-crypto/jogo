"""Trilha do Ep. 06 no estilo da música-assinatura do canal (vinheta final): caixinha de música, violoncelo e
sino distante, em LÁ MENOR. Pedido do usuário em 12/11 ("tenta fazer uma versão parecida com a música da
vinheta final, gostei bastante dela"). As faixas do Flow Music foram descartadas por ele.
Mesma linguagem da vinheta (lá menor, cello grave em lá → si bemol → mi, caixinha nos agudos), melodias NOVAS.
Uso: python3 sintetizar_caixinha_ep06.py fundo  saida.mp3 [segundos]   (caixinha de ninar + cello, calma, triste)
     python3 sintetizar_caixinha_ep06.py tensao saida.mp3 [segundos]   (a caixinha "dando corda" errado, cello, sino)
"""
import subprocess
import sys

import numpy as np

from sintetizar_trilha import SR, cordas, hz, reverb

rng = np.random.default_rng(66)


def caixinha(f, vel=0.25, dur=3.2, desafina=0.0):
    """Caixinha de música: lâmina de metal beliscada — fundamental + parciais inarmônicos (lâmina, não corda),
    ataque seco e decaimento rápido dos agudos; um leve "tic" do pino no começo."""
    n = int(dur * SR); t = np.arange(n) / SR
    f = f * 2 ** (desafina / 1200)
    s = np.sin(2 * np.pi * f * t) * np.exp(-t * 1.6)
    for r, a, d in ((2.0, 0.12, 3.0), (2.76, 0.34, 4.5), (5.40, 0.22, 6.5), (8.93, 0.12, 9.0)):   # modos da lâmina
        if f * r < 9000:
            s += a * np.sin(2 * np.pi * f * r * t + rng.random() * 6) * np.exp(-t * d)
    s *= np.minimum(1, t / 0.0015)
    tic = rng.standard_normal(int(0.004 * SR)) * np.exp(-np.arange(int(0.004 * SR)) / 40) * 0.05
    s[: len(tic)] += tic
    return s * vel


def sino(f, vel=0.12, dur=9.0):
    """Sino distante: parciais de sino (hum, fundamental, terça menor, quinta, oitava) com batimento lento."""
    n = int(dur * SR); t = np.arange(n) / SR
    s = np.zeros(n)
    for r, a, d in ((0.5, 0.5, 0.25), (1.0, 1.0, 0.35), (1.19, 0.45, 0.5), (1.5, 0.3, 0.6), (2.0, 0.35, 0.8), (2.52, 0.2, 1.1)):
        s += a * np.sin(2 * np.pi * f * r * t + rng.random() * 6) * np.exp(-t * d) * (1 + 0.15 * np.sin(2 * np.pi * 0.7 * t))
    s *= np.minimum(1, t / 0.01)
    return s * vel


def cello(f, dur, vel=0.16):
    return cordas([f, f * 2], dur, vel=vel, ataque=min(2.5, dur / 3))


class Mesa:
    def __init__(self, dur):
        self.n = int(dur * SR); self.x = np.zeros(self.n + SR * 12)

    def por(self, s, t0):
        i = int(max(0, t0) * SR)
        if i < len(self.x):
            self.x[i:i + len(s)] += s[: len(self.x) - i]

    def sair(self, mistura):
        m = reverb(self.x[: self.n + SR * 5], seg=4.2, mistura=mistura)[: self.n]
        k = np.arange(self.n)
        m *= np.minimum(1, k / (SR * 3)) * np.minimum(1, (self.n - k) / (SR * 6))
        return m / (np.abs(m).max() + 1e-9) * 0.8


# frases de 4 compassos (3/4). Cada nota: (nota, tempos). "-" = pausa. Baixo do cello por compasso.
FRASES = [
    ([("A5", 1), ("C6", 1), ("E5", 1), ("B5", 2), ("A5", 1), ("C6", 1), ("E6", 1), ("D6", 1), ("C6", 3)], ["A2", "A2", "F2", "E2"]),
    ([("E5", 1), ("A5", 1), ("C6", 1), ("Bb5", 2), ("A5", 1), ("F5", 1), ("E5", 2), ("-", 3)], ["A2", "Bb2", "F2", "E2"]),
    ([("C6", 1), ("B5", 1), ("A5", 1), ("E5", 3), ("F5", 1), ("A5", 1), ("C6", 1), ("B5", 3)], ["A2", "E2", "F2", "E2"]),
    ([("A5", 1), ("E6", 1), ("C6", 1), ("A5", 2), ("E5", 1), ("Bb5", 1), ("A5", 1), ("E5", 1), ("A5", 3)], ["A2", "A2", "Bb2", "A2"]),
]


def fundo(dur=900.0, tempo=0.66):
    """Caixinha de ninar: uma frase, depois espaço (só cello e um eco da caixinha), depois outra frase.
    A cada volta a caixinha "cansa": um pouco mais lenta e desafinada — a mesma sensação da vinheta."""
    M = Mesa(dur); t = 1.0; k = 0
    comp = 3 * tempo
    while t < dur:
        mel, baixos = FRASES[k % len(FRASES)]
        volta = k // len(FRASES)
        canso = 1 + 0.04 * (volta % 3)                    # mais lenta nas voltas seguintes
        des = 6 * (volta % 3)                              # e mais desafinada (cents)
        tp = tempo * canso
        for i, b in enumerate(baixos):                    # cello: uma nota longa por compasso
            M.por(cello(hz(b), 3 * tp + 1.6, vel=0.15), t + i * 3 * tp - 0.4)
        tv = t
        for nota, n in mel:
            if nota != "-":
                M.por(caixinha(hz(nota), vel=0.22 + 0.04 * rng.random(), desafina=des * (rng.random() - 0.3)), tv + rng.random() * 0.02)
            tv += n * tp
        t += 4 * 3 * tp
        # respiro: 2 compassos só de cello (e às vezes o sino lá longe), para a voz do narrador ter espaço
        resp = 2 * 3 * tp
        M.por(cello(hz("A2"), resp + 1.6, vel=0.12), t - 0.4)
        if k % 3 == 2:
            M.por(sino(hz("A4"), vel=0.07), t + 0.5)
        if k % 2 == 1:                                     # eco: as três primeiras notas da frase, bem baixinho
            for j, (nota, n) in enumerate(mel[:3]):
                if nota != "-":
                    M.por(caixinha(hz(nota), vel=0.08, desafina=12), t + 0.6 + j * tp * 1.2)
        t += resp
        k += 1
    return M.sair(0.45)


def tensao(dur=480.0, tempo=0.95):
    """A caixinha dando corda errado: notas soltas, lentas, desafinadas, com meio-tom (lá/si bemol) e trítono
    (lá/mi bemol); cello grave em lá com si bemol por cima que cresce e some; sino distante de tempos em tempos."""
    M = Mesa(dur); t = 0.5; k = 0
    soltas = ["A5", "Bb5", "E5", "A5", "Eb6", "C6", "B5", "Bb5", "A5", "E5", "F5", "E5"]
    while t < dur:
        M.por(cello(hz("A1"), 15.0, vel=0.2), t)
        if k % 2:
            M.por(cordas([hz("Bb2") * 2], 11.0, vel=0.07, ataque=4.5), t + 2.5)
        tv = t + 1.0
        for j in range(6):
            nota = soltas[(k * 5 + j) % len(soltas)]
            if rng.random() < 0.8:
                M.por(caixinha(hz(nota), vel=0.2, dur=3.8, desafina=rng.uniform(-35, 35)), tv)
            tv += tempo * (1.0 + 0.6 * rng.random()) * (1 + 0.12 * j)      # cada nota demora mais (a corda acaba)
        if k % 3 == 1:
            M.por(sino(hz("E4"), vel=0.09), t + 7.0)
        t += 14.0; k += 1
    return M.sair(0.55)


if __name__ == "__main__":
    modo, saida = sys.argv[1], sys.argv[2]
    dur = float(sys.argv[3]) if len(sys.argv) > 3 else (900.0 if modo == "fundo" else 480.0)
    m = {"fundo": fundo, "tensao": tensao}[modo](dur).astype(np.float32)
    est = np.stack([m, np.roll(m, int(0.011 * SR))], 1)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-af",
                    "highpass=f=55,treble=g=7:f=3500:t=s,acompressor=threshold=-30dB:ratio=2.5:attack=300:release=2500:makeup=2,loudnorm=I=-20:TP=-3:LRA=7",
                    "-ar", "44100", "-b:a", "192k", saida], input=est.tobytes(), check=True)
    print("ok", saida, f"{dur:.0f}s")
