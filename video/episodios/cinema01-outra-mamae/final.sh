#!/bin/bash
# O QUE É A CRIATURA? #1: render final 1080p (aprovado no rascunho 7, 22/11) → revisão. Log em previas/final_run.log
# O filme fica a 24 q/s como no rascunho aprovado (PAINEL_SEM_RIFE=1): o RIFE das ~60 cenas não cabe no disco (≈7 h, +1,5 GB)
cd "$(dirname "$0")"
R=../../painel/ferramentas/revisar.py
export PAINEL_SEM_RIFE=1
SAI=previas/O_Que_E_A_Criatura_01_Outra_Mamae_1080p.mp4
python3 ../../painel/gerar.py roteiro.json $SAI || exit 1
python3 $R video $SAI previas/final.log
echo "FIM codigo=$?"
