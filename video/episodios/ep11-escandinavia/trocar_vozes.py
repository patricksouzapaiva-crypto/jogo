"""Ep. 11 — troca, na narração do Vigia, as falas do Lucas marcadas com 🎙 no ROTEIRO pelos áudios dele
(Lucas = Achird, escolhido pelo usuário 16/11; tomadas em vozes/limpas_escolhidas/f<id>.wav, de
vozes/gerar_vozes.py). Todas são áudio de celular: filtro CEL. A fala nova nunca é acelerada: se for mais longa, a pausa
seguinte encolhe o mesmo tanto (audio/ajuste_pausas.json). Saída: audio/voz_personagens.wav. Precisa de audio/alinhamento.json."""
import json, subprocess, sys
import numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "painel"))
from gerar import tokens  # noqa: E402
import falas as F

AQUI = Path(__file__).parent
SR = 48000
CEL = "highpass=f=300,lowpass=f=3600,acompressor=threshold=-24dB:ratio=4:attack=5:release=80"
ESCOLHA = {
    62: ("f62", CEL, 0.9),            # áudio do quarto de madeira, aliviado e com frio
    72: ("f72", CEL, 0.85),           # vídeo escondido atrás do celeiro, sussurrando
}
FIM = {}


def ler(arq, filtro="anull"):
    return np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", str(arq), "-af", filtro, "-ac", "1", "-ar", str(SR),
                                         "-f", "f32le", "-"], capture_output=True, check=True).stdout, np.float32).copy()


def rms(x):
    x = x[np.abs(x) > 0.003]
    return float(np.sqrt((x ** 2).mean())) if len(x) else 1e-6


fl, pers, _, _, _ = F.ler(); fl = fl + [F.VINHETA]
TROCAS = {i: pers.get(i, "narracao") for i in ESCOLHA}

tempos = json.load(open(AQUI / "audio" / "alinhamento.json"))
voz = ler(AQUI / "audio" / "voz_com_vinheta_limpa.wav")
ini, k = [], 0
for f in fl:
    ini.append(k); k += len(tokens(f))
LIMPA = ("highpass=f=70,"   # sem afftdn: o sussurro é quase só ar e o redutor de ruído come a voz
         
         "silenceremove=start_periods=1:start_threshold=-42dB:start_silence=0.03,"
         "areverse,silenceremove=start_periods=1:start_threshold=-42dB:start_silence=0.08,areverse")


def inicio_real(t0, tp):
    """Onde a fala do personagem começa a substituir a narração. 15/11 (rascunho 2: "o Vigia fala algo, corta e a mãe
    fala por cima" / "o Vigia fala O e corta pra ela"): o alinhamento às vezes marca o começo da fala DEPOIS de onde o
    Vigia começa a dizer. Aqui o corte vai para o MEIO do maior silêncio real entre o fim da frase anterior e o começo
    desta (janela de 10 ms, abaixo de -45 dB) — o que vem antes do silêncio é a frase anterior; o que vem depois é a fala
    que sai inteira."""
    ini, fim = max(tp - 0.6, t0 - 1.2), t0 + 0.15
    passo = int(0.01 * SR)
    x = voz[int(ini * SR):int(fim * SR)]
    n = len(x) // passo
    if n < 5:
        return t0 - 0.05
    e = 20 * np.log10(np.sqrt((x[: n * passo].reshape(n, passo) ** 2).mean(1)) + 1e-9)
    quieto = e < -45
    melhor, atual, ini_atual, ini_melhor = 0, 0, 0, 0
    for k, q in enumerate(quieto):
        if q:
            if atual == 0:
                ini_atual = k
            atual += 1
            if atual > melhor:
                melhor, ini_melhor = atual, ini_atual
        else:
            atual = 0
    if melhor < 6:                       # menos de 60 ms de silêncio: fica no alinhamento
        return t0 - 0.05
    return ini + (ini_melhor + melhor / 2) * 0.01


pedacos, cursor, ajuste, lugar = [], 0, {}, []
for i, chave in sorted(TROCAS.items()):
    nome, filtro, ganho, *resto = ESCOLHA[i]
    pan = resto[0] if resto else 0.0
    t0 = inicio_real(tempos[ini[i]][0], tempos[ini[i] - 1][1])
    t1 = FIM.get(i, tempos[ini[i + 1]][0] - 0.10)         # começo da fala seguinte
    fim_ant = min(tempos[ini[i + 1] - 1][1], t1)
    x0, x1 = max(int(t0 * SR), cursor), int(t1 * SR)   # fala colada na anterior (90 → 91): começa onde a outra acabou
    nova = ler(AQUI / "vozes" / "limpas_escolhidas" / f"{nome}.wav", LIMPA + "," + filtro)
    nova *= rms(voz[x0:int(fim_ant * SR)]) / rms(nova) * ganho     # mesmo volume da fala que sai
    f = int(0.02 * SR)
    nova[:f] *= np.linspace(0, 1, f); nova[-f:] *= np.linspace(1, 0, f)
    # a fala nova NUNCA é acelerada. Se for mais longa que o espaço da antiga, o arquivo cresce — e a pausa
    # que o roteiro põe depois dela diminui o mesmo tanto (ajuste_pausas.json): o tempo do vídeo não muda.
    espaco = x1 - x0
    sobra = len(nova) + int(0.6 * SR) - espaco   # 16/11: respiro claro entre o áudio e a narração seguinte
    extra = max(0, sobra)
    # 16/11 (rascunho 2: "uma pausa grande demais"): fala nova mais CURTA que a antiga não deixa o buraco — o bloco
    # termina 0,6 s depois dela
    bloco = np.zeros(len(nova) + int(0.6 * SR), np.float32); bloco[:len(nova)] = nova
    antes = voz[cursor:x0].copy()
    if len(antes) >= f:
        antes[-f:] *= np.linspace(1, 0, f)
    lugar.append((sum(len(p) for p in pedacos) + len(antes), len(bloco), pan))
    pedacos += [antes, bloco]; cursor = x1
    if extra:
        ajuste[str(i + 1)] = round(-extra / SR, 3)
    print(f"{i:3d} {nome:14s} espaço {espaco / SR:.2f}s  fala nova {len(nova) / SR:.2f}s"
          f"{f'  -> cresce {extra / SR:.2f}s (tira da pausa da fala {i + 1})' if extra else ''}")
resto = voz[cursor:].copy(); resto[:int(0.02 * SR)] *= np.linspace(0, 1, int(0.02 * SR))
voz = np.concatenate(pedacos + [resto])
json.dump(ajuste, open(AQUI / "audio" / "ajuste_pausas.json", "w"))
# 15/11: estéreo — o narrador no centro, cada personagem do lado de onde a voz vem (feito para fone de ouvido)
L, R = voz.copy(), voz.copy()
for a0, n_, pan in lugar:
    if pan:
        L[a0:a0 + n_] *= min(1.0, 1 - pan); R[a0:a0 + n_] *= min(1.0, 1 + pan)
est = np.stack([L, R], 1)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                str(AQUI / "audio" / "voz_personagens.wav")], input=np.clip(est, -1, 1).tobytes(), check=True)
print("duração nova:", round(len(voz) / SR, 2), "s · pausas a compensar:", ajuste)
