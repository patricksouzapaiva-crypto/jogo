"""Refaz todo o pacote do heroi a partir das poses em fonte/.

python3 rodar_tudo.py            -> quadros (paleta unica + respirar), folha do Godot, pranchas,
                                    GIFs e videos de cada direcao e o video final
python3 rodar_tudo.py --rapido   -> so quadros, folha do Godot e pranchas (sem videos)

Obs.: os scripts anim_*.py sozinhos geram cada direcao com paleta propria (servem para testar
uma direcao). O pacote final sai do montar_heroi.py, que usa uma paleta so para as 4 direcoes.
"""
import os, subprocess, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable


def roda(*args):
    print(">>", " ".join(args), flush=True)
    subprocess.run([PY, os.path.join(AQUI, args[0]), *args[1:]], check=True)


if __name__ == "__main__":
    roda("montar_heroi.py")
    rev = os.path.join(AQUI, "..", "revisao")
    for d in ("lado", "lado_esq", "frente", "costas"):
        roda("previa.py", os.path.join(rev, d))
    roda("comparar_lados.py")
    if "--rapido" not in sys.argv:
        for d in ("lado", "lado_esq", "frente", "costas"):
            roda("video_andar.py", d)
        roda("video_final.py")
    print("pronto")
