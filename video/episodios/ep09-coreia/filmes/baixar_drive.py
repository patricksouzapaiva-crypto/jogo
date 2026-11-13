"""Baixa os arquivos da pasta do Drive que o usuário compartilhou (13/11) para filmes/; repete até não chegar nada
novo por 30 min. Os vídeos não vão para o git (só este script)."""
import time, sys, gdown
from pathlib import Path
PASTA = "https://drive.google.com/drive/folders/1QBKiUWbwEfHYEZmiBAlKRESsmS9KmZ1a"
AQUI = Path(__file__).parent
ultimo = time.time()
while time.time() - ultimo < 1800:
    try:
        fs = gdown.download_folder(PASTA, skip_download=True, quiet=True) or []
    except Exception as e:
        print("erro ao listar:", e, flush=True); fs = []
    for f in fs:
        alvo = AQUI / f.path
        if alvo.exists():
            continue
        print("baixando:", f.path, flush=True)
        alvo.parent.mkdir(parents=True, exist_ok=True)
        try:
            gdown.download(id=f.id, output=str(alvo) + ".parcial", quiet=True)
            Path(str(alvo) + ".parcial").rename(alvo)
            print("ok:", f.path, f"{alvo.stat().st_size / 1e6:.0f} MB", flush=True); ultimo = time.time()
        except Exception as e:
            print("falhou:", f.path, e, flush=True)
    time.sleep(120)
print("fim: nada novo há 30 min", flush=True)
