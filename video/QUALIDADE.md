# Checklist de qualidade — vale para TODO episódio (14/11)

Nasceu dos erros apontados pelo usuário nos rascunhos (Ep. 08 e rascunho 1 do Ep. 09). Antes de mandar qualquer vídeo:
`rascunho.sh` roda `painel/ferramentas/revisar.py` (voz → roteiro → vídeo) e eu olho TODAS as folhas de cenas.

## Voz
- [ ] Narração em blocos: do 2º bloco em diante o TTS recebe as últimas frases do bloco anterior (`refazer_blocos.py`),
      senão o timbre muda na emenda ("a voz muda um pouco").
- [ ] `revisar.py voz`: ouvir cada frase marcada (palavra lida errada: "coreano", nomes coreanos, hangul).
- [ ] Hangul nunca vai para o TTS (ele soletra "B. A."): o texto em coreano aparece só na tela.
- [ ] Personagens só com som de lugar (celular, corredor). Sem acelerar fala.

## Imagem e câmera
- [ ] **Sem foco redondo (`dof`)**. Foco de lente só o da câmera 3D (profundidade real).
- [ ] Foco/zoom conferidos na GRADE de cada imagem: o assunto inteiro no quadro (a plaquinha toda, não uma letra; a
      linha inteira da regra, não um círculo). Zoom > 1,45 só se o assunto couber.
- [ ] Movimento natural (aproximação lenta ou deslize); nada de zoom "dramático" sem motivo.
- [ ] Mesma imagem no máximo 3 vezes (usar a variação B, C ou outro ângulo).
- [ ] Ninguém de frente (rosto de IA); a criatura e o fantasma nunca mostram o rosto.

## Texto na tela
- [ ] Kanji/hangul legível: em imagem escura, modo `luz` ou `sangue` (nunca `tinta` preta).
- [ ] Tempo de leitura: kanji com legenda fica ≥ 6,5 s depois de aparecer; se a frase é curta, aparece no começo dela
      (não na última palavra) e a pausa seguinte cresce.
- [ ] Ficha/texto com tempo de leitura (`garantir_leitura`).

## Trechos de filme
- [ ] `cortar_filmes.py` → olhar a folha `<trecho>_conferir.jpg` quadro a quadro: ícone de carregando, legenda
      gravada, letreiro, logo (Netflix), deformação da câmera lenta.
- [ ] Quadros repetidos da gravação de tela tirados (`mpdecimate`) e o trecho cobre a cena inteira: o motor NÃO pode
      desacelerar (o log "desacelerado" vira ERRO no revisar — trava na tela).
- [ ] Crédito em cima do quadro (embaixo a legenda cobre).

## Montagem
- [ ] Abertura: título do episódio ao lado do Vigia (`titulo_ep`), sem cartão que corta e volta.
- [ ] O Vigia entra e sai junto com a fusão do abrigo (motor), nunca de repente por cima da cena anterior.
- [ ] Uma cena por frase, sem corte rápido, saída lenta das cenas tensas.
- [ ] Sustos (liberados no Ep. 09 v3): silêncio antes, ameaça anunciada, rosto nunca mostrado, saída lenta depois.

## Som
- [ ] Trilha composta por parte (uma faixa por momento), checada contra "pancada" (`trilha/analisar.py`).
- [ ] Mix: poucos "aviso mix" (≤ 40 num episódio); música presente mas abaixo da voz.
