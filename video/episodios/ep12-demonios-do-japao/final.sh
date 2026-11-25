#!/bin/bash
# Ep. 12: render final 1080p (aprovado no rascunho 4, 25/11) → revisão. O disco está cheio: o render vai para a RAM.
cd "$(dirname "$0")"
export TMPDIR=/dev/shm
R=../../painel/ferramentas/revisar.py
F=/dev/shm/O_Vigia_Ep12_Os_demonios_do_Japao_nao_querem_a_sua_alma_1080p.mp4
python3 montar_roteiro.py || exit 1
python3 $R roteiro || exit 1
python3 ../../painel/ferramentas/auditar_imagens.py roteiro.json previas/auditoria_imagens.txt
python3 ../../painel/gerar.py roteiro.json $F || exit 1
python3 $R video $F previas/final.log
echo "FIM codigo=$?"
