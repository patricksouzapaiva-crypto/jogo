#!/bin/bash
# renderiza todas as peças do #2 (3 por vez). As do julgamento: placar_d1 (sai a pata), d2 (+ o gênio), d3 (+ o dybbuk)
cd "$(dirname "$0")"
jobs_=(
 "abertura pecas/abertura.mp4"
 "veredito pecas/veredito.mp4"
 "placar pecas/placar.mp4"
 "placar pecas/placar_d1.mp4 3"
 "placar pecas/placar_d2.mp4 3,0"
 "placar pecas/placar_d3.mp4 3,0,2"
)
for n in 1 2 3 4 5 6 7; do jobs_+=("pista pecas/pista$n.mp4 $n"); done
for n in 1 2 3 4; do jobs_+=("teoria pecas/teoria$n.mp4 $n" "suspeito pecas/suspeito$n.mp4 $n"); done
for n in 1 3 4; do jobs_+=("checklist pecas/checklist$n.mp4 $n"); done
for j in "${jobs_[@]}"; do
  while [ $(jobs -r | wc -l) -ge 3 ]; do sleep 2; done
  python3 feitico.py $j > /dev/null 2>&1 && echo "ok $j" || echo "FALHOU $j" &
done
wait; echo FIM
