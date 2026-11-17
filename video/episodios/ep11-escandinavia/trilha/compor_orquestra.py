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


if __name__ == "__main__" and len(sys.argv) == 1:
    o = Orquestra(200)
    t = gancho(o, 0.5); t = capitulos(o, t + 0.5); t = historia(o, t); t = fecho(o, t)
    wav = AQUI / "previa_orquestra.wav"; o.salvar(wav, corte=t + 0.5, silencios=SILENCIOS)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(wav), "-af", "loudnorm=I=-16:TP=-1.5", "-b:a", "192k", str(AQUI / "previa_orquestra.mp3")], check=True)
    wav.unlink(); print("ok", AQUI / "previa_orquestra.mp3", f"{t + 0.5:.0f} s")


# ---------------------------------------------------------------- som dos cartões de capítulo (8 s, golpe em 1.6 s)
def cartao(n):
    """O cartão em xilogravura: bordão subindo do nada; em 1.6 s (a gravura acende) tímpano + bumbo; depois a cabeça da
    polska, com a cor de cada capítulo: 1 = viola grave (pântano), 2 = trêmulo e semitom (a águia), 3 = violino agudo e
    cluster (as criaturas), 4 = o tema inteiro mais claro, em ré dórico (o verão do Midsommar)."""
    o = Orquestra(10); TB = 1.6
    o.cresc("cb", "D2", 0.0, 8.0, 0.05, 0.6); o.cresc("vc", "D2", 0.2, 7.8, 0.05, 0.5, pan=-0.3)
    o.golpe("timp", TB, 1.3, 2 + n); o.golpe("bumbo", TB, 1.2, 4 + n)
    t = TB + 0.35
    if n == 1:
        for k, (nt, q) in enumerate(TEMA[:5]): o.nota("vla", nt[:-1] + str(int(nt[-1]) - 1), t, q * Q * 1.1, 0.8, ataque=0.08, solta=0.5, pan=0.2); t += q * Q
        o.cresc("vc", "A2", TB, 6.4, 0.3, 0.6, pan=0.3)
    elif n == 2:
        o.cresc("vlns_trem", "D5", TB, 6.4, 0.5, 0.15, pan=-0.4); o.cresc("vlns_trem", "Eb5", TB + 0.6, 5.8, 0.4, 0.15, pan=0.4)
        for k, nt in enumerate(["D2", "Eb2", "D2", "Eb2", "D2"]): o.nota("vc", nt, TB + 0.3 + k * 1.1, 1.0, 0.75, ataque=0.03, solta=0.2)
    elif n == 3:
        o.cresc("vlns_trem", "A5" if False else "E5", TB, 6.4, 0.45, 0.1, pan=-0.3); o.cresc("vla_trem", "F4", TB + 0.3, 6.0, 0.35, 0.1, pan=0.3)
        tema(o, t, 0.55, oitava=1, ate=4)
    else:
        tema(o, t, 0.85, ate=7, din="f"); o.cresc("vla", "F3", TB, 6.4, 0.3, 0.5, pan=0.3)
    o.golpe("timp", TB + 4.95, 0.5, 7)
    return o


if __name__ == "__main__" and "cartoes" in sys.argv:
    SONS = AQUI.parents[2] / "painel" / "sons"
    for n in (1, 2, 3, 4):
        w = AQUI / f"_cap{n}.wav"; cartao(n).salvar(w, rev=0.38, corte=8.05)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(w), "-af", "afade=t=in:d=0.02,afade=t=out:st=7.0:d=1.05,volume=-1dB",
                        "-b:a", "192k", str(SONS / f"ep11_cap{n}.mp3")], check=True); w.unlink()
        print("ok", f"ep11_cap{n}.mp3")


# ---------------------------------------------------------------- a trilha do episódio inteiro, sob medida para a montagem
def episodio(plano, saida):
    """plano = {"secoes": [[nome, inicio, fim], ...], "climax": t, "fim": t, "cartoes": [[ini, fim], ...]}.
    Cada seção recebe sua parte; nos cartões a trilha some (o cartão tem a música própria)."""
    fim = plano["fim"]; o = Orquestra(fim + 10); SIL = []
    def polska_em(t0, t1, vel, **kw):   # o tema inteiro (ou o pedaço que couber), repetindo
        t = t0
        while t + 8 < t1:
            ate = None if t + 16 * BAR <= t1 else max(4, int(len(TEMA) * (t1 - t) / (16 * BAR)))
            t = tema(o, t, vel, ate=ate, **kw) + 2 * BAR
    for nome, a, b in plano["secoes"]:
        d = b - a
        if nome == "gancho":
            o.cresc("cb", "D2", a, d, 0.05, 0.85)
            o.cresc("vlns_trem", "D5", a + d * 0.15, d * 0.85, 0.0, 0.5, pan=-0.4); o.cresc("vlns_trem", "Eb5", a + d * 0.35, d * 0.65, 0.0, 0.42, pan=0.4)
            o.cresc("vc_trem", "D3", a + d * 0.5, d * 0.5, 0.0, 0.55)
            t, passo = a + d * 0.25, 2.6
            while t < b - 1.2: o.golpe("bumbo", t, 0.35 + 0.4 * (t - a) / d, int(t)); t += passo; passo = max(0.7, passo * 0.86)
            o.golpe("timp", b - 0.9, 1.4, 3); o.golpe("bumbo", b - 0.9, 1.6, 12)
        elif nome == "tema":   # destaque: a polska inteira entra com o título, bordão por baixo
            o.cresc("cb", "D2", a, d, 0.55, 0.45); o.cresc("vc", "D2", a, d, 0.5, 0.4, pan=-0.3); o.cresc("vc", "A2", a + 0.3, d, 0.45, 0.35, pan=0.3)
            polska_em(a + 0.4, b, 0.95, din="f")
        elif nome.startswith("cap"):
            n = int(nome[3]); bordao(o, a, d + 2, 0.32)
            if n == 1: polska_em(a + 6, b, 0.42, oitava=-1, pan=0.25)
            elif n == 2:
                o.cresc("vlns_trem", "D5", a + 4, d - 4, 0.05, 0.3, pan=-0.4); o.cresc("vc_trem", "D3", a + d * 0.5, d * 0.5, 0.05, 0.35)
                t = a + 3
                while t < b - 3: o.golpe("timp", t, 0.35, int(t)); t += 4 * BAR
            elif n == 3:
                o.cresc("vlns_trem", "E5", a + 3, d - 3, 0.05, 0.28, pan=-0.3); o.cresc("vla_trem", "F4", a + d * 0.3, d * 0.7, 0.05, 0.25, pan=0.3)
                polska_em(a + 10, b, 0.32, oitava=1)
            else: polska_em(a + 3, b, 0.5, din="f")
        elif nome == "aparte":
            o.cresc("cb", "D2", a, d, 0.2, 0.45); o.cresc("vla", "A3", a + 2, d - 2, 0.1, 0.3, pan=0.3); o.cresc("vc", "F3", a + 4, d - 4, 0.1, 0.25, pan=-0.3)
        elif nome == "hist1":   # a chegada à aldeia: a polska quente nas violas (a "sensação boa" antes do horror)
            o.cresc("cb", "D2", a, d, 0.5, 0.3); o.cresc("vc", "D2", a, d, 0.45, 0.3, pan=-0.3); o.cresc("vc", "A2", a, d, 0.4, 0.3, pan=0.3)
            tema(o, a + 0.3, 0.9, ate=9, din="f")   # o respiro: o violino canta sozinho em primeiro plano
            t = a + 16
            while t + 8 < b:
                for nt, q in TEMA[:18]:
                    if t > b - 2: break
                    o.nota("vla", nt[:-1] + str(int(nt[-1]) - 1), t, q * Q * 1.2 * 1.3, 0.45, ataque=0.12, solta=0.5, pan=0.2); t += q * Q * 1.3
                t += 3 * BAR
        elif nome == "hist2":   # o celeiro: trêmulos crescendo e o coração
            o.cresc("cb", "D2", a, d, 0.2, 0.7); o.cresc("vlns_trem", "D5", a + 2, d - 2, 0.02, 0.45, pan=-0.4)
            o.cresc("vlns_trem", "Eb5", a + d * 0.4, d * 0.6, 0.02, 0.4, pan=0.4); o.cresc("vla_trem", "Ab3", a + d * 0.6, d * 0.4, 0.02, 0.45)
            t = a + d * 0.45
            while t < b - 1: o.golpe("bumbo", t, 0.3, int(t * 3)); t += 1.15
        elif nome == "hist3":   # a fuga: semitom acelerando até o golpe do clímax; silêncio; só o grave depois
            c = plano["climax"]; t, passo = a, 1.2
            while t < c - 0.6:
                o.nota("vc", "D2", t, passo * 0.95, 0.7, ataque=0.03, solta=0.15, pan=-0.2)
                o.nota("vc", "Eb2", t + passo, passo * 0.95, 0.75, ataque=0.03, solta=0.15, pan=-0.2)
                t += 2 * passo; passo = max(0.3, passo * 0.955)
            o.cresc("cb", "D2", a, c - a, 0.2, 1.0); o.cresc("vlns_trem", "D5", a + (c - a) * 0.3, (c - a) * 0.7, 0.0, 0.7, pan=-0.5)
            o.cresc("vlns_trem", "Eb5", a + (c - a) * 0.5, (c - a) * 0.5, 0.0, 0.6, pan=0.5); o.cresc("vla_trem", "Ab3", a + (c - a) * 0.6, (c - a) * 0.4, 0.0, 0.6)
            o.golpe("rufo", max(a, c - 14), 0.9, 1)
            o.golpe("timp", c, 1.6, 5); o.golpe("bumbo", c, 1.9, 13); SIL.append((c + 0.9, 1.8))
            o.cresc("cb", "D2", c + 2.7, b - c - 2.7, 0.55, 0.45); o.cresc("vc", "D2", c + 2.9, b - c - 2.9, 0.45, 0.35)
            o.cresc("vla_trem", "A3", c + 3.0, b - c - 3.0, 0.3, 0.1)
        elif nome == "fecho":   # o violino sozinho, longe, o tema parado no meio; no fim, só o bordão
            o.cresc("cb", "D2", a, d, 0.45, 0.35)
            tema(o, a + 0.5, 0.6, ate=9, pan=0.3); o.nota("vln", "C#5", a + 0.5 + 16 * Q, 3.5, 0.4, ataque=0.6, solta=2.0, pan=0.3)
            if d > 60: tema(o, b - 30, 0.45, ate=9, pan=-0.2)
    for a, b in plano.get("cartoes", []):   # o cartão tem a música dele: a trilha some e volta
        SIL.append((a - 0.3, b - a + 0.3))
    o.salvar(saida, corte=fim, silencios=SIL)


if __name__ == "__main__" and "episodio" in sys.argv:   # python3 compor_orquestra.py episodio plano.json saida.mp3
    import json
    w = AQUI / "_episodio.wav"; episodio(json.load(open(sys.argv[2])), w)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(w), "-b:a", "192k", sys.argv[3]], check=True); w.unlink(); print("ok", sys.argv[3])
