# Prompt para o ChatGPT: herói no tamanho certo do jogo

**O tamanho certo:** no jogo o herói tem **64 pixels de altura**, dentro de um quadro de **48 x 72 pixels**.
O ChatGPT não consegue desenhar tão pequeno, então pedimos tudo **8 vezes maior**: cada pixel do jogo
vira um quadradinho de 8 x 8 na imagem. Depois eu reduzo exatamente 8 vezes e fica nítido, sem perder nada.

## O que anexar

Estão na pasta `heroi_preparado/referencias_chatgpt/`:
- **`REF_1_heroi_tamanho_certo.png`**: o nosso herói parado nas 4 direções, **já no tamanho e na grade certos**
  (8 x 8 por pixel, 4 quadros lado a lado). Anexe **sempre**.
- **`REF_2_ferramentas_tamanho_certo.png`**: as 7 ferramentas no tamanho certo, ao lado do herói.
  Anexe **quando pedir ações com ferramenta**.

## Como fazer

1. Abra uma **conversa nova** no ChatGPT.
2. Anexe a REF_1 (e a REF_2, se for fazer ferramentas) e cole a **Mensagem 1** (as regras).
3. Depois mande **um pedido por mensagem** (Mensagens 2 em diante), sempre na mesma conversa.
   Cada imagem tem **4 quadros** da animação lado a lado.
4. Se uma imagem sair errada, use as **correções prontas** no fim deste arquivo.
5. Antes de me mandar, confira a **lista de conferência**.

---

## Mensagem 1: regras (cole uma vez, no começo)

```
Vou te pedir animações em pixel art do personagem principal do meu jogo de fazenda. A imagem
anexada (REF_1) é o personagem no TAMANHO E NA GRADE EXATOS que eu preciso. Siga estas regras em
TODAS as imagens desta conversa:

TAMANHO E GRADE (o mais importante):
1. Imagem de 1536 x 1024 px (deitada).
2. Cada pixel da arte é um quadrado de EXATAMENTE 8 x 8 px na imagem, todos do mesmo tamanho,
   alinhados numa grade que começa no canto de cima à esquerda. Nada de pixel pela metade, torto,
   deslocado ou de tamanho diferente. É exatamente o tamanho dos pixels da REF_1.
3. A imagem é dividida em 4 colunas iguais de 384 px (48 pixels de arte cada), como na REF_1.
   Um quadro da animação em cada coluna, centralizado nela. Os quadros não se encostam.
4. O personagem tem EXATAMENTE 512 px de altura (64 pixels de arte), da sola da bota até o topo
   do chapéu, igual na REF_1. Nunca maior, nunca menor, em nenhum quadro.
5. Os pés ficam todos na mesma linha: a sola da bota encosta na altura y = 784 px, como na REF_1.

PERSONAGEM E ESTILO:
6. Copie o personagem da REF_1 exatamente: mesmo rosto, cabelo castanho, chapéu de palha grande
   com faixa marrom, camisa azul com as mangas dobradas claras, calça marrom, botas marrons.
   Mesmas proporções: cabeça e chapéu grandes (estilo fofo), corpo curto. Não mude o desenho dele.
7. Use somente as cores que aparecem na REF_1. Não invente cores novas.
8. Contorno escuro de 1 pixel de arte em volta de tudo, marrom bem escuro (não preto puro),
   igual à REF_1. Luz vindo de cima à esquerda.
9. Pixel art de verdade: sem degradê suave, sem borrão, sem antisserrilhado (nenhum pixel de cor
   misturada na borda), sem pontilhado, sem brilho em volta do personagem.

FUNDO:
10. Fundo magenta puro e liso (#FF00FF) em toda a imagem, inclusive entre as pernas e entre o
    braço e o corpo. Sem sombra no chão, sem chão, sem texto, sem números, sem linhas de grade,
    sem moldura.
11. Nada de magenta, rosa ou roxo dentro do personagem (essa cor vai ser apagada).

ANIMAÇÃO:
12. É o mesmo personagem em todos os quadros, do mesmo tamanho. Só se mexe o que a pose pede.
    A cabeça e o chapéu não mudam de desenho; quando eu pedir, sobem ou descem só 1 pixel de arte.
13. Os 4 quadros de uma imagem são na mesma direção (de frente, de costas ou de lado), da esquerda
    para a direita na ordem que eu der.

Responda só "entendi" e espere o primeiro pedido.
```

---

## Andar (8 quadros por direção = 2 imagens por direção)

> Precisa de **de frente**, **de costas** e **para a direita**. Para a esquerda eu viro o da direita.

### Mensagem 2: andando de frente, quadros 1 a 4

```
Pedido: ANDANDO DE FRENTE (vindo na direção da câmera), quadros 1 a 4 de 8. Mesmas regras.
"Esquerda" e "direita" aqui são da imagem (de quem olha).

Quadro 1 (contato): o pé da ESQUERDA está à frente, apoiado inteiro, 1 pixel mais embaixo que o
outro. O pé da DIREITA está atrás, só com a ponta no chão. O braço da direita vai para a frente
(mão 2 pixels mais baixa) e o braço da esquerda vai para trás (mão 2 pixels mais alta, um pouco
escondida atrás do quadril).
Quadro 2 (descida): o peso está no pé da esquerda. O corpo inteiro (cabeça, chapéu e tronco) fica
1 pixel mais baixo. O pé da direita sai do chão.
Quadro 3 (passagem): o pé da direita está no ar passando ao lado do outro, com o joelho dobrado
(essa perna parece mais curta) e a bota 2 a 3 pixels acima do chão. O corpo volta à altura normal.
Os braços ficam quase retos ao lado do corpo.
Quadro 4 (subida): o pé da direita vai descendo para pisar à frente. Corpo na altura normal.
Os braços começam a trocar de lado.
```

### Mensagem 3: andando de frente, quadros 5 a 8

```
Agora os quadros 5 a 8 do ANDANDO DE FRENTE. São iguais aos quadros 1 a 4, só que trocando os
lados: no quadro 5 o pé da DIREITA está à frente e o da ESQUERDA atrás; o braço da esquerda vai
para a frente e o da direita para trás. Quadro 6: corpo 1 pixel mais baixo. Quadro 7: o pé da
esquerda passa no ar. Quadro 8: o pé da esquerda desce para pisar à frente.
```

### Mensagem 4: andando de costas, quadros 1 a 4

```
Pedido: ANDANDO DE COSTAS (indo para longe da câmera; vemos as costas, o chapéu por trás e o
cabelo), quadros 1 a 4 de 8. Mesmas regras. Use a segunda figura da REF_1 (de costas).

Quadro 1 (contato): o pé da DIREITA da imagem está à frente (indo para longe, então fica 1 pixel
mais ALTO na imagem), apoiado inteiro. O pé da ESQUERDA está atrás, só com a ponta no chão (aparece
um pouco da sola da bota). O braço da esquerda vai para a frente (sobe um pouco) e o da direita
vai para trás (desce um pouco).
Quadro 2 (descida): o corpo inteiro fica 1 pixel mais baixo. O pé da esquerda sai do chão
(aparece a sola).
Quadro 3 (passagem): o pé da esquerda passa no ar ao lado do outro, joelho dobrado, bota 2 a 3
pixels acima do chão. Corpo na altura normal. Braços quase retos.
Quadro 4 (subida): o pé da esquerda vai para a frente para pisar. Braços começando a trocar.
```

### Mensagem 5: andando de costas, quadros 5 a 8

```
Agora os quadros 5 a 8 do ANDANDO DE COSTAS: iguais aos 1 a 4 trocando os lados (no quadro 5 o pé
da ESQUERDA está à frente e o da DIREITA atrás; os braços trocam também). Quadro 6 com o corpo
1 pixel mais baixo; quadro 7 o pé da direita passa no ar; quadro 8 ele vai para a frente.
```

### Mensagem 6: andando para a direita, quadros 1 a 4

```
Pedido: ANDANDO PARA A DIREITA (de lado, olhando para a direita da imagem), quadros 1 a 4 de 8.
Mesmas regras. Use a terceira figura da REF_1 (de lado, olhando para a direita).
"Perna de perto" é a que está do nosso lado (mais visível); a "de longe" fica um pouco atrás e um
pouco mais escura. O mesmo vale para os braços.

Quadro 1 (contato): a perna de perto está à frente, esticada, com o calcanhar tocando o chão. A
perna de longe está atrás, só com a ponta do pé no chão. O braço de perto vai para trás e o braço
de longe vai para a frente.
Quadro 2 (descida): o pé da frente está plano no chão e o joelho dobra um pouco. O corpo inteiro
fica 1 pixel mais baixo. O pé de trás sai do chão.
Quadro 3 (passagem): a perna de perto está reta embaixo do corpo, segurando o peso. A perna de longe
passa no ar com o joelho dobrado. Braços ao lado do corpo. Corpo na altura normal.
Quadro 4 (subida): a perna de perto empurra (o calcanhar sobe) e a perna de longe vai para a
frente. Corpo na altura normal.
O corpo não anda para a frente dentro do quadro: o tronco fica sempre no meio da coluna e só as
pernas e os braços se mexem.
```

### Mensagem 7: andando para a direita, quadros 5 a 8

```
Agora os quadros 5 a 8 do ANDANDO PARA A DIREITA: iguais aos 1 a 4, mas agora é a perna de LONGE
que está à frente no quadro 5 (e a de perto atrás); os braços trocam também. Quadro 6 com o corpo
1 pixel mais baixo; quadro 7 a perna de perto passa no ar com o joelho dobrado; quadro 8 ela vai
para a frente.
```

---

## Ações com ferramenta (4 quadros por direção = 1 imagem por direção)

> Anexe também a **REF_2**. O jeito é o do Stardew Valley: levanta, desce rápido, bate e volta.
> Faça **de frente, de costas e para a direita** de cada ferramenta (a esquerda eu viro).
> **Sem terra, água, lascas, linha de pesca ou boia**: eu coloco esses efeitos depois.

### Mensagem 8: enxada de frente (modelo para as outras)

```
Pedido: USANDO A ENXADA, DE FRENTE (virado para a câmera), 4 quadros. Mesmas regras.
A enxada é EXATAMENTE a da REF_2 (mesmas cores, mesmo desenho e mesmo tamanho em relação ao
personagem: 40 pixels de arte de comprimento), segurada com as DUAS mãos no cabo, uma acima da outra.
Não desenhe terra voando.

Quadro 1 (levantar): os dois braços erguidos, as mãos juntas acima da cabeça segurando o cabo; a
enxada fica atrás da cabeça, em pé, e a lâmina aparece por cima do chapéu.
Quadro 2 (golpe): os braços descendo na frente do peito; a enxada vem para a frente, apontando
para a câmera (por isso parece curta), com a lâmina perto das mãos.
Quadro 3 (impacto): os braços esticados para baixo na frente do corpo, as mãos juntas na altura do
quadril; a enxada em pé na frente das pernas, com a lâmina vista de frente (larga) batendo no chão
logo abaixo e na frente dos pés. Joelhos um pouco dobrados: o corpo 1 pixel mais baixo.
Quadro 4 (voltar): igual ao quadro 3, mas a lâmina 2 pixels acima do chão e o corpo na altura normal.
```

### Mensagem 9: enxada de costas

```
Pedido: USANDO A ENXADA, DE COSTAS (de costas para a câmera), 4 quadros. Mesmas regras e mesma
enxada. Use a figura de costas da REF_1.

Quadro 1 (levantar): braços erguidos, as mãos atrás do chapéu (escondidas); a enxada cai por trás,
por cima das costas, com a lâmina no meio das costas (fica na frente do corpo, para a câmera).
Quadro 2 (golpe): a enxada passa por cima da cabeça indo para a frente: aparecem o cabo e a lâmina
por cima do chapéu, apontando para cima.
Quadro 3 (impacto): a enxada bate no chão na frente dele, escondida pelo corpo. Dos braços só
aparecem os cotovelos, um pouco para fora do corpo (as mãos estão na frente dele). Corpo 1 pixel
mais baixo.
Quadro 4 (voltar): igual ao 3, com o corpo na altura normal.
```

### Mensagem 10: enxada para a direita

```
Pedido: USANDO A ENXADA, OLHANDO PARA A DIREITA (de lado), 4 quadros. Mesmas regras e mesma enxada.
Use a figura de lado da REF_1 (olhando para a direita). Um pé um pouco à frente do outro, firme.

Quadro 1 (levantar): a enxada erguida acima da cabeça e um pouco para trás das costas, os braços
para cima; o corpo inclina 1 pixel para trás.
Quadro 2 (golpe): a enxada descendo na frente, os braços esticados para a frente na altura do peito.
Quadro 3 (impacto): a lâmina batendo no chão na frente dos pés; os braços esticados para baixo e
para a frente; o corpo inclina 1 pixel para a frente e fica 1 pixel mais baixo.
Quadro 4 (voltar): a lâmina 2 pixels acima do chão, corpo voltando ao normal.
```

### As outras ferramentas

Repita as Mensagens 8, 9 e 10 trocando a primeira linha e o que muda em cada uma:

- **PICARETA:** igual à enxada (a picareta da REF_2, 37 pixels de arte de comprimento). No impacto a
  ponta bate no chão.
- **MACHADO:** igual à enxada (o machado da REF_2, 35 pixels), mas no impacto a lâmina para na altura
  do joelho, como se batesse num tronco de árvore na frente dele (não bate no chão).
- **PÁ** (a pá da REF_2, 40 pixels): quadro 1 = a pá em pé na frente com a ponta no chão; quadro 2 =
  ele empurra e a lâmina entra na terra (corpo 1 pixel mais baixo); quadro 3 = ele levanta a pá com a
  lâmina na altura da cintura; quadro 4 = ele joga para o lado (a pá deitada para o lado, a lâmina virada).
- **FOICE** (a foice da REF_2, 21 pixels), **só com a mão direita do personagem**, a outra mão parada
  ao lado do corpo: quadro 1 = puxa a foice para trás, ao lado do quadril; quadro 2 = começa a passar baixo
  na frente; quadro 3 = corte, a foice passando bem baixo na frente dos pés, na altura do mato; quadro 4 =
  termina o movimento do outro lado.
- **REGADOR** (o regador da REF_2), **só com a mão direita do personagem, segurando pela alça de TRÁS**
  (não pela alça de cima), do lado de fora do corpo, com o bico para fora: quadro 1 = segurando em pé;
  quadro 2 = começando a inclinar; quadros 3 e 4 = inclinado, bico para baixo, regando (sem desenhar água).
- **VARA DE PESCAR** (a vara da REF_2, 50 pixels), com as duas mãos, **sem linha e sem boia**.
  Duas imagens:
  - imagem A = segurar (a vara em pé ao lado do corpo), recuar (a vara para trás da cabeça), lançar
    (a vara vindo para a frente) e soltar (a vara apontando para a frente, onde está a água);
  - imagem B = esperar (parado, a vara apontando para a água), esperar com a ponta 1 pixel mais
    baixa, fisgar (puxa a vara para cima, para trás) e recolher (a vara de novo para a frente).
  De frente a água fica na frente dele, embaixo na imagem; de costas fica longe, em cima na imagem;
  de lado fica à direita.

---

## Correções prontas (se a imagem sair errada)

- Pixels borrados ou de tamanhos diferentes:
  `Os pixels saíram de tamanhos diferentes ou borrados. Refaça com cada pixel da arte sendo um quadrado exato de 8 x 8 px, todos do mesmo tamanho, sem borrão e sem cores misturadas nas bordas, igual à REF_1.`
- Personagem grande ou pequeno demais:
  `O personagem ficou do tamanho errado. Ele precisa ter exatamente 512 px de altura (64 pixels de arte), da sola até o topo do chapéu, igual à REF_1. Refaça.`
- O personagem mudou (rosto, roupa, proporção):
  `O personagem mudou. Copie exatamente o da REF_1: mesmo rosto, chapéu, camisa, calça, botas, cores e proporções. Refaça.`
- Os pés em alturas diferentes:
  `Os pés dos quadros estão em alturas diferentes. A sola de todos os quadros tem que encostar na mesma linha (y = 784 px). Refaça.`
- Os quadros grudados ou fora das colunas:
  `Os quadros têm que ficar separados, um no meio de cada uma das 4 colunas de 384 px. Refaça.`
- Sombra, chão, texto ou grade:
  `Tire a sombra, o chão, o texto e as linhas. O fundo tem que ser só magenta liso #FF00FF. Refaça.`
- A ferramenta diferente da REF_2:
  `A ferramenta tem que ser exatamente a da REF_2 (mesmo desenho, cores e tamanho). Refaça.`

## Lista de conferência (antes de me mandar)

- [ ] Com zoom, os pixels parecem quadradinhos todos do mesmo tamanho (não borrados).
- [ ] O fundo é magenta liso em tudo, sem sombra, chão, texto ou linhas.
- [ ] São 4 quadros separados, um em cada quarto da imagem.
- [ ] Nos 4 quadros o personagem tem a mesma altura e os pés ficam na mesma linha.
- [ ] É o nosso herói (chapéu, camisa azul, calça e botas marrons, cabeça grande).
- [ ] A ordem dos quadros é a que foi pedida.
- [ ] Nas ações: a ferramenta é a da REF_2 e está na mão certa.

**Não precisa sair perfeito:** se o tamanho ou a grade ficarem só um pouco fora, eu corrijo na hora
de reduzir. O que eu não consigo consertar é personagem diferente, borrão forte ou quadros de tamanhos
muito diferentes.

## O que me mandar

As imagens na ordem, dizendo o que é cada uma (por exemplo: "andar de frente 1 a 4"). Eu reduzo
(cada 8 x 8 vira 1 pixel), limpo as cores com a paleta do herói, coloco o pivô nos pés, ajusto o tempo
dos quadros, monto o atlas e testo no Godot antes de te mostrar.
