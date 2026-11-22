#!/bin/bash
# O QUE É A CRIATURA? #1: monta → revisão do roteiro → rascunho → revisão quadro a quadro. Log em previas/rascunho.log
cd "$(dirname "$0")"
R=../../painel/ferramentas/revisar.py
python3 montar_roteiro.py || exit 1
python3 $R roteiro || { echo "REVISÃO DO ROTEIRO FALHOU: corrigir antes de renderizar"; exit 1; }
python3 ../../painel/gerar.py roteiro.json previas/cin01_rascunho4.mp4 --rascunho
python3 $R video previas/cin01_rascunho4.mp4 previas/rascunho.log
echo "FIM codigo=$?"
