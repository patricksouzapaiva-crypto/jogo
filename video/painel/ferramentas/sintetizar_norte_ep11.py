"""Trilha do Ep. 11 (Escandinávia), sintetizada em código como as dos Ep. 08–10 (16/11).
Pacote: 1ª metade (capítulos) = folk nórdico sombrio — tambor grave de pele, canto KULNING distante; 2ª metade (a
história na floresta) = drone grave e gelado, vento nos pinheiros, estalos de madeira congelada. Os links do YouTube
do pacote não dá para baixar daqui e a licença deles é incerta: a trilha é composta aqui, no mesmo espírito.
Modo: Ré eólio (D E F G A Bb C) com o Lá e o Ré soltos de bordão (afinação da nyckelharpa); o Si♭ é a ameaça.
Instrumentos: nyckelharpa (rabeca de teclas sueca: arco, cordas simpáticas que ressoam), tambor de moldura de pele,
kulning (o chamado agudo de pastora, com saltos e glissandos), trompa de chifre (lur), vento, gelo.
Uso: python3 sintetizar_norte_ep11.py folk|kulning|gelo saida.mp3 [segundos]
     python3 sintetizar_norte_ep11.py unida saida.mp3 folk:300,kulning:200,gelo:400
     python3 sintetizar_norte_ep11.py cap <pasta>   (música dos 4 cartões de runa)"""
import subprocess, sys
import numpy as np
from sintetizar_trilha import SR, hz, reverb
from sintetizar_caixinha_ep06 import Mesa

rng = np.random.default_rng(1111)
EOLIO = ["D4", "E4", "F4", "G4", "A4", "Bb4", "C5", "D5"]


def _ruido_banda(n, centro, largura):
    N = 1 << (n - 1).bit_length(); fr = np.fft.rfftfreq(N, 1 / SR)
    x = np.fft.irfft(np.fft.rfft(rng.standard_normal(N)) * np.exp(-((fr - centro) / largura) ** 2), N)[:n]
    return x / (np.abs(x).max() + 1e-9)


def nyckelharpa(f, dur, vel=0.12, bordao=True):
    """Arco numa corda (parciais de dente de serra filtrados pelo corpo de madeira), vibrato lento que entra
    depois do ataque, ruído do arco, e as cordas simpáticas ressoando (o 'halo' metálico da nyckelharpa)."""
    n = int(dur * SR); t = np.arange(n) / SR
    vib = 1 + 0.004 * np.sin(2 * np.pi * 5.2 * t) * np.minimum(1, t / 0.8)
    ph = 2 * np.pi * np.cumsum(f * vib) / SR
    s = np.zeros(n)
    for k in range(1, 24):
        fk = f * k
        corpo = np.exp(-((fk - 520) / 380) ** 2) + 0.7 * np.exp(-((fk - 2600) / 900) ** 2) + 0.15
        s += np.sin(k * ph + rng.random()) / k * corpo
    arco = _ruido_banda(n, 2400, 1500) * 0.025
    env = np.minimum(1, t / 0.25) * np.minimum(1, (dur - t) / 0.6).clip(0)
    s = (s + arco) * env
    simp = sum(np.sin(2 * np.pi * hz(x) * t) for x in ("D4", "A4", "D5", "F5")) * 0.025 * np.minimum(1, t / 1.5)
    if bordao:
        s += np.sin(2 * np.pi * hz("D3") * t + 1) * 0.18 * env
    return (s + simp * env) * vel


def tambor(vel=0.5, grave=1.0, dur=1.8):
    """Tambor de moldura de pele grande, batido com maço: tom grave que cai e o tapa da pele."""
    n = int(dur * SR); t = np.arange(n) / SR
    f = (44 + 36 * np.exp(-t / 0.06)) * grave
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.45)
    s += 0.35 * np.sin(2 * np.pi * np.cumsum(f * 1.59) / SR) * np.exp(-t / 0.15)
    pele = np.convolve(rng.standard_normal(n), np.ones(40) / 40, "same") * np.exp(-t / 0.025) * 1.4
    return np.tanh((s + pele) * 1.3) * vel


def kulning(notas, vel=0.06):
    """O chamado de pastora sueco: voz feminina aguda e reta (pouco vibrato), saltos com glissando no início das
    notas, vogal 'ô/a' (formantes ~750 e ~1150 Hz sobre um fundamental de 600–900 Hz). notas = [(nota, s), ...]."""
    dur = sum(d for _, d in notas) + 2.0
    n = int(dur * SR); fseq = np.zeros(n); i = 0; prev = hz(notas[0][0])
    for nota, d in notas:
        m = int(d * SR); f1 = hz(nota)
        g = int(min(0.18, d / 3) * SR)
        fseq[i:i + g] = np.linspace(prev * 0.94, f1, g); fseq[i + g:i + m] = f1; i += m; prev = f1
    fseq[i:] = prev
    t = np.arange(n) / SR
    vib = 1 + 0.002 * np.sin(2 * np.pi * 5.8 * t)
    ph = 2 * np.pi * np.cumsum(fseq * vib) / SR
    s = np.zeros(n)
    for k in range(1, 9):
        fk = fseq * k
        peso = np.exp(-((fk - 750) / 260) ** 2) + 0.8 * np.exp(-((fk - 1150) / 320) ** 2) + 0.25 * np.exp(-((fk - 2900) / 500) ** 2)
        s += np.sin(k * ph) * peso
    env = np.minimum(1, t / 0.12) * np.minimum(1, (sum(d for _, d in notas) + 0.4 - t) / 0.6).clip(0)
    sopro = _ruido_banda(n, 1800, 900) * 0.012
    return (s * env + sopro * env) * vel


def lur(f, dur, vel=0.05):
    """Trompa de chifre/lur: tom grave e áspero, ataque lento, harmônicos ímpares fortes."""
    n = int(dur * SR); t = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f * k * t + rng.random()) / k ** (0.8 if k % 2 else 1.4) for k in range(1, 12))
    env = np.minimum(1, t / 1.2) * np.minimum(1, (dur - t) / 1.5).clip(0)
    return s * env * vel * 0.5


def vento(dur, vel=0.05):
    """Vento nos pinheiros: ruído em duas bandas que sobem e descem em rajadas lentas e desiguais."""
    n = int(dur * SR); t = np.arange(n) / SR
    a = _ruido_banda(n, 260, 160); b = _ruido_banda(n, 700, 300)   # grave: rajada, nunca chiado (usuário vetou chiado de fundo)
    raj = 0.35 + 0.65 * (0.5 + 0.5 * np.sin(2 * np.pi * t / 11 + 0.4) * np.sin(2 * np.pi * t / 4.3)) ** 2
    return (a * 0.7 + b * 0.3 * raj) * raj * vel


def gelo(dur, vel=0.03):
    """Cintilar de gelo: aglomerado agudo de senoides quase iguais (batimento lento) + estalos raros de madeira congelada."""
    n = int(dur * SR); t = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f * t + rng.random() * 6) for f in (2349, 2352.5, 3136, 3141, 3520)) / 5
    s *= 0.4 + 0.6 * (0.5 + 0.5 * np.sin(2 * np.pi * t / 19)) ** 2
    est = np.zeros(n)
    for _ in range(int(dur / 9)):
        i = int(rng.random() * (n - SR)); m = int(0.08 * SR); tt = np.arange(m) / SR
        est[i:i + m] += rng.standard_normal(m) * np.exp(-tt / 0.01) * (0.3 + 0.7 * rng.random())
    return (s * vel + np.convolve(est, np.ones(6) / 6, "same") * vel * 2.5)


def drone(dur, vel=0.2):
    t = np.arange(int(dur * SR)) / SR; f = hz("D1")
    s = np.sin(2 * np.pi * f * t) + np.sin(2 * np.pi * f * 1.003 * t) + 0.45 * np.sin(2 * np.pi * f * 1.5 * t) + 0.2 * np.sin(2 * np.pi * f * 2.997 * t)
    return s / 2.6 * (0.78 + 0.22 * np.sin(2 * np.pi * t / 21)) * vel


def compor_folk(dur):
    """Capítulos: ciclos de ~20 s. Bordão grave sempre; frases de nyckelharpa em Ré eólio com respiro entre elas;
    tambor de pele lento (forte-fraco) como um coração; o kulning muito longe de vez em quando."""
    M = Mesa(dur); t = 0.5; k = 0
    M.por(drone(dur + 2, vel=0.12), 0)
    while t < dur:
        tp = t + 2.0
        for j in range(int(rng.integers(3, 5))):
            nota = EOLIO[int(rng.integers(0, len(EOLIO)))] if rng.random() > 0.18 else "Bb4"
            d = 1.6 + 1.6 * rng.random()
            M.por(nyckelharpa(hz(nota) / 2 if rng.random() < 0.3 else hz(nota), d + 0.6, vel=0.09), tp); tp += d
        if k % 3 == 1:
            M.por(kulning([("A5", 1.4), ("D6", 2.2), ("C6", 0.8), ("A5", 2.0)], vel=0.035), t + 10.0)
        if k % 4 == 3:
            M.por(lur(hz("D2"), 9.0, vel=0.05), t + 4.0)
        t += 20.0; k += 1
    tb = 1.0
    while tb < dur:
        M.por(tambor(vel=0.18, grave=0.85), tb); M.por(tambor(vel=0.09, grave=1.0), tb + 0.5); tb += 3.2
    return reverb(M.sair(0.45), 4.5, 0.4)


def compor_kulning(dur):
    """O meio (cap. 3/4, aparte, chegada à aldeia): o ritual se aproximando — tambor mais presente, o canto agudo mais
    perto, o lur grave e a nyckelharpa só em notas longas de bordão."""
    M = Mesa(dur); t = 0.5; k = 0
    M.por(drone(dur + 2, vel=0.14), 0)
    M.por(vento(dur + 2, vel=0.007), 0)
    chamados = [[("D6", 1.6), ("A5", 1.0), ("C6", 2.4)], [("A5", 1.2), ("Bb5", 1.0), ("A5", 2.6)], [("F5", 1.0), ("A5", 1.4), ("D6", 2.8)]]
    while t < dur:
        M.por(nyckelharpa(hz("D3"), 18.0, vel=0.05), t)
        M.por(kulning(chamados[k % 3], vel=0.05), t + 5.0)
        if k % 2 == 1:
            M.por(lur(hz("A1"), 10.0, vel=0.06), t + 9.0)
        t += 19.0; k += 1
    tb = 1.0
    while tb < dur:
        M.por(tambor(vel=0.22, grave=0.8), tb); M.por(tambor(vel=0.11, grave=0.95), tb + 0.45); tb += 2.4
    return reverb(M.sair(0.45), 5.0, 0.45)


def compor_gelo(dur):
    """A história na floresta: drone grave contínuo, vento nos pinheiros em rajadas, cintilar de gelo, estalos;
    de vez em quando o kulning MUITO longe (quase vento) e uma nota de nyckelharpa em 2ª menor."""
    M = Mesa(dur)
    M.por(drone(dur + 2, vel=0.24), 0)
    M.por(vento(dur + 2, vel=0.014), 0)
    M.por(gelo(dur + 2, vel=0.02), 0)
    t = 8.0; k = 0
    while t < dur:
        if k % 3 == 0:
            M.por(kulning([("D6", 2.0), ("C#6", 2.6)], vel=0.018), t)
        else:
            M.por(nyckelharpa(hz("A3") if k % 2 else hz("Bb3"), 8.0, vel=0.035, bordao=False), t + 3.0)
        t += 17.0; k += 1
    return reverb(M.sair(0.4), 6.0, 0.5)


def compor_unida(partes):
    """As três como UMA: cada parte entra por baixo da anterior numa fusão de 18 s; um pedal em Ré atravessa tudo."""
    F = 18.0; tot = sum(d for _, d in partes) - F * (len(partes) - 1)
    out = np.zeros(int(tot * SR) + SR); t0 = 0.0
    for i, (nome, d) in enumerate(partes):
        x = {"folk": compor_folk, "kulning": compor_kulning, "gelo": compor_gelo}[nome](d)
        x /= np.sqrt(np.mean(x ** 2)) + 1e-9; x *= 0.12
        n = len(x); k = np.arange(n) / SR; env = np.ones(n)
        if i > 0: env *= np.clip(k / F, 0, 1) ** 0.5
        if i < len(partes) - 1: env *= np.clip((d - k) / F, 0, 1) ** 0.5
        a = int(t0 * SR); out[a:a + n] += (x * env)[: len(out) - a]
        t0 += d - F
    t = np.arange(len(out)) / SR
    out += np.sin(2 * np.pi * hz("D1") * t) * 0.02 * (0.8 + 0.2 * np.sin(2 * np.pi * t / 29))
    return out / (np.abs(out).max() + 1e-9) * 0.8


def entalhe(dur=1.4):
    """A faca entalhando a runa na madeira gelada: raspadas curtas de ruído médio-agudo com 'pega' da lâmina."""
    n = int(dur * SR); s = np.zeros(n)
    for k in range(5):
        i = int((0.05 + k * 0.24) * SR); m = int(0.18 * SR); tt = np.arange(m) / SR
        s[i:i + m] += _ruido_banda(m, 2600 + 400 * k, 900) * np.sin(np.pi * tt / tt[-1]) ** 0.6 * (0.6 + 0.4 * rng.random())
    return s * 0.12


# cartões de runa: 0–1.4 s a lâmina entalha · 1.6 s o TAMBOR (a runa acende) · depois o chamado próprio do capítulo
CAPS = {1: ([("A5", 1.2), ("D6", 2.4)], "D2"), 2: ([("F5", 1.0), ("E5", 1.0), ("D5", 2.4)], "A1"),
        3: ([("D6", 1.4), ("C#6", 2.6)], "D2"), 4: ([("A5", 0.8), ("C6", 0.8), ("D6", 2.6)], "A1")}


def capitulo(n, dur=8.0):
    M = Mesa(dur)
    M.por(vento(dur, vel=0.05), 0)
    M.por(entalhe(), 0.1)
    M.por(tambor(vel=0.7, grave=0.75, dur=3.0), 1.6)
    M.por(lur(hz(CAPS[n][1]), 5.5, vel=0.07), 1.7)
    M.por(kulning(CAPS[n][0], vel=0.06), 2.6)
    return reverb(M.sair(0.5), 4.0, 0.4)


def _salvar(m, saida, af):
    est = np.stack([m, np.roll(m, int(0.012 * SR))], 1).astype(np.float32)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-af", af,
                    "-ar", "44100", "-b:a", "192k", saida], input=est.tobytes(), check=True)


if __name__ == "__main__" and sys.argv[1] == "cap":
    for n in CAPS:
        _salvar(capitulo(n), f"{sys.argv[2]}/ep11_cap{n}.mp3", "highpass=f=30,loudnorm=I=-16:TP=-1.5:LRA=9")
        print("ok cap", n)
    sys.exit()

if __name__ == "__main__":
    modo, saida = sys.argv[1], sys.argv[2]
    if modo == "unida":
        m = compor_unida([(p.split(":")[0], float(p.split(":")[1])) for p in sys.argv[3].split(",")])
    else:
        dur = float(sys.argv[3]) if len(sys.argv) > 3 else 90.0
        m = {"folk": compor_folk, "kulning": compor_kulning, "gelo": compor_gelo}[modo](dur)
    _salvar(m, saida, "highpass=f=35,acompressor=threshold=-30dB:ratio=2.5:attack=300:release=2500:makeup=2,loudnorm=I=-20:TP=-3:LRA=7")
    print("ok", saida, f"{len(m) / SR:.0f}s")
