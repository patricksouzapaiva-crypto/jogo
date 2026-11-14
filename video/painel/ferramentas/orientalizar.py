"""Dá "cara oriental" a uma faixa já composta (ElevenLabs): acrescenta, POR BAIXO da música, a pulsação do buk, o janggu,
frases de daegeum e dedilhados de gayageum (trechos do Stable Audio, ataques amaciados), sem mexer na faixa original.
15/11 (pedido do usuário): "pegar o último fundo do ElevenLabs e colocar tambores, flautas, cara mais oriental".
Uso: python3 orientalizar.py <faixa.mp3|wav> <saída.mp3>"""
import subprocess, sys
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from montar_loop import ler, corrente, por, db, SR  # noqa: E402

MAC = "lowpass=f=5000,acompressor=threshold=-28dB:ratio=4:attack=30:release=400"
ECO = "aecho=0.8:0.6:180|340:0.3|0.18," + MAC


def ler_arq(arq):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(arq), "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()


def env(x, jan=0.5):
    n = int(jan * SR); m = len(x) // n
    return 20 * np.log10(np.sqrt((x[: m * n].mean(1).reshape(m, n) ** 2).mean(1)) + 1e-7)


def orientalizar(arq, saida):
    mus = ler_arq(arq); dur = len(mus) / SR
    e = env(mus)
    vivo = np.where(e > e.max() - 22)[0]                       # onde a música está tocando de fato (sem o fade final)
    t0, t1 = vivo[0] * 0.5, min(dur, (vivo[-1] + 1) * 0.5)
    cam = np.zeros_like(mus)
    tam = corrente(["ep09_amb_tambor_lento_2", "ep09_amb_tambor_lento_1"], t1 - t0, 1.5, "lowpass=f=1800," + MAC)
    f_in, f_out = int(4 * SR), int(6 * SR)
    tam[:f_in] *= np.linspace(0, 1, f_in)[:, None]; tam[-f_out:] *= np.linspace(1, 0, f_out)[:, None]
    por(cam, tam, t0, -13)
    meio = (t1 - t0) / 2 + t0
    jan = corrente(["ep09_amb_janggu_suave_1", "ep09_amb_janggu_suave_2"], min(30, (t1 - t0) * 0.45), 1.5, "lowpass=f=2500," + MAC)
    jan[:f_in] *= np.linspace(0, 1, f_in)[:, None]; jan[-f_out:] *= np.linspace(1, 0, f_out)[:, None]
    por(cam, jan, meio - len(jan) / SR / 2, -17)
    passo = (t1 - t0) / 4
    for k in range(4):                                        # flauta e gayageum se revezando, longe
        t = t0 + 3 + k * passo
        if k % 2 == 0:
            por(cam, ler(f"ep09_amb_daegeum_longe_{k // 2 + 1}", "lowpass=f=6000," + ECO), t, -12)
        else:
            por(cam, ler(f"ep09_amb_gayageum_suave_{(k // 2) % 2 + 1}", ECO), t, -11)
    por(cam, ler("ep09_ah_buk_jing_1", "lowpass=f=2500,afade=t=in:d=0.4," + MAC), max(0, t0 - 0.3), -20)   # o gongo de entrada
    # a camada se abaixa onde a música cresce (não disputa), e sobe um pouco onde a música respira
    em = np.repeat(env(mus, 0.5), int(0.5 * SR))[:, None]
    em = np.pad(em, ((0, max(0, len(cam) - len(em))), (0, 0)), constant_values=em[-1, 0])[: len(cam)]
    g = np.clip(1.0 - (em - np.median(em)) / 18.0, 0.45, 1.25)
    out = mus + cam * g
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-af",
                    "alimiter=limit=0.89,loudnorm=I=-18:TP=-2:LRA=14", "-b:a", "192k", str(saida)],
                   input=np.clip(out, -1, 1).astype(np.float32).tobytes(), check=True)
    print("ok", saida, f"(música {t0:.0f}–{t1:.0f} s)")


if __name__ == "__main__":
    orientalizar(sys.argv[1], sys.argv[2])
