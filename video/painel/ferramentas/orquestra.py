"""Sampler de orquestra com gravações reais (VSCO-2 Community Edition, CC0 — baixadas em ~/.cache/vsco, fora do repo).
16/11 (Ep. 11: "a trilha sonora nesse episódio será extremamente importante, então capriche").
Instrumentos: violino solo (arco com vibrato, p/f), naipe de violinos/violas/cellos (sustentado e trêmulo), contrabaixo
(sustentado sem vibrato), tímpanos (golpes e rufos) e bumbo sinfônico. Nota = a gravação mais próxima transposta por
reamostragem (no máx. ~2 semitons); notas longas encadeiam gravações com cruzamento. Reverb = resposta de sala sintética
(salão de pedra frio, ~4.5 s), por convolução.
Uso como biblioteca: o = Orquestra(dur_s); o.nota("vln", "A4", t, d, vel); o.golpe("bumbo", t, vel); o.salvar(arq)"""
import glob, re
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy.signal import fftconvolve, butter, sosfilt

SR = 44100
BASE = Path.home() / ".cache" / "vsco"
NOMES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def midi(n):
    if isinstance(n, (int, float)): return n
    m = re.match(r"([A-G])(#|b)?(-?\d)", n)
    return NOMES[m.group(1)] + {"#": 1, "b": -1, None: 0}[m.group(2)] + 12 * (int(m.group(3)) + 1)


GRUPOS = {   # nome → (padrão de arquivos, regex que tira a nota e a dinâmica do nome)
    "vln": ("Strings/Solo Violin/Arco Vib/*.wav", r"ArcoVib_([A-G]#?\d)_([pf])"),
    "vlns": ("Strings/Violin Section/susVib/*.wav", r"susVib_([A-G]#?\d)_"),
    "vlns_trem": ("Strings/Violin Section/Trem/*.wav", r"Trem_([A-G]#?\d)_"),
    "vla": ("Strings/Viola Section/susvib/*.wav", r"susvib_([A-G]#?\d)_"),
    "vla_trem": ("Strings/Viola Section/trem/*.wav", r"trem_([A-G]#?\d)_"),
    "vc": ("Strings/Cello Section/susvib/*.wav", r"susvib_([A-G]#?\d)_"),
    "vc_trem": ("Strings/Cello Section/trem/*.wav", r"trem_([A-G]#?\d)_"),
    "cb": ("Strings/Solo Contrabass/SusNV/*.wav", r"SusNV_([A-G]#?\d)_"),
    # 21/11 (O que é a criatura?): pizzicatos, harpa, glockenspiel (a caixinha de música), metais graves
    "vc_pizz": ("Strings/Cello Section/pizzT/*.wav", r"pizzT_([A-G]#?\d)_"),
    "vla_pizz": ("Strings/Viola Section/pizz/*.wav", r"pizz_([A-G]#?\d)_"),
    "vlns_pizz": ("Strings/Violin Section/Pizz/*.wav", r"Pizz_([A-G]#?\d)_"),
    "cb_pizz": ("Strings/Solo Contrabass/Pizz/*.wav", r"Pizz_([A-G]#?\d)_"),
    "harpa": ("Strings/Harp/*.wav", r"KSHarp_([A-G]#?\d)_"),
    "glock": ("Percussion/Glock/*.wav", r"glock_medium_([A-G]#?\d)"),
    "tuba": ("Brass/Tuba/sus/*.wav", r"sus_([A-G]#?\d)_"),
    "trombone": ("Brass/Tenor Trombone/sus/*.wav", r"sus_([A-G]#?\d)_"),
}
_cache = {}


def carregar(arq):
    if arq not in _cache:
        x, sr = sf.read(arq, dtype="float32", always_2d=True)
        if x.shape[1] == 1: x = np.repeat(x, 2, 1)
        if sr != SR: x = reamostrar(x, SR / sr)
        # tira o silêncio do começo (ataque no ponto certo)
        e = np.abs(x).max(1); i0 = int(np.argmax(e > e.max() * 0.02)); x = x[max(0, i0 - 64):]
        _cache[arq] = x / (np.sqrt(np.mean(x[: SR * 2] ** 2)) + 1e-9) * 0.1   # todas no mesmo volume de base
    return _cache[arq]


def reamostrar(x, fator):   # fator > 1 = mais amostras (mais grave se for tocado na mesma taxa)
    n = int(len(x) * fator); t = np.linspace(0, len(x) - 1, n)
    return np.stack([np.interp(t, np.arange(len(x)), x[:, c]) for c in range(x.shape[1])], 1).astype(np.float32)


class Orquestra:
    def __init__(self, dur):
        self.buf = np.zeros((int(dur * SR) + SR * 8, 2), np.float32); self.seco = np.zeros_like(self.buf)
        self.tab = {}
        for g, (pad, rx) in GRUPOS.items():
            for f in glob.glob(str(BASE / pad)):
                m = re.search(rx, Path(f).name)
                if m: self.tab.setdefault(g, []).append((midi(m.group(1)), m.group(2) if m.lastindex > 1 else "p", f))
        # piano de armário: arquivos numerados (MappingChart: índice k → tecla MIDI 21 + 2k), 3 dinâmicas
        for f in glob.glob(str(BASE / "Keys/Upright Piano/Player_dyn*_rr1_*.wav")):
            m = re.search(r"dyn(\d)_rr1_(\d+)", Path(f).name)
            if m: self.tab.setdefault("piano", []).append((21 + 2 * int(m.group(2)), {"1": "p", "2": "m", "3": "f"}[m.group(1)], f))
        self.perc = {"bumbo": sorted(glob.glob(str(BASE / "Percussion/BDrumNewhit_*.wav"))),
                     "timp": sorted(glob.glob(str(BASE / "Percussion/Timpani/Timpani*_Hit_*.wav"))),
                     "rufo": sorted(glob.glob(str(BASE / "Percussion/Timpani/Rolls/*.wav")))}

    def _amostra(self, g, alvo, din):
        cand = [c for c in self.tab[g] if c[1] == din] or self.tab[g]
        m, _, f = min(cand, key=lambda c: (abs(c[0] - alvo), c[0] < alvo))
        x = carregar(f)
        return reamostrar(x, 2 ** ((m - alvo) / 12)) if abs(m - alvo) > 1e-6 else x

    def _por(self, x, t, vel, pan, molhado=1.0):
        i = int(t * SR); x = x[: len(self.buf) - i]
        l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        y = x * vel * np.array([l * 1.414, r * 1.414], np.float32)
        self.buf[i:i + len(y)] += y * molhado; self.seco[i:i + len(y)] += y * (1 - molhado * 0.5)

    def nota(self, g, n, t, d, vel=1.0, ataque=0.06, solta=0.6, pan=0.0, din="p", molhado=1.0):
        """nota de duração d (s); se a gravação for curta, encadeia outra com cruzamento de 1.5 s"""
        alvo = midi(n); x = self._amostra(g, alvo, din)
        total = int((d + solta) * SR); y = np.zeros((total, 2), np.float32); pos = 0; xf = int(1.5 * SR)
        while pos < total:
            seg = x[int(0.15 * SR) if pos else 0:]; k = min(len(seg), total - pos)
            s = seg[:k].copy()
            if pos: s[:xf] *= np.linspace(0, 1, min(xf, k))[:, None]
            if pos + k < total and k > xf: s[-xf:] *= np.linspace(1, 0, xf)[:, None]
            y[pos:pos + k] += s
            if pos + k >= total: break
            pos += max(int(0.5 * SR), k - xf)
        env = np.ones(total, np.float32); a = max(1, int(ataque * SR)); env[:a] = np.linspace(0, 1, a) ** 1.5
        r = int(solta * SR); env[-r:] *= np.linspace(1, 0, r) ** 2
        self._por(y * env[:, None], t, vel, pan, molhado)

    def toque(self, g, n, t, vel=1.0, pan=0.0, din="p", dur=None, desafina=0.0, molhado=1.0):
        """nota que soa e decai sozinha (pizzicato, harpa, glockenspiel, piano): a gravação inteira, sem emendar.
        desafina: em semitons (o piano 'errado' da Outra Mamãe)."""
        alvo = midi(n); x = self._amostra(g, alvo + desafina, din)
        if dur:
            k = int(dur * SR); x = x[:k].copy(); f = min(len(x), int(0.25 * SR)); x[-f:] *= np.linspace(1, 0, f)[:, None]
        self._por(x, t, vel, pan, molhado)

    def cresc(self, g, n, t, d, v0, v1, pan=0.0, din="p"):
        """nota com crescendo/decrescendo (curva) — para os trêmulos e os bordões que incham"""
        alvo = midi(n); x = self._amostra(g, alvo, din); total = int(d * SR)
        y = np.zeros((total, 2), np.float32); pos = 0; xf = int(1.5 * SR)
        while pos < total:
            seg = x[int(0.15 * SR) if pos else 0:]; k = min(len(seg), total - pos); s = seg[:k].copy()
            if pos: s[:xf] *= np.linspace(0, 1, min(xf, k))[:, None]
            if pos + k < total and k > xf: s[-xf:] *= np.linspace(1, 0, xf)[:, None]
            y[pos:pos + k] += s
            if pos + k >= total: break
            pos += max(int(0.5 * SR), k - xf)
        env = np.linspace(v0, v1, total, dtype=np.float32) ** 1.6
        f = min(int(0.4 * SR), total // 4); env[-f:] *= np.linspace(1, 0, f)
        self._por(y * env[:, None], t, 1.0, pan)

    def golpe(self, tipo, t, vel=1.0, k=0, pan=0.0, transp=0):
        fs = self.perc[tipo]; x = carregar(fs[k % len(fs)])
        if transp: x = reamostrar(x, 2 ** (-transp / 12))
        self._por(x, t, vel, pan)

    def salvar(self, arq, rev=0.32, corte=None, silencios=()):
        # sala de pedra fria: ruído decaindo (estéreo descorrelacionado), agudos morrendo antes
        n = int(4.5 * SR); tt = np.arange(n) / SR; rng = np.random.default_rng(7)
        ir = rng.standard_normal((n, 2)).astype(np.float32) * np.exp(-tt / 1.15)[:, None]
        ir = sosfilt(butter(2, 3800, fs=SR, output="sos"), ir, axis=0); ir[: int(0.02 * SR)] *= np.linspace(0, 1, int(0.02 * SR))[:, None]
        ir /= np.sqrt((ir ** 2).sum(0)); mol = np.stack([fftconvolve(self.buf[:, c], ir[:, c])[: len(self.buf)] for c in range(2)], 1)
        y = self.seco + self.buf * (1 - rev) + mol * rev * 2.2
        y = sosfilt(butter(2, 30, "hp", fs=SR, output="sos"), y, axis=0)
        for sil in silencios:   # silêncio de verdade (o reverb também é cortado); (t, d) = borda de 25 ms, (t, d, f) =
            t, d = sil[:2]          # a música vai sumindo em f segundos (20/11: entrada dos cartões, nunca um corte seco)
            f = int((sil[2] if len(sil) > 2 else 0.025) * SR); i, j = int(t * SR), int((t + d) * SR)
            y[i:i + f] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, f)))[:, None]; y[i + f:j] = 0
            g = int(0.6 * SR); y[j:j + g] *= np.linspace(0, 1, g)[:, None] ** 2
        if corte: y = y[: int(corte * SR)]
        y /= max(1e-9, np.abs(y).max()) / 0.89
        sf.write(arq, y, SR)
        return arq
