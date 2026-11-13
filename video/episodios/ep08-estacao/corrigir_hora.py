"""13/11 — a narração dizia "Meio-dia e quarenta, em Londrina", mas a diferença Brasília–Japão é de 12 h
(23:40 em Hamamatsu = 11:40 em Londrina, como mostra a tela dos relógios). Troca "Meio-dia e quarenta" pelo
"Onze e quarenta" da primeira frase (mesma voz, mesma tomada) e completa com silêncio para a duração total não
mudar (o resto do vídeo fica no lugar). Rodar DEPOIS de trocar_vozes.py.
Uso: python3 corrigir_hora.py   (lê/grava audio/voz_personagens.wav; guarda o original em *_meiodia.wav)"""
import shutil, wave
import numpy as np
from pathlib import Path

A = Path(__file__).parent / "audio"
ARQ, ORIG = A / "voz_personagens.wav", A / "voz_personagens_meiodia.wav"
ONZE = (0.0, 0.84)        # "Onze e quarenta" (antes do "da noite")
TROCA = (2.86, 3.85)      # "Meio-dia e quarenta," (o fôlego antes fica)

if not ORIG.exists():
    shutil.copy(ARQ, ORIG)
w = wave.open(str(ORIG)); sr = w.getframerate(); p = w.getparams()
x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32); w.close()
i = lambda t: int(round(t * sr))
clip = x[i(ONZE[0]):i(ONZE[1])].copy()
f = i(0.012); clip[:f] *= np.linspace(0, 1, f); clip[-f:] *= np.linspace(1, 0, f)
vao = i(TROCA[1]) - i(TROCA[0])
novo = np.concatenate([clip, np.zeros(vao - len(clip), np.float32)])
y = x.copy(); y[i(TROCA[0]):i(TROCA[1])] = novo
o = wave.open(str(ARQ), "wb"); o.setparams(p); o.writeframes(np.clip(y, -32768, 32767).astype(np.int16).tobytes()); o.close()
print(f"ok: {ARQ.name} ({len(y) / sr:.4f} s, igual ao original: {len(y) == len(x)})")
