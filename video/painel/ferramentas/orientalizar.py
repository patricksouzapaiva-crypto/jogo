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
    """v3 (15/11): a v2 ficou "bagunçada — um aglomerado de tudo sem parar, com áudio estourando". Agora o EQUILÍBRIO:
    a música continua na frente; por baixo, um leito oriental CONSTANTE e suave (o loop de ambiente, que já tem tambor
    lento, janggu, cordas e flauta longe); por cima, poucos detalhes espaçados e baixos (um gongo longo a cada ~20 s,
    uma flauta distante duas vezes). Sem piri/haegeum/sinawi gritando, sem transe, sem rangido. Ganhos com folga e
    limitador suave: nada passa de -3 dBFS antes do limitador."""
    mus = ler_arq(arq); dur = len(mus) / SR; ref = nivel(mus)
    cam = np.zeros_like(mus)
    # 1) o leito: o loop de ambiente oriental, emendado sem costura, entrando e saindo devagar
    loop = ler("ep09_loop_terror_asiatico", "lowpass=f=6000")
    leito = np.zeros_like(mus); pos = 0
    while pos < len(leito):
        n = min(len(loop), len(leito) - pos); leito[pos:pos + n] = loop[:n]; pos += n
    f = int(4 * SR); leito[:f] *= np.linspace(0, 1, f)[:, None]; leito[-f:] *= np.linspace(1, 0, f)[:, None]
    colocar(cam, leito, 0, -4, ref)
    # 2) poucos detalhes, longe e macios: gongo jing longo a cada ~20 s (abafado), flauta daegeum distante 2×
    macio = "lowpass=f=3000,acompressor=threshold=-26dB:ratio=3:attack=40:release=500"
    for k, t in enumerate(np.arange(6, dur - 8, 20.0)):
        colocar(cam, ler(f"ep09_gut_jing_{k % 2 + 1}", "afade=t=in:d=0.08,afade=t=out:st=4:d=3," + macio), t, -13, ref)
    longe = "afade=t=in:d=2,afade=t=out:st=6:d=3,highpass=f=300,lowpass=f=4000,aecho=0.8:0.6:180|340:0.25|0.12"
    # flauta "de vez em quando" (pedido 15/11): a cada ~28 s, alternando as duas tomadas, longe, nunca junto do gongo
    for k, t in enumerate(np.arange(14, dur - 10, 28.0)):
        colocar(cam, ler(f"ep09_amb_daegeum_longe_{k % 2 + 1}", longe), t, -8, ref)
    # 3) cola: compressão leve no conjunto para não ter picos, e a música só 1,5 dB mais baixa (continua sendo a faixa)
    out = mus * 10 ** (-1.5 / 20) + cam
    pico = np.abs(out).max(); out *= min(1.0, 10 ** (-3 / 20) / pico)
    print(f"música {ref:.1f} dB · camada oriental {nivel(cam):.1f} dB · pico antes do limitador {20*np.log10(np.abs(out).max()):.1f} dBFS")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-af",
                    "acompressor=threshold=-20dB:ratio=2:attack=20:release=300,loudnorm=I=-18:TP=-2:LRA=9,"
                    "alimiter=limit=0.79", "-b:a", "192k", str(saida)],
                   input=out.astype(np.float32).tobytes(), check=True)
    print("ok", saida)


if __name__ == "__main__":
    orientalizar(sys.argv[1], sys.argv[2])
