"""Refaz toda a preparacao a partir das folhas originais (Windows, Linux ou Mac).

Uso (na pasta do projeto, onde fica JogoFazenda/):
    python fauna_preparada/ferramentas/rodar_tudo.py ^
        --entrada JogoFazenda/arte/entrada/fauna ^
        --metadata MOVIMENTACOES_DOS_ANIMAIS_v1/METADATA_ANIMAIS.json ^
        --saida JogoFazenda/arte/preparado/fauna

Precisa de: Python 3.10+ e  pip install pillow numpy scipy
Para mudar o tamanho de um animal, edite escala_especies.json e rode de novo.
"""
import argparse, os, subprocess, sys, tempfile

aqui = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument("--entrada", required=True, help="pasta com <animal>_walk.png e <animal>_actions.png")
ap.add_argument("--metadata", required=True, help="METADATA_ANIMAIS.json do pacote")
ap.add_argument("--saida", required=True, help="pasta de saida dos atlas (ex.: JogoFazenda/arte/preparado/fauna)")
ap.add_argument("--escala", default=os.path.join(aqui, "escala_especies.json"))
ap.add_argument("--sem-melhorias", action="store_true", help="gera a v1 (sem as melhorias do andar)")
a = ap.parse_args()

tmp = tempfile.mkdtemp(prefix="fauna_")
seg, prep, prep2 = os.path.join(tmp, "seg"), os.path.join(tmp, "prep"), os.path.join(tmp, "prep_v2")
def rodar(script, *args):
    print(">>", script, *args, flush=True)
    subprocess.check_call([sys.executable, os.path.join(aqui, script), *args])
rodar("segmentar.py", a.entrada, seg, a.metadata)
rodar("preparar.py", seg, prep, a.escala, a.metadata)
final = prep
if not a.sem_melhorias:
    rodar("melhorar_andar.py", prep, prep2)    # v2: sobe e desce, ritmo, textura, pose de parado
    final = prep2
rodar("validar.py", final)
rodar("montar_atlas.py", final, a.saida)
rodar("pranchas.py", final, os.path.join(tmp, "pranchas"), "3")
print("\nPronto. Atlas e JSON em", a.saida)
print("Pranchas de revisao e medidas em", tmp)
