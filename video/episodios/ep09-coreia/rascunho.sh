#!/bin/bash
# Ep. 09: monta o roteiro (gera a câmera 3D na primeira vez) e renderiza o rascunho. Log em previas/rascunho.log
cd "$(dirname "$0")"
python3 montar_roteiro.py && MANTER_TEMP=0 python3 ../../painel/gerar.py roteiro.json previas/ep09_rascunho.mp4 --rascunho
echo "FIM codigo=$?"
