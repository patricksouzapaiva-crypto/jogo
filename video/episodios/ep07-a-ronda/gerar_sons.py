"""Gera os efeitos do PEDIDO_SONS.md no ElevenLabs (Sound Effects), 2 versões de cada → busca/sons/Sxx_a.mp3, _b.
A chave é injetada pelo proxy do ambiente (cabeçalho xi-api-key). Uso: python3 gerar_sons.py [S05 S06 ...]"""
import re, sys, time, requests
from pathlib import Path
AQUI = Path(__file__).parent
SAI = AQUI / "busca" / "sons"; SAI.mkdir(parents=True, exist_ok=True)
linhas = [l for l in (AQUI / "PEDIDO_SONS.md").read_text().splitlines() if l.startswith("| **S")]
pedidos = []
for l in linhas:
    c = [x.strip() for x in l.strip("|").split("|")]
    cod = re.search(r"S\d\d", c[0]).group(0); dur = float(re.search(r"\d+", c[1]).group(0)); laco = "loop" in c[1]
    pedidos.append((cod, min(dur, 30.0), laco, c[2]))
so = set(sys.argv[1:])
for cod, dur, laco, txt in pedidos:
    if so and cod not in so:
        continue
    for v in "ab":
        arq = SAI / f"{cod}_{v}.mp3"
        if arq.exists():
            continue
        for k in range(4):
            r = requests.post("https://api.elevenlabs.io/v1/sound-generation", headers={"xi-api-key": "proxy"},
                              json={"text": txt, "duration_seconds": dur, "prompt_influence": 0.55, "loop": laco}, timeout=180)
            if r.status_code == 200:
                arq.write_bytes(r.content); print(cod, v, "ok", len(r.content)); break
            print(cod, v, r.status_code, r.text[:200]); time.sleep(8)
