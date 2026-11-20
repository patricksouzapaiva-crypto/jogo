#!/bin/bash
# Ep. 11: render final 1080p (aprovado no rascunho 4, 20/11) → revisão → cópia de entrega
cd "$(dirname "$0")"
R=../../painel/ferramentas/revisar.py
python3 montar_roteiro.py || exit 1
python3 $R roteiro || exit 1
python3 ../../painel/gerar.py roteiro.json previas/O_Vigia_Ep11_Por_que_voce_nunca_deve_entrar_na_floresta_escandinava_1080p.mp4 || exit 1
python3 $R video previas/O_Vigia_Ep11_Por_que_voce_nunca_deve_entrar_na_floresta_escandinava_1080p.mp4 previas/final.log
echo "FIM codigo=$?"
