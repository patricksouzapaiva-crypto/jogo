"""Trilha do Ep. 10 (Tailândia / Isan), sintetizada em código como a do Ep. 08 (a preferida do usuário).
Pacote do Ep. 10: 1ª metade (capítulos) = cordas tensas de suspense psicológico + o alaúde PHIN e o órgão de bambu KHAEN
de Isan (desacelerados, -4 semitons, reverb longo); 2ª metade (o Mateus / CCTV) = drone grave, contínuo e sufocante,
cigarras da mata de Isan e o zumbido elétrico baixo das câmeras. Os links do YouTube do pacote não dá para baixar daqui
(bloqueio de robô) e a licença deles é incerta: a trilha é composta aqui, no mesmo espírito.
Modo: "lai" de Isan, pentatônica menor em Lá (A C D E G) com o Si♭ entrando de vez em quando (a 2ª menor = ameaça).
Uso: python3 sintetizar_isan_ep10.py cordas|ritual|drone saida.mp3 [segundos]
     python3 sintetizar_isan_ep10.py unida saida.mp3 cordas:600,ritual:240,drone:540   (as três como uma só)
     python3 sintetizar_isan_ep10.py cap <pasta>   (a música de cada cartão de capítulo)"""
import subprocess, sys
import numpy as np
from sintetizar_trilha import SR, cordas, hz
from sintetizar_caixinha_ep06 import cello, Mesa

rng = np.random.default_rng(1010)
DESCE = 2 ** (-4 / 12)          # -4 semitons (o pedido do pacote)
LAI = ["A3", "C4", "D4", "E4", "G4", "A4", "C5", "D5"]


def phin(f, vel=0.16, dur=3.5):
    """Alaúde de Isan: corda de metal beliscada com palheta (ataque brilhante, parciais quase harmônicos),
    a nota 'escorrega' de baixo para cima e a corda solta (drone) vibra por simpatia."""
    f *= DESCE
    n = int(dur * SR); t = np.arange(n) / SR
    bend = f * 2 ** ((-60 * np.exp(-t / 0.08) * (rng.random() < 0.5)) / 1200)
    ph = 2 * np.pi * np.cumsum(bend) / SR
    s = sum(np.sin(k * ph + rng.random()) * np.exp(-t * (1.2 + 0.9 * k)) / k ** 0.9 for k in range(1, 10))
    s += 0.25 * np.sin(2 * np.pi * hz("A2") * DESCE * 2 * t) * np.exp(-t * 0.8)          # corda solta
    pal = np.convolve(rng.standard_normal(n), np.ones(8) / 8, "same") * np.exp(-t / 0.004) * 0.25   # palheta (sem o estalo agudo)
    return (s * np.minimum(1, t / 0.003) + pal) * vel


def khaen(freqs, dur, vel=0.05, respira=0.0):
    """Órgão de bambu: palhetas livres (timbre de harmônica, harmônicos ímpares fortes), acorde com bordão,
    entrada de ar audível; 'respira' > 0 pulsa o fole no ritmo da respiração (inspira/expira)."""
    n = int(dur * SR); t = np.arange(n) / SR; s = np.zeros(n)
    for f in freqs:
        f *= DESCE
        for d in (-0.08, 0.08):
            ph = 2 * np.pi * f * (1 + d / 100) * t + rng.random() * 6
            s += sum(np.sin(k * ph) * (1.0 if k % 2 else 0.35) / k ** 1.1 for k in range(1, 12))
    s /= len(freqs) * 2
    ar = np.convolve(rng.standard_normal(n), np.ones(6) / 6, "same") * 0.05
    env = np.minimum(1, t / 1.2) * np.minimum(1, (dur - t) / 2.0).clip(0)
    if respira:
        env *= 0.65 + 0.35 * np.abs(np.sin(np.pi * t / respira))
    return (s + ar) * env * vel


def tremolo(freqs, dur, vel=0.05):
    """Cordas em tremolo sul ponticello (o 'suspense psicológico'): mais harmônicos agudos, arco tremendo."""
    s = cordas(freqs, dur, vel=vel, ataque=dur / 2.5)
    t = np.arange(len(s)) / SR
    return s * (0.7 + 0.3 * np.sin(2 * np.pi * 7.5 * t))


def cigarras(dur, vel=0.03):
    """Cigarras/insetos de Isan: chiado agudo (4–7 kHz) trinado ~45 Hz que cresce e some em ondas lentas."""
    n = int(dur * SR); t = np.arange(n) / SR
    N = 1 << (n - 1).bit_length(); fr = np.fft.rfftfreq(N, 1 / SR)
    x = np.fft.irfft(np.fft.rfft(rng.standard_normal(N)) * np.exp(-((fr - 5200) / 1300) ** 2), N)[:n]
    x /= np.abs(x).max() + 1e-9
    trino = 0.55 + 0.45 * np.sin(2 * np.pi * 44 * t) ** 2
    onda = 0.35 + 0.65 * (0.5 + 0.5 * np.sin(2 * np.pi * t / 23 + 1.3)) ** 2
    return x * trino * onda * vel


def drone(dur, vel=0.2):
    """Sub grave sufocante: duas notas quase iguais (batimento lento) + o zumbido de 60 Hz das câmeras."""
    t = np.arange(int(dur * SR)) / SR
    f = hz("A1") * DESCE
    s = np.sin(2 * np.pi * f * t) + np.sin(2 * np.pi * f * 1.004 * t) + 0.4 * np.sin(2 * np.pi * f * 1.5 * t)
    s *= 0.75 + 0.25 * np.sin(2 * np.pi * t / 17)
    hum = sum(np.sin(2 * np.pi * 60 * k * t) / k ** 1.5 for k in (1, 2, 3, 5)) * 0.04
    return (s / 2.4 + hum) * vel


def compor_cordas(dur):
    """1ª metade: ciclos de ~19 s. Pedal grave sempre; tremolo que cresce em 2ª menor; frases de phin com
    silêncio entre elas; o khaen respira por baixo a cada dois ciclos."""
    M = Mesa(dur); t = 0.5; k = 0
    while t < dur:
        M.por(cello(hz("A1") * DESCE * 2, 20.0, vel=0.15), t)
        M.por(tremolo([hz("E3") * DESCE, hz("F3") * DESCE if k % 2 else hz("A3") * DESCE], 16.0, vel=0.04), t + 2.0)
        if k % 2 == 0:
            M.por(khaen([hz("A2"), hz("E3"), hz("A3")], 17.0, vel=0.035, respira=3.4), t + 1.0)
        tp = t + 3.0
        for j in range(int(rng.integers(3, 6))):
            nota = LAI[int(rng.integers(0, len(LAI)))] if rng.random() > 0.15 else "Bb4"
            M.por(phin(hz(nota), vel=0.15), tp)
            if rng.random() < 0.3: M.por(phin(hz(nota), vel=0.08), tp + 0.16)      # nota repetida (estilo lai)
            tp += 0.9 + 1.1 * rng.random()
        t += 19.0; k += 1
    return M.sair(0.45)


def compor_drone(dur):
    """2ª metade: o drone nunca para; cigarras em ondas; de vez em quando um acorde de khaen muito longe
    e uma nota grave de cordas em 2ª menor."""
    M = Mesa(dur)
    M.por(drone(dur + 2, vel=0.22), 0)
    M.por(cigarras(dur + 2, vel=0.02), 0)
    t = 6.0; k = 0
    while t < dur:
        if k % 2 == 0: M.por(khaen([hz("A3"), hz("Bb3")], 14.0, vel=0.02), t)
        else: M.por(tremolo([hz("A2") * DESCE, hz("Bb2") * DESCE], 14.0, vel=0.03), t)
        if k % 3 == 1: M.por(phin(hz("E4"), vel=0.06, dur=5.0), t + 8.0)
        t += 16.0; k += 1
    return M.sair(0.35)


def coro_monge(f, dur, vel=0.05):
    """Canto grave e fechado (o 'o' de uma reza de monges ao longe): harmônicos com formantes de ~400 e ~750 Hz."""
    n = int(dur * SR); t = np.arange(n) / SR; s = np.zeros(n)
    for d in (-0.12, 0.0, 0.11):
        vib = 1 + 0.003 * np.sin(2 * np.pi * 4.3 * t + rng.random() * 6)
        ph = 2 * np.pi * np.cumsum(f * DESCE * (1 + d / 100) * vib) / SR
        for k in range(1, 18):
            fk = f * DESCE * k; peso = np.exp(-((fk - 400) / 130) ** 2) + 0.5 * np.exp(-((fk - 750) / 180) ** 2) + 0.3 / k
            s += np.sin(k * ph) * peso
    env = np.minimum(1, t / 3) * np.minimum(1, (dur - t) / 3).clip(0)
    return s / 6 * env * vel


def compor_ritual(dur):
    """3ª trilha (16/11): a do meio (capítulo 3, aparte, começo do Mateus). O ritual ao longe: um tambor de moldura
    bem baixo marcando o tempo devagar (como um coração), o khaen respirando, a reza grave dos monges e o phin raro."""
    M = Mesa(dur); t = 0.5; k = 0
    while t < dur:
        M.por(khaen([hz("A2"), hz("E3")], 21.0, vel=0.03, respira=4.2), t)
        if k % 2 == 0: M.por(coro_monge(hz("A2"), 18.0, vel=0.05), t + 2.0)
        else: M.por(coro_monge(hz("E2"), 18.0, vel=0.04), t + 2.0)
        if k % 3 == 1: M.por(phin(hz("D4"), vel=0.08, dur=4.0), t + 9.0); M.por(phin(hz("C4"), vel=0.07, dur=4.0), t + 10.2)
        t += 20.0; k += 1
    tb = 1.0
    while tb < dur:   # o pulso: duas batidas (forte-fraca) a cada 2.6 s, abafadas
        M.por(tambor(vel=0.16, grave=0.9), tb); M.por(tambor(vel=0.09, grave=1.05), tb + 0.42); tb += 2.6
    return M.sair(0.45)


def compor_unida(partes):
    """As três trilhas como UMA só: cada parte entra por baixo da anterior numa fusão longa (18 s), e um pedal grave
    em Lá (-4 st) atravessa o episódio inteiro, por baixo de tudo — é ele que 'cola' as três.
    partes: [("cordas"|"ritual"|"drone", segundos), ...]"""
    F = 18.0; tot = sum(d for _, d in partes) - F * (len(partes) - 1)
    out = np.zeros(int(tot * SR) + SR); t0 = 0.0
    for i, (nome, d) in enumerate(partes):
        x = {"cordas": compor_cordas, "ritual": compor_ritual, "drone": compor_drone}[nome](d)
        x /= np.sqrt(np.mean(x ** 2)) + 1e-9; x *= 0.12 if nome != "drone" else 0.10   # mesmo volume percebido
        n = len(x); k = np.arange(n) / SR; env = np.ones(n)
        if i > 0: env *= np.clip(k / F, 0, 1) ** 0.5
        if i < len(partes) - 1: env *= np.clip((d - k) / F, 0, 1) ** 0.5
        a = int(t0 * SR); out[a:a + n] += (x * env)[: len(out) - a]
        t0 += d - F
    t = np.arange(len(out)) / SR; f = hz("A1") * DESCE
    out += (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 2.003 * t)) * 0.02 * (0.8 + 0.2 * np.sin(2 * np.pi * t / 29))
    return out / (np.abs(out).max() + 1e-9) * 0.8


def tambor(vel=0.6, grave=1.0):
    """Tambor ritual seco: pele grande, o tom cai (90 → 48 Hz) e morre rápido; o golpe da mão por cima."""
    n = int(1.6 * SR); t = np.arange(n) / SR
    f = (48 + 42 * np.exp(-t / 0.05)) * grave
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.35)
    s += 0.5 * np.sin(2 * np.pi * np.cumsum(f * 1.6) / SR) * np.exp(-t / 0.12)
    pele = np.convolve(rng.standard_normal(n), np.ones(30) / 30, "same") * np.exp(-t / 0.02) * 1.5
    return np.tanh((s + pele) * 1.4) * vel


# a música de cada cartão de capítulo (16/11, pedido do usuário: "cada apresentação de capítulo com a música dela").
# Mesma assinatura em todas (o khaen respira enquanto o pano desenrola; o TAMBOR bate em 1.6 s junto com o tranco do
# pano; o phin responde) e um tema próprio para cada capítulo. (tambores, frase do phin [(nota, s)], acorde do khaen)
CAPS = {
    1: ([1.6], [("A3", 2.0), ("C4", 2.45), ("D4", 2.9), ("E4", 3.35), ("E4", 4.3), ("D4", 4.75), ("A3", 5.4)], ["A2", "E3", "A3"]),   # a terra: sobe e assenta
    2: ([1.6, 1.95], [("E4", 2.3), ("Bb4", 2.75), ("A4", 3.05), ("Bb4", 3.3), ("A4", 3.55), ("E4", 4.4), ("Bb3", 5.3)], ["A2", "Bb2", "E3"]),   # a criatura: 2ª menor, coração
    3: ([1.6, 2.25, 2.7, 3.05], [("D4", 3.4), ("D4", 3.6), ("C4", 3.95), ("A3", 4.35), ("D4", 5.0), ("C4", 5.25), ("A3", 5.7)], ["A2", "Bb2", "D3", "E3"]),   # o ritual: tambores acelerando
    4: ([1.6], [("G4", 2.1), ("E4", 2.5), ("D4", 2.9), ("C4", 3.3), ("A3", 3.9), ("Bb3", 5.0)], ["A2", "E3"]),   # a câmera: desce, termina na 2ª menor
}


def capitulo(n, dur=8.0):
    tambores, frase, acorde = CAPS[n]
    M = Mesa(dur)
    M.por(khaen([hz(x) for x in acorde], 6.5, vel=0.05, respira=0.0) * np.linspace(0.2, 1, int(6.5 * SR)) ** 0.5, 0.0)
    M.por(cordas([hz("A1") * DESCE * 2, hz("E2") * DESCE * 2], 7.0, vel=0.08, ataque=1.6), 0.9)
    for k, tb in enumerate(tambores):
        M.por(tambor(vel=0.75 if k == 0 else 0.5, grave=1.0 if k == 0 else 1.15), tb)
    for nota, tn in frase:
        M.por(phin(hz(nota), vel=0.17, dur=3.0), tn)
    if n == 2: M.por(tremolo([hz("A4") * DESCE, hz("Bb4") * DESCE], 5.0, vel=0.025), 2.0)
    if n == 4:   # o chiado digital da câmera junto do tambor
        t = np.arange(int(0.5 * SR)) / SR; M.por(rng.standard_normal(len(t)) * np.exp(-t / 0.12) * 0.05, 1.6)
    return M.sair(0.4)


def desenrolar(dur=1.9):
    """O pano desenrolando (16/11: substitui a gravação de pano amassado, que 'parecia alguém mastigando'): o toque
    seco da vara de madeira, o tecido batendo no ar (ruído de banda média, tremulando cada vez mais devagar) e o
    baque macio do rolo no fim."""
    n = int(dur * SR); t = np.arange(n) / SR
    N = 1 << (n - 1).bit_length(); fr = np.fft.rfftfreq(N, 1 / SR)
    x = np.fft.irfft(np.fft.rfft(rng.standard_normal(N)) * (np.exp(-((fr - 900) / 700) ** 2) + 0.3 * np.exp(-((fr - 2600) / 1200) ** 2)), N)[:n]
    x /= np.abs(x).max() + 1e-9
    trem = 0.55 + 0.45 * np.sin(2 * np.pi * np.cumsum(26 * np.exp(-t / 0.9) + 6) / SR) ** 2
    env = np.minimum(1, t / 0.25) * np.exp(-np.clip(t - 1.1, 0, None) / 0.25)
    s = x * trem * env * 0.35
    tok = np.sin(2 * np.pi * 420 * t) * np.exp(-t / 0.03) * 0.25 + np.sin(2 * np.pi * 760 * t) * np.exp(-t / 0.015) * 0.12
    s += tok
    i = int(1.45 * SR); m = n - i; tt = t[:m]
    s[i:] += np.sin(2 * np.pi * (70 + 40 * np.exp(-tt / 0.04)) * tt) * np.exp(-tt / 0.12) * 0.3
    return s


if __name__ == "__main__" and sys.argv[1] == "desenrolar":
    m = desenrolar().astype(np.float32); est = np.stack([m, np.roll(m, int(0.008 * SR))], 1)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-af", "highpass=f=60,loudnorm=I=-20:TP=-3",
                    "-ar", "44100", "-b:a", "192k", sys.argv[2]], input=est.tobytes(), check=True)
    print("ok", sys.argv[2]); sys.exit()

if __name__ == "__main__" and sys.argv[1] == "cap":
    for n in CAPS:
        m = capitulo(n).astype(np.float32); est = np.stack([m, np.roll(m, int(0.011 * SR))], 1)
        saida = f"{sys.argv[2]}/ep10_cap{n}.mp3"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-af",
                        "highpass=f=30,loudnorm=I=-16:TP=-1.5:LRA=9", "-ar", "44100", "-b:a", "192k", saida], input=est.tobytes(), check=True)
        print("ok", saida)
    sys.exit()

if __name__ == "__main__":
    modo, saida = sys.argv[1], sys.argv[2]; dur = float(sys.argv[3]) if len(sys.argv) > 3 and modo != "unida" else 600.0
    if modo == "unida":   # unida saida.mp3 cordas:70,ritual:70,drone:70
        m = compor_unida([(p.split(":")[0], float(p.split(":")[1])) for p in sys.argv[3].split(",")]).astype(np.float32); dur = len(m) / SR
    else:
        m = {"cordas": compor_cordas, "ritual": compor_ritual, "drone": compor_drone}[modo](dur).astype(np.float32)
    est = np.stack([m, np.roll(m, int(0.013 * SR))], 1)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-af",
                    "highpass=f=35,acompressor=threshold=-30dB:ratio=2.5:attack=300:release=2500:makeup=2,loudnorm=I=-20:TP=-3:LRA=7",
                    "-ar", "44100", "-b:a", "192k", saida], input=est.tobytes(), check=True)
    print("ok", saida, f"{dur:.0f}s")
