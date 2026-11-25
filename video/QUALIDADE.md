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
- [ ] **(24/11, usuário) Letras SEMPRE centralizadas e DENTRO do papel/placa/rolo** onde estão escritas (nunca encostando
      na borda, no brocado ou saindo do suporte). Título centralizado no elemento que ele acompanha.
- [ ] **Objetos na posição física certa:** carimbo desce RETO (vista de cima), exatamente sobre a marca que deixa; nada
      torto ou num ângulo impossível. Conferir em quadros parados (`--quadros`) antes de renderizar.

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

## Imagem certa para cada fala (24/11, Ep. 12)
- Usuário: "continua repetindo imagens mesmo falando de outros onis… analise isso de verdade pra que não fique acontecendo".
- Uma frase só pode CONTINUAR a imagem anterior se for a mesma obra. Assunto novo = imagem nova, mesmo que a cena fique curta.
- O motor (gerar.py) só absorve cena curta numa vizinha com a mesma obra.
- Todo rascunho roda `painel/ferramentas/auditar_imagens.py` (está no rascunho.sh): ler `previas/auditoria_imagens.txt`
  cena por cena (obra × palavras ditas) ANTES de mandar o vídeo, e justificar cada repetição que sobrar.
- Conferir também se a imagem PARECE outro yokai (ex.: a nure-onna-cobra parecia a rokurokubi de pescoço comprido).

## Telas, capítulos e trilha (25/11, Ep. 12 rascunho 3)
- **Tela preta (ficha) nunca em silêncio:** ela entra junto com a fala que diz aquilo, digitando no ritmo da voz.
- **Fim de capítulo tem gancho narrado** que puxa o próximo ("…e pode até virar um deus" → cartão "O demônio que
  virou deus"). Depois do gancho, 1 s de respiro com a música crescendo, e o cartão entra em fusão (nada de corte seco).
- **Música do cartão forte:** sem voz, a trilha sobe (não desce) e o cartão tem tema próprio.
- **Trilha o episódio inteiro, uniforme.** Silêncio só no momento mais necessário (um por episódio). O compositor mede a
  trilha e preenche sozinho qualquer trecho baixo demais (medir_buracos).
- **Legenda nunca em cima de texto da imagem:** quadro com texto deixa a faixa de baixo (y > 850) livre.
- **Referência a outro vídeo nosso:** usar a capa REAL (print do usuário), sem contagem de views.
