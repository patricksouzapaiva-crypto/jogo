"""Trilha do Ep. 11 com orquestra de verdade (painel/ferramentas/orquestra.py, gravações CC0), 16/11.
Identidade: uma POLSKA (dança folclórica sueca em 3/4) em ré menor no violino solo, com bordão de quintas nos cellos
(o som da rabeca de Hälsingland), que o episódio deforma aos poucos: no gancho só restam trêmulos e o coração no bumbo;
nos capítulos o tema volta inteiro; na história ele vira ostinato de semitom (ré–mi bemol) até o silêncio do clímax;
no fecho, o violino sozinho, longe, com o tema incompleto.
Prévia: python3 compor_orquestra.py → trilha/previa_orquestra.mp3 (~2:40, os 4 momentos em sequência)."""
import subprocess, sys
from pathlib import Path
AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI.parents[2] / "painel" / "ferramentas"))
from orquestra import Orquestra   # noqa: E402

Q = 0.56            # semínima (s): polska lenta, ~107 bpm
BAR = 3 * Q
SILENCIOS = []
# o tema: (nota, duração em semínimas). Ritmo de polska: longa-curta-curta, apoio no 1º tempo; 7º grau elevado (dó#)
# no fim da frase, como nas polskas em menor de Hälsingland
TEMA = [("A4", 1.5), ("Bb4", .5), ("A4", 1), ("G4", 1), ("F4", 1), ("E4", 1), ("D4", 2), ("A4", 1), ("D5", 3),
        ("C5", 1.5), ("D5", .5), ("C5", 1), ("Bb4", 1), ("A4", 1), ("G4", 1), ("A4", 1), ("F4", 1), ("E4", 1), ("D4", 3),
        ("D5", 1.5), ("E5", .5), ("F5", 1), ("E5", 1), ("D5", 1), ("C5", 1), ("D5", 1), ("A4", 2), ("Bb4", 1), ("A4", 1), ("G4", 1),
        ("F4", 1.5), ("G4", .5), ("A4", 1), ("E4", 1), ("C#5", 2), ("D5", 3), ("D5", 3)]


def tema(o, t0, vel=0.9, oitava=0, ate=None, din="p", pan=-0.15):
    t = t0
    for k, (n, q) in enumerate(TEMA[:ate]):
        nn = n if not oitava else n[:-1] + str(int(n[-1]) + oitava)
        o.nota("vln", nn, t, q * Q * 1.02, vel * (1.0 if q >= 1 else 0.8), ataque=0.05 if q < 1 else 0.09, solta=0.35, pan=pan, din=din)
        t += q * Q
    return t


def bordao(o, t0, d, vel=0.55):   # quinta ré–lá nos cellos + ré grave no contrabaixo: a "rabeca" embaixo de tudo
    o.cresc("vc", "D2", t0, d, 0.2 * vel, vel, pan=-0.3); o.cresc("vc", "A2", t0 + 0.4, d - 0.4, 0.15 * vel, 0.8 * vel, pan=0.3)
    o.cresc("cb", "D2", t0, d, 0.1 * vel, 0.7 * vel)


def gancho(o, t0):   # ~36 s: frio, trêmulo inchando em cluster, coração no bumbo acelerando, golpe e corte seco
    o.cresc("cb", "D2", t0, 34, 0.05, 0.9)
    o.cresc("vlns_trem", "D5", t0 + 4, 30, 0.0, 0.55, pan=-0.4); o.cresc("vlns_trem", "Eb5", t0 + 9, 25, 0.0, 0.45, pan=0.4)
    o.cresc("vla_trem", "A3", t0 + 12, 22, 0.0, 0.5, pan=0.1); o.cresc("vc_trem", "D3", t0 + 18, 16, 0.0, 0.6, pan=-0.2)
    for k, t in enumerate([7, 13.5, 18.5, 22.5, 25.5, 27.8, 29.6, 31.0, 32.1, 33.0, 33.7]):
        o.golpe("bumbo", t0 + t, 0.35 + 0.05 * k, k)
    o.golpe("timp", t0 + 34.2, 1.4, 3); o.golpe("bumbo", t0 + 34.2, 1.6, 12)
    SILENCIOS.append((t0 + 35.4, 1.6))
    return t0 + 37.0


def capitulos(o, t0):   # ~58 s: o tema inteiro duas vezes; na 2ª, violas e cellos harmonizam e o tímpano marca o 1º tempo
    n = 16 * BAR; bordao(o, t0 - 1.5, 2 * n + 3)
    t = tema(o, t0, 0.8)
    acordes = ["D3", "D3", "Bb2", "A2", "F3", "G2", "A2", "D3", "D3", "C3", "D3", "G2", "F2", "A2", "D3", "D3"]
    for k, a in enumerate(acordes):
        o.nota("vla", a, t + k * BAR, BAR * 1.05, 0.5, ataque=0.25, solta=0.6, pan=0.35)
        if k % 2 == 0: o.golpe("timp", t + k * BAR, 0.45, k)
    tema(o, t, 0.95, din="f")
    return t + n + 1.5


def historia(o, t0):   # ~45 s: semitom ré–mi bemol nos cellos acelerando, rufo crescendo, cluster agudo e SILÊNCIO
    t, passo = t0, 1.1
    while t < t0 + 38:
        o.nota("vc", "D2", t, passo * 0.95, 0.7, ataque=0.03, solta=0.15, pan=-0.2)
        o.nota("vc", "Eb2", t + passo, passo * 0.95, 0.75, ataque=0.03, solta=0.15, pan=-0.2)
        t += 2 * passo; passo = max(0.32, passo * 0.93)
    o.cresc("vlns_trem", "D5", t0 + 10, 30, 0.0, 0.7, pan=-0.5); o.cresc("vlns_trem", "Eb5", t0 + 16, 24, 0.0, 0.6, pan=0.5)
    o.cresc("vla_trem", "Ab3", t0 + 20, 20, 0.0, 0.65); o.cresc("cb", "D2", t0, 40, 0.2, 1.0)
    o.golpe("rufo", t0 + 22, 0.9, 1)
    for k in range(14): o.golpe("bumbo", t0 + 26 + k * (1.0 - k * 0.045), 0.5 + 0.06 * k, k)
    o.golpe("timp", t0 + 40, 1.5, 5); o.golpe("bumbo", t0 + 40, 1.8, 13)
    SILENCIOS.append((t0 + 40.9, 1.8))   # o golpe soa ~0.9 s e então: nada
    return t0 + 40.9 + 1.8


def fecho(o, t0):   # o violino sozinho, longe (mais reverb), o tema parado no meio — sem resolver
    o.cresc("cb", "D2", t0 + 1, 18, 0.0, 0.3)
    tema(o, t0 + 1, 0.55, ate=9, pan=0.3)
    o.nota("vln", "C#5", t0 + 1 + 16 * Q, 3.5, 0.4, ataque=0.6, solta=2.0, pan=0.3)
    return t0 + 24


if __name__ == "__main__":
    o = Orquestra(200)
    t = gancho(o, 0.5); t = capitulos(o, t + 0.5); t = historia(o, t); t = fecho(o, t)
    wav = AQUI / "previa_orquestra.wav"; o.salvar(wav, corte=t + 0.5, silencios=SILENCIOS)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(wav), "-af", "loudnorm=I=-16:TP=-1.5", "-b:a", "192k", str(AQUI / "previa_orquestra.mp3")], check=True)
    wav.unlink(); print("ok", AQUI / "previa_orquestra.mp3", f"{t + 0.5:.0f} s")
