#!/bin/bash
# rev. 2 (23/11): bonecos de pano (teoria, placar, veredito), abertura só com o galho do filme, pistas com o galho novo
cd "$(dirname "$0")"
jobs_=("abertura pecas/abertura.mp4" "veredito pecas/veredito.mp4" "placar pecas/placar.mp4" "placar pecas/placar_d1.mp4 3"
       "placar pecas/placar_d2.mp4 3,0" "placar pecas/placar_d3.mp4 3,0,2")
for n in 1 2 3 4; do jobs_+=("teoria pecas/teoria$n.mp4 $n"); done
for n in 1 2 3 4 5 6 7; do jobs_+=("pista pecas/pista$n.mp4 $n"); done
for j in "${jobs_[@]}"; do
  while [ $(jobs -r | wc -l) -ge 3 ]; do sleep 2; done
  python3 feitico.py $j > /dev/null 2>&1 && echo "ok $j" || echo "FALHOU $j" &
done
wait; echo FIM
