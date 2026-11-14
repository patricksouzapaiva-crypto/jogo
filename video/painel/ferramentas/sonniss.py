"""Biblioteca Sonniss GDC (efeitos profissionais royalty-free, uso comercial liberado, sem crédito obrigatório) pelo
espelho do archive.org, arquivo por arquivo (os pacotes inteiros têm 12–70 GB; aqui baixamos só o que a cena pede).
Uso:
  python3 sonniss.py indice                 → baixa a lista de arquivos de todos os anos (sonniss/indice.json)
  python3 sonniss.py busca "elevator door"  → mostra os melhores resultados (todas as palavras precisam aparecer)
  python3 sonniss.py baixa <n> [nome]       → baixa o resultado n da última busca para sons/sonniss/<nome>.flac
15/11 (Ep. 09): ElevenLabs sem créditos e o Lyria fora do plano gratuito — esta é a biblioteca fixa do canal."""
import json, re, subprocess, sys, urllib.parse
from pathlib import Path
import requests

PASTA = Path(__file__).resolve().parents[1] / "sons" / "sonniss"; PASTA.mkdir(exist_ok=True)
INDICE, ULTIMA = PASTA / "indice.json", PASTA / "_ultima_busca.json"
ANOS = ["sonniss-gdc-2015-game-audio-bundle-normalized", "sonniss-gdc-2016-game-audio-bundle-normalized",
        "sonniss-gdc-2017-game-audio-bundle-normalized", "sonniss-gdc-2018-game-audio-bundle-normalized",
        "sonniss-gdc-2019-game-audio-bundle-normalized", "sonniss-gdc-2020-game-audio-bundle-normalized",
        "sonniss-gdc-2023-game-audio-bundle-normalized", "sonniss-gdc-2024-game-audio-bundle-normalized",
        "sonniss-gdc-2026-game-audio-bundle-normalized"]


def indice():
    tudo = []
    for ident in ANOS:
        r = requests.get(f"https://archive.org/metadata/{ident}/files", timeout=120)
        fs = r.json().get("result", []) if r.ok else []
        n = 0
        for f in fs:
            nome = f["name"]
            if nome.lower().endswith(".flac"):          # a versão leve e sem perda (o .wav original é 3–5× maior)
                tudo.append({"id": ident, "arq": nome, "mb": round(int(f.get("size", 0)) / 1e6, 2)}); n += 1
        print(ident, n, "sons")
    json.dump(tudo, open(INDICE, "w"))
    print("total:", len(tudo))


def busca(consulta, n=25):
    idx = json.load(open(INDICE))
    ps = [p.lower() for p in consulta.split()]
    achou = [f for f in idx if all(p in f["arq"].lower() for p in ps)]
    achou.sort(key=lambda f: (len(f["arq"]), f["mb"]))
    json.dump(achou[:n], open(ULTIMA, "w"))
    for k, f in enumerate(achou[:n]):
        print(f"{k:2d} {f['mb']:6.1f}MB {f['arq'][:120]}")
    print(f"({len(achou)} resultados)")


def baixa(k, nome=None):
    f = json.load(open(ULTIMA))[int(k)]
    nome = nome or re.sub(r"[^a-z0-9]+", "_", Path(f["arq"]).stem.lower())[:60]
    url = f"https://archive.org/download/{f['id']}/" + urllib.parse.quote(f["arq"])
    dest = PASTA / f"{nome}.flac"
    subprocess.run(["curl", "-sL", "--fail", "-o", str(dest), url], check=True)
    print("ok", dest.name, f"{dest.stat().st_size / 1e6:.1f} MB ←", f["arq"])
    return dest


if __name__ == "__main__":
    a = sys.argv[1:]
    {"indice": lambda: indice(), "busca": lambda: busca(" ".join(a[1:])), "baixa": lambda: baixa(*a[1:])}[a[0]]()
