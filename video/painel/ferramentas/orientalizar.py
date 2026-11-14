"""Trilha de terror ORIENTAL a partir de uma faixa composta (ElevenLabs).
15/11 — v1 (camada baixa por baixo da música) foi reprovada: "está igual". Pesquisa (The Wailing, Exhuma, sinawi, J-horror):
no terror coreano o CONJUNTO XAMÂNICO é o protagonista — um ciclo rítmico (jangdan, 12/8) que nunca para no janggu/buk, o
gongo jing marcando as voltas, os sininhos bangul, e piri/haegeum improvisando por cima (sinawi, heterofonia), crescendo
até o transe; no japonês, um rangido metálico sustentado avisa o fantasma. Então aqui a faixa original vai para o FUNDO
(-7 dB) e o conjunto vem para a frente, com volumes MEDIDOS em relação à música (não "a gosto").
Uso: python3 orientalizar.py <faixa> <saída.mp3>"""
import subprocess, sys
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from montar_loop import ler, corrente, SR  # noqa: E402


def ler_arq(arq):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(arq), "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()


def nivel(x):
    """dB RMS só das partes que soam (ignora silêncios), para comparar camadas."""
    n = SR // 2; m = len(x) // n
    e = 20 * np.log10(np.sqrt((x[: m * n].mean(1).reshape(m, n) ** 2).mean(1)) + 1e-7)
    return float(np.median(e[e > e.max() - 30]))


def colocar(cam, x, t, alvo_db, ref_db):
    """Põe x em t com o nível `alvo_db` RELATIVO à música (ref_db)."""
    g = 10 ** ((ref_db + alvo_db - nivel(x)) / 20)
    a = int(t * SR); n = min(len(x), len(cam) - a)
    if n > 0:
        cam[a:a + n] += x[:n] * g


def orientalizar(arq, saida):
    mus = ler_arq(arq); dur = len(mus) / SR; ref = nivel(mus)
    cam = np.zeros_like(mus)
    seco = "acompressor=threshold=-22dB:ratio=3:attack=10:release=200"
    eco = "aecho=0.8:0.55:120|260:0.28|0.15," + seco
    # 1) o ciclo do ritual, do começo ao fim: calmo nos primeiros 2/3, transe no último terço
    a = corrente(["ep09_gut_jangdan_1", "ep09_gut_jangdan_2"], dur * 0.7, 1.0, seco)
    b = corrente(["ep09_gut_jangdan_forte_1", "ep09_gut_jangdan_forte_2"], dur * 0.38, 1.0, seco)
    f = int(3 * SR); a[:f] *= np.linspace(0, 1, f)[:, None]; a[-f:] *= np.linspace(1, 0, f)[:, None]
    b[:f] *= np.linspace(0, 1, f)[:, None]; b[-int(5 * SR):] *= np.linspace(1, 0, int(5 * SR))[:, None]
    colocar(cam, a, 0, -3, ref); colocar(cam, b, dur * 0.62, -1, ref)
    # 2) o gongo jing marcando as voltas do ciclo (a cada ~7 s), e os sininhos bangul nas viradas
    for k, t in enumerate(np.arange(0.2, dur - 4, 7.0)):
        colocar(cam, ler(f"ep09_gut_jing_{k % 2 + 1}", "afade=t=out:st=5:d=2"), t, -5, ref)
    for t, v in ((dur * 0.3, 1), (dur * 0.62, 2), (dur * 0.85, 1)):
        colocar(cam, ler(f"ep09_gut_bangul_{v}", seco), t, -7, ref)
    # 3) a voz do ritual: piri e haegeum chorando, e o sinawi (os dois juntos, improvisando) nas partes fortes
    for t, nome, alvo in ((dur * 0.08, "ep09_gut_piri_1", -1), (dur * 0.25, "ep09_gut_haegeum_1", -1),
                          (dur * 0.42, "ep09_gut_sinawi_1", 0), (dur * 0.6, "ep09_gut_piri_2", -1),
                          (dur * 0.74, "ep09_gut_sinawi_2", 1), (dur * 0.88, "ep09_gut_haegeum_2", -2)):
        colocar(cam, ler(nome, "afade=t=in:d=0.3,afade=t=out:st=9:d=2," + eco), t, alvo, ref)
    # 4) o rangido metálico do terror japonês, uma vez só, baixo, quando o ritual vira transe
    colocar(cam, ler("ep09_jh_rangido_1", "afade=t=in:d=2,afade=t=out:st=8:d=3"), dur * 0.6, -9, ref)
    out = mus * 10 ** (-7 / 20) + cam
    print(f"música {ref:.1f} dB · conjunto coreano {nivel(cam):.1f} dB (antes: só a música)")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-af",
                    "alimiter=limit=0.89,loudnorm=I=-16:TP=-1.5:LRA=12", "-b:a", "192k", str(saida)],
                   input=np.clip(out, -1, 1).astype(np.float32).tobytes(), check=True)
    print("ok", saida)


if __name__ == "__main__":
    orientalizar(sys.argv[1], sys.argv[2])
