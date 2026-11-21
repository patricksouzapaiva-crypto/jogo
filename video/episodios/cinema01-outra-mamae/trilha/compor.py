"""Trilha de "O QUE É A CRIATURA? #1 — Outra Mamãe" (21/11), orquestra com gravações reais (painel/ferramentas/orquestra.py).
Usuário: "temos que pensar na trilha sonora boa e envolvente para esse episódio".
Duas camadas:
- TEMA DO FORMATO (fixo, toda semana): um relógio de investigação — ostinato em pizzicato (cellos, violas, contrabaixo),
  oitavas graves no piano, violinos em trêmulo subindo. Marca pistas, teorias e o veredito.
- MOTIVO DO EPISÓDIO: uma canção de ninar original (lá menor, 3/4) — na caixinha de música (glockenspiel + harpa), no
  piano desafinado ("a mãe errada"), em lamento irlandês no violino (Bridget Cleary) e, no veredito, nas cordas sobre o
  relógio da investigação; no fim a caixinha perde a corda.
Prévia: python3 compor.py → trilha/previa_trilha.mp3 (~2 min: tema · canção de ninar · lamento · veredito)"""
import math, subprocess, sys
from pathlib import Path
import numpy as np
AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI.parents[2] / "painel" / "ferramentas"))
from orquestra import Orquestra   # noqa: E402

rng = np.random.default_rng(21)
Q = 0.66                     # semínima da canção de ninar (lenta, de berço)
# a canção de ninar (nota, semínimas): duas frases de 8 compassos em 3/4
NINAR = [("E5", 1), ("C5", 1), ("A4", 1), ("B4", 1), ("G#4", 1), ("E4", 1), ("A4", 1), ("B4", 1), ("C5", 1), ("B4", 3),
         ("E5", 1), ("C5", 1), ("A4", 1), ("D5", 1), ("B4", 1), ("G#4", 1), ("A4", 1), ("C5", 1), ("B4", 1), ("A4", 3),
         ("F5", 1), ("E5", 1), ("D5", 1), ("C5", 1), ("B4", 1), ("A4", 1), ("D5", 1), ("C5", 1), ("B4", 1), ("E5", 3),
         ("F5", 1), ("E5", 1), ("D5", 1), ("C5", 1), ("A4", 1), ("F4", 1), ("E4", 1), ("G#4", 1), ("B4", 1), ("A4", 3)]
# um acorde por compasso (baixo, terça/quinta)
ACORDES = ["A2", "E2", "A2", "E2", "A2", "D2", "E2", "A2", "D2", "A2", "E2", "E2", "D2", "F2", "E2", "A2"]
TRIADE = {"A2": ["A3", "C4", "E4"], "E2": ["G#3", "B3", "E4"], "D2": ["A3", "D4", "F4"], "F2": ["A3", "C4", "F4"]}


def oit(n, k):
    return n[:-1] + str(int(n[-1]) + k)


def caixinha(o, t0, vel=1.0, ate=None, cansa=False):
    """A canção de ninar na caixinha de música: glockenspiel + harpa uma oitava abaixo, com o leve 'tic' mecânico.
    cansa=True: a corda acaba — o andamento cai e a última nota sai desafinada."""
    t = t0; notas = NINAR[:ate]
    for k, (n, q) in enumerate(notas):
        f = 1.0
        if cansa:
            f = 1 + 1.6 * (k / len(notas)) ** 2.2
        des = -0.6 if (cansa and k == len(notas) - 1) else rng.normal(0, 0.03)
        o.toque("glock", oit(n, 1), t, 0.55 * vel, pan=0.15, desafina=des)
        o.toque("harpa", n, t + 0.012, 0.45 * vel, pan=-0.1, desafina=des)
        t += q * Q * f
    return t


def piano_errado(o, t0, vel=1.0, ate=None):
    """A mesma canção no piano de armário, desafinado e oscilando — 'a mãe que não é a mãe'."""
    t = t0
    for k, (n, q) in enumerate(NINAR[:ate]):
        des = 0.28 * math.sin(k * 1.7) + rng.normal(0, 0.06)
        o.toque("piano", n, t, 0.8 * vel, pan=0.1, din="p", desafina=des, dur=q * Q * 1.6 + 0.8)
        if k % 3 == 0:
            b = ACORDES[(k // 3) % len(ACORDES)]
            o.toque("piano", oit(b, 0), t, 0.5 * vel, pan=-0.2, din="p", desafina=des * 0.5, dur=3 * Q + 1)
        t += q * Q * (1 + 0.06 * math.sin(k))
    return t


def relogio(o, t0, compassos, vel=1.0, sobe=True):
    """TEMA DO FORMATO: o relógio da investigação. Colcheias em pizzicato (6 por compasso de 6/8), baixo no 1º tempo,
    piano grave a cada 2 compassos, violinos em trêmulo subindo por cima."""
    E = 0.2; BAR = 6 * E; prog = ["A2", "F2", "D2", "E2"]
    for c in range(compassos):
        b = prog[c % 4]; tr = TRIADE[b]; tc = t0 + c * BAR
        figura = [b, tr[0], oit(b, 1), tr[1], tr[0], tr[2]]
        for k, n in enumerate(figura):
            g = "vc_pizz" if k % 2 == 0 else "vla_pizz"
            nn = n if g == "vc_pizz" else oit(n, 0)
            o.toque(g, nn, tc + k * E, (0.75 if k == 0 else 0.5) * vel, pan=(-0.3 if g == "vc_pizz" else 0.3))
        o.toque("cb_pizz", oit(b, -1), tc, 0.9 * vel)
        if c % 2 == 0:
            o.toque("piano", oit(b, -1), tc, 0.6 * vel, din="m", dur=2 * BAR)
            o.toque("piano", b, tc, 0.45 * vel, din="m", dur=2 * BAR)
    d = compassos * BAR
    if sobe:
        o.cresc("vlns_trem", "E5", t0 + d * 0.25, d * 0.75, 0.02, 0.45 * vel, pan=-0.35)
        o.cresc("vlns_trem", "A5", t0 + d * 0.55, d * 0.45, 0.02, 0.35 * vel, pan=0.35)
        o.cresc("vc", "A2", t0, d, 0.15, 0.4 * vel)
    o.golpe("timp", t0 + d - 0.05, 0.9 * vel, 3)
    return t0 + d


def lamento(o, t0, vel=1.0):
    """Bridget Cleary, 1895: um lamento irlandês lento no violino solo, harpa em arpejos e bordão grave."""
    L = [("A4", 2), ("C5", 1), ("D5", 1), ("E5", 3), ("D5", 1), ("C5", 1.5), ("A4", 0.5), ("G4", 1), ("E4", 1), ("A4", 4),
         ("C5", 1), ("D5", 1), ("E5", 2), ("G5", 1), ("E5", 1), ("D5", 2), ("C5", 1), ("D5", 1), ("A4", 4)]
    q = 0.78; t = t0
    o.cresc("cb", "A2", t0 - 0.5, 34 * q, 0.2, 0.35); o.cresc("vc", "E3", t0, 32 * q, 0.1, 0.28, pan=0.25)
    for k, (n, d) in enumerate(L):
        o.nota("vln", n, t, d * q * 1.03, 1.05 * vel, ataque=0.12 if d >= 1 else 0.05, solta=0.6, pan=-0.12)
        t += d * q
    for b in range(0, 34, 2):           # arpejos da harpa: Am, G, Am, Em
        raiz = ["A2", "G2", "A2", "E2"][(b // 4) % 4]
        acc = {"A2": ["A2", "E3", "A3", "C4"], "G2": ["G2", "D3", "G3", "B3"], "E2": ["E2", "B2", "E3", "G3"]}[raiz]
        for i, n in enumerate(acc):
            o.toque("harpa", n, t0 + b * q + i * 0.13, 0.5 * vel, pan=0.2)
    return t


def veredito(o, t0):
    """O veredito: o relógio da investigação por baixo, a canção de ninar inteira nas cordas por cima (violinos, violas
    em terças), tímpanos na resolução — e a caixinha perdendo a corda no fim."""
    BAR = 1.2
    fim_rel = relogio(o, t0, 16, vel=0.8, sobe=False)
    q = BAR / 3; t = t0 + 2 * BAR
    for k, (n, d) in enumerate(NINAR[:20]):
        o.nota("vlns", n, t, d * q * 1.02, 0.9, ataque=0.08, solta=0.5, pan=-0.25)
        o.nota("vla", oit(n, -1), t, d * q * 1.02, 0.55, ataque=0.08, solta=0.5, pan=0.25)
        t += d * q
    o.cresc("vc", "A2", t0, t - t0, 0.25, 0.6, pan=-0.2); o.cresc("cb", "A1" if False else "A2", t0, t - t0, 0.2, 0.55)
    o.golpe("timp", t - 0.1, 1.3, 5); o.golpe("bumbo", t - 0.1, 1.2, 8)
    o.cresc("vlns", "A4", t - 0.1, 4.5, 0.6, 0.05, pan=-0.2); o.cresc("vc", "A2", t - 0.1, 5, 0.6, 0.05)
    return caixinha(o, t + 2.2, 0.8, ate=10, cansa=True)


if __name__ == "__main__":
    o = Orquestra(150); t = 0.5
    # 1. o tema do formato (o relógio da investigação)
    t = relogio(o, t, 20) + 0.4
    # 2. a canção de ninar: na caixinha, depois no piano errado, com bordão grave por baixo (nunca silêncio)
    o.cresc("cb", "A2", t - 0.6, 46, 0.15, 0.3); o.cresc("vc", "E3", t, 44, 0.08, 0.2, pan=0.3)
    t = caixinha(o, t, 1.0) + 0.6
    t = piano_errado(o, t, 1.0, ate=20) + 0.8
    # 3. o lamento de Bridget Cleary
    t = lamento(o, t) + 0.5
    # 4. o veredito
    t = veredito(o, t) + 3.0
    wav = AQUI / "previa_trilha.wav"; o.salvar(wav, rev=0.34, corte=t)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(wav), "-af", "afade=t=out:st=%.2f:d=2.5" % (t - 2.6), "-b:a", "192k",
                    str(AQUI / "previa_trilha.mp3")], check=True); wav.unlink()
    print("ok", AQUI / "previa_trilha.mp3", f"{t:.1f}s")
