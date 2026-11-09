"""Gera trilhas instrumentais de terror pela API da KIE.AI (modelos Suno), como o app MySuno faz.

Fluxo (o mesmo do MySuno: src/js/api.js):
  POST https://api.kie.ai/api/v1/jobs/createTask   {model: "ai-music-api/generate", input: {...}}
  GET  https://api.kie.ai/api/v1/jobs/recordInfo?taskId=...   (até state == success)
  -> resultJson com as URLs dos áudios (cada pedido devolve 2 variações)

A chave da KIE é injetada pelo proxy desta sessão (cadastrada como credencial de api.kie.ai);
fora daqui, defina KIE_API_KEY.

Uso:
  python musica_kie.py <nome> "<estilo em inglês>" [--modelo V5] [--titulo "..."]
Salva em video/painel/sons/<nome>_1.mp3 e <nome>_2.mp3, já niveladas (-23 LUFS).
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import requests

BASE = "https://api.kie.ai"
SONS = Path(__file__).resolve().parents[1] / "sons"
CAB = {"Authorization": f"Bearer {os.environ.get('KIE_API_KEY', 'proxy')}", "Content-Type": "application/json"}

ESTILO_PADRAO = ("dark cinematic horror underscore, instrumental, slow, quiet and tense, low sustained cello drones, "
                 "sparse minor-key piano notes, dissonant high string harmonics, deep sub bass swells, long silences, "
                 "no drums, no melody hook, no vocals, background music for narration")


def modelos():
    """Lê o catálogo atual da KIE (mesma fonte que o MySuno usa)."""
    md = requests.get("https://docs.kie.ai/suno-api/generate-music.md", timeout=20).text
    import re
    ids = sorted(set(re.findall(r"\bV\d+(?:_\d+)?(?:_[A-Z]+)?\b", md)), reverse=True)
    return ids


def gerar(nome, estilo=ESTILO_PADRAO, modelo=None, titulo="Ultimo Abrigo - trilha"):
    modelo = modelo or (modelos() or ["V5"])[0]
    corpo = {"model": "ai-music-api/generate",
             "input": {"model": modelo, "instrumental": True, "custom_mode": True,
                       "title": titulo[:80], "style": estilo[:1000]}}
    r = requests.post(f"{BASE}/api/v1/jobs/createTask", headers=CAB, json=corpo, timeout=30)
    d = r.json()
    if r.status_code != 200 or d.get("code") not in (0, 200, None):
        raise SystemExit(f"KIE recusou: HTTP {r.status_code} {d}")
    tid = (d.get("data") or {}).get("taskId") or d.get("taskId")
    print("tarefa", tid, "modelo", modelo)
    for _ in range(120):  # até ~10 min
        time.sleep(5)
        info = requests.get(f"{BASE}/api/v1/jobs/recordInfo", params={"taskId": tid}, headers=CAB, timeout=30).json()
        dado = info.get("data") or {}
        estado = str(dado.get("state", "")).lower()
        if estado in ("fail", "failed", "error"):
            raise SystemExit(f"falhou: {dado.get('failMsg') or dado}")
        if estado == "success":
            res = dado.get("resultJson")
            res = json.loads(res) if isinstance(res, str) else (res or {})
            urls = [x for x in json.dumps(res).replace("\\/", "/").split('"') if x.startswith("http") and
                    (".mp3" in x or "audio" in x)]
            urls = list(dict.fromkeys(urls))
            saidas = []
            for i, u in enumerate(urls[:2], 1):
                bruto = SONS / f"{nome}_{i}_bruto.mp3"
                bruto.write_bytes(requests.get(u, timeout=120).content)
                final = SONS / f"{nome}_{i}.mp3"
                subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", bruto, "-af", "loudnorm=I=-23:TP=-2:LRA=18",
                                "-ar", "44100", "-b:a", "192k", final], check=True)
                bruto.unlink()
                saidas.append(final)
            print("pronto:", *saidas)
            return saidas
    raise SystemExit("tempo esgotado esperando a KIE")


if __name__ == "__main__":
    a = sys.argv[1:]
    nome = a[0]
    estilo = a[1] if len(a) > 1 and not a[1].startswith("--") else ESTILO_PADRAO
    mod = a[a.index("--modelo") + 1] if "--modelo" in a else None
    gerar(nome, estilo, mod)
