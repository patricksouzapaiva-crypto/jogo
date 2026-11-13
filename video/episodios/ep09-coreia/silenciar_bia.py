"""Silencia o "B. A." que o TTS leu no lugar de 비아 (fim do episódio: "Escrito em vermelho. [비아] Bia.").
O 비아 aparece pintado na tela nesse silêncio. Acha o trecho com o Whisper entre "vermelho" e "Bia".
Uso: python3 silenciar_bia.py   (lê/grava audio/voz_com_vinheta_limpa.wav; guarda _original.wav)"""
import shutil, subprocess
from pathlib import Path
import numpy as np
from faster_whisper import WhisperModel
A = Path(__file__).parent / "audio"; SR = 48000
w = A / "voz_com_vinheta_limpa.wav"; orig = A / "voz_com_vinheta_limpa_original.wav"
shutil.copy(w, orig)
x = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", str(orig), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                                 capture_output=True, check=True).stdout, np.float32).copy()
dur = len(x) / SR
a0 = max(0, dur - 120)                                      # está nos últimos 2 minutos
y16 = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{a0}", "-i", str(orig), "-f", "f32le", "-ac", "1", "-ar", "16000", "-"],
                                   capture_output=True, check=True).stdout, np.float32)
seg, _ = WhisperModel("small", compute_type="int8").transcribe(y16, language="pt", word_timestamps=True)
ws = [(w_.word.strip().lower().strip(".,!?…"), w_.start + a0, w_.end + a0) for s in seg for w_ in s.words]
iv = next(i for i in range(len(ws)) if ws[i][0] == "vermelho" and any(ws[j][0] == "bia" for j in range(i + 1, min(i + 6, len(ws)))))
ib = next(j for j in range(iv + 1, len(ws)) if ws[j][0] == "bia")
print("entre:", [w_[0] for w_ in ws[iv:ib + 1]])
s0, s1 = ws[iv][2] + 0.15, ws[ib][1] - 0.12
if ib - iv > 1:                                             # tem algo lido entre "vermelho" e "Bia": silencia
    a, b = int(s0 * SR), int(s1 * SR); f = int(0.03 * SR)
    x[a - f:a] *= np.linspace(1, 0, f); x[a:b] = 0; x[b:b + f] *= np.linspace(0, 1, f)
    print(f"silêncio de {s0:.2f} a {s1:.2f} s")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", str(w)], input=x.tobytes(), check=True)
