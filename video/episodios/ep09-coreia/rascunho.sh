#!/bin/bash
# Ep. 09: revisão do roteiro → monta → renderiza o rascunho → revisão quadro a quadro. Log em previas/rascunho.log
# 14/11: nada vai para o usuário sem passar pelo revisar.py (erros do rascunho 1 do Ep. 09).
cd "$(dirname "$0")"
R=../../painel/ferramentas/revisar.py
python3 $R voz || true
python3 montar_roteiro.py || exit 1
python3 $R roteiro || { echo "REVISÃO DO ROTEIRO FALHOU: corrigir antes de renderizar"; exit 1; }
python3 ../../painel/gerar.py roteiro.json previas/ep09_rascunho.mp4 --rascunho
python3 $R video previas/ep09_rascunho.mp4 previas/rascunho.log
echo "FIM codigo=$?"
