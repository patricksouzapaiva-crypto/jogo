#!/bin/bash
# Cantiga "sinistra" (11/11/2026, 2ª versão — o usuário achou a 1ª "muito normal ainda").
# 3 semitons mais grave e ~19% mais lenta; fita velha (afinação que balança fundo e treme); uma segunda voz
# levemente desafinada (as duas "brigam"); um fantasma uma oitava abaixo; eco invertido que chega ANTES da nota;
# abafada (sem agudos) e com eco longo de casa vazia.
# Uso: ./distorcer_cantiga.sh entrada.mp3 saida.mp3
set -e
ffmpeg -v error -y -i "$1" -filter_complex "
[0:a]aresample=44100,asplit=4[a][b][c][d];
[a]asetrate=37044,aresample=44100,vibrato=f=0.31:d=0.42,vibrato=f=5.7:d=0.07[v1];
[b]asetrate=36300,aresample=44100,atempo=0.98,vibrato=f=0.23:d=0.5,volume=-5dB[v2];
[c]asetrate=18522,aresample=44100,atempo=2.0,lowpass=f=700,volume=-7dB[fant];
[d]asetrate=37044,aresample=44100,areverse,aecho=0.8:0.9:700|1300:0.5|0.35,areverse,lowpass=f=1800,volume=-8dB[inv];
[v1][v2][fant][inv]amix=inputs=4:normalize=0:duration=first,
highpass=f=110,lowpass=f=2500,aecho=0.8:0.75:240|510|930:0.42|0.3|0.2,
tremolo=f=0.13:d=0.35,acompressor=threshold=-26dB:ratio=3:attack=200:release=1500,
loudnorm=I=-20:TP=-3:LRA=7,afade=t=in:d=4,areverse,afade=t=in:d=7,areverse" -b:a 192k "$2"
