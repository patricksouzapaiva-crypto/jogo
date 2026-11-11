"""Efeitos do Ep. 05 feitos em código (sem direitos de terceiros): batidas na porta, saltos na escada, bigorna
distante, celular vibrando, raspado no muro. Todos começam com 0,3 s de silêncio (o motor faz a entrada suave) e
ficam em volume moderado — nada de susto. Uso: python3 sintetizar_sons_ep05.py"""
import subprocess
from pathlib import Path

import numpy as np

SR = 44100
rng = np.random.default_rng(21)
SONS = Path(__file__).resolve().parents[1] / "sons"


def salvar(nome, x, lufs=-20):
    x = np.concatenate([np.zeros(int(0.3 * SR)), x, np.zeros(int(0.4 * SR))]).astype(np.float32)
    x /= np.abs(x).max() + 1e-9
    est = np.stack([x, np.roll(x, 90)], 1) * 0.7
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                    "-af", "aecho=0.8:0.5:60|130:0.25|0.15", "-b:a", "192k", str(SONS / f"{nome}.mp3")],
                   input=est.tobytes(), check=True)
    print("ok:", nome)


def batida(f0=150.0, dur=0.45, dureza=1.0):
    """Nó de dedo em porta de madeira maciça: estalo curto + corpo grave da folha da porta."""
    n = int(dur * SR); t = np.arange(n) / SR
    corpo = sum(np.sin(2 * np.pi * f * t + rng.random() * 6) * np.exp(-t * d) * a
                for f, d, a in ((f0, 22, 1.0), (f0 * 1.9, 30, 0.55), (f0 * 3.1, 45, 0.3), (f0 * 5.3, 70, 0.15)))
    estalo = rng.standard_normal(n) * np.exp(-t * 320) * 0.5 * dureza
    estalo = np.convolve(estalo, np.ones(6) / 6, mode="same")
    return (corpo + estalo) * np.minimum(1, t / 0.002)


def sequencia(tempos, **kw):
    x = np.zeros(int((max(tempos) + 1.2) * SR))
    for i, t0 in enumerate(tempos):
        b = batida(f0=150 + rng.random() * 12, **kw) * (1.0 - 0.08 * i)
        j = int(t0 * SR); x[j:j + len(b)] += b
    return x


def salto(dur=0.6):
    """Algo pesado e duro batendo em degrau de pedra: baque grave + clique seco (casco)."""
    n = int(dur * SR); t = np.arange(n) / SR
    baque = np.sin(2 * np.pi * 62 * t * (1 + 0.5 * np.exp(-t * 30))) * np.exp(-t * 14)
    casco = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * 90) for f in (900, 1450, 2100)) * 0.22
    return baque + casco


def saltos(n_saltos=5, intervalo=0.95):
    x = np.zeros(int((n_saltos * intervalo + 1.5) * SR))
    for i in range(n_saltos):
        s = salto() * (1.0 - 0.14 * i)          # vai se afastando
        for off in (0.0, 0.11):                   # dois apoios quase juntos
            j = int((i * intervalo + off + rng.random() * 0.03) * SR); x[j:j + len(s)] += s * (1.0 if off == 0 else 0.7)
    return x


def bigorna(n_golpes=3, intervalo=1.25):
    """Martelo na bigorna, longe e abafado (parciais inarmônicas que demoram a morrer)."""
    x = np.zeros(int((n_golpes * intervalo + 3.5) * SR))
    for i in range(n_golpes):
        n = int(3.2 * SR); t = np.arange(n) / SR
        g = sum(np.sin(2 * np.pi * f * t + rng.random() * 6) * np.exp(-t * d) * a
                for f, d, a in ((1180, 2.2, 1.0), (2260, 3.0, 0.5), (3040, 4.5, 0.3), (640, 5.0, 0.35)))
        g += rng.standard_normal(n) * np.exp(-t * 200) * 0.3
        j = int(i * intervalo * SR); x[j:j + n] += g * (0.9 + 0.1 * rng.random())
    # longe: sem agudos
    k = np.ones(18) / 18
    return np.convolve(x, k, mode="same")


def vibrar(n_vezes=2):
    """Celular vibrando sobre madeira."""
    x = np.zeros(int((n_vezes * 1.1 + 0.6) * SR))
    for i in range(n_vezes):
        n = int(0.65 * SR); t = np.arange(n) / SR
        z = np.sign(np.sin(2 * np.pi * 172 * t)) * 0.4 + np.sin(2 * np.pi * 86 * t)
        z += rng.standard_normal(n) * 0.15 * (np.sin(2 * np.pi * 172 * t) > 0.6)   # o aparelho trepidando na mesa
        z *= np.minimum(1, t / 0.03) * np.minimum(1, (0.65 - t) / 0.05)
        j = int(i * 1.1 * SR); x[j:j + n] += z
    return np.convolve(x, np.ones(10) / 10, mode="same")


def raspar(dur=2.6):
    """Algo duro raspando devagar em reboco: ruído em faixa estreita que sobe e desce."""
    n = int(dur * SR); t = np.arange(n) / SR
    r = rng.standard_normal(n)
    S = np.fft.rfft(r); f = np.fft.rfftfreq(n, 1 / SR)
    S *= np.exp(-((f - 1700) / 650) ** 2) + 0.4 * np.exp(-((f - 420) / 200) ** 2)
    r = np.fft.irfft(S, n)
    env = np.sin(np.pi * t / dur) ** 0.7 * (0.75 + 0.25 * np.sin(2 * np.pi * 7 * t + np.sin(2 * np.pi * 0.8 * t) * 3))
    return r * env


if __name__ == "__main__":
    salvar("ep05_batidas", sequencia([0.0, 0.62, 1.24]))                 # as três batidas da mãe
    salvar("ep05_batidas_lentas", sequencia([0.0, 1.15, 2.3], dureza=0.7))   # devagar demais
    salvar("ep05_saltos", saltos())
    salvar("ep05_bigorna", bigorna())
    salvar("ep05_vibrar", vibrar())
    salvar("ep05_raspar", raspar())
