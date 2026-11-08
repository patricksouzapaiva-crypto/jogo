"""Gera legendas .srt e os capítulos da descrição a partir do .tempos.json do vídeo final.
Uso: python gerar_pacote.py <video.mp4.tempos.json>"""
import json, sys
from pathlib import Path
AQUI = Path(__file__).parent
d = json.load(open(sys.argv[1]))
W = d["palavras"]

def ts(t, srt=True):
    h, m, s = int(t // 3600), int(t % 3600 // 60), t % 60
    return f"{h:02d}:{m:02d}:{int(s):02d},{int((s - int(s)) * 1000):03d}" if srt else f"{m}:{int(s):02d}"

blocos, at = [], []
for i, (w, s, e) in enumerate(W):
    at.append((w, s, e)); txt = " ".join(x[0] for x in at)
    prox = W[i + 1][0] if i + 1 < len(W) else None
    if w[-1] in ".!?" or w.endswith("...") or prox is None or len(txt) + 1 + len(prox) > 60 or (w[-1] == "," and len(txt) > 30):
        blocos.append(at); at = []
out = []
for k, b in enumerate(blocos):
    t0, t1 = b[0][1] - 0.05, b[-1][2] + 0.6
    if k + 1 < len(blocos): t1 = min(t1, blocos[k + 1][0][1] - 0.07)
    out.append(f"{k+1}\n{ts(t0)} --> {ts(t1)}\n{' '.join(x[0] for x in b)}\n")
(AQUI / "legendas_pt-BR.srt").write_text("\n".join(out), encoding="utf-8")

def quando(frase):
    alvo = frase.split()
    for i in range(len(W)):
        if [x[0] for x in W[i:i + len(alvo)]] == alvo:
            return W[i][1]
    raise SystemExit(f"não achei: {frase}")

caps = [("0:00", "3h12 da manhã"),
        (ts(quando("Marcos e Helena estavam"), False), "Coisas normais de sonâmbulo"),
        (ts(quando("Foi numa quinta-feira."), False), "A noite que mudou tudo"),
        (ts(quando("Depois daquela quinta-feira,"), False), "Ela só ficava ali"),
        (ts(quando("Naquela noite, ele tomou"), False), "A câmera"),
        (ts(quando("Na manhã seguinte, Marcos"), False), "A gravação"),
        (ts(quando("Helena nunca foi sonâmbula."), False), "O que o Vigia sabe")]
(AQUI / "capitulos.txt").write_text("\n".join(f"{a} {b}" for a, b in caps) + "\n", encoding="utf-8")
print(open(AQUI / "capitulos.txt").read(), len(out), "legendas")
