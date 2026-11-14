"""Ep. 09 — troca, na narração do Vigia, as falas de personagem marcadas com 🎙 no ROTEIRO (Bia = Leda, mãe = Sulafat;
"voz" = a voz falsa da mãe no corredor, Sulafat sussurrada, ouvida de dentro do áudio da Bia; tomadas em
vozes/limpas_escolhidas/). A voz ganha o filtro do lugar (celular). O som do lugar entra na montagem.
A fala nova nunca é acelerada: se for mais longa, a pausa seguinte encolhe o mesmo tanto (audio/ajuste_pausas.json).
Saída: audio/voz_personagens.wav. Precisa de audio/alinhamento.json."""
import json, subprocess, sys
import numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "painel"))
from gerar import tokens  # noqa: E402
import falas as F

AQUI = Path(__file__).parent
SR = 48000
CEL = "highpass=f=300,lowpass=f=3600,acompressor=threshold=-24dB:ratio=4:attack=5:release=80"
ESCOLHA = {"bia": {30: "bia1_Leda", 87: "bia2_Leda", 107: "bia3_Leda"},
           "mae": {6: "mae2_Sulafat", 91: "mae1_Sulafat"}, "voz": {111: "voz1_Sulafat"}}
# todas chegam pelo celular (áudio no grupo ou ligação); a voz do corredor é a mais abafada (atrás da porta, gravada
# pelo celular da Bia) e com eco de corredor
FILTRO = {"bia": CEL, "mae": CEL,
          "voz": "highpass=f=380,lowpass=f=2400,aecho=0.8:0.6:70|140:0.35|0.2,acompressor=threshold=-26dB:ratio=4,"
                 "vibrato=f=0.7:d=0.06"}
GANHO = {"bia": 0.85, "mae": 0.9, "voz": 0.7}
FIM = {}


def ler(arq, filtro="anull"):
    return np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", str(arq), "-af", filtro, "-ac", "1", "-ar", str(SR),
                                         "-f", "f32le", "-"], capture_output=True, check=True).stdout, np.float32).copy()


def rms(x):
    x = x[np.abs(x) > 0.003]
    return float(np.sqrt((x ** 2).mean())) if len(x) else 1e-6


fl, pers, _, _, _ = F.ler(); fl = fl + [F.VINHETA]
TROCAS = {i: k for i, k in pers.items()}

tempos = json.load(open(AQUI / "audio" / "alinhamento.json"))
voz = ler(AQUI / "audio" / "voz_com_vinheta_limpa.wav")
ini, k = [], 0
for f in fl:
    ini.append(k); k += len(tokens(f))
LIMPA = ("highpass=f=70,"   # sem afftdn: o sussurro é quase só ar e o redutor de ruído come a voz
         
         "silenceremove=start_periods=1:start_threshold=-42dB:start_silence=0.03,"
         "areverse,silenceremove=start_periods=1:start_threshold=-42dB:start_silence=0.08,areverse")
pedacos, cursor, ajuste = [], 0, {}
for i, chave in sorted(TROCAS.items()):
    nome = ESCOLHA[chave][i]
    t0 = tempos[ini[i]][0] - 0.06
    t1 = FIM.get(i, tempos[ini[i + 1]][0] - 0.10)         # começo da fala seguinte
    fim_ant = min(tempos[ini[i + 1] - 1][1], t1)
    x0, x1 = int(t0 * SR), int(t1 * SR)
    nova = ler(AQUI / "vozes" / "limpas_escolhidas" / f"{nome}.wav", LIMPA + "," + FILTRO[chave])
    nova *= rms(voz[x0:int(fim_ant * SR)]) / rms(nova) * GANHO[chave]     # mesmo volume da fala que sai
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
