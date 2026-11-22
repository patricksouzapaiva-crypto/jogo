"""Legenda pt-BR para o YouTube: a narração (as legendas que o vídeo mostra, do .tempos.json) + as falas do filme
(as amarelas dentro do quadro, de filmes_prontos/trechos.json, no tempo da cena). Os cartões lidos em voz alta não têm
legenda no vídeo e também não entram aqui. Uso: python3 publicacao/gerar_srt.py"""
import json
from pathlib import Path
A = Path(__file__).resolve().parents[1]
T = json.load(open(A / "previas/O_Que_E_A_Criatura_01_Outra_Mamae_1080p.mp4.tempos.json", encoding="utf-8"))
TR = json.load(open(A / "filmes_prontos/trechos.json", encoding="utf-8"))
hms = lambda t: f"{int(t // 3600):02d}:{int(t % 3600 // 60):02d}:{int(t % 60):02d},{int(round(t % 1 * 1000)) % 1000:03d}"
ev = [(a, b, x.replace(" / ", "\n")) for a, b, x in T["legendas"]]
cenas = T["cenas"]
for i, c in enumerate(cenas):
    n = Path(c.get("arquivo", "")).stem
    fim = cenas[i + 1]["t0"] if i + 1 < len(cenas) else 1e9
    for x, y, t in TR.get(n, {}).get("falas", []):
        if c["t0"] + x < fim - 0.3:
            ev.append((c["t0"] + x, min(c["t0"] + y, fim), t))
ev.sort()
out = []
for i, (a, b, x) in enumerate(ev):
    if i + 1 < len(ev): b = min(b, ev[i + 1][0] - 0.04)
    out.append(f"{len(out) + 1}\n{hms(a)} --> {hms(max(b, a + 0.5))}\n{x}\n")
(A / "publicacao/legendas_pt-BR.srt").write_text("\n".join(out), encoding="utf-8")
print(len(out), "legendas")
