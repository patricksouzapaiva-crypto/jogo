#!/bin/bash
# renderiza os 3 Shorts (9:16) e gera a legenda .srt de cada um
cd "$(dirname "$0")"
export PAINEL_SEM_RIFE=1   # 24 q/s como no episódio
for s in s1_cleary s2_tulpa s3_trocado; do
  python3 ../../painel/gerar.py shorts/$s.json publicacao/shorts_final/$s.mp4 > publicacao/shorts_final/$s.log 2>&1 || { echo "ERRO $s"; continue; }
  python3 ../../painel/ferramentas/gerar_srt.py publicacao/shorts_final/$s.mp4.tempos.json publicacao/shorts_final/$s.srt
  python3 ../../painel/ferramentas/revisar.py video publicacao/shorts_final/$s.mp4 publicacao/shorts_final/$s.revisao 2>&1 | tail -1
done
echo FIM
