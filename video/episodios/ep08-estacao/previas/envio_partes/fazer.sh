#!/bin/bash
# Codifica a cópia de envio em 4 pedaços (vídeo) + áudio inteiro, e junta. Retomável.
cd "$(dirname "$0")"
M=../ep08_final.mp4; Q=9404   # quadros por pedaço (30 fps); o último leva o resto
for i in 0 1 2 3; do
  [ -f v$i.ok ] && continue
  ( s=$(python3 -c "print($i*$Q/30)"); ex=""; [ $i -lt 3 ] && ex="-frames:v $Q"
    ffmpeg -nostdin -y -v error -ss $s -i $M $ex -an -c:v libx264 -preset slow -b:v 3000k -maxrate 5000k -bufsize 7500k -threads 2 v$i.mp4 && touch v$i.ok ) &
done
[ -f a.ok ] || ( ffmpeg -nostdin -y -v error -i $M -vn -c:a aac -b:a 192k a.m4a && touch a.ok ) &
wait
ls v0.ok v1.ok v2.ok v3.ok a.ok >/dev/null || { echo FALHOU; exit 1; }
printf "file 'v%d.mp4'\n" 0 1 2 3 > lista.txt
ffmpeg -nostdin -y -v error -f concat -safe 0 -i lista.txt -i a.m4a -map 0:v -map 1:a -c copy -movflags +faststart ../O_Vigia_Ep08_envio.mp4 && echo PRONTO
