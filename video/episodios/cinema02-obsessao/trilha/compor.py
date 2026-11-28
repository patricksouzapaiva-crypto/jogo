"""Trilha de "O QUE É A CRIATURA? #2 — Obsessão" (27/11), orquestra com gravações reais (painel/ferramentas/orquestra.py).
Mesmo esqueleto do #1 (cinema01/trilha/compor.py, importado daqui):
- TEMA DO FORMATO (fixo): o relógio da investigação (pizzicato + piano grave + trêmulos) nas pistas, no julgamento e
  nas provas; o veredito cai no sinete.
- MOTIVO DO EPISÓDIO, NOVO: "o nó" — uma valsa lenta em lá menor que sobe e é puxada de volta pela mesma nota (sol#→lá),
  como um fio que aperta. Na caixinha (o salgueiro vem numa caixinha de loja), no piano desafinado, em cânone consigo
  mesma na amarração (duas vozes presas uma à outra), em lamento no violino (o dybbuk e Mary Blandy), nos metais graves
  no "por que é o pior", e no fim a caixinha perde a corda.
Bordão grave contínuo do começo ao fim: nunca há silêncio.
Uso: python3 compor.py episodio plano.json saida.mp3   |   python3 compor.py → previa_trilha.mp3"""
import importlib.util, json, subprocess, sys
from pathlib import Path
import numpy as np

AQUI = Path(__file__).parent
_spec = importlib.util.spec_from_file_location("c1", AQUI.parents[1] / "cinema01-outra-mamae" / "trilha" / "compor.py")
c1 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(c1)

# "o nó": 4 frases de 4 compassos (3/4). Cada frase sobe e volta para o lá pelo sol# (o fio puxa de volta).
c1.NINAR = [("A4", 2), ("B4", 1), ("C5", 2), ("E5", 1), ("D5", 1), ("C5", 1), ("B4", 1), ("G#4", 2), ("A4", 1),
            ("A4", 2), ("C5", 1), ("E5", 2), ("A5", 1), ("G#5", 1), ("F5", 1), ("E5", 1), ("D5", 1), ("B4", 1), ("C5", 1),
            ("F5", 2), ("E5", 1), ("D5", 2), ("C5", 1), ("B4", 1), ("C5", 1), ("D5", 1), ("E5", 3),
            ("A5", 1), ("G#5", 1), ("F5", 1), ("E5", 1), ("D5", 1), ("C5", 1), ("B4", 1), ("G#4", 1), ("B4", 1), ("A4", 3)]
c1.ACORDES = ["A2", "E2", "A2", "E2", "A2", "A2", "D2", "E2", "D2", "F2", "D2", "E2", "F2", "D2", "E2", "A2"]
c1.Q = 0.62
encher, caixinha, piano_errado, relogio = c1.encher, c1.caixinha, c1.piano_errado, c1.relogio
lamento, veredito, duplo, demonio, tulpa, tensao = c1.lamento, c1.veredito, c1.duplo, c1.demonio, c1.tulpa, c1.tensao
Orquestra = c1.Orquestra


def episodio(plano, saida):
    fim = plano["fim"]; o = Orquestra(fim + 10)
    t = 0.0
    while t < fim:                                # o bordão (lá grave), em ondas de 18 s que se cruzam
        o.cresc("cb", "A2", t, 20, 0.16, 0.2); o.cresc("vc", "E3", t + 9, 20, 0.06, 0.1, pan=0.3); t += 18
    for nome, a, b in plano["secoes"]:
        if nome == "gancho": encher(o, tensao, a, b, d=min(30.0, max(12.0, b - a - 6)), vel=0.6)
        elif nome == "apresenta": caixinha(o, a + 0.5, 0.7, ate=18)
        elif nome in ("pistas", "julgamento", "porque"): encher(o, relogio, a, b, compassos=16, vel=0.5, sobe=False)
        elif nome == "genio": demonio(o, a, 0.7, d=b - a)
        elif nome == "amarracao": encher(o, duplo, a, b, vel=0.8)
        elif nome in ("dybbuk", "blandy"): encher(o, lamento, a, b, vel=0.5)
        elif nome == "pata": encher(o, tulpa, a, b, vel=0.8)
        elif nome == "erotomania": encher(o, piano_errado, a, b, vel=0.5)
        elif nome == "spoiler": encher(o, tensao, a, b, d=34.0, vel=0.7)
        elif nome == "decisao": encher(o, relogio, a, b, compassos=12, vel=0.6, sobe=True)
        elif nome == "veredito": encher(o, caixinha, a + 9, b, vel=0.55)   # o sinete (veredito) cai antes
        elif nome == "pior": demonio(o, a, 0.75, d=b - a)
        elif nome == "louvre": encher(o, duplo, a, b, vel=0.6); o.cresc("vc_trem", "A2", a, b - a, 0.05, 0.25)
        elif nome == "salgueiro": encher(o, caixinha, a, b, vel=0.6)
        elif nome == "fecho": caixinha(o, max(a, b - 26), 0.7, cansa=True); piano_errado(o, a, 0.45, ate=12)
    for g in plano.get("golpes", []):
        o.golpe("timp", g, 0.7, int(g))
    if plano.get("veredito"):
        veredito(o, plano["veredito"] - 2.4)
    wav = Path(saida).with_suffix(".wav"); o.salvar(wav, rev=0.34, corte=fim)
    import soundfile as sf
    y, sr = sf.read(wav); env = np.ones(len(y))
    for a, b in plano.get("furos", []):            # fala do filme: a música desce 9 dB (nunca some)
        i, j, r = int(a * sr), int(b * sr), int(1.2 * sr)   # 28/11: desce e volta devagar (era 0,35 s)
        env[i:j] = np.minimum(env[i:j], 0.35)
        env[max(0, i - r):i] = np.minimum(env[max(0, i - r):i], np.linspace(1, 0.35, i - max(0, i - r)))
        env[j:j + r] = np.minimum(env[j:j + r], np.linspace(0.35, 1, len(env[j:j + r])))
    sf.write(wav, y * env[:, None], sr)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(wav), "-af", f"afade=t=out:st={fim - 4:.2f}:d=4", "-b:a", "192k",
                    str(saida)], check=True); wav.unlink()
    print("ok", saida, f"{fim:.1f}s")


if __name__ == "__main__" and len(sys.argv) > 2 and sys.argv[1] == "episodio":
    episodio(json.load(open(sys.argv[2])), sys.argv[3]); sys.exit()

if __name__ == "__main__":
    o = Orquestra(130); t = 0.5
    o.cresc("cb", "A2", 0, 125, 0.15, 0.3)
    t = caixinha(o, t, 1.0) + 0.6          # o nó na caixinha
    t = duplo(o, t, 0.9) + 0.6              # amarrado a si mesmo
    t = lamento(o, t, 0.6) + 0.5
    t = veredito(o, t) + 3.0
    wav = AQUI / "previa_trilha.wav"; o.salvar(wav, rev=0.34, corte=t)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(wav), "-af", "afade=t=out:st=%.2f:d=2.5" % (t - 2.6), "-b:a", "192k",
                    str(AQUI / "previa_trilha.mp3")], check=True); wav.unlink()
    print("ok", AQUI / "previa_trilha.mp3", f"{t:.1f}s")
