#!/bin/bash
# O QUE É A CRIATURA? #1: render final 1080p → revisão. Log em previas/final_run.log
# 23/11 (r9): filme só nas 18 falas-pista, ilustrações com câmera 3D, cenas animadas, gancho com o caso Cleary.
# Monta e revisa o roteiro ANTES (como o rascunho). O filme fica a 24 q/s (PAINEL_SEM_RIFE=1), como nos rascunhos aprovados.
cd "$(dirname "$0")"
R=../../painel/ferramentas/revisar.py
export PAINEL_SEM_RIFE=1
SAI=previas/O_Que_E_A_Criatura_01_Outra_Mamae_1080p.mp4
python3 montar_roteiro.py || exit 1
python3 $R roteiro || { echo "REVISÃO DO ROTEIRO FALHOU: corrigir antes de renderizar"; exit 1; }
python3 ../../painel/gerar.py roteiro.json $SAI || exit 1
python3 $R video $SAI previas/final.log
echo "FIM codigo=$?"
