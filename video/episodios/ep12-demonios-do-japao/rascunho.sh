#!/bin/bash
# Ep. 12: revisão do roteiro → monta → renderiza o rascunho → revisão quadro a quadro. Log em previas/rascunho.log
cd "$(dirname "$0")"
export TMPDIR=/dev/shm   # 24/11: o disco tem ~1,5 GB livres; o temporário do render (~3 GB) vai para a RAM
R=../../painel/ferramentas/revisar.py
python3 montar_roteiro.py || exit 1
python3 $R roteiro || { echo "REVISÃO DO ROTEIRO FALHOU: corrigir antes de renderizar"; exit 1; }
python3 ../../painel/gerar.py roteiro.json previas/ep12_rascunho1.mp4 --rascunho
python3 $R video previas/ep12_rascunho1.mp4 previas/rascunho.log
echo "FIM codigo=$?"
