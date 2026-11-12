"""Sons do Ep. 07 "A ronda" feitos em código (os créditos do ElevenLabs acabaram em 11/11).
Efeitos (curtos, volume moderado, sem susto): a corrente arrastando elo por elo (perto e longe), a respiração do
outro lado da porta, a maçaneta girando meia volta.
Ambientes (laços longos, sem emenda audível): o hospital de noite (zumbido de luz + ar + bipes distantes), o
quarto em silêncio total da 3ª noite (só o "ar" do quarto — nunca silêncio absoluto), a colônia abandonada.
Uso: python3 sintetizar_sons_ep07.py"""
import subprocess
from pathlib import Path

import numpy as np

SR = 44100
rng = np.random.default_rng(77)
SONS = Path(__file__).resolve().parents[1] / "sons"


def filtro(x, lo=None, hi=None):
    """Passa-faixa por FFT (simples e sem fase estranha para sons longos)."""
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    m = np.ones_like(f)
    if lo:
        m *= 1 / (1 + (lo / np.maximum(f, 1)) ** 4)
    if hi:
        m *= 1 / (1 + (f / hi) ** 4)
    return np.fft.irfft(X * m, len(x))


def salvar(nome, x, lufs, laco=False, eco=True):
    if not laco:
        x = np.concatenate([np.zeros(int(0.3 * SR)), x, np.zeros(int(0.4 * SR))])
    x = (x / (np.abs(x).max() + 1e-9)).astype(np.float32)
    est = np.stack([x, np.roll(x, 70)], 1) * 0.7
    af = ("aecho=0.8:0.55:70|160:0.22|0.12," if eco else "") + f"loudnorm=I={lufs}:TP=-3"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                    "-af", af, "-ar", "44100", "-b:a", "192k", str(SONS / f"{nome}.mp3")], input=est.tobytes(), check=True)
    print("ok:", nome)


def laco_suave(x, cruz=2.0):
    """Faz o fim emendar no começo: cruza os últimos `cruz` s com os primeiros."""
    n = int(cruz * SR); a = np.linspace(0, 1, n)
    y = x[:-n].copy(); y[:n] = y[:n] * a + x[-n:] * (1 - a)
    return y


def elo(vel=1.0):
    """Um elo de corrente de ferro batendo/raspando no piso: ping metálico inarmônico curto + raspão grave."""
    n = int(0.35 * SR); t = np.arange(n) / SR
    f0 = 1800 + rng.random() * 900
    ping = sum(np.sin(2 * np.pi * f0 * r * t + rng.random() * 6) * np.exp(-t * d) * a
               for r, d, a in ((1.0, 38, 1.0), (1.47, 52, 0.6), (2.31, 70, 0.4), (3.02, 95, 0.25)))
    tum = np.sin(2 * np.pi * (140 + rng.random() * 40) * t) * np.exp(-t * 35) * 0.8   # o peso do ferro no chão
    return (ping * 0.5 + tum) * np.minimum(1, t / 0.001) * vel


def corrente(dur=7.0, passo=0.55):
    """Arrasto lento: um raspão contínuo (ruído grave áspero) e elos batendo em grupos irregulares."""
    n = int(dur * SR); t = np.arange(n) / SR
    rasp = filtro(rng.standard_normal(n), 150, 1400) * (0.35 + 0.25 * np.sin(2 * np.pi * 0.45 * t) ** 2)
    rasp *= np.minimum(1, t / 0.8) * np.minimum(1, (dur - t) / 1.0)
    x = rasp * 0.25
    tt = 0.2
    while tt < dur - 0.6:
        for k in range(rng.integers(2, 5)):                 # 2 a 4 elos por "puxada"
            e = elo(0.5 + 0.5 * rng.random()); i = int((tt + k * 0.07 + rng.random() * 0.03) * SR)
            x[i:i + len(e)] += e[: n - i]
        tt += passo * (0.8 + 0.5 * rng.random())
    return x


def respiracao(ciclos=3, periodo=4.2):
    """Respiração funda e lenta, molhada, do outro lado de uma porta (abafada: só graves e médios)."""
    n = int(ciclos * periodo * SR); t = np.arange(n) / SR
    fase = (t % periodo) / periodo
    puxa = np.where(fase < 0.42, np.sin(np.pi * fase / 0.42), 0)
    solta = np.where((fase > 0.5) & (fase < 0.95), np.sin(np.pi * (fase - 0.5) / 0.45), 0)
    ar = filtro(rng.standard_normal(n), 180, 1100)
    molhado = filtro(rng.standard_normal(n), 300, 900) * (rng.random(n) < 0.002) * 6   # estalinhos de saliva
    x = ar * (puxa ** 1.5 * 0.7 + solta ** 1.2 * 1.0) + molhado * solta
    return filtro(x, 120, 900)


def macaneta():
    """Maçaneta velha girando meia volta e parando: rangido metálico com atrito (tom que sobe), clique seco."""
    dur = 1.6; n = int(dur * SR); t = np.arange(n) / SR
    f = 520 + 380 * np.clip(t / 1.2, 0, 1) ** 0.7
    atrito = 0.6 + 0.4 * (rng.random(n) > 0.55)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * atrito
    s = filtro(s + 0.3 * rng.standard_normal(n), 300, 3500)
    s *= np.minimum(1, t / 0.05) * np.clip((1.25 - t) / 0.1, 0, 1)
    clique = np.zeros(n); i = int(1.3 * SR); c = elo(0.6)[: int(0.12 * SR)]; clique[i:i + len(c)] += c
    return s * 0.6 + clique


def hospital_noite(dur=40.0):
    """Ala velha de noite: zumbido de reator de lâmpada (120 Hz e harmônicos), ar-condicionado distante, um bipe
    de aparelho lá longe de tempos em tempos."""
    n = int(dur * SR); t = np.arange(n) / SR
    zum = sum(np.sin(2 * np.pi * 120 * k * t + rng.random() * 6) / k ** 1.4 for k in range(1, 9))
    zum *= 0.06 * (1 + 0.15 * np.sin(2 * np.pi * 0.13 * t))
    ar = filtro(rng.standard_normal(n), 60, 600) * 0.25
    x = zum + ar
    for t0 in np.arange(3.0, dur - 2, 9.5):                 # bipe distante (abafado, baixo)
        b = np.sin(2 * np.pi * 980 * t[: int(0.12 * SR)]) * np.hanning(int(0.12 * SR)) * 0.05
        i = int((t0 + rng.random()) * SR); x[i:i + len(b)] += filtro(b, 400, 1500)
    return laco_suave(x)


def quarto_silencio(dur=30.0):
    """O silêncio errado da 3ª noite: sem zumbido, sem bipe — só o ar do quarto, muito baixo e grave."""
    n = int(dur * SR)
    return laco_suave(filtro(rng.standard_normal(n), 40, 260) * 0.2)


def colonia(dur=40.0):
    """O outro hospital: vento entrando por janela quebrada, gotas, um metal batendo muito longe."""
    n = int(dur * SR); t = np.arange(n) / SR
    vento = filtro(rng.standard_normal(n), 120, 1800) * (0.25 + 0.2 * np.sin(2 * np.pi * 0.07 * t) ** 2)
    x = vento
    for _ in range(int(dur * 0.5)):                          # gotas
        i = rng.integers(0, n - SR); g = np.sin(2 * np.pi * (1300 + rng.random() * 700) * t[: int(0.08 * SR)]) * np.exp(-t[: int(0.08 * SR)] * 60) * 0.15
        x[i:i + len(g)] += g
    for t0 in np.arange(5, dur - 3, 13):                     # metal batendo longe
        e = filtro(np.concatenate([elo(0.4), np.zeros(SR)]), 200, 1200) * 0.5; i = int(t0 * SR); x[i:i + len(e)] += e[: n - i]
    return laco_suave(x)


if __name__ == "__main__":
    salvar("ep07_corrente", corrente(), -21)
    salvar("ep07_corrente_longe", filtro(corrente(9.0, 0.7), 100, 1600), -27)
    salvar("ep07_respiracao", respiracao(), -24)
    salvar("ep07_macaneta", macaneta(), -22)
    salvar("ep07_hospital_noite", hospital_noite(), -30, laco=True, eco=False)
    salvar("ep07_quarto_silencio", quarto_silencio(), -38, laco=True, eco=False)
    salvar("ep07_colonia", colonia(), -28, laco=True, eco=False)
