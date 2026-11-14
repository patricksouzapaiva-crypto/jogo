"""Ep. 09 v3 — troca (o da v2 está em trocar_vozes_v2_bia.py), na narração do Vigia, as falas de personagem marcadas com 🎙 no ROTEIRO (Bia = Leda, mãe = Sulafat;
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
# v3 (14/11): cada fala com o filtro do LUGAR onde ela acontece (fala → tomada, filtro, ganho)
LONGE_MATA = ("highpass=f=200,lowpass=f=3000,aecho=0.8:0.7:180|320:0.3|0.18,volume=0.9")      # da mata, de longe
PERTO = "highpass=f=90,lowpass=f=7000,acompressor=threshold=-28dB:ratio=3"                    # sussurro colado na orelha
QUARTO = "highpass=f=150,lowpass=f=4200,aecho=0.8:0.5:40|75:0.25|0.15"                        # do quarto, atrás dele
PORTA = "highpass=f=250,lowpass=f=1800,aecho=0.8:0.5:30:0.2"                                  # atrás da porta 402
CORREDOR = "highpass=f=220,lowpass=f=3200,aecho=0.8:0.75:220|420:0.35|0.22"                   # do fim do corredor
ELEVADOR = "highpass=f=120,lowpass=f=6000,aecho=0.8:0.4:18|33:0.2|0.12"                        # dentro da caixa de metal
ESCOLHA = {
    2: ("rafa1_Umbriel", CEL, 0.85),          # o áudio no grupo (celular)
    19: ("livia1_Despina", LONGE_MATA, 0.7),
    23: ("livia1_Despina", LONGE_MATA, 0.7),  # "a mesma frase. Igualzinha. Com a mesma risada": a MESMA gravação
    43: ("mae1_Sulafat", CEL, 0.9),
    77: ("pai1_Orus", CEL, 0.9),
    86: ("livia2_Despina", QUARTO, 0.75),
    122: ("rafa1_Umbriel", ELEVADOR, 0.85),   # o áudio do gancho, agora ouvido de dentro do elevador
    130: ("falsa1_Despina", PERTO, 0.7),
    132: ("falsa2_Despina", PERTO, 0.7),
    142: ("livia3_Despina", PORTA, 0.65),
    146: ("livia4_Despina", PERTO, 0.6),
    151: ("rafa_falso1_Umbriel", CORREDOR, 0.65),
    155: ("rafa2_Umbriel", CEL, 0.9),
    # 157 (mãe, "Que Lívia, filho?…"): a cota do Gemini acabou antes dela — por enquanto fica a leitura do Vigia
    161: ("falsa3_Despina", CEL, 0.85),       # pela chamada de vídeo
}
FIM = {}


def ler(arq, filtro="anull"):
    return np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", str(arq), "-af", filtro, "-ac", "1", "-ar", str(SR),
                                         "-f", "f32le", "-"], capture_output=True, check=True).stdout, np.float32).copy()


def rms(x):
    x = x[np.abs(x) > 0.003]
    return float(np.sqrt((x ** 2).mean())) if len(x) else 1e-6


fl, pers, _, _, _ = F.ler(); fl = fl + [F.VINHETA]
TROCAS = {i: k for i, k in pers.items() if i in ESCOLHA}

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
    nome, filtro, ganho = ESCOLHA[i]
    t0 = tempos[ini[i]][0] - 0.06
    t1 = FIM.get(i, tempos[ini[i + 1]][0] - 0.10)         # começo da fala seguinte
    fim_ant = min(tempos[ini[i + 1] - 1][1], t1)
    x0, x1 = int(t0 * SR), int(t1 * SR)
    nova = ler(AQUI / "vozes" / "limpas_escolhidas" / f"{nome}.wav", LIMPA + "," + filtro)
    nova *= rms(voz[x0:int(fim_ant * SR)]) / rms(nova) * ganho     # mesmo volume da fala que sai
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
