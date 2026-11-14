"""Narração em inglês do Ep. 03: o Vigia (Gemini Algenib) em blocos + a mensagem de voz do Rafael (outra voz,
sussurrada; o efeito de telefone é aplicado no render via "voz_fx"). Gera en/voz_completa_en.wav."""
import subprocess, sys
from pathlib import Path
import numpy as np
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[2] / "painel"))
sys.path.insert(0, str(AQUI))
from gerar import narrar, CACHE  # noqa: E402
from traducao_en import EN  # noqa: E402

# REGRA: o inglês NÃO usa o modelo principal (gemini-3.8, cota do português); usa o 3.1 em streaming
VIGIA_MODELO, VIGIA_VOZ = "gemini-3.1-flash-tts-preview", "Algenib"
RAFAEL = {"modelo": "gemini-2.5-flash-preview-tts", "nome": "Puck",
          "estilo": "Whisper urgently and fearfully, out of breath, like a frightened man leaving a voice message "
                    "at 3 AM, trying not to be heard"}
SR = 48000
RAFAEL_IDX = {0, 1, 2, 96}


def ler(w):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(w), "-af",
                          "silenceremove=start_periods=1:start_threshold=-55dB:start_silence=0.12,areverse,"
                          "silenceremove=start_periods=1:start_threshold=-55dB:start_silence=0.25,areverse",
                          "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


def sil(s):
    return np.zeros(int(s * SR), np.float32)


def blocos(idx, maxc=1400):
    out, atual = [], []
    for i in idx:
        if atual and sum(len(EN[j][0]) for j in atual) + len(EN[i][0]) > maxc:
            out.append(atual); atual = []
        atual.append(i)
    return out + ([atual] if atual else [])


partes = []
# 1) mensagem do Rafael (0–2): cada frase separada, com respiros
raf = {i: ler(narrar(EN[i][0].strip('"'), RAFAEL, CACHE)) for i in (0, 1, 2)}
for i in (0, 1, 2):
    partes += [raf[i], sil(1.1)]
partes.append(sil(0.6))
# 2) Vigia até a batida 95, depois a mensagem repetida (96 = 1 + 2), depois o resto
import hashlib
def vigia(texto):
    w = CACHE / ("en_" + hashlib.sha1(f"{VIGIA_MODELO}|{VIGIA_VOZ}|{texto}".encode()).hexdigest()[:16] + ".wav")
    if not w.exists():
        t = CACHE / "en_bloco.txt"; t.write_text(texto, encoding="utf-8")
        subprocess.run([sys.executable, str(AQUI / "tts_stream.py"), VIGIA_MODELO, VIGIA_VOZ, str(t), str(w)], check=True)
    return ler(w)

BLOCOS = {3: [list(range(3, 19))] + blocos(list(range(19, 96)), 2000), 97: blocos(list(range(97, 133)), 2000)}
for ini in (3, 97):
    for bl in BLOCOS[ini]:
        partes += [vigia("\n".join(EN[i][0] for i in bl)), sil(0.75)]
    if ini == 3:
        partes += [sil(0.4), raf[1], sil(0.6), raf[2], sil(1.2)]
voz = np.concatenate(partes)
dest = AQUI / "voz_completa_en.wav"
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                "-af", "afftdn=nr=12:nf=-50:tn=1,highpass=f=70", str(dest)], input=voz.tobytes(), check=True)
print("pronto:", dest, f"{len(voz) / SR:.1f} s")
