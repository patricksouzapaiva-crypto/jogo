"""Regrava UMA fala da narração (mesmo timbre: o TTS recebe as 2 frases anteriores como contexto) e troca no bloco.
15/11 (rascunho 2): "hospital" saiu "hopital" na fala 13. Gera até 4 tomadas e fica com a primeira em que o Whisper
ouve todas as palavras-chave; o trecho entra no lugar da fala velha (do começo dela ao começo da seguinte, cortando
no meio dos silêncios). Depois: narrar.py → alinhar.py → trocar_vozes.py → alinhar.py voz_personagens.wav.
Uso: python3 refazer_fala.py <fala> <bloco> "palavra1,palavra2"   (ex.: 13 1 "hospital")"""
import os, subprocess, sys
import numpy as np
import falas as F
import narrar_v4 as N   # reaproveita tts_texto, palavras, ler, achar, gravar (o import não roda o narrar_v4: ver abaixo)

i, bloco, chaves = int(sys.argv[1]), int(sys.argv[2]), [N.norm(c) for c in sys.argv[3].split(",")]
fl, *_ = F.ler()
A = N.A; SR = N.SR
arq = A / f"bloco{bloco}.wav"
contexto, texto = N.tts_texto(fl[i - 2:i]), N.tts_texto([fl[i]])
y = None
for t in range(1, 5):
    bruto = A / f"refazer_{i}_t{t}.wav"; ent = A / f"refazer_{i}.txt"; ent.write_text(contexto + "\n\n" + texto + "\n")
    if not bruto.exists():
        subprocess.run([sys.executable, str(N.FERR), str(ent), str(bruto)], env={**os.environ, "VOZ": "Algenib"}, check=True)
    ws = N.palavras(bruto); k = N.achar(ws, texto)
    ouvido = [w[0] for w in ws[k:]] if k is not None else []
    print(f"tomada {t}: {' '.join(ouvido)}")
    if k is not None and all(any(c in w for w in ouvido) for c in chaves):
        x = N.ler(bruto); c0 = int((ws[k - 1][2] + (ws[k][1] - ws[k - 1][2]) * 0.5) * SR) if k else 0
        y = x[c0:]; v = np.where(np.abs(y) > 0.01)[0]; y = y[: v[-1] + int(0.35 * SR)]
        f = int(0.02 * SR); y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
        break
if y is None:
    sys.exit("nenhuma tomada com todas as palavras")
b = N.ler(arq); wb = N.palavras(arq)
k0 = N.achar(wb, fl[i]); k1 = N.achar(wb, fl[i + 1], depois=wb[k0][1] if k0 is not None else 0)
if k0 is None or k1 is None:
    sys.exit("não achei a fala velha no bloco")
c0 = int((wb[k0 - 1][2] + (wb[k0][1] - wb[k0 - 1][2]) * 0.5) * SR)
c1 = int((wb[k1 - 1][2] + (wb[k1][1] - wb[k1 - 1][2]) * 0.5) * SR)
velho = b[c0:c1]
y *= N.rms(velho) / N.rms(y)
silencio = np.zeros(max(0, int(0.25 * SR)), np.float32)
novo = np.concatenate([b[:c0], silencio, y, silencio, b[c1:]])
os.replace(arq, A / f"bloco{bloco}_antes_refazer_{i}.wav")
N.gravar(novo, arq)
print(f"ok: fala {i} trocada no bloco {bloco} ({len(velho) / SR:.1f}s → {(len(y) + 2 * len(silencio)) / SR:.1f}s)")
