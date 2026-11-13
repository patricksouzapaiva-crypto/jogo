"""Corta, em cada amostra bruta, o trecho em que o TTS leu a instrução de estilo: acha (Whisper) onde começa a fala
de verdade e grava só ela em limpas/. Mostra a transcrição para conferir."""
import glob, json, os, re, subprocess, unicodedata
import numpy as np
from faster_whisper import WhisperModel
from gerar_vozes import FALAS
AQUI = os.path.dirname(os.path.abspath(__file__)); os.makedirs(f"{AQUI}/limpas", exist_ok=True)
norm = lambda s: re.sub(r"[^a-z0-9 ]", "", unicodedata.normalize("NFKD", s.lower()).encode("ascii", "ignore").decode())
m = WhisperModel("small", compute_type="int8"); cortes = {}
for f in sorted(glob.glob(f"{AQUI}/brutas/*.wav")):
    nome = os.path.basename(f)[:-4]; chave = nome.split("_")[0]
    alvo = norm(FALAS[chave][1]).split()[:3]
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True).stdout
    ws = [(norm(w.word).strip(), w.start, w.end) for s in m.transcribe(np.frombuffer(raw, np.float32), language="pt", word_timestamps=True)[0] for w in s.words]
    ini = None
    for i in range(len(ws)):
        if [w[0] for w in ws[i:i + len(alvo)]] == alvo or (ws[i][0] == alvo[0] and i + 1 < len(ws) and ws[i + 1][0] == alvo[1]):
            ini = ws[i][1]
    if ini is None:
        print("NÃO ACHEI:", nome, " ".join(w[0] for w in ws)); continue
    ini = max(0, ini - 0.12); cortes[nome] = ini
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{ini:.2f}", "-i", f, "-af", "afade=t=in:d=0.03,areverse,silenceremove=start_periods=1:start_threshold=-50dB,areverse", f"{AQUI}/limpas/{nome}.wav"], check=True)
    print(nome, f"{ini:.2f}s →", " ".join(w[0] for w in ws if w[1] >= ini))
json.dump(cortes, open(f"{AQUI}/cortes.json", "w"), indent=1)
