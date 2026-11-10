#!/bin/bash
# Conserta as trilhas graves do Suno para tocarem no alto-falante do celular (10/11/2026):
# soma à faixa original duas cópias dela mesma, uma oitava e duas oitavas acima (com eco de sala), corta o
# subgrave que o celular não reproduz e nivela. O caráter da música é o mesmo; só passa a existir som no médio.
# Uso: ./consertar.sh entrada.mp3 saida.wav
set -e
ffmpeg -v error -y -i "$1" -filter_complex "
[0:a]aresample=44100,asplit=3[o][a][b];
[o]highpass=f=45,volume=-3dB[g];
[a]asetrate=88200,aresample=44100,atempo=0.5,highpass=f=180,lowpass=f=2400,aecho=0.8:0.7:90|170:0.35|0.25,volume=+7dB[o1];
[b]asetrate=176400,aresample=44100,atempo=0.5,atempo=0.5,highpass=f=400,lowpass=f=3800,aecho=0.8:0.8:130|260:0.4|0.3,volume=+3dB[o2];
[g][o1][o2]amix=inputs=3:normalize=0,acompressor=threshold=-22dB:ratio=3:attack=200:release=1500,loudnorm=I=-20:TP=-3:LRA=7" -ar 44100 -ac 2 "$2"
