"""Instrumentos japoneses GRAVADOS para a trilha do Ep. 12 (24/11; pedido do usuário: "uma trilha ainda mais bem feita
do que a do episódio 8"). Estende a Orquestra (VSCO-2, cordas/tímpanos/bumbo) com gravações CC0 da Versilian Community
Sample Library (VCSL, em ~/.cache/vcsl, fora do repo):
- koto: o DAN TRANH (cítara vietnamita, da mesma família do koto japonês e do guzheng), notas soltas em 3 dinâmicas,
  com vibrato de mão esquerda, trêmulo e glissandos gravados. Dobras de afinação (oshide: aperta a corda e a nota sobe)
  feitas por reamostragem variável sobre a gravação;
- taiko: bumbo sinfônico + tambor de moldura grave, em camadas e afinados para baixo (corpo grande, pele seca);
- hyoshigi: woodblock em dupla batida; gongo (dora) e sinos de templo (sinos tubulares graves, sinos nepaleses = rin);
- shakuhachi: não existe gravação CC0 — sopro sintetizado (Ep. 08, meri + ar + vibrato no fim), agora com sala e
  respiração de verdade por cima.
Uso: j = Japao(dur); j.koto("D4", t, vel, oshi=1); j.taiko(t, vel); j.hyoshigi(t); j.gongo(t); j.salvar(arq)"""
import glob, re, sys
from pathlib import Path
import numpy as np
from orquestra import Orquestra, SR, midi, carregar, reamostrar

V = Path.home() / ".cache" / "vcsl"
DT = V / "Chordophones/Zithers/Dan Tranh"


class Japao(Orquestra):
    def __init__(self, dur):
        super().__init__(dur)
        for g, pasta, rx in (("koto", "Normal", r"^([A-G]#?\d)_(mf|f|ff)_"), ("koto_vib", "Vibrato", r"^([A-G]#?\d)_vib_(mf|ff)_"),
                             ("koto_trem", "Tremolo", r"^([A-G]#?\d)_Trem_()")):
            for f in glob.glob(str(DT / pasta / "*.wav")):
                m = re.search(rx, Path(f).name)
                if m: self.tab.setdefault(g, []).append((midi(m.group(1)), m.group(2) or "p", f))
        P = lambda p: sorted(glob.glob(str(V / p)))
        self.perc.update({
            "bumbo2": P("Membranophones/Struck Membranophones/Bass Drum 2/bassdrum_hit_*.wav"),
            "bumbo_rufo": P("Membranophones/Struck Membranophones/Bass Drum 2/bassdrum_cresc_*.wav"),
            "moldura": P("Membranophones/Struck Membranophones/Frame Drum/HDrumL_Hit_*.wav"),
            "moldura_abafada": P("Membranophones/Struck Membranophones/Frame Drum/HDrumL_HitMuted_*.wav"),
            "madeira": P("Idiophones/Struck Idiophones/Woodblock/wood_click_*.wav"),
            "gongo": P("Idiophones/Struck Idiophones/Gong 1/gong_*.wav") + P("Idiophones/Struck Idiophones/Gong 2/*.wav"),
            "rin": P("Idiophones/Struck Idiophones/Hand Bells, Nepalese/*.wav"),
            "sino": P("Idiophones/Struck Idiophones/Tubular Bells 1/chimes_*.wav"),
            "tora": P("Idiophones/Struck Idiophones/Slit Drum/LogDrumLo_*.wav"),
            "gliss_desce": P("Chordophones/Zithers/Dan Tranh/Gliss/Gliss_Dwn_*.wav"),
            "gliss_sobe": P("Chordophones/Zithers/Dan Tranh/Gliss/Gliss_Up_*.wav"),
            "koto_fx": P("Chordophones/Zithers/Dan Tranh/FX/*.wav"),
        })
        self.rng = np.random.default_rng(1212)

    # ------------------------------------------------------------------ koto
    def koto(self, n, t, vel=0.8, din="f", oshi=0.0, oshi_t=0.35, vib=False, pan=0.0, dur=None, molhado=0.8):
        """Uma corda pinçada. oshi = semitons que a nota SOBE depois do ataque (a mão esquerda aperta a corda atrás da
        ponte); oshi negativo = a nota afrouxa (hiki). oshi_t = quando a dobra acontece (s)."""
        g = "koto_vib" if vib else "koto"
        alvo = midi(n); x = self._amostra(g, alvo, "ff" if din == "ff" else ("mf" if din in ("mf", "p") else "f"))
        if dur:
            k = int(dur * SR); x = x[:k].copy(); f = min(len(x), int(0.3 * SR)); x[-f:] *= np.linspace(1, 0, f)[:, None]
        if oshi:
            # leitura com velocidade variável: 1 → 2^(oshi/12), curva suave depois de oshi_t
            n_s = len(x); tt = np.arange(n_s) / SR
            curva = 1 / (1 + np.exp(-(tt - oshi_t - 0.09) / 0.045))
            vel_l = 2 ** (oshi * curva / 12)
            pos = np.cumsum(vel_l); pos = pos[pos < n_s - 1]
            x = np.stack([np.interp(pos, np.arange(n_s), x[:, c]) for c in range(2)], 1).astype(np.float32)
        self._por(x, t, vel, pan, molhado)

    def koto_trem(self, n, t, d, vel=0.6, pan=0.0):
        self.nota("koto_trem", n, t, d, vel, ataque=0.3, solta=1.2, pan=pan)

    def gliss(self, t, vel=0.7, sobe=False, k=0, pan=0.0):
        self.golpe("gliss_sobe" if sobe else "gliss_desce", t, vel, k, pan)

    # ------------------------------------------------------------------ percussão
    def taiko(self, t, vel=1.0, k=None, pan=0.0, grave=True):
        """Ō-daiko: bumbo grave (corpo) + tambor de moldura (pele), afinados para baixo."""
        k = int(self.rng.integers(0, 6)) if k is None else k
        self.golpe("bumbo2", t, vel * 0.9, k, pan, transp=-3 if grave else 0)
        self.golpe("moldura", t + 0.004, vel * 0.55, k, pan, transp=-5)

    def shime(self, t, vel=0.5, pan=0.2):
        """Tambor pequeno e seco (shime-daiko): a moldura abafada, aguda."""
        self.golpe("moldura_abafada", t, vel, int(self.rng.integers(0, 4)), pan, transp=4)

    def hyoshigi(self, t, vel=0.6, pan=0.0):
        """As duas madeiras do teatro: duas batidas secas, a segunda um pouco mais forte."""
        self.golpe("madeira", t, vel * 0.8, 5, pan); self.golpe("madeira", t + 0.16, vel, 4, pan)

    def gongo(self, t, vel=0.8, k=0, pan=0.0, transp=0):
        self.golpe("gongo", t, vel, k, pan, transp)

    def rin(self, t, vel=0.5, k=0, pan=0.0, transp=0):
        self.golpe("rin", t, vel, k, pan, transp)

    def bonsho(self, t, vel=0.8, pan=0.0):
        """Sino de templo: sino tubular grave abaixado uma oitava + gongo bem baixo por baixo."""
        self.golpe("sino", t, vel, 2, pan, transp=-12); self.golpe("gongo", t, vel * 0.4, 2, pan, transp=-5)

    # ------------------------------------------------------------------ shakuhachi (sintetizado, ver docstring)
    def shakuhachi(self, n, t, d, vel=0.5, pan=-0.2):
        sys.path.insert(0, str(Path(__file__).parent))
        import sintetizar_japones_ep08 as J
        from sintetizar_trilha import SR as SR0
        J.rng = self.rng
        hz = 440.0 * 2 ** ((midi(n) - 69) / 12)
        s = J.shakuhachi(hz, d, vel=1.0).astype(np.float32)
        s = reamostrar(np.stack([s, s], 1), SR / SR0)
        s /= np.sqrt(np.mean(s ** 2)) + 1e-9; s *= 0.1
        self._por(s, t, vel, pan, molhado=1.0)
