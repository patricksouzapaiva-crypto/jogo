"""Refaz blocos da narração sem mudar o timbre (13/11, rascunho 1: "a voz muda um pouco" no começo do bloco 3 e
"coreano" saiu errado no bloco 4). Como no Ep. 08: o TTS recebe as últimas frases do bloco anterior antes do texto
(ele continua no mesmo tom); depois o Whisper acha onde o bloco começa de verdade e corta o que sobra antes.
Uso: python3 refazer_blocos.py 3 4   → audio/bloco3.wav, bloco4.wav (os antigos ficam como bloco3_antigo.wav…)"""
import os, re, shutil, subprocess, sys, unicodedata
from pathlib import Path
import numpy as np
from faster_whisper import WhisperModel

AQUI = Path(__file__).parent
A = AQUI / "audio"
FERR = AQUI.parents[1] / "painel" / "ferramentas" / "narrar_fluxo.py"
norm = lambda s: re.sub(r"[^a-z0-9 ]", "", unicodedata.normalize("NFKD", s.lower()).encode("ascii", "ignore").decode())
modelo = WhisperModel("small", compute_type="int8")


def palavras(wav):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(wav), "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    seg, _ = modelo.transcribe(np.frombuffer(raw, np.float32), language="pt", word_timestamps=True)
    return [(norm(w.word).strip(), w.start, w.end) for s in seg for w in s.words]


for b in map(int, sys.argv[1:]):
    txt = (A / f"bloco{b}.txt").read_text().strip()
    ant = (A / f"bloco{b - 1}.txt").read_text().strip().split("\n\n")[-1]
    frases = re.split(r"(?<=[.?!…])\s+", ant)
    contexto = " ".join(frases[-3:])                       # as 3 últimas frases do bloco anterior
    entrada = A / f"bloco{b}_novo.txt"; entrada.write_text(contexto + "\n\n" + txt + "\n")
    bruto = A / f"bloco{b}_novo_bruto.wav"
    for tent in range(4):
        r = subprocess.run([sys.executable, str(FERR), str(entrada), str(bruto)], env={**os.environ, "VOZ": "Algenib"})
        if r.returncode == 0 and bruto.exists():
            break
    ws = palavras(bruto)
    alvo = norm(txt).split()[:4]
    ini = next((ws[i][1] for i in range(len(ws) - 3) if [w[0] for w in ws[i:i + 4]] == alvo), None)
    if ini is None:
        ini = next((ws[i][1] for i in range(len(ws) - 1) if [w[0] for w in ws[i:i + 2]] == alvo[:2]), None)
    if ini is None:
        sys.exit(f"bloco {b}: não achei o começo ({' '.join(alvo)}) em: {' '.join(w[0] for w in ws[:40])}")
    if not (A / f"bloco{b}_antigo.wav").exists():
        shutil.copy(A / f"bloco{b}.wav", A / f"bloco{b}_antigo.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{max(0, ini - 0.12):.2f}", "-i", str(bruto),
                    "-af", "afade=t=in:d=0.03", str(A / f"bloco{b}.wav")], check=True)
    ouvido = " ".join(w[0] for w in ws if w[1] >= ini)
    print(f"bloco {b}: corte em {ini:.2f}s; começa: {ouvido[:90]}")
    if "coreano pesa" in norm(txt):
        k = ouvido.find("terror")
        print("   conferir 'coreano':", ouvido[ouvido.find("o terror coreano") - 10:ouvido.find("o terror coreano") + 60]
              if "o terror coreano pesa" in ouvido else "!! 'o terror coreano pesa' NÃO reconhecido")
