"""Auditoria IMAGEM × FALA na linha do tempo FINAL (depois de todos os ajustes do motor), sem renderizar.

24/11 (Ep. 12, usuário: "ainda continua repetindo imagens mesmo falando de outros onis… analise isso de verdade pra
que não fique acontecendo"). Roda o gerar.py só até a linha do tempo (SO_LINHA) e escreve uma tabela com cada cena:
início, duração, a obra na tela e as palavras ditas enquanto ela está lá. Avisa:
  - obra que volta em blocos separados (a mesma imagem em assuntos diferentes);
  - obra usada mais de MAX vezes;
  - cena longa demais (a mesma imagem por muitas frases).

Uso: python3 auditar_imagens.py roteiro.json saida.txt
"""
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

PAINEL = Path(__file__).resolve().parents[1]
MAX = 3
LONGA = 16.0
IGNORA = re.compile(r"^(abrigo|vigia|texto|chat|capitulo|cap\d|00001|relogios)")


def obra(c):
    a = c.get("imagem") or c.get("video") or c.get("tipo") or "?"
    a = re.sub(r"^.*/", "", a); a = re.sub(r"\.(jpg|jpeg|png|mp4)$", "", a)
    return re.sub(r"^restauro_", "", a)


def main(roteiro, saida):
    linha = Path(tempfile.gettempdir()) / "auditoria_linha.json"
    env = dict(os.environ, SO_LINHA=str(linha))
    r = subprocess.run([sys.executable, str(PAINEL / "gerar.py"), roteiro, str(linha.with_suffix(".mp4")), "--rascunho"],
                       env=env, capture_output=True, text=True, cwd=Path(roteiro).resolve().parent)
    if not linha.exists():
        print(r.stdout[-2000:], r.stderr[-2000:]); sys.exit(1)
    D = json.loads(linha.read_text()); cs = D["cenas"]; P = D["_palavras"]
    usos, blocos, linhas, avisos = defaultdict(int), defaultdict(list), [], []
    ant = None
    for i, c in enumerate(cs):
        n = obra(c); usos[n] += 1
        if n != ant:
            blocos[n].append(i)
        ant = n
    for i, c in enumerate(cs):
        t0 = c["t0"]; t1 = cs[i + 1]["t0"] if i + 1 < len(cs) else t0 + 5
        ws = " ".join(w for w, a, b in P if t0 - 0.1 <= a < t1 - 0.1)
        n = obra(c)
        linhas.append(f"{i:3d} {int(t0 // 60)}:{t0 % 60:04.1f} {t1 - t0:4.1f}s {n[:32]:32s}| {ws}")
        if not IGNORA.match(n) and t1 - t0 > LONGA:
            avisos.append(f"cena longa ({t1 - t0:.0f}s) em {int(t0 // 60)}:{t0 % 60:04.1f}: {n}")
    for n, bl in blocos.items():
        if IGNORA.match(n):
            continue
        if len(bl) > 1:
            ts = ", ".join(f"{int(cs[k]['t0'] // 60)}:{cs[k]['t0'] % 60:04.1f}" for k in bl)
            avisos.append(f"volta em {len(bl)} momentos diferentes: {n} ({ts})")
        elif usos[n] > MAX:
            avisos.append(f"usada {usos[n]} vezes seguidas: {n}")
    txt = "\n".join(linhas) + "\n\nAVISOS\n" + "\n".join(avisos) + "\n"
    Path(saida).write_text(txt)
    print(f"auditoria de imagens: {len(cs)} cenas, {len(avisos)} aviso(s) → {saida}")
    for a in avisos:
        print("  aviso ", a)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
