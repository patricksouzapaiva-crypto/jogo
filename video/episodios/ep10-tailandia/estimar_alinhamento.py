"""Alinhamento ESTIMADO (teste da montagem antes da narração inteira): 0,36 s por palavra, 0,45 s entre as falas.
Saída: audio/estimado.json (mesmo formato do alinhamento.json). Uso: ALINHAMENTO=audio/estimado.json python3 montar_roteiro.py"""
import json, sys
from pathlib import Path
AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI.parents[1] / "painel"))
from gerar import tokens  # noqa: E402
import falas as F
t, out = 0.3, []
for f in F.ler()[0] + [F.VINHETA]:
    for _ in tokens(f):
        out.append([round(t, 3), round(t + 0.3, 3)]); t += 0.36
    t += 0.45
json.dump(out, open(AQUI / "audio" / "estimado.json", "w"))
print(len(out), "palavras,", round(t / 60, 1), "min")
