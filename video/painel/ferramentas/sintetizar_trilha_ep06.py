"""Trilha do Ep. 06 "A porta na mata" — piano velho, violoncelo e violinos, composta em código (11/11/2026).
Mesmos timbres do Ep. 05 (aprovados), música nova: si menor, 4/4 muito lento, um motivo de três notas que
"bate na porta" (fá#–fá#–sol) e nunca resolve. A mata é o resto do som: a música deixa espaço.
Uso: python3 sintetizar_trilha_ep06.py fundo saida.mp3 [segundos]
     python3 sintetizar_trilha_ep06.py tensao saida.mp3 [segundos]
"""
import subprocess
import sys

import numpy as np

from sintetizar_piano_violino import Mesa, ao_contrario, gliss, nuvem, piano_velho, violino
from sintetizar_trilha import SR, cordas, hz

rng = np.random.default_rng(6)

# baixo, duas notas do acorde (com 2ª menor ou trítono), nota longa do violino
PROG = [("B1", ("F#3", "D4"), "F#4"), ("B1", ("F#3", "C4"), "G4"), ("G1", ("D3", "B3"), "D5"), ("G1", ("D3", "C#4"), "C#5"),
        ("E2", ("B3", "G4"), "B4"), ("E2", ("Bb3", "G4"), "Bb4"), ("F#1", ("E3", "A#3"), "F#4"), ("F#1", ("C#3", "A#3"), None),
        ("B1", ("F#3", "D4"), "D5"), ("C2", ("G3", "E4"), "E5"), ("B1", ("F#3", "D4"), "F#5"), ("G1", ("D3", "Bb3"), "D5"),
        ("E2", ("B3", "G4"), "G4"), ("F2", ("C4", "F4"), "F4"), ("F#1", ("E3", "A#3"), "E4"), ("B1", ("F#3", "B3"), None)]


def motivo(M, t, tempo, oitava=1.0, vel=0.22):
    """As três batidas, no piano: fá#, fá#, sol (a terceira sobe meio-tom e fica)."""
    for i, nota in enumerate(("F#4", "F#4", "G4")):
        M.por(piano_velho(hz(nota) * oitava, dur=6, vel=vel * (1.0, 0.85, 1.1)[i]), t + i * tempo * 0.5)


def fundo(dur=960.0, tempo=1.5):
    M = Mesa(dur); comp = 4 * tempo; t = 0.8; k = 0
    while t < dur:
        secao = (k // 8) % 4; baixo, ac, mel = PROG[k % 16]
        vazio = rng.random() < 0.15 and k % 8 not in (0, 7)       # compasso em que o piano não vem
        if not vazio:
            M.por(piano_velho(hz(baixo) * 2, dur=comp * 1.7, vel=0.32), t)
            M.por(piano_velho(hz(baixo), dur=comp * 1.7, vel=0.11), t)
            M.por(piano_velho(hz(ac[0]), dur=6, vel=0.22), t + 1.5 * tempo + (rng.random() - 0.5) * 0.1)
            if secao != 0:
                M.por(piano_velho(hz(ac[1]), dur=6, vel=0.24), t + 3 * tempo + (rng.random() - 0.5) * 0.1)
        if k % 8 == 7:                                            # o motivo das batidas fecha cada frase
            motivo(M, t + 2 * tempo, tempo, vel=0.2 if secao else 0.15)
        if k % 4 == 1:                                            # nota ao contrário inchando até o compasso seguinte
            r = ao_contrario(piano_velho(hz(ac[1]) * 2, dur=comp * 0.9, vel=0.26))
            M.por(r, t + comp - len(r) / SR)
        M.por(cordas([hz(baixo) * 4, hz(baixo) * 6], comp + 2.5, vel=0.08 if secao < 2 else 0.12, ataque=1.8), t - 0.5)
        if mel and secao in (1, 2):
            M.por(violino(hz(mel), comp + 0.4, vel=0.20 if secao == 1 else 0.13), t)
            if secao == 2:
                M.por(violino(hz(mel) * 2, comp + 0.4, vel=0.07), t)
        if secao == 3:
            if k % 2 == 0:
                M.por(nuvem(mel or "F#5", comp * 2, vel=0.035), t)
            if k % 8 == 5:
                M.por(gliss(hz("B5"), hz("F5"), comp * 1.5, vel=0.06), t)
        t += comp; k += 1
    return M.sair(mistura=0.46)


def tensao(dur=480.0):
    """Sem melodia: pedal de si grave com o dó natural por cima (2ª menor), nuvens de violinos, glissandos para
    baixo e — de tempos em tempos — o motivo das três batidas, grave, como alguém do outro lado."""
    M = Mesa(dur); t = 0.0; k = 0
    while t < dur:
        M.por(cordas([hz("B2"), hz("F#3")], 17.0, vel=0.20, ataque=4.0), t)
        if k % 2:
            M.por(cordas([hz("C3")], 12.0, vel=0.09, ataque=5.0), t + 3)
        M.por(nuvem(("F#5", "G5", "C5", "B4", "F5")[k % 5], 12.0, vel=0.05), t + 1.5)
        if k % 3 == 1:
            M.por(gliss(hz("G5"), hz("C#5"), 9.0, vel=0.08), t + 4)
        if k % 4 == 2:
            M.por(violino(hz("F#5"), 9.0, vel=0.06), t + 5.0)
        if k % 3 == 2:
            motivo(M, t + 7.0, 1.3, oitava=0.25, vel=0.34)
        t += 13.5; k += 1
    graves = ["B2", "F#2", "C3", "B2", "G2", "B2", "F2"]
    for i, t0 in enumerate(np.arange(4.0, dur - 6, 7.0)):
        M.por(piano_velho(hz(graves[i % len(graves)]), vel=0.30 + 0.06 * rng.random()), t0 + rng.random() * 0.6)
    return M.sair(mistura=0.5)


if __name__ == "__main__":
    modo, saida = sys.argv[1], sys.argv[2]
    dur = float(sys.argv[3]) if len(sys.argv) > 3 else (960.0 if modo == "fundo" else 480.0)
    m = {"fundo": fundo, "tensao": tensao}[modo](dur).astype(np.float32)
    est = np.stack([m, np.roll(m, int(0.013 * SR))], 1)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-af",
                    "highpass=f=70,acompressor=threshold=-32dB:ratio=3:attack=400:release=2500:makeup=2,loudnorm=I=-20:TP=-3:LRA=6",
                    "-ar", "44100", "-b:a", "192k", saida], input=est.tobytes(), check=True)
    print("ok", saida, f"{dur:.0f}s")
