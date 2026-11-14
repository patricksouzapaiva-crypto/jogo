"""Monta um AMBIENTE em loop (sem emenda audível) a partir de trechos curtos (Stable Audio / Sonniss).
15/11 (pedido do usuário): "menos ataques altos, mais ambientado — tambores, cordas e flautas criando o ambiente, não
assustando; que possa rodar em looping". Camadas: pads contínuos (drone + cordas) emendados com fusão em potência
constante; pulsação lenta de tambor; gayageum e flauta esparsos, longe. Ataques amaciados (compressão + limitador,
passa-baixa), e o fim do laço é fundido no começo."""
import subprocess, sys
import numpy as np
from pathlib import Path

SONS = Path(__file__).resolve().parents[1] / "sons"
SR = 48000


def ler(nome, filtro="anull"):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(SONS / f"{nome}.mp3"), "-af", filtro, "-ac", "2", "-ar", str(SR),
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()


def db(x, g):
    return x * 10 ** (g / 20)


def corrente(nomes, total, fusao, filtro="anull"):
    """Emenda trechos um depois do outro com fusão em potência constante até cobrir `total` s."""
    pcs = [ler(n, filtro) for n in nomes]
    out = np.zeros((int(total * SR), 2), np.float32); pos, k, f = 0, 0, int(fusao * SR)
    while pos < len(out):
        x = pcs[k % len(pcs)].copy(); k += 1
        x[:f] *= np.sin(np.linspace(0, np.pi / 2, f))[:, None]; x[-f:] *= np.cos(np.linspace(0, np.pi / 2, f))[:, None]
        n = min(len(x), len(out) - pos); out[pos:pos + n] += x[:n]; pos += len(x) - f
    return out


def por(bed, x, t, g):
    a = int(t * SR); n = min(len(x), len(bed) - a)
    if n > 0:
        bed[a:a + n] += db(x[:n], g)


def montar(saida, L=88.0, FUS=5.0, PRE=6.0):
    T = L + FUS + PRE          # PRE: as camadas sustentadas nascem com fade-in — o laço começa depois disso
    mac = "lowpass=f=5200,acompressor=threshold=-28dB:ratio=4:attack=30:release=400"   # tira o "estalo" dos ataques
    # os "pads" do modelo crescem no começo e morrem nos últimos 4–5 s: usa só o miolo estável de cada trecho, achatado
    # por compressão, e emenda com fusões longas (senão o ambiente "respira" em vales de 10–15 dB a cada 8 s)
    chato = ",acompressor=threshold=-34dB:ratio=6:attack=200:release=1500:makeup=6"
    bed = db(corrente(["ep09_amb_drone_montanha_1", "ep09_amb_cordas_suaves_1", "ep09_amb_drone_montanha_2"], T, 2.2,
                      "atrim=1.2:6.4,asetpts=PTS-STARTPTS,lowpass=f=3500" + chato), -6)
    bed += db(corrente(["ep09_amb_cordas_suaves_2", "ep09_amb_drone_montanha_1", "ep09_amb_cordas_suaves_1"], T, 2.2,
                       "atrim=1.4:7.0,asetpts=PTS-STARTPTS,lowpass=f=4500" + chato), -9)
    bed += db(corrente(["ep09_amb_tambor_lento_1", "ep09_amb_tambor_lento_2"], T, 1.5, "lowpass=f=1800," + mac), -11)
    jan = corrente(["ep09_amb_janggu_suave_1", "ep09_amb_janggu_suave_2"], 40, 1.5, "lowpass=f=2500," + mac)
    jan[: 4 * SR] *= np.linspace(0, 1, 4 * SR)[:, None]; jan[-6 * SR:] *= np.linspace(1, 0, 6 * SR)[:, None]
    por(bed, jan, 26 + PRE, -15)                                              # o janggu entra e sai devagar no meio
    eco = "aecho=0.8:0.6:180|340:0.3|0.18," + mac
    for t, v in ((5, 1), (33, 2), (61, 1)):
        por(bed, ler(f"ep09_amb_gayageum_suave_{v}", eco), t + PRE, -9)
    for t, v in ((17, 1), (47, 2), (73, 1)):
        por(bed, ler(f"ep09_amb_daegeum_longe_{v}", "lowpass=f=6000," + eco), t + PRE, -10)
    bed = bed[int(PRE * SR):]
    n, f = int(L * SR), int(FUS * SR)
    out = bed[:n].copy(); w = np.sin(np.linspace(0, np.pi / 2, f))[:, None]
    out[:f] = out[:f] * w + bed[n:n + f] * np.cos(np.linspace(0, np.pi / 2, f))[:, None]   # o fim vira o começo
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-af",
                    "acompressor=threshold=-24dB:ratio=3:attack=50:release=600,alimiter=limit=0.7,loudnorm=I=-20:TP=-3:LRA=6",
                    "-b:a", "192k", str(saida)], input=np.clip(out, -1, 1).astype(np.float32).tobytes(), check=True)
    print("ok", saida)


if __name__ == "__main__":
    montar(sys.argv[1] if len(sys.argv) > 1 else str(SONS / "ep09_loop_terror_asiatico.mp3"))
