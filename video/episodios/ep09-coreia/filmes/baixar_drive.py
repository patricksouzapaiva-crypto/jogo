"""Baixa os arquivos da pasta do Drive que o usuário compartilhou (13/11) para filmes/; repete até não chegar nada
novo por LIMITE segundos (arg 1, padrão 1800). Controla por ID do Drive (a pasta pode ter dois arquivos com o mesmo
nome — um envio que falhou fica vazio). Arquivo vazio = Drive ainda processando: tenta de novo na próxima volta.
Os vídeos não vão para o git (só este script)."""
import json, sys, time
from pathlib import Path
import gdown
PASTA = "https://drive.google.com/drive/folders/1QBKiUWbwEfHYEZmiBAlKRESsmS9KmZ1a"
AQUI = Path(__file__).parent
FEITOS = AQUI / "baixados.json"
LIMITE = float(sys.argv[1]) if len(sys.argv) > 1 else 1800
feitos = json.loads(FEITOS.read_text()) if FEITOS.exists() else {}
ultimo = time.time()
while time.time() - ultimo < LIMITE:
    try:
        fs = gdown.download_folder(PASTA, skip_download=True, quiet=True) or []
    except Exception as e:
        print("erro ao listar:", e, flush=True); fs = []
    for f in fs:
        if f.id in feitos:
            continue
        alvo = AQUI / f.path
        if alvo.exists() and alvo.stat().st_size > 200_000:      # mesmo nome, outro ID: guarda com o ID no nome
            if f.path in feitos.values():
                alvo = alvo.with_name(f"{alvo.stem}_{f.id[:6]}{alvo.suffix}")
            else:                                               # baixado antes desta versão do script
                feitos[f.id] = f.path; FEITOS.write_text(json.dumps(feitos, indent=1)); continue
        print("baixando:", alvo.name, flush=True)
        parc = alvo.with_name(alvo.name + ".parcial")
        try:
            gdown.download(id=f.id, output=str(parc), quiet=True)
        except Exception as e:
            print("falhou:", alvo.name, e, flush=True); continue
        if not parc.exists() or parc.stat().st_size < 200_000:
            parc.unlink(missing_ok=True); print("vazio (Drive processando), tento de novo:", alvo.name, flush=True)
            continue
        parc.rename(alvo); feitos[f.id] = alvo.name; FEITOS.write_text(json.dumps(feitos, indent=1))
        print("ok:", alvo.name, f"{alvo.stat().st_size / 1e6:.0f} MB", flush=True); ultimo = time.time()
    time.sleep(120)
print(f"fim: nada novo há {LIMITE / 60:.0f} min", flush=True)
