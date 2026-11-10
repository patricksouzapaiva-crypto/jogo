#!/bin/bash
# Monta as trilhas longas do Ep. 05 a partir das faixas do Suno consertadas (consertar.sh).
# Ciclo = faixa 2, faixa 1, faixa 2 ao contrário, faixa 1 ao contrário, emendadas com fusão de 8 s (não dá para
# perceber a emenda nem a repetição); o ciclo se repete até a duração pedida.
# Uso: ./montar_trilhas.sh   -> ../../../painel/sons/ep05_fundo_longa.mp3 (16 min) e ep05_tensao_longa.mp3 (8 min)
set -e
T=$(mktemp -d); SONS=../../../painel/sons
ciclo() { # $1 $2 = faixas, $3 = saída
  ./consertar.sh "$1" $T/a.wav; ./consertar.sh "$2" $T/b.wav
  ffmpeg -v error -y -i $T/b.wav -i $T/a.wav -i $T/b.wav -i $T/a.wav -filter_complex "
    [2:a]areverse[br];[3:a]areverse[ar];
    [0:a][1:a]acrossfade=d=8:c1=tri:c2=tri[x1];[x1][br]acrossfade=d=8:c1=tri:c2=tri[x2];
    [x2][ar]acrossfade=d=8:c1=tri:c2=tri" $3
}
longa() { # $1 = ciclo.wav, $2 = segundos, $3 = saída mp3
  # o ciclo termina e recomeça na mesma faixa (2 → ... → 1 ao contrário → 2): emenda do laço com fusão de 8 s
  ffmpeg -v error -y -i $1 -i $1 -i $1 -i $1 -i $1 -i $1 -filter_complex "
    [0:a][1:a]acrossfade=d=8:c1=tri:c2=tri[a];[a][2:a]acrossfade=d=8:c1=tri:c2=tri[b];
    [b][3:a]acrossfade=d=8:c1=tri:c2=tri[c];[c][4:a]acrossfade=d=8:c1=tri:c2=tri[d];
    [d][5:a]acrossfade=d=8:c1=tri:c2=tri,atrim=0:$2,afade=t=in:d=3,afade=t=out:st=$(($2-5)):d=5" -b:a 192k $3
}
ciclo suno_A1_fundo.mp3 suno_A2_fundo.mp3 $T/fundo.wav
ciclo suno_B1_tensao.mp3 suno_B2_tensao.mp3 $T/tensao.wav
longa $T/fundo.wav 960 $SONS/ep05_fundo_longa.mp3
longa $T/tensao.wav 480 $SONS/ep05_tensao_longa.mp3
# cantiga: só nivelada (sem o salto de volume) e com as pontas suaves
ffmpeg -v error -y -i suno_C2_cantiga.mp3 -af "acompressor=threshold=-24dB:ratio=3:attack=300:release=2000,loudnorm=I=-20:TP=-3:LRA=6,afade=t=in:d=4,areverse,afade=t=in:d=6,areverse" -b:a 192k $SONS/ep05_cantiga.mp3
rm -rf $T; echo ok
