"""Trilha do Ep. 12 — "Os demônios do Japão não querem a sua alma" (24/11).
Pedido do usuário: "faça uma trilha ainda mais bem feita do que a do episódio 8, porque de lá pra cá evoluímos bem".
O que mudou desde o Ep. 08 (que era toda sintetizada e em laço de 17 s, igual do começo ao fim):
- instrumentos GRAVADOS (painel/ferramentas/japao.py): koto (dan tranh) com oshide de verdade, taiko em camadas,
  hyoshigi, gongo, sino de templo, rin, e as cordas da orquestra (VSCO) por baixo;
- um TEMA só deste episódio, na escala In em ré (ré–mi♭–sol–lá–si♭), que muda de roupa a cada parte;
- composta SOBRE OS TEMPOS DA MONTAGEM (trilha/plano.json, gerado pelo montar_roteiro.py): cada seção tem a sua
  música, os golpes caem na palavra ("atenderam", "mordeu", "raio", "rachou", "rosto"), e há silêncio de verdade antes
  do susto da história. Nos cartões de capítulo a música abre espaço para a tinta e o taiko do cartão.
24/11: trilha APROVADA pelo usuário ("Trilha aprovada"), pela prévia trilha_previa_v2.mp3.
Uso: python3 compor_trilha.py plano.json saida.mp3      (prévia: python3 compor_trilha.py --previa → trilha/previa.mp3)"""
import json, subprocess, sys
from pathlib import Path
import numpy as np

AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI.parents[2] / "painel" / "ferramentas"))
from japao import Japao  # noqa: E402

Q = 0.75                       # um tempo (s): 80 bpm, lento
ESCALA = ["D3", "Eb3", "G3", "A3", "Bb3", "D4", "Eb4", "G4", "A4", "Bb4", "D5", "Eb5", "G5"]
# o tema: (nota, tempos, enfeite). "o" = a corda é pinçada meio tom abaixo e a mão esquerda empurra até a nota
# (atooshi, o gesto mais típico do koto); "O" = um tom abaixo
TEMA = [("D4", 2, ""), ("Eb4", 1, ""), ("G4", 1, "o"), ("A4", 3, ""), ("Bb4", 1, ""), ("A4", 2, "o"), ("G4", 1, ""),
        ("Eb4", 1, ""), ("D4", 4, ""),
        ("A4", 2, ""), ("Bb4", 1, ""), ("D5", 1, "O"), ("Eb5", 3, ""), ("D5", 1, ""), ("Bb4", 2, ""), ("A4", 1, "o"),
        ("G4", 1, ""), ("A4", 4, "")]
NOTA_MENOS = {"o": 1, "O": 2}


def baixar(n, s):
    from orquestra import midi
    m = midi(n) - s
    nomes = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "G#", "A", "Bb", "B"]
    return nomes[m % 12] + str(m // 12 - 1)


class Trilha:
    def __init__(self, plano):
        self.p = plano; self.fim = plano["fim"]
        self.j = Japao(self.fim + 4); self.rng = np.random.default_rng(1212)
        self.m = plano["marcos"]; self.sil = []

    # ---------------------------------------------------------------- frases
    def tema(self, t0, vel=0.8, oitava=0, ate=None, ritmo=1.0, pan=0.1, vib_final=True):
        t = t0; notas = TEMA[:ate]
        for k, (n, b, enf) in enumerate(notas):
            if oitava: n = n[:-1] + str(int(n[-1]) + oitava)
            v = vel * (1.0 if b >= 2 else 0.8)
            vib = vib_final and b >= 3
            if enf:
                self.j.koto(baixar(n, NOTA_MENOS[enf]), t, v, oshi=NOTA_MENOS[enf], oshi_t=0.28 * ritmo, pan=pan, vib=False)
            else:
                self.j.koto(n, t, v, pan=pan, vib=vib, din="ff" if v > 0.85 else "f")
            t += b * Q * ritmo
        return t

    def koto_solto(self, t0, t1, dens=0.25, vel=0.55, reg=(0, 9), pan=0.15):
        """Notas soltas do koto, como alguém tocando sozinho num quarto vazio (ma: silêncio entre as frases)."""
        t = t0 + 0.5
        while t < t1 - 2:
            for _ in range(int(self.rng.integers(2, 5))):
                n = ESCALA[int(self.rng.integers(*reg))]
                if self.rng.random() < 0.3:
                    self.j.koto(baixar(n, 1), t, vel, oshi=1, pan=pan)
                else:
                    self.j.koto(n, t, vel * (0.7 + 0.3 * self.rng.random()), pan=pan)
                t += Q * (1 + self.rng.integers(0, 3))
            t += (1 / dens) * (0.6 + 0.8 * self.rng.random())

    def chao(self, t0, t1, notas=("D2", "A2"), vel=0.35, escuro=False):
        """O chão: contrabaixo e cellos sustentados (com trítono ré–lá♭ quando o assunto escurece)."""
        d = t1 - t0; vel *= 0.55   # 24/11: o grave tomava tudo no espectro (a voz precisa do meio limpo)
        if d < 2: return
        self.j.cresc("cb", notas[0], t0, d, 0.0, vel)
        self.j.cresc("vc", "Ab2" if escuro else notas[1], t0 + 1.5, max(1.0, d - 1.5), 0.0, vel * 0.8)

    def tremulo(self, t0, t1, nota="D4", v0=0.0, v1=0.5, grupo="vlns_trem"):
        if t1 - t0 > 1.5: self.j.cresc(grupo, nota, t0, t1 - t0, v0, v1)

    def coracao(self, t0, t1, periodo=1.6, vel=0.5, acelera=1.0):
        t = t0; p = periodo; vel *= 0.7   # 24/11: o coração competia com a voz (revisão do rascunho 1)
        while t < t1:
            self.j.taiko(t, vel); self.j.taiko(t + 0.32 * p / 1.6, vel * 0.55)
            t += p; p = max(0.55, p / acelera)

    def cortejo(self, t0, t1, vel=0.7):
        """O desfile dos cem demônios: taiko marcando, shime no contratempo, hyoshigi a cada 8 tempos, shakuhachi por
        cima e o koto em trêmulo. Cresce até o fim da seção."""
        t = t0; k = 0
        while t < t1:
            f = 0.5 + 0.5 * (t - t0) / max(1, t1 - t0)
            if k % 2 == 0: self.j.taiko(t, vel * f)
            if k % 4 == 3: self.j.taiko(t + Q * 0.5, vel * 0.5 * f)
            self.j.shime(t + Q * 0.5, 0.35 * f)
            if k % 8 == 0: self.j.hyoshigi(t, 0.5 * f)
            t += Q; k += 1

    def flauta(self, t0, notas, vel=0.45, pan=-0.25):
        t = t0
        for n, d in notas:
            self.j.shakuhachi(n, t, d, vel, pan); t += d + 0.5 + 0.6 * self.rng.random()
        return t

    def golpe(self, t, forte=1.0, gongo=True):
        self.j.taiko(t, 1.0 * forte); self.j.taiko(t + 0.02, 0.6 * forte, grave=True)
        if gongo: self.j.gongo(t + 0.03, 0.7 * forte, k=1)
        self.j.golpe("timp", t, 0.6 * forte, 3)

    def silencio(self, t, d, f=0.4):
        self.sil.append((t, d, f))

    # ---------------------------------------------------------------- o episódio
    def compor(self):
        S = {n: (a, b) for n, a, b in self.p["secoes"]}; M = self.m; j = self.j

        if "gancho" in S:
            a, b = S["gancho"]   # o caso de Matsudo e o ritual: trêmulos, o coração, o koto pinçado e dobrado
            self.chao(a, b, escuro=True, vel=0.3)
            self.tremulo(a + 2, M["maldicao"], "D5", 0.0, 0.35)
            self.coracao(a + 1.0, M["maldicao"] - 1, 1.7, 0.35)
            self.koto_solto(a + 3, M["maldicao"] - 2, dens=0.2, vel=0.45, reg=(5, 11))
            j.hyoshigi(M["maldicao"] - 0.25, 0.7)
            self.tremulo(M["maldicao"], M["atenderam"], "Ab4", 0.2, 0.7, "vla_trem")
            self.silencio(M["atenderam"] - 0.9, 0.85, 0.3)
            self.golpe(M["atenderam"], 1.0)
            j.koto("D3", M["atenderam"] + 2.5, 0.7, oshi=-1, oshi_t=0.6)
            self.koto_solto(M["atenderam"] + 4, b, dens=0.25, vel=0.4, reg=(0, 6))

        if "vigia" in S:
            a, b = S["vigia"]    # o título: o tema inteiro aparece pela 1ª vez
            j.bonsho(a + 0.2, 0.6)
            self.chao(a, S["tema"][1], vel=0.28)
            self.tema(a + 1.2, 0.85)

        if "tema" in S:
            a, b = S["tema"]     # Ocidente × Japão: o tema se desfaz em notas soltas; rin no "ninguém nasce demônio"
            self.koto_solto(a + 3, b - 4, dens=0.18, vel=0.45)
            self.flauta(a + 20, [("A4", 4.0), ("G4", 3.0), ("D4", 5.0)])
            j.rin(b - 3.5, 0.5)

        if "p1" in S:
            a, b = S["p1"]       # Hashihime: o tema lento, o trêmulo que sobe até ela correr pela cidade
            self.chao(a, b, escuro=True, vel=0.3)
            t = self.tema(a + 1, 0.7, ate=9, ritmo=1.25)
            self.tremulo(t, M["correndo"], "D4", 0.05, 0.6, "vla_trem")
            self.coracao(M["correndo"] - 6, M["correndo"], 1.2, 0.45, acelera=1.08)
            self.golpe(M["correndo"], 0.8, gongo=False)
            self.cortejo(M["correndo"] + 0.5, M["correndo"] + 9, 0.55)
            j.gongo(M["nao_mulher"], 0.6, k=0)
            self.koto_solto(M["nao_mulher"] + 3, M["hashihime"], dens=0.3, vel=0.5, reg=(0, 7))
            j.bonsho(M["hashihime"] - 0.2, 0.55)
            self.tema(M["hashihime"] + 6, 0.6, oitava=1, ate=9)
            self.flauta(b - 26, [("D5", 5.0), ("Bb4", 3.5), ("A4", 6.0)], 0.4)

        if "p2" in S:
            a, b = S["p2"]       # a porta do demônio: o koto grave em ostinato (as direções) e a madeira marcando
            self.chao(a, b, vel=0.26)
            t = a + 1; k = 0
            while t < b - 3:
                j.koto(["D3", "A3", "Eb3", "A3"][k % 4], t, 0.45, pan=-0.1)
                if k % 8 == 7: j.hyoshigi(t + Q, 0.35)
                t += Q * 2; k += 1
            self.flauta(a + 25, [("Eb5", 4.0), ("D5", 3.0), ("A4", 5.0)], 0.38)
            self.tema(M["kimon"] + 1, 0.55, ate=9)

        if "p3" in S:
            a, b = S["p3"]       # Shuten-dōji: a festa no castelo (shime e koto mais rápidos), o corte, a cabeça que voa
            self.chao(a, b, escuro=True, vel=0.28)
            t = a + 1
            while t < M["cortaram"] - 3:
                j.shime(t, 0.3); j.shime(t + Q * 0.5, 0.18)
                if self.rng.random() < 0.6:
                    j.koto(ESCALA[int(self.rng.integers(5, 11))], t, 0.4, pan=0.2)
                t += Q
            self.silencio(M["cortaram"] - 0.6, 0.55, 0.25)
            j.golpe("timp", M["cortaram"], 0.8, 2)
            self.tremulo(M["cortaram"] + 0.5, M["mordeu"], "Eb5", 0.1, 0.6)
            self.golpe(M["mordeu"], 1.0)
            j.gliss(M["mordeu"] + 0.4, 0.6)
            self.koto_solto(M["mordeu"] + 5, b - 2, dens=0.25, vel=0.45, reg=(0, 7))
            j.bonsho(M["kubizuka"], 0.55)

        if "p4" in S:
            a, b = S["p4"]       # o demônio que virou deus: tímpano rolando, o raio, e depois a paz (o tema em sol, aberto)
            j.golpe("rufo", M["raio"] - 3.0, 0.6, 0)
            self.chao(a, M["tenjin"], escuro=True, vel=0.3)
            self.tremulo(a + 3, M["raio"], "A4", 0.1, 0.6)
            self.golpe(M["raio"], 0.9)
            j.rin(M["tenjin"] - 0.3, 0.6, 0); j.rin(M["tenjin"] + 2.5, 0.4, 1)
            self.chao(M["tenjin"], b, ("G2", "D3"), vel=0.25)
            self.tema(M["tenjin"] + 1.5, 0.6, oitava=0, ate=9, ritmo=1.1)
            self.koto_solto(M["tenjin"] + 18, b - 2, dens=0.35, vel=0.5, reg=(5, 12))

        if "p5" in S:
            a, b = S["p5"]       # as regras: leve e estranho, o koto em notas curtas e a madeira (um jogo de sobrevivência)
            self.chao(a, b, vel=0.22)
            t = a + 1; k = 0
            while t < b - 3:
                if k % 16 < 12:
                    j.koto(ESCALA[[5, 7, 8, 7, 5, 6, 5, 3][k % 8]], t, 0.38, dur=0.9, pan=0.25)
                if k % 8 == 0: j.golpe("madeira", t, 0.3, 6)
                if k % 32 == 31: j.hyoshigi(t, 0.4)
                t += Q; k += 1
            j.bonsho(M["dormiu"], 0.6)

        if "p6" in S:
            a, b = S["p6"]       # os piores: o mais escuro (cluster grave, o coração acelerando), a pedra rachando
            self.chao(a, b, escuro=True, vel=0.35)
            self.tremulo(a + 2, M["pesar"], "D3", 0.1, 0.55, "vc_trem")
            self.coracao(M["pesar"] - 2, M["pesar"] + 8, 1.3, 0.5, acelera=1.05)
            j.gongo(M["cranios"], 0.6, k=2)
            self.koto_solto(M["cranios"] + 3, M["rachou"] - 25, dens=0.25, vel=0.45, reg=(0, 6))
            self.tremulo(M["rachou"] - 18, M["rachou"], "Ab4", 0.05, 0.7, "vla_trem")
            self.coracao(M["rachou"] - 10, M["rachou"] - 0.5, 1.2, 0.55, acelera=1.08)
            self.silencio(M["rachou"] - 0.7, 0.65, 0.2)
            self.golpe(M["rachou"], 1.1)
            j.gliss(M["rachou"] + 1.0, 0.5)
            self.tremulo(M["rachou"] + 3, M["saido"], "D5", 0.25, 0.0)
            j.koto("D4", M["saido"] + 0.4, 0.7, oshi=1, oshi_t=0.8)

        if "p7" in S:
            a, b = S["p7"]       # o desfile: o cortejo cresce até a morte; a reza; o desfile passa por cima
            self.chao(a, b, escuro=True, vel=0.3)
            self.cortejo(M["desfile"] - 1, M["morria"] + 0.5, 0.8)
            self.tremulo(M["desfile"], M["morria"], "D4", 0.1, 0.6, "vlns_trem")
            self.golpe(M["morria"] + 0.6, 0.9)
            self.cortejo(M["morosuke"], M["reza"] - 1.5, 0.6)
            self.flauta(M["morosuke"] + 4, [("A4", 3.0), ("Bb4", 2.0), ("A4", 2.5), ("G4", 2.0), ("Eb4", 4.0)], 0.4)
            self.silencio(M["reza"] - 1.0, 1.0, 1.2)
            j.rin(M["reza"], 0.5, 2)
            self.tema(M["bebado"] + 2, 0.55, ate=9, ritmo=1.3)
            j.bonsho(b - 2.5, 0.7)

        if "hist" in S:
            a, b = S["hist"]     # a sétima noite: quase nada. O koto em ré–mi♭ (meio tom) que insiste e cresce a cada noite
            self.chao(a, b, escuro=True, vel=0.25)
            t = a + 2; k = 0; aperta = 1.0
            while t < M["rosto"] - 1.5:
                v = 0.3 + 0.35 * (t - a) / max(1, M["rosto"] - a)
                j.koto("D4" if k % 2 == 0 else "Eb4", t, v, pan=0.1, dur=2.5)
                if M["setima"] < t: aperta = 0.6
                t += Q * 3 * aperta; k += 1
            self.coracao(M["tres_chamas"] - 1, M["tres_chamas"] + 10, 1.6, 0.35)
            j.golpe("madeira", M["metal"], 0.35, 0); j.golpe("madeira", M["metal"] + 0.9, 0.3, 1)
            j.gongo(M["a_dela"] + 0.2, 0.55, k=0)
            self.coracao(M["setima"], M["lanterna"] - 0.3, 1.4, 0.4, acelera=1.06)
            self.tremulo(M["setima"] + 2, M["rosto"] - 0.4, "Eb5", 0.05, 0.75)
            self.tremulo(M["lanterna"] - 4, M["rosto"] - 0.4, "D3", 0.1, 0.7, "vc_trem")
            self.silencio(M["rosto"] - 0.35, M["seis_anos"] - M["rosto"] + 0.6, 0.15)    # o rosto: silêncio total
            j.bonsho(M["seis_anos"] + 0.4, 0.9)
            self.koto_solto(M["seis_anos"] + 6, M["sumiu"] + 4, dens=0.18, vel=0.4, reg=(0, 6))
            self.coracao(M["prego_novo"] - 1, M["nao_dela"], 1.5, 0.35)
            self.tremulo(M["prego_novo"], M["ninguem_viu"], "D4", 0.05, 0.55, "vla_trem")
            self.silencio(M["nao_dela"] - 0.3, 0.9, 0.2)
            self.golpe(M["ninguem_viu"] + 1.6, 0.8)
            j.gliss(M["ninguem_viu"] + 2.2, 0.5)

        if "fecho" in S:
            a, b = S["fecho"]    # o fecho: a flauta sozinha, longe; o tema incompleto; o sino de templo no "boa noite"
            self.chao(a, b, vel=0.22)
            self.flauta(a + 2, [("D5", 4.0), ("A4", 3.0), ("Bb4", 2.5), ("A4", 5.0)], 0.38, pan=0.3)
            self.tema(a + 18, 0.5, ate=6, ritmo=1.4)
            j.bonsho(b - 3.0, 0.65)

        # 24/11 (revisão do rascunho 1): nas FICHAS a narração para por 7–10 s e ficava quase silêncio. A música segura
        # a leitura: um trêmulo baixo de violas, o koto tocando sozinho e um rin na entrada (nunca silêncio)
        for f0, f1 in self.p.get("fichas", []):
            j.rin(f0 + 0.3, 0.55, 1)
            self.tremulo(f0, f1 + 1.0, "D4", 0.3, 0.5, "vla_trem")
            self.j.cresc("vc", "D3", f0, f1 - f0 + 1.0, 0.25, 0.35)
            self.koto_solto(f0 + 0.6, f1 + 1.5, dens=0.9, vel=0.8, reg=(3, 10))
        return self

    def salvar(self, saida):
        wav = Path(saida).with_suffix(".wav")
        self.j.salvar(str(wav), rev=0.34, corte=self.fim, silencios=self.sil)
        # nos cartões a música desce 10 dB (o cartão tem o taiko e a tinta dele)
        vol = "".join(f"volume=enable='between(t,{c0:.2f},{c1:.2f})':volume=0.32," for c0, c1 in self.p["cartoes"])
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(wav), "-af",
                        f"{vol}lowshelf=f=140:g=-4,equalizer=f=2500:t=q:w=1.2:g=-2.5,loudnorm=I=-20:TP=-2:LRA=11", "-ar", "44100", "-b:a", "224k", str(saida)], check=True)
        wav.unlink()


def previa():
    """~2:40 com os momentos principais em sequência (para ouvir sem o vídeo)."""
    m = {k: 0.0 for k in ("maldicao", "atenderam", "correndo", "nao_mulher", "hashihime", "kimon", "cortaram", "mordeu",
                          "kubizuka", "raio", "tenjin", "dormiu", "pesar", "cranios", "rachou", "saido", "desfile",
                          "morria", "morosuke", "reza", "bebado", "tres_chamas", "metal", "a_dela", "setima", "lanterna",
                          "rosto", "seis_anos", "sumiu", "prego_novo", "nao_dela", "ninguem_viu")}
    m.update(maldicao=14, atenderam=22)
    secoes = [["gancho", 0, 34], ["vigia", 34, 60], ["tema", 60, 61]]
    m.update(desfile=63, morria=82, morosuke=86, reza=104, bebado=108)
    secoes += [["p7", 61, 130]]
    m.update(tres_chamas=138, metal=142, a_dela=150, setima=156, lanterna=170, rosto=178, seis_anos=180, sumiu=186,
             prego_novo=190, nao_dela=196, ninguem_viu=200)
    secoes += [["hist", 130, 208]]
    plano = {"secoes": secoes, "marcos": m, "fim": 210, "cartoes": []}
    Trilha(plano).compor().salvar(AQUI / "previa.mp3")


if __name__ == "__main__":
    if "--previa" in sys.argv:
        previa()
    else:
        T = Trilha(json.load(open(sys.argv[1]))).compor(); T.salvar(sys.argv[2])
        print("ok", sys.argv[2])
