"""Troca, na narração do Vigia, as DUAS falas do cabo Caio pela voz dele (Gemini TTS, voz Puck, sem instrução de
estilo). A fala nova nunca é acelerada: se for mais longa, a pausa seguinte encolhe o mesmo tanto
(audio/ajuste_pausas.json). Saída: audio/voz_personagens.wav
Uso: python3 trocar_vozes.py [voz]   (precisa de audio/alinhamento.json e audio/personagens/*.wav)"""
import json, subprocess, sys
import numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "painel"))
from gerar import tokens  # noqa: E402

AQUI = Path(__file__).parent
SR = 48000
VOZ = sys.argv[1] if len(sys.argv) > 1 else "Puck"
TROCAS = {45: f"chefe_{VOZ}", 51: f"viram_{VOZ}"}
FIM = {}


def ler(arq, filtro="anull"):
    return np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", str(arq), "-af", filtro, "-ac", "1", "-ar", str(SR),
                                         "-f", "f32le", "-"], capture_output=True, check=True).stdout, np.float32).copy()


def rms(x):
    x = x[np.abs(x) > 0.003]
    return float(np.sqrt((x ** 2).mean())) if len(x) else 1e-6


r = json.load(open(AQUI / "roteiro.json"))
tempos = json.load(open(AQUI / "audio" / "alinhamento.json"))
voz = ler(AQUI / "audio" / "voz_com_vinheta_limpa.wav")
ini, k = [], 0
for b in r["batidas"]:
    ini.append(k); k += len(tokens(b["fala"]))
LIMPA = ("afftdn=nr=18:nf=-50:tn=1,highpass=f=70,"
         "silenceremove=start_periods=1:start_threshold=-42dB:start_silence=0.03,"
         "areverse,silenceremove=start_periods=1:start_threshold=-42dB:start_silence=0.08,areverse")
pedacos, cursor, ajuste = [], 0, {}
for i, nome in sorted(TROCAS.items()):
    t0 = tempos[ini[i]][0] - 0.06
    t1 = FIM.get(i, tempos[ini[i + 1]][0] - 0.10)         # começo da fala seguinte
    fim_ant = min(tempos[ini[i + 1] - 1][1], t1)
    x0, x1 = int(t0 * SR), int(t1 * SR)
    nova = ler(AQUI / "audio" / "personagens" / f"{nome}.wav", LIMPA)
    nova *= rms(voz[x0:int(fim_ant * SR)]) / rms(nova)     # mesmo volume da fala que sai
    f = int(0.02 * SR)
    nova[:f] *= np.linspace(0, 1, f); nova[-f:] *= np.linspace(1, 0, f)
    # a fala nova NUNCA é acelerada. Se for mais longa que o espaço da antiga, o arquivo cresce — e a pausa
    # que o roteiro põe depois dela diminui o mesmo tanto (ajuste_pausas.json): o tempo do vídeo não muda.
    espaco = x1 - x0
    sobra = len(nova) + int(0.25 * SR) - espaco
    extra = max(0, sobra)
    bloco = np.zeros(espaco + extra, np.float32); bloco[:len(nova)] = nova
    antes = voz[cursor:x0].copy(); antes[-f:] *= np.linspace(1, 0, f)
    pedacos += [antes, bloco]; cursor = x1
    if extra:
        ajuste[str(i + 1)] = round(-extra / SR, 3)
    print(f"{i:3d} {nome:14s} espaço {espaco / SR:.2f}s  fala nova {len(nova) / SR:.2f}s"
          f"{f'  -> cresce {extra / SR:.2f}s (tira da pausa da fala {i + 1})' if extra else ''}")
resto = voz[cursor:].copy(); resto[:int(0.02 * SR)] *= np.linspace(0, 1, int(0.02 * SR))
voz = np.concatenate(pedacos + [resto])
json.dump(ajuste, open(AQUI / "audio" / "ajuste_pausas.json", "w"))
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                str(AQUI / "audio" / "voz_personagens.wav")], input=np.clip(voz, -1, 1).tobytes(), check=True)
print("duração nova:", round(len(voz) / SR, 2), "s · pausas a compensar:", ajuste)
